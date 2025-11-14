import inspect
import logging
import math
import os
import re
import time
import warnings
from base64 import b64encode
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime
from enum import Enum
from functools import reduce, wraps
from json.decoder import JSONDecodeError
from pprint import pformat
from time import sleep
from typing import TYPE_CHECKING, Any, TypeVar

import humps
from pypika import Query
from requests import Response

from mstrio import config
from mstrio.helpers import (
    IServerError,
    MstrTimeoutError,
    PromptedContentError,
    VersionException,
)
from mstrio.types import ObjectSubTypes
from mstrio.utils.dict_filter import filter_list_of_dicts
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.time_helper import (
    DatetimeFormats,
    map_datetime_to_str,
    map_str_to_datetime,
)

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.modeling.expression import Expression
    from mstrio.object_management import SearchPattern  # noqa: F401
    from mstrio.project_objects.datasets import OlapCube, SuperCube
    from mstrio.server import Project
    from mstrio.types import ObjectTypes  # noqa: F401
    from mstrio.users_and_groups import User
    from mstrio.utils.entity import EntityBase

logger = logging.getLogger(__name__)


def deprecation_warning(
    deprecated: str,
    new: str | None,
    version: str,
    module: bool = True,
    change_compatible_immediately: bool = True,
):
    """This function is used to provide a user with a warning, that a given
    functionality is now deprecated, and won't be supported from a given
    version.

    Args:
        deprecated (str): name of a functionality that is deprecated
        new (str): name of a functionality that replaces deprecated one
        version (str): version from which deprecated functionality won't be
            supported
        module (bool, optional): Whether deprecated functionality is a module.
        Defaults to True.
        change_compatible_immediately (bool, optional): Whether the new
        functionality can be used immediately. Defaults to True.
    """

    module = " module" if module else ""
    if change_compatible_immediately:
        msg = (
            f"{deprecated}{module} is deprecated and will not be supported starting "
            f"from mstrio-py {version}."
        )
        if new:
            msg += f" Please use {new} instead."
    else:
        suffix = f" and replaced with {new}" if new else ""
        msg = f"From version {version} {deprecated}{module} will be removed{suffix}."

    ASSIGN_WARNING_TO_ACTUAL_DEPRECATED_SOURCE_AND_NOT_CALLER__MAGIC_INT = 1
    exception_handler(
        msg=msg,
        exception_type=DeprecationWarning,
        stack_lvl=ASSIGN_WARNING_TO_ACTUAL_DEPRECATED_SOURCE_AND_NOT_CALLER__MAGIC_INT,
    )


def url_check(url):
    """Checks the validity of the url required in the connection object and
    returns a validated url."""
    regex = r'^https?://.+$'
    match = re.search(regex, url)
    api_index = url.find('/api')

    if match is None:
        msg = (
            "Please check the validity of the base_url parameter. Typically of the "
            "form 'https://<<MSTR Domain>>/MicroStrategyLibrary/'"
        )
        raise ValueError(msg)
    if api_index != -1:
        url = url[:api_index]
    if url.endswith('/'):
        url = url[:-1]

    return url


def version_cut(version):
    res = ".".join([str(int(i)) for i in version.split(".")])
    return res[:-2]


def get_args_from_func(func: Callable[[Any], Any]):
    signature = inspect.signature(func)
    return list(signature.parameters.keys())


def get_default_args_from_func(func: Callable[[Any], Any]):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def camel_to_snake(
    response: dict | list,
    whitelist: list[str] = None,
) -> dict | list[dict]:
    """Converts dictionary keys from camelCase to snake_case.
    It works recursively for dicts in dicts."""

    whitelist = whitelist or []

    def convert_dict(source):
        return {
            humps.decamelize(key): (
                value
                if not isinstance(value, dict) or key in whitelist
                else convert_dict(value)
            )
            for key, value in source.items()
        }

    if isinstance(response, list):
        return [convert_dict(source) for source in response if isinstance(source, dict)]
    elif isinstance(response, dict):
        return convert_dict(response)

    raise ValueError("Not supported data type for camel_to_snake conversion")


def snake_to_camel(
    response: dict | list,
    whitelist: list[str] = None,
) -> dict | list[dict]:
    """Converts dictionary keys from snake_case to camelCase.
    It works recursively for dicts in dicts."""
    whitelist = whitelist or []

    def convert_dict(source):
        return {
            humps.camelize(key): (
                value
                if not isinstance(value, dict) or key in whitelist
                else convert_dict(value)
            )
            for key, value in source.items()
        }

    if isinstance(response, list):
        return [convert_dict(source) for source in response if isinstance(source, dict)]
    elif isinstance(response, dict):
        return convert_dict(response)

    raise ValueError("Not supported data type for snake_to_camel conversion")


def check_duplicated_column_names(data_frame):
    list_of_columns = list(data_frame.columns)
    return len(list_of_columns) == len(set(list_of_columns))


def exception_handler(
    msg: str, exception_type: type[Exception] = Exception, stack_lvl: int = 2
):
    """Generic error message handler.

    Args:
        msg (str): Message to print in the Exception or Warning
        exception_type (Exception): Instance of Exception or Warning class
        stack_lvl (int, optional): controls how deep the stacktrace will be
    """
    if not isinstance(exception_type, type) or not issubclass(
        exception_type, Exception
    ):
        raise ValueError("exception_type has to be a subclass of Exception class")
    elif issubclass(exception_type, Exception) and not issubclass(
        exception_type, Warning
    ):
        raise exception_type(msg)
    elif issubclass(exception_type, Warning):
        warnings.warn(message=msg, category=exception_type, stacklevel=stack_lvl)


def response_handler(
    response: 'Response',
    msg: str | None = None,
    throw_error: bool = True,
    verbose: bool = True,
    whitelist: list | None = None,
):
    """Generic error message handler for transactions against I-Server.

    Args:
        response: Response object returned by HTTP request.
        msg (str, optional): Message to print in addition to any
            server-generated error message(s).
        throw_error (bool, optional): Flag indicates if the error should
            be thrown (defaults to True).
        verbose (bool, optional): controls if messages/errors will be printed
            (defaults to True).
        whitelist(list, optional): list of tuples of I-Server Error and
            HTTP errors codes respectively (you may add optional third value
            as string, representing message that the error need to contain to
            be whitelisted), which will not be handled (defaults to None).
            i.e. whitelist = [
                ('ERR001', 500),('ERR004', 404),('ERR003', 403, 'not allowed')
            ]
    """
    whitelist = whitelist or []

    try:
        logger.debug(f"{response} url = '{response.url}'")
        logger.debug(f"headers = {pformat(response.headers)}")
        logger.debug(f"content = {response.text}")

        if (
            response.ok
            and response.text == ''
            and (200 < response.status_code < 300 or response.request.method == 'HEAD')
        ):
            # we can expect empty response body and it's fine
            return

        res: dict | list = response.json()

        if response.ok:
            return

        if res.get('errors') is not None:
            res = res.get('errors')
            if len(res) > 0:
                res = res[0]
            else:
                res = {}

        server_code = res.get('code')
        server_msg = res.get('message')
        ticket_id = res.get('ticketId')
        iserver_code = res.get('iServerCode')

        def check_if_whitelisted():
            if not whitelist:
                return False
            for item in whitelist:
                if len(item) == 2:
                    code, http_code = item
                    if (server_code, response.status_code) == (code, http_code):
                        return True
                elif len(item) == 3:
                    code, http_code, part_of_msg = item
                    if (server_code, response.status_code) == (
                        code,
                        http_code,
                    ) and part_of_msg in server_msg:
                        return True
            return False

        if not check_if_whitelisted():
            if (
                server_code == 'ERR004'
                and response.status_code == 404
                and server_msg == 'HTTP 404 Not Found'
            ) or (
                server_code == 'ERR001'
                and response.status_code == 405
                and server_msg == 'HTTP 405 Method Not Allowed'
            ):
                msg = (
                    "This REST API functionality is not supported on this version "
                    f"of the I-Server: {version_cut(config.iserver_version)}."
                )
                exception_handler(msg, exception_type=VersionException)
            elif iserver_code == -2147206497:  # MSI_REQUEST_TIMEOUT on server-side
                raise MstrTimeoutError(res)
            elif iserver_code == -2147468903:
                raise PromptedContentError(
                    'Prompted content subscription creation is not supported.'
                )
            if verbose:
                logger.error(
                    (f'{msg}\n' if msg else '')
                    + f'I-Server Error {server_code}, {server_msg}\n'
                    f'Ticket ID: {ticket_id}'
                )
            if throw_error and server_code:
                raise IServerError(
                    message=(
                        f"{server_msg}; code: '{server_code}', ticket_id: '{ticket_id}'"
                    ),
                    http_code=response.status_code,
                )
    except JSONDecodeError:
        logger.debug(f"Response body: {response.text}")

        if verbose:
            logger.error(
                (f"{msg}\n" if msg else '')
                + "Could not decode the response from the I-Server. Please check if "
                "I-Server is running correctly"
            )
            # raise error if I-Server response cannot be decoded
            if throw_error:
                response.raise_for_status()


def get_response_json(response: 'Response', /, **kwargs) -> dict:
    """Get JSON from response object in a safe, error-handled way.

    Under the hood, it uses `response_handler` to handle errors but returns
    simply `response.json()` if the response is OK.

    Args:
        response: Response object returned by HTTP request.
        **kwargs: Additional arguments to pass to `response_handler`.

    Returns:
        dict: Parsed JSON from the response.
    """
    if not response.ok:
        response_handler(response, **kwargs)
        # if `response_handler` does not raise an error, it means
        # we want to fall through and return the JSON,
        # even if the response is not OK.

    return response.json()


def fallback_on_timeout(min_limit: int = 50):
    """Return a decorator, which decorates a function with one argument,
    `limit`, to retry with half as big limit if it encounters a timeout error.

    Do note that the wrapped function will return a (result, working_limit)
    tuple, not just the result, to allow for using the working limit further.

    Args:
        min_limit: The minimum limit that will be attempted as retry. If the
            wrapper recurses past it, it will just raise the error back.
    """

    def decorate(func: Callable[[int], Any]):
        """Replaces `fot_wrapper`'s __name__, __doc__ and __module__ with those
        of `func`."""

        @wraps(func)
        def fot_wrapper(limit: int) -> tuple[Any, int]:
            try:
                return func(limit), limit
            except MstrTimeoutError as err:
                new_limit = limit // 2
                if new_limit >= min_limit:
                    logger.warning(
                        f"Timeout hit when executing {func.__name__} with limit "
                        f"{limit}, retrying with limit {new_limit}"
                    )
                    return fot_wrapper(new_limit)
                else:
                    raise err

        return fot_wrapper

    return decorate


def get_parallel_number(total_chunks):
    """Returns the optimal number of threads to be used for downloading
    cubes/reports in parallel."""

    threads = min(8, os.cpu_count() + 4)
    if total_chunks > 0:
        threads = min(total_chunks, threads)

    return threads


def _prepare_objects(
    objects: dict | list[dict],
    filters: dict | None = None,
    dict_unpack_value: str | None = None,
    project_id: str | None = None,
):
    if isinstance(objects, dict) and dict_unpack_value:
        objects = objects[dict_unpack_value]
    objects = camel_to_snake(objects)
    if filters:
        objects = filter_list_of_dicts(objects, **filters)  # type: ignore
    if project_id:
        for obj in objects:
            obj.setdefault('project_id', project_id)
    return objects


def get_total_count_of_objects(
    source: Callable[["Connection", int], Response] | Response,
    connection: "Connection | None" = None,
    **kwargs: Any,
) -> int:
    """Get total count of objects from server Response object
    or getter returning server Response object.

    Args:
        source: GET API wrapper function that will return a Response object
            (fn accepting `limit` parameter) or Response object with
            the total count in headers
        connection: Strategy One REST API connection object if `source`
            is a callable.
        **kwargs: additional parameters to pass to the `source` function if it
            is a callable

    Returns:
        int: total count of objects
    """
    # circular import prevention
    from mstrio.connection import Connection
    from mstrio.utils.api_helpers import is_response_like

    HEADER_KEY = 'x-mstr-total-count'

    if is_response_like(source):
        assert HEADER_KEY in source.headers, (
            f"Response headers do not contain '{HEADER_KEY}' entry. "
            "Cannot get total count of objects from this response."
        )
        v = source.headers.get(HEADER_KEY)
        assert isinstance(v, int) or (
            isinstance(v, str) and v.isnumeric()
        ), f"Expected '{HEADER_KEY}' header to be numerical, got {v}."
        return int(v)

    if callable(source):
        kwargs.pop('limit', None)  # limit for count is forced in this fn

        assert isinstance(connection, Connection), (
            "Expected 'connection' to be a Connection object when 'source' "
            "is a callable."
        )
        return get_total_count_of_objects(
            source=source(connection, limit=1, **kwargs),
            connection=connection,
        )

    raise TypeError(
        f"Expected 'source' to be a Response object or a callable, got {type(source)}"
    )


def fetch_objects_async(
    connection: "Connection",
    api: Callable,
    async_api: Callable,
    limit: int | None,
    chunk_size: int,
    filters: dict,
    error_msg: str | None = None,
    dict_unpack_value: str | None = None,
    **kwargs,
) -> list:
    """Get all objects asynchronously. Optionally filter the objects using
    `filters` parameter. Works only for endpoints with `limit` and `offset`
    query parameter (pagination).

    Args:
        connection: Strategy One REST API connection object
        api: GET API wrapper function that will return list of objects in bulk
        async_api: asynchronous wrapper of the `api` function
        dict_unpack_value: if the response needs to be unpacked to get into
            the values, specify the keyword
        limit: cut-off value for the number of objects returned
        chunk_size: number of objects in each chunk
        error_msg: specifies error_msg for failed requests
        **filters: dict that specifies filter expressions by which objects will
            be filtered locally
        kwargs: all specific parameters that the api methods require that need
            to be additionally specified
    """
    validate_param_value('limit', limit, int, min_val=1, special_values=[None])
    offset = 0
    chunk_size = min(limit, chunk_size) if limit else chunk_size
    all_objects = []

    # Extract parameters of the api wrapper and set them using the kwargs
    args = get_args_from_func(api)
    param_value_dict = {
        arg: kwargs.get(arg)
        for arg in args
        if arg not in ['connection', 'limit', 'offset', 'error_msg']
    }
    response = api(
        connection=connection,
        offset=offset,
        limit=chunk_size,
        error_msg=error_msg,
        **param_value_dict,
    )
    project_id = kwargs.get('project_id') or kwargs.get('project')
    objects = _prepare_objects(response.json(), filters, dict_unpack_value, project_id)
    all_objects.extend(objects)
    current_count = offset + chunk_size
    total_objects = get_total_count_of_objects(response)
    total_objects = min(limit, total_objects) if limit else total_objects

    if total_objects > current_count:
        it_total = math.ceil(total_objects / chunk_size)
        threads = get_parallel_number(it_total)
        with FuturesSessionWithRenewal(
            connection=connection, max_workers=threads
        ) as session:
            # Extract parameters of the api wrapper and set them using kwargs
            param_value_dict = auto_match_args(
                api,
                kwargs,
                exclude=[
                    'connection',
                    'limit',
                    'offset',
                    'future_session',
                    'error_msg',
                ],
            )
            futures = [
                async_api(
                    future_session=session,
                    offset=offset,
                    limit=chunk_size,
                    **param_value_dict,
                )
                for offset in range(current_count, total_objects, chunk_size)
            ]

        for f in futures:
            response = f.result()
            if not response.ok:
                response_handler(response, error_msg, throw_error=False)
                continue
            objects = _prepare_objects(
                response.json(), filters, dict_unpack_value, project_id
            )
            all_objects.extend(objects)
    return all_objects


def fetch_objects(
    connection: "Connection",
    api: Callable,
    limit: int | None,
    filters: dict,
    error_msg: str | None = None,
    dict_unpack_value: str | None = None,
    **kwargs,
) -> list:
    """Fetch and prepare objects. Optionally filter the objects by using the
    filters parameter. This function only supports endpoints without pagination.

    Args:
        connection: Strategy One REST API connection object
        api: GET API wrapper function that will return list of objects in bulk
        dict_unpack_value: if the response needs to be unpacked to get into
            the values specify the keyword
        limit: value to be provided in REST request to limit count of
            returned objects
        error_msg: specifies error_msg for failed requests
        **filters: dict that specifies filter expressions by which objects will
            be filtered locally
        kwargs: all specific parameters that the api methods require that need
            to be additionally specified
    """
    validate_param_value('limit', limit, int, min_val=1, special_values=[None])

    # Extract parameters of the api wrapper and set them using kwargs
    dic = {**kwargs}
    if limit is not None:
        dic['limit'] = limit  # yes, overwrite if exists

    param_value_dict = auto_match_args(api, dic, exclude=['connection', 'error_msg'])
    response = api(connection=connection, error_msg=error_msg, **param_value_dict)

    if response.ok:
        project_id = kwargs.get('project_id') or kwargs.get('project')
        objects = _prepare_objects(
            response.json(), filters, dict_unpack_value, project_id
        )
        if limit is not None:
            # If response returned more than `limit` objects -> cut-off.
            # This can happen if limiting is done ex. per node.
            # Some endpoints return `limit` objects PER NODE.
            # We don't validate: just get first `limit` amount of them.
            objects = objects[:limit]
        return objects
    else:
        return []


def key_fn_for_sort_object_properties(source: Any) -> int:
    """Sort all properties of an object representing an MSTR object."""
    preferred_order = {
        'id': 1,
        'name': 2,
        'description': 3,
        'alias': 4,
        'type': 5,
        'subtype': 6,
        'ext_type': 7,
        'acg': 101,
        'acl': 102,
    }
    return preferred_order.get(source, 50)


def auto_match_args(
    func: Callable,
    param_dict: dict,
    exclude: list | None = None,
    include_defaults: bool = True,
    id_weak_match: bool = False,
) -> dict:
    """Automatically match dict data to function arguments.

    Handles default parameters. Extracts value from Enums. Returns matched
    arguments as dict.

    Note:
        don't use it for alter purposes as, changing parameter value
        back to default currently doesn't work (Rework line 413?)

    Args:
        func: function for which args will be matched
        param_dict: dict to use for matching the function args
        exclude: set `exclude` parameter to exclude specific param-value pairs
        include_defaults: if `False` then values which have the same value as
            default will not be included in the result
        id_weak_match: if `True`, the function will try to match IDs even if
            they are not exact (e.g. by ignoring certain prefixes)
    Raises:
        KeyError: could not match all required arguments
    """

    exclude = exclude or []
    args = get_args_from_func(func)
    default_dict = get_default_args_from_func(func)

    param_value_dict = {}
    for arg in args:
        if arg in exclude:
            continue

        val = get_val_safely(param_dict, arg, default_dict)
        if not include_defaults and arg in default_dict and val == default_dict[arg]:
            continue

        if (
            id_weak_match
            and val is None
            and arg != 'project_id'
            and arg.endswith('_id')
        ):
            val = get_val_safely(param_dict, 'id', default_dict)

        val = val.value if isinstance(val, Enum) else val
        param_value_dict.update({arg: val})

    return param_value_dict


def get_val_safely(param_dict: dict, key: str, default_dict: dict) -> Any:
    """Safely get a value from a dictionary."""
    return (
        param_dict.get(key)
        if param_dict.get(key) is not None
        else default_dict.get(key)
    )


def flatten2list(object) -> list:
    """Flatten to list nested objects of type list, tuple, sets."""
    gather = []
    for item in object:
        if isinstance(item, (list, tuple, set)):
            gather.extend(flatten2list(item))
        else:
            gather.append(item)
    return gather


def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = {o for o in intersect_keys if d1[o] == d2[o]}
    return added, removed, modified, same


def __validate_single_param_value(
    value,
    param_name,
    data_type,
    max_val,
    min_val,
    regex,
    valid_example,
    inv_val,
    special_values=None,
):
    special_values = special_values or []
    if value in special_values:
        return True

    if max_val is not None and value > max_val:
        msg = f"'{param_name}' has to be less than or equal to {max_val}"
        exception_handler(msg, inv_val)
        return False
    elif min_val is not None and value < min_val:
        msg = f"'{param_name}' has to be greater than or equal to {min_val}"
        exception_handler(msg, inv_val)
        return False
    elif regex is not None and not re.match(regex, value):
        pattern = valid_example or regex
        msg = f"'{param_name}' has to match pattern '{pattern}'"
        exception_handler(msg, inv_val)
        return False
    elif (
        all(cond is None for cond in [max_val, min_val, regex])
        and special_values
        and str not in data_type
    ):
        msg = f"'{param_name}' has to be one of {special_values}"
        exception_handler(msg, inv_val)
        return False
    return True


def validate_param_value(
    param_name,
    param_val,
    data_type,
    max_val=None,
    min_val=None,
    special_values=None,
    regex=None,
    exception=True,
    valid_example=None,
) -> bool:
    """Validate param data type and optionally max, min special values.

    Raise:
        TypeError
        ValueError
    """
    special_values = special_values or []
    inv_type = TypeError if exception else Warning
    inv_val = ValueError if exception else Warning
    data_type = data_type if isinstance(data_type, list) else [data_type]

    if any(x == param_val and isinstance(x, type(param_val)) for x in special_values):
        return True

    if type(param_val) not in data_type:
        msg = f"'{param_name}' needs to be of type {data_type}"
        exception_handler(msg, inv_type)
        return False
    if isinstance(param_val, list):
        return all(
            __validate_single_param_value(
                value,
                param_name,
                data_type,
                max_val,
                min_val,
                regex,
                valid_example,
                inv_val,
                special_values,
            )
            for value in param_val
        )

    return __validate_single_param_value(
        param_val,
        param_name,
        data_type,
        max_val,
        min_val,
        regex,
        valid_example,
        inv_val,
        special_values,
    )


def extract_all_dict_values(list_of_dicts: list[dict]) -> list[Any]:
    """Extract list of dicts values into list."""
    all_options = []
    for option in list_of_dicts:
        all_options.extend(option.values())
    return all_options


def delete_none_values(
    source: dict, *, whitelist_attributes: list | None = None, recursion: bool
) -> dict:
    """Delete keys with None values from dictionary.

    Args:
        source (dict): dict object from which none values will be deleted
        whitelist_attributes (list): keyword-only argument containing name
            of attribute, which should be left alone even if they contain
            none values
        recursion (bool): flag that turns recursion on or off
    """
    whitelist = whitelist_attributes or []

    new_dict = {}
    for key, value in source.items():
        if recursion and isinstance(value, dict):
            new_dict[key] = delete_none_values(
                value, whitelist_attributes=whitelist, recursion=recursion
            )
        elif value not in [[], {}, None] or key in whitelist:
            new_dict[key] = value

    return new_dict


def get_objects_id(obj, obj_class):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, obj_class):
        return obj.id
    return None


def merge_id_and_type(
    object_id: str,
    object_type: 'ObjectTypes | ObjectSubTypes | int',
    error_msg: str | None = None,
) -> str:
    if not object_id or not object_type:
        exception_handler(
            msg=error_msg or "Please provide both `id` and `type`.",
            exception_type=AttributeError,
        )
    object_id = get_objects_id(object_id, type(object_id))
    object_type = (
        get_enum_val(object_type, type(object_type))
        if isinstance(object_type, Enum)
        else object_type
    )
    return f'{object_id};{object_type}'


def rsetattr(obj, attr, val):
    """Recursive setattr. This can only modify last attr in the chain.
    For example rsetattr(obj, 'attr1.attr2.attr3', new_value) won't work
    if attr2 doesn't exist.

    Args:
        obj: An object that is edited
        attr: attribute name chain/path
        val: new value
    Returns:
        None on success
    Raises:
        AttributeError on failure, when the 'attr' is incorrect
    Example:
        rsetattr(obj, 'attr1.attr2', new_value)
    """

    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *default):
    """Recursive getattr. Third parameter is the default value.

    Args:
        obj: An object that is inspected
        attr: attribute name chain/path
        default (optional): value returned if 'attr' not found
    Returns:
        value of 'attr' on success. On failure, default value.
    Raises:
        AttributeError on failure, when the 'attr' is incorrect
        and no default provided
    Example:
        rgetattr(obj, 'attr1.attr2', 'default value')
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *default)

    return reduce(_getattr, [obj] + attr.split('.'))


def filter_params_for_func(
    func: Callable, params: dict, exclude: list | None = None
) -> dict:
    """Filter dict of parameters and return only those that are parameters
    of a `func`.
    Mainly used in `EntityBase.alter()`, before calling
    `EntityBase._alter_properties()` as shown in `Example`.

    Args:
        func: a function that the params are going to be fit for
        params: a dict with parameters that will be filtered
        exclude: set `exclude` parameter to exclude specific param-value pairs
    Returns:
        a dict with parameters of `func` that exist in `params` dict
    Example:
        params = filter_params_for_func(self.alter, locals())
        self._alter_properties(**params)
    """
    args = get_args_from_func(func)
    defaults_dict = get_default_args_from_func(func)
    exclude = exclude or []
    properties = {}

    for arg in args:
        if arg in exclude:
            continue
        elif params.get(arg) is not None:
            properties.update({arg: params.get(arg)})
        elif defaults_dict.get(arg) is not None:
            properties.update({arg: defaults_dict.get(arg)})
    return properties


T = TypeVar("T")


def filter_obj_list(obj_list: list[T], **filters: dict[str, Any]) -> list[T]:
    """
    Filter a list of objects by providing one or more key-value pair filters.
    """
    return [
        obj for obj in obj_list if all(getattr(obj, f) == v for f, v in filters.items())
    ]


def choose_cube(
    connection: 'Connection', cube_dict: dict
) -> 'OlapCube | SuperCube | None':
    """Return correct cube object based on dictionary with cube's info.

    Note: In case of wrong subtype, `None` is returned.
    """
    cube_subtype = cube_dict['subtype']
    if cube_subtype == ObjectSubTypes.OLAP_CUBE.value:
        from mstrio.project_objects.datasets.olap_cube import OlapCube

        return OlapCube.from_dict(cube_dict, connection)
    elif cube_subtype == ObjectSubTypes.SUPER_CUBE.value:
        from mstrio.project_objects.datasets.super_cube import SuperCube

        return SuperCube.from_dict(cube_dict, connection)


def get_temp_connection(
    connection: "Connection",
    project_id: str | None = None,
) -> "Connection":
    """Return a temporary connection object with a selected project.

    Args:
        connection: Strategy One connection object
        project_id: Project ID
    """
    temp_conn = deepcopy(connection)
    temp_conn.select_project(project_id=project_id)
    return temp_conn


class Dictable:
    """The fundamental class in mstrio-py package. Includes support for
    converting an object to a dictionary, and creating an object from a
    dictionary."""

    _FROM_DICT_MAP: dict[str, Callable] = {}  # map attributes to Enums and components
    # list of attribute name, which are allowed to have none values
    # in dict returned by .to_dict()
    _ALLOW_NONE_ATTRIBUTES: list[str] = []
    _KEEP_CAMEL_CASE: list[str] = []

    @classmethod
    def _unpack_objects(cls, key, val, camel_case=True):
        """Unpack Enums, Dictable obj, list of Enums"""
        if isinstance(val, datetime):
            return map_datetime_to_str(key, val, cls._FROM_DICT_MAP)
        elif isinstance(val, Enum):
            return val.value
        elif isinstance(val, Dictable):
            return val.to_dict(camel_case)
        elif isinstance(val, list):
            return [cls._unpack_objects(key, v, camel_case) for v in val]
        return val

    @classmethod
    def _dict_to_obj(cls, connection, val, key):
        def constructor():
            if isinstance(cls._FROM_DICT_MAP[key], DatetimeFormats):
                return map_str_to_datetime(key, val, cls._FROM_DICT_MAP)
            elif isinstance(cls._FROM_DICT_MAP[key], type(Enum)):
                return cls._FROM_DICT_MAP[key](val)
            elif isinstance(cls._FROM_DICT_MAP[key], type(Dictable)):
                return cls._FROM_DICT_MAP[key].from_dict(val)
            elif isinstance(cls._FROM_DICT_MAP[key], list):
                if isinstance(cls._FROM_DICT_MAP[key][0], list):
                    # for: List[List[handling_cls]]
                    handling_cls = cls._FROM_DICT_MAP[key][0][0]
                    return [[handling_cls.from_dict(item) for item in v] for v in val]
                elif (
                    all(isinstance(v, type(Enum)) for v in cls._FROM_DICT_MAP[key])
                    and val is not None
                ):
                    return [cls._FROM_DICT_MAP[key][0](v) for v in val]
                elif all(
                    isinstance(v, type(Dictable)) for v in cls._FROM_DICT_MAP[key]
                ):
                    return [cls._FROM_DICT_MAP[key][0].from_dict(v) for v in val]
                elif callable(cls._FROM_DICT_MAP[key][0]):
                    return [cls._FROM_DICT_MAP[key][0](v, connection) for v in val]
            else:
                return cls._FROM_DICT_MAP[key](val, connection)

        return val if key not in cls._FROM_DICT_MAP else constructor()

    def to_dict(self, camel_case: bool = True) -> dict:
        """Converts an object to a dictionary excluding object's private
        properties. When converting the object to a dictionary, the object's
        attributes become the dictionary's keys and are in camel case by default
        Attribute values stored as objects are automatically converted to
        non-/ primitive data structures.

        Args:
            camel_case (bool, optional): Set to True if attribute names should
                be converted from snake case to camel case. Defaults to True.

        Returns:
            dict: A dictionary representation of object's attributes and values.
                By default, the dictionary keys are in camel case.
        """

        hidden_keys = [
            '_fetched_attributes',
            '_altered_properties',
            '_connection',
            'connection',
            '_type',
            '_WITH_MISSING_VALUE',
        ]
        cleaned_dict = self.__dict__.copy()

        properties = get_object_properties(self)
        for prop in properties:
            to_be_deleted = '_' + prop
            cleaned_dict[prop] = cleaned_dict.pop(to_be_deleted, None)
        result = {
            key: self._unpack_objects(key, val, camel_case)
            for key, val in cleaned_dict.items()
            if key not in hidden_keys
        }

        result = delete_none_values(
            result, whitelist_attributes=self._ALLOW_NONE_ATTRIBUTES, recursion=False
        )
        result = {
            key: result[key]
            for key in sorted(result, key=key_fn_for_sort_object_properties)
        }
        return (
            snake_to_camel(result, whitelist=self._KEEP_CAMEL_CASE)
            if camel_case
            else result
        )

    @classmethod
    def from_dict(
        cls: T,
        source: dict[str, Any],
        connection: 'Connection | None' = None,
        to_snake_case: bool = True,
        with_missing_value: bool = False,
    ) -> T:
        """Creates an object from a dictionary. The dictionary's keys in camel
        case are changed to object's attribute names (by default in snake case)
        and dict values are composed to their proper data types such as Enums,
        list of Enums etc. as specified in _FROM_DICT_MAP.

        Args:
            cls (T): Class (type) of an object that should be created.
            source (Dict[str, Any]): A dictionary from which an object will be
                constructed.
            connection (Connection, optional): A MSTR Connection object.
                Defaults to None.
            to_snake_case (bool, optional): Set to True if attribute names
                should be converted from camel case to snake case. Defaults to
                True.
            with_missing_value: (bool, optional): If True, class attributes
                possible to fetch and missing in `source` will be set as
                `MissingValue` objects.

        Returns:
            T: An object of type T.
        """
        object_source = (
            camel_to_snake(source, whitelist=cls._KEEP_CAMEL_CASE)
            if to_snake_case
            else source
        )

        if connection is not None:
            object_source["connection"] = connection

        args = {
            key: cls._dict_to_obj(connection, val, key)
            for key, val in object_source.items()
            if key in cls.__init__.__code__.co_varnames
        }
        obj = cls(**args)  # type: ignore
        return obj

    @classmethod
    def bulk_from_dict(
        cls: T,
        source_list: list[dict[str, Any]],
        connection: 'Connection | None' = None,
        to_snake_case: bool = True,
        with_missing_value: bool = False,
    ) -> list[T]:
        """Creates multiple objects from a list of dictionaries. For each
        dictionary provided the keys in camel case are changed to object's
        attribute names (by default in snake case) and dict values are composed
        to their proper data types such as Enums, list of Enums etc. as
        specified in the object's _FROM_DICT_MAP.

        Args:
            cls (T): Class (type) of the objects that should be created.
            source_list (List[Dict[str, Any]]): A list of dictionaries from
                which the objects will be constructed.
            connection (Connection, optional): A MSTR Connection object.
                Defaults to None.
            to_snake_case (bool, optional): Set to True if attribute names
                should be converted from camel case to snake case. Defaults to
                True.
            with_missing_value: (bool, optional): If True, class attributes
                possible to fetch and missing in `source` will be set as
                `MissingValue` objects.

        Returns:
            T: A list of objects of type T.
        """
        return [
            cls.from_dict(
                source=source,
                connection=connection,
                to_snake_case=to_snake_case,
                with_missing_value=with_missing_value,
            )
            for source in source_list
        ]

    def __repr__(self) -> str:
        from mstrio.utils.entity import auto_match_args_entity

        param_dict = auto_match_args_entity(
            self.__init__,
            self,
            exclude=['self'],
            include_defaults=False,
        )
        formatted_params = ', '.join(
            (f'{param}={repr(value)}' for param, value in param_dict.items())
        )
        return f'{self.__class__.__name__}({formatted_params})'


def is_dashboard(view_media: int) -> bool:
    """Documents and dashboards have the same type and subtype when returned
    from search api. They can be distinguished only by view_media value.
    """
    # bits 30-29 are 1, bits 31 and 27 are 0 (011x 0xxx, then 3 bytes)
    return view_media & 0xE800_0000 == 0x6000_0000


def is_document(view_media: int) -> bool:
    """Documents and dashboards have the same type and subtype when returned
    from search api. They can be distinguished only by view_media value.
    """
    return not is_dashboard(view_media)


def rename_dict_keys(source: dict, mapping: dict) -> dict:
    """Rename dict keys according to mapping.

    Args:
        source (dict): An original dictionary, which keys are to be renamed.
        mapping (dict): A dictionary containing mapping of keys.

    Returns:
        dict: A dictionary with keys renamed.
    """
    for rest_name, python_name in mapping.items():
        if rest_name in source:
            old = source.pop(rest_name)
            if python_name:
                source[python_name] = old
    return source


def verify_project_status(
    project: 'Project',
    correct_statuses: list[str] | str,
    node: str | None = None,
    timeout: int = 60,
) -> bool:
    """Verify if provided status is correct for given project.

    Args:
        project (Project): Project for which statuses will be verified.
        correct_statuses (list[str], str): A list of correct statuses
            or just one status.
        node (str, optional): Node name on which status should be verified,
            represented as name of first node if not provided.

    Returns:
        bool: True if status is correct and False otherwise.
    """

    def get_status(project: 'Project', node: str | None = None) -> str:
        node_name = node if node else project.nodes[0]['name']
        nodes_filtered = [node for node in project.nodes if node['name'] == node_name]

        if not nodes_filtered:
            raise ValueError(
                f"Node {node} not found. Available nodes "
                f"{[node['name'] for node in project.nodes]}"
            )

        projects_filtered = [
            proj
            for node in nodes_filtered
            for proj in node['projects']
            if proj['id'] == project.id
        ]

        return projects_filtered[0]['status']

    status = get_status(project=project, node=node)
    iteration = 0
    correct_statuses = (
        correct_statuses if isinstance(correct_statuses, list) else [correct_statuses]
    )

    while status not in correct_statuses and iteration < timeout:
        time.sleep(1)
        project.fetch('nodes')
        status = get_status(project=project, node=node)
        iteration += 1

    return status in correct_statuses


def find_object_with_name(
    connection: 'Connection',
    cls,
    name: str,
    listing_function: callable,
    search_pattern: 'SearchPattern | None' = None,
) -> dict:
    """Find objects with given name if no id is given.

    Args:
        connection: A Strategy One connection object
        name: name of the object. Defaults to None.
        listing_function: function called to list all the objects
            with given name
        search_pattern: search pattern used to find the object.

    Returns:
        dict: object properties in a dictionary.

    Raises:
        ValueError: if both `id` and `name` are not provided,
            if there is more than 1 object with the given `name` or
            if object with the given `name` doesn't exist.
    """
    if search_pattern:
        results = listing_function(
            connection=connection, name=name, search_pattern=search_pattern
        )
    else:
        results = listing_function(connection=connection, name=name)

    if results:
        number_of_objects = len(results)

        if 1 < number_of_objects <= 5:
            error_string = (
                f"There are {number_of_objects} {cls.__name__} objects"
                f" with name: {name}:\n"
            )
            for obj in results:
                path = "/".join(ancestor['name'] for ancestor in obj.ancestors)
                error_string += f"ID: {obj.id} in folder: {path}\n"

            error_string += "Please initialize with ID."

            raise ValueError(error_string)

        if number_of_objects > 5:
            raise ValueError(
                f"There are {number_of_objects} {cls.__name__}"
                " objects with this name. Please initialize with ID."
            )

        return results[0].to_dict()
    else:
        raise ValueError(f"There is no {cls.__name__} with the given name: '{name}'")


def get_object_properties(obj: object) -> set[str]:
    """Extract private object properties.

    Args:
        obj (object): An object which properties will be extracted.

    Returns:
        set[str]: Names of object properties in a set.
    """

    return {
        elem[0]
        for elem in inspect.getmembers(obj.__class__, lambda x: isinstance(x, property))
    }


def encode_as_b64(query: str | Query) -> str:
    """Encodes a query as base64.

    Args:
        query (str | Query): query to be encoded

    Returns:
        Base64 format encoded query."""
    return b64encode(str(query).encode('utf-8')).decode('utf-8')


def get_string_exp_body(expression: str) -> dict:
    return {
        "tokens": [
            {"value": "%", "type": "character"},
            {"value": expression},
        ]
    }


def construct_expression_body(expression: 'str | Expression | dict') -> dict:
    from mstrio.modeling.expression import Expression

    if isinstance(expression, Expression):
        return expression.to_dict()
    if isinstance(expression, str):
        return get_string_exp_body(expression)
    return expression


def deduplicated_name(name: str, existing_names: list[str]) -> str:
    """
    Deduplicate a name by adding a number in parentheses if it already exists.

    Args:
        name: The user-provided name to deduplicate.
        existing_names: A list of existing names to check against.

    Returns:
        The deduplicated name, e.g. 'Schedule (1)'.
    """
    if name not in existing_names:
        return name

    # found duplicate, candidate would be '{name} (1)'
    # find more names that would conflict with the new name

    # trim potential conflicts, e.g. 'Schedule (1)' -> '1'
    trim_index = len(name) + 2
    conflict_strs = [n[trim_index:-1] for n in existing_names if n.startswith(name)]
    conflict_inds: list[int] = [int(n) for n in conflict_strs if n.isnumeric()]

    # find lowest positive integer not in found indices
    i = 1
    while i in conflict_inds:
        i += 1

    return f"{name} ({i})"


def wait_for_stable_status(
    obj: 'EntityBase',
    property: str,
    not_stable_val: list,
    timeout: int = 240,
    interval: int = 1,
) -> bool:
    """Wait for a specific property of an object to reach a stable state.

    Args:
        obj (EntityBase): The object to monitor.
        property (str): The property to check.
        not_stable_val (list): List of values that indicate the property is not
            stable.
        timeout (int, optional): Maximum time to wait in seconds.
            Defaults to 240.
        interval (int, optional): Time between checks in seconds.
            Defaults to 1.

    Returns:
        bool: True if stable state is reached False otherwise.
    """
    start_time = datetime.now()
    while (getattr(obj, property) in not_stable_val) and (
        (datetime.now() - start_time).total_seconds() < timeout
    ):
        obj.fetch()
        sleep(interval)

    return getattr(obj, property) not in not_stable_val


def get_owner_id(
    connection: 'Connection',
    owner: 'str | User | dict | None' = None,
    owner_id: str | None = None,
    owner_username: str | None = None,
) -> str | None:
    """Get owner ID based on provided parameters.

    Args:
        connection (Connection): Strategy One connection object.
        owner (str | User | dict | None): Owner as ID, User object or dict.
            Will take precedence over other parameters.
        owner_id (str | None): Owner's ID.
        owner_username (str | None): Owner's username.

    Returns:
        str | None: User ID of the owner or None if not found.
    """
    from mstrio.users_and_groups import User

    # If owner is a User object, return its ID directly
    if isinstance(owner, User):
        return owner.id

    owner_name = None
    # Dict can contain 'id', but also only 'name'
    if isinstance(owner, dict):
        owner_id = owner.get('id')
        owner_name = owner.get('name')
        owner = None

    # Determine the user identifier to look up
    user_identifier = owner or owner_id or owner_username
    if not user_identifier and not owner_name:
        return None

    # Get user and return ID if found
    if user := get_user_based_on_id_or_username(
        connection, user_identifier, user_identifier, owner_name
    ):
        return user.id

    return None


def get_user_based_on_id_or_username(
    connection: 'Connection',
    user_id: str | None = None,
    user_username: str | None = None,
    user_name: str | None = None,
) -> 'User | None':
    """Get User object based on provided user ID or username.

    Args:
        connection (Connection): Strategy One connection object.
        user_id (str | None): User's ID.
        user_username (str | None): User's username (e.g. 'mstr').
        user_name (str | None): User's name (e.g. 'MSTR User').

    Returns:
        User | None: User object if found, None otherwise.
    """
    from mstrio.users_and_groups import User

    both_the_same = user_id == user_username
    if user_id:
        try:
            with config.temp_verbose_disable():
                return User(connection=connection, id=user_id)
        except IServerError:
            if not both_the_same:
                logger.warning(
                    f"Could not find user with ID '{user_id}'. "
                    "Please provide a valid user ID."
                )
    if user_username:
        try:
            with config.temp_verbose_disable():
                return User(connection=connection, username=user_username)
        except ValueError:
            if not both_the_same:
                logger.warning(
                    f"Could not find user with username '{user_username}'. "
                    "Please provide a valid user username."
                )
    if both_the_same:
        logger.warning(
            f"Could not find user with ID or username '{user_id}'. "
            "Please provide a valid user ID or username."
        )
    if user_name:
        try:
            return User(connection=connection, name=user_name)
        except ValueError:
            if not both_the_same:
                logger.warning(
                    f"Could not find user with name '{user_name}'. "
                    "Please provide a valid user name."
                )
    return None


def is_valid_str_id(str_id: Any) -> bool:
    """Check if the provided Strategy ID has valid format.

    Args:
        str_id (Any): The Strategy ID to check.

    Returns:
        bool: True if the ID is valid, False otherwise.
    """
    if not str_id or not isinstance(str_id, str) or len(str_id) != 32:
        return False

    HEX32 = re.compile(r"^[0-9A-F]{32}$")
    return HEX32.match(str_id) is not None
