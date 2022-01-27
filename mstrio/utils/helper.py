from datetime import datetime
from enum import Enum
from functools import reduce, wraps
import inspect
from json.decoder import JSONDecodeError
from math import floor
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, TypeVar, Union
import warnings

import pandas as pd
import stringcase

from mstrio import __version__ as mstrio_version
from mstrio import config
from mstrio.api.exceptions import MstrTimeoutError, PromptedContentError, VersionException
from mstrio.types import ObjectSubTypes
from mstrio.utils.dict_filter import filter_list_of_dicts
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.time_helper import DatetimeFormats, map_datetime_to_str, map_str_to_datetime
from mstrio.utils.sessions import FuturesSessionWithRenewal


if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.project_objects.datasets import OlapCube, SuperCube
    from mstrio.types import ObjectTypes


def deprecation_warning(deprecated: str, new: str, version: str, module: bool = True,
                        change_compatible_immediately=True):
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
            f"{deprecated}{module} is deprecated and will not be supported starting from mstrio-py"
            f"{version}. Please use {new} instead.")
    else:
        msg = (f"From version {version} {deprecated}{module} will be removed and replaced with "
               f"{new}")
    warnings.warn(DeprecationWarning(msg))


def url_check(url):
    """Checks the validity of the url required in the connection object and
    returns a validated url."""
    regex = r'^https?://.+$'
    match = re.search(regex, url)
    api_index = url.find('/api')

    if match is None:
        msg = ("Please check the validity of the base_url parameter. Typically of the form "
               "'https://<<MSTR Domain>>/MicroStrategyLibrary/'")
        raise ValueError(msg)
    if api_index != -1:
        url = url[:api_index]
    if url.endswith('/'):
        url = url[:-1]

    return url


def version_cut(version):
    res = ".".join([str(int(i)) for i in version.split(".")])
    return res[:6]


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


def camel_to_snake(response: Union[dict, list]) -> Union[dict, List[dict]]:
    """Converts dictionary keys from camelCase to snake_case.
       It works recursively for dicts in dicts."""

    def convert_dict(source):
        return {
            stringcase.snakecase(key):
            value if not isinstance(value, dict) else convert_dict(value)
            for key, value in source.items()
        }

    if type(response) == list:
        return [convert_dict(source) for source in response if type(source) == dict]
    elif type(response) == dict:
        return convert_dict(response)
    else:
        raise ValueError("Not supported data type for camel_to_snake conversion")


def snake_to_camel(response: Union[dict, list]) -> Union[dict, List[dict]]:
    """Converts dictionary keys from snake_case to camelCase.
       It works recursively for dicts in dicts."""

    def convert_dict(source):
        return {
            stringcase.camelcase(key):
            value if not isinstance(value, dict) else convert_dict(value)
            for key, value in source.items()
        }

    if type(response) == list:
        return [convert_dict(source) for source in response if type(source) == dict]
    elif type(response) == dict:
        return convert_dict(response)
    else:
        raise ValueError("Not supported data type for snake_to_camel conversion")


def check_duplicated_column_names(data_frame):
    list_of_columns = list(data_frame.columns)
    return len(list_of_columns) == len(set(list_of_columns))


def exception_handler(msg, exception_type=Exception, stack_lvl=2):
    """Generic error message handler.

    Args:
        msg (str): Message to print in the Exception or Warning
        exception_type (Exception): Instance of Exception or Warning class
        stack_lvl (int, optional): controls how deep the stacktrace will be
    """
    if not isinstance(exception_type, type) or not issubclass(exception_type, Exception):
        raise ValueError("exception_type has to be a subclass of Exception class")
    elif (issubclass(exception_type, Exception) and not issubclass(exception_type, Warning)):
        raise exception_type(msg)
    elif issubclass(exception_type, Warning):
        warnings.warn(msg, exception_type, stacklevel=stack_lvl)


def response_handler(response, msg, throw_error=True, verbose=True, whitelist=None):
    """Generic error message handler for transactions against I-Server.

    Args:
        response: Response object returned by HTTP request.
        msg (str): Message to print in addition to any server-generated error
            message(s)
        throw_error (bool): Flag indicates if the error should be thrown
        verbose (bool, optional): controls if messages/errors will be printed
        whitelist(list): list of tuples of I-Server Error and HTTP errors codes
            respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]
    """
    if whitelist is None:
        whitelist = []

    try:
        res = response.json()

        if res.get('errors') is not None:
            res = res.get('errors')
            if len(res) > 0:
                res = res[0]

        server_code = res.get('code')
        server_msg = res.get('message')
        ticket_id = res.get('ticketId')
        iserver_code = res.get('iServerCode')
        is_whitelisted = (server_code, response.status_code) in whitelist

        if not is_whitelisted:
            if ((server_code == 'ERR004' and response.status_code == 404
                 and server_msg == 'HTTP 404 Not Found')
                    or (server_code == 'ERR001' and response.status_code == 405
                        and server_msg == 'HTTP 405 Method Not Allowed')):
                msg = ("This REST API functionality is not yet supported on this version of "
                       f"the I-Server: {version_cut(config.iserver_version)}. Please upgrade "
                       "the I-Server version or downgrade the mstrio-py package (current "
                       f"version: {version_cut(mstrio_version)}) in order for the versions to "
                       "match.")
                exception_handler(msg, exception_type=VersionException)
            elif iserver_code == -2147206497:  # MSI_REQUEST_TIMEOUT on server-side
                raise MstrTimeoutError(res)
            elif iserver_code == -2147468903:
                raise PromptedContentError(
                    'Prompted content subscription creation is not supported.')
            if verbose:
                print(msg)
                print("I-Server Error %s, %s\nTicket ID: %s\n" %
                      (server_code, server_msg, ticket_id))
            if throw_error:
                response.raise_for_status()
    except JSONDecodeError:
        if verbose:
            print(msg)
            print(("Could not decode the response from the I-Server. Please check if I-Server "
                   "is running correctly\n"))
            response.raise_for_status()  # raise error if I-Server response cannot be decoded


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
        def fot_wrapper(limit: int) -> Tuple[Any, int]:
            try:
                return func(limit), limit
            except MstrTimeoutError as err:
                new_limit = floor(limit / 2)
                if new_limit >= min_limit:
                    warnings.warn((f"Timout hit when executing {func.__name__} with limit "
                                   f"{limit}, retrying with limit {new_limit}"))
                    return fot_wrapper(new_limit)
                else:
                    raise err

        return fot_wrapper

    return decorate


def get_parallel_number(total_chunks):
    """Returns the optimal number of threads to be used for downloading
    cubes/reports in parallel."""

    threads = min(8, os.cpu_count() + 4)
    if (total_chunks > 0):
        threads = min(total_chunks, threads)

    return threads


def _prepare_objects(objects: Union[dict, List[dict]], filters: Optional[dict] = None,
                     dict_unpack_value: Optional[str] = None):
    if type(objects) is dict and dict_unpack_value:
        objects = objects[dict_unpack_value]
    objects = camel_to_snake(objects)
    if filters:
        objects = filter_list_of_dicts(objects, **filters)  # type: ignore
    return objects


def fetch_objects_async(connection: "Connection", api: Callable, async_api: Callable,
                        limit: Optional[int], chunk_size: int, filters: dict,
                        error_msg: Optional[str] = None, dict_unpack_value: Optional[str] = None,
                        **kwargs) -> list:
    """Get all objects asynchronously. Optionally filter the objects using
    `filters` parameter. Works only for endpoints with `limit` and `offset`
    query parameter (pagination).

    Args:
        connection: MicroStrategy REST API connection object
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
    response = api(connection=connection, offset=offset, limit=chunk_size, error_msg=error_msg,
                   **param_value_dict)
    objects = _prepare_objects(response.json(), filters, dict_unpack_value)
    all_objects.extend(objects)
    current_count = offset + chunk_size
    total_objects = int(response.headers.get('x-mstr-total-count'))
    total_objects = min(limit, total_objects) if limit else total_objects

    if total_objects > current_count:
        it_total = int(total_objects / chunk_size) + (total_objects % chunk_size != 0)
        threads = get_parallel_number(it_total)
        with FuturesSessionWithRenewal(connection=connection, max_workers=threads) as session:
            # Extract parameters of the api wrapper and set them using kwargs
            param_value_dict = auto_match_args(
                api, kwargs,
                exclude=['connection', 'limit', 'offset', 'future_session', 'error_msg'])
            futures = [
                async_api(future_session=session, connection=connection, offset=offset,
                          limit=chunk_size, **param_value_dict)
                for offset in range(current_count, total_objects, chunk_size)
            ]

        for f in futures:
            response = f.result()
            if not response.ok:
                response_handler(response, error_msg, throw_error=False)
            objects = _prepare_objects(response.json(), filters, dict_unpack_value)
            all_objects.extend(objects)
    return all_objects


def fetch_objects(connection: "Connection", api: Callable, limit: Optional[int], filters: dict,
                  error_msg: Optional[str] = None, dict_unpack_value: Optional[str] = None,
                  **kwargs) -> list:
    """Fetch and prepare objects. Optionally filter the objects by using the
    filters parameter. This function only supports endpoints without pagination.

    Args:
        connection: MicroStrategy REST API connection object
        api: GET API wrapper function that will return list of objects in bulk
        dict_unpack_value: if the response needs to be unpacked to get into
            the values specify the keyword
        limit: cut-off value for the number of objects returned
        error_msg: specifies error_msg for failed requests
        **filters: dict that specifies filter expressions by which objects will
            be filtered locally
        kwargs: all specific parameters that the api methods require that need
            to be additionally specified
    """
    validate_param_value('limit', limit, int, min_val=1, special_values=[None])

    # Extract parameters of the api wrapper and set them using kwargs
    param_value_dict = auto_match_args(api, kwargs, exclude=['connection', 'error_msg'])
    response = api(connection=connection, error_msg=error_msg, **param_value_dict)
    if response.ok:
        objects = _prepare_objects(response.json(), filters, dict_unpack_value)
        if limit:
            objects = objects[:limit]
        return objects
    else:
        return []


def sort_object_properties(source: dict) -> int:
    """Sort all properties of an object representing an MSTR object."""
    preffered_order = {
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
    return preffered_order.get(source, 50)


def auto_match_args(func: Callable, param_dict: dict, exclude: list = [],
                    include_defaults: bool = True) -> dict:
    """Automatically match dict data to function arguments.

    Handles default parameters. Extracts value from Enums. Returns matched
    arguments as dict.

    Args:
        function: function for which args will be matched
        param_dict: dict to use for matching the function args
        exclude: set `exclude` parameter to exclude specific param-value pairs
        include_defaults: if `False` then values which have the same value as
            default will not be included in the result
    Raises:
        KeyError: could not match all required arguments
    """

    args = get_args_from_func(func)
    default_dict = get_default_args_from_func(func)

    param_value_dict = {}
    for arg in args:
        if arg in exclude:
            continue
        else:
            val = param_dict.get(arg) if param_dict.get(arg) is not None else default_dict.get(arg)
            if not include_defaults and arg in default_dict and val == default_dict[arg]:
                continue

            if isinstance(val, Enum):
                val = val.value
        param_value_dict.update({arg: val})

    return param_value_dict


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
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


def __validate_single_param_value(value, param_name, data_type, max_val, min_val, regex,
                                  valid_example, inv_val, special_values=[]):
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
    elif (all(cond is None for cond in [max_val, min_val, regex]) and special_values
          and str not in data_type):
        msg = f"'{param_name}' has to be one of {special_values}"
        exception_handler(msg, inv_val)
        return False
    return True


def validate_param_value(param_name, param_val, data_type, max_val=None, min_val=None,
                         special_values=[], regex=None, exception=True,
                         valid_example=None) -> bool:
    """Validate param data type and optionally max, min special values.

    Raise:
        TypeError
        ValueError
    """
    inv_type = TypeError if exception else Warning
    inv_val = ValueError if exception else Warning
    data_type = data_type if isinstance(data_type, list) else [data_type]

    if any(map(lambda x: x == param_val and isinstance(x, type(param_val)), special_values)):
        return True

    if type(param_val) not in data_type:
        msg = f"'{param_name}' needs to be of type {data_type}"
        exception_handler(msg, inv_type)
        return False
    if type(param_val) == list:
        return all([
            __validate_single_param_value(value, param_name, data_type, max_val, min_val, regex,
                                          valid_example, inv_val, special_values)
            for value in param_val
        ])

    return __validate_single_param_value(param_val, param_name, data_type, max_val, min_val, regex,
                                         valid_example, inv_val, special_values)


def extract_all_dict_values(list_of_dicts: List[Dict]) -> List[Any]:
    """Extract list of dicts values into list."""
    all_options: List = []
    for option in list_of_dicts:
        all_options.extend(option.values())
    return all_options


def delete_none_values(source: dict) -> dict:
    """Delete keys with None values from dictionary.

    Args:
        source (dict): dict object from which none values will be deleted
    """
    new_dict = {}
    for key, value in source.items():
        if isinstance(value, dict):
            new_dict[key] = delete_none_values(value)
        elif value not in [[], {}, None]:
            new_dict[key] = value
    return new_dict


def get_objects_id(obj, obj_class):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, obj_class):
        return obj.id
    return None


def list_folders(connection, name: Optional[str] = None, to_dataframe: bool = False,
                 limit: Optional[int] = None, **filters) -> Union[List[dict], pd.DataFrame]:
    """List folders.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        name (string, optional): exact name of a folder to filter results.
            If `None`, all folders will be retrieved.
        to_dataframe (bool, optional): determine if result of retrieval will
            be returned as a list of dicts or DataFrame.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'subtype',
            'type','date_created', 'date_modified', 'version', 'acg', 'owner']

    Returns:
        When `to_dataframe` set to False (default value) then DataFrame with
        folders, otherwise list of dictionaries with folders.
    """
    from mstrio.api import objects

    DSS_XML_SEARCH_TYPE_EXACTLY = 2
    FOLDER_TYPE = 8

    msg = "Error while creating an instance for searching objects"
    res_e = objects.create_search_objects_instance(connection=connection, name=name,
                                                   pattern=DSS_XML_SEARCH_TYPE_EXACTLY,
                                                   object_type=FOLDER_TYPE, error_msg=msg)
    search_id = res_e.json()['id']
    msg = "Error while retrieving folders from the environment."
    fldrs = fetch_objects_async(connection, api=objects.get_objects,
                                async_api=objects.get_objects_async, limit=limit, chunk_size=1000,
                                error_msg=msg, filters=filters, search_id=search_id)

    if to_dataframe:
        return pd.DataFrame(fldrs)
    else:
        return fldrs


def create_folder(connection, folder_name: str, folder_description: Optional[str] = None,
                  parent_name: Optional[str] = None, parent_id: Optional[str] = None,
                  error_msg=None):
    """Create a folder.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        folder_name (string): name of the folder which will be created
        folder_description (string, optional): description of the folder which
            will be created
        parent_name (string, optional): name of the folder in which new folder
            will be created
        parent_id (string, optional): id of the folder in which new folder
            will be created
        error_msg (string, optional): error message

    Returns:
        full response about the creation of the folder

    Raises:
        Exception when:
            - neither `parent_name` nor `parent_id` is specified
            - both `parent_name` and `parent_id` are specified
            - parent folder was not found or multiple folders with the same
              name exists when providing `parent_name`
    """
    from mstrio.api import folders

    if parent_id is None and parent_name is None:
        exception_handler("Please specify either 'parent_name' or 'parent_id'.")
    if parent_name is not None and parent_id is not None:
        exception_handler("Please specify either 'parent_name' or 'parent_id' but not both.")
    if parent_id is None:
        fldrs = list_folders(connection=connection, name=parent_name)
        if len(fldrs) != 1:
            msg = f"Parent folder with name '{parent_name}' was either not found "
            msg += "or multiple folders with the same name exists."
            exception_handler(msg)
        parent_id = fldrs[0]['id']
    return folders.create_folder(connection=connection, name=folder_name, parent_id=parent_id,
                                 description=folder_description)


def delete_folder(connection, id: Optional[str] = None, name: Optional[str] = None,
                  error_msg=None):
    """Delete a folder.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string, optional): id of the folder which will be deleted
        name (string, optional): name of the folder which will be deleted
        error_msg (string, optional): error message

    Returns:
        full response about the deletion of the folder

    Raises:
        Exception when:
            - neither `name` nor `id` is specified
            - both `name` and `id` are specified
            - folder was not found or multiple folders with the same name
              exists when providing `name`
    """
    from mstrio.api import objects

    if id is None and name is None:
        exception_handler("Please specify either 'name' or 'id' of the folder to be deleted.")
    if name is not None and id is not None:
        msg = "Please specify either 'name' or 'id' of the folder to be deleted but not both."
        exception_handler(msg)
    if id is None:
        fldrs = list_folders(connection=connection, name=name)
        if len(fldrs) != 1:
            msg = f"Folder with name '{name}' was either not found "
            msg += "or multiple folders with the same name exists."
            exception_handler(msg)
        id = fldrs[0]['id']
    FOLDER_TYPE = 8
    return objects.delete_object(connection=connection, id=id, object_type=FOLDER_TYPE,
                                 error_msg=error_msg)


def merge_id_and_type(object_id: str, object_type: Union["ObjectTypes", "ObjectSubTypes", int],
                      error_msg: Optional[str] = None) -> str:
    if not object_id or not object_type:
        exception_handler(msg=error_msg or "Please provide both `id` and `type`.",
                          exception_type=AttributeError)
    object_id = get_objects_id(object_id, type(object_id))
    object_type = get_enum_val(object_type, type(object_type)) if isinstance(
        object_type, Enum) else object_type
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


T = TypeVar("T")


def filter_obj_list(obj_list: List[T], **filters: Dict[str, Any]) -> List[T]:
    """Filter a list of objects by providing one or more key-value pair filters.
    """
    return [obj for obj in obj_list if all(getattr(obj, f) == v for f, v in filters.items())]


def choose_cube(connection: "Connection", cube_dict: dict) -> Union["OlapCube", "SuperCube", None]:
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


class Dictable:
    _FROM_DICT_MAP: Dict[str, Callable] = {}  # map attributes to Enums and components

    @classmethod
    def _obj_to_dict(cls, key, val, camel_case=True):
        """Unpack Enums, Dictable obj, list of Enums"""
        if isinstance(val, datetime):
            return map_datetime_to_str(key, val, cls._FROM_DICT_MAP)
        elif isinstance(val, Enum):
            return val.value
        elif isinstance(val, Dictable):
            return val.to_dict(camel_case)
        elif isinstance(val, list):
            return [cls._obj_to_dict(key, v, camel_case) for v in val]
        return val

    @classmethod
    def _dict_to_obj(cls, connection, val, key):

        def constructor():
            if isinstance(val, type(DatetimeFormats)):
                return map_str_to_datetime(key, val, cls._FROM_DICT_MAP)
            elif isinstance(cls._FROM_DICT_MAP[key], type(Enum)):
                return cls._FROM_DICT_MAP[key](val)
            elif isinstance(cls._FROM_DICT_MAP[key], type(Dictable)):
                return cls._FROM_DICT_MAP[key].from_dict(val)
            elif isinstance(cls._FROM_DICT_MAP[key], list):
                if (all(isinstance(v, type(Enum)) for v in cls._FROM_DICT_MAP[key])
                        and val is not None):
                    return [cls._FROM_DICT_MAP[key][0](v) for v in val]
                elif all([isinstance(v, type(Dictable)) for v in cls._FROM_DICT_MAP[key]]):
                    return [cls._FROM_DICT_MAP[key][0].from_dict(v) for v in val]
            else:
                return cls._FROM_DICT_MAP[key](val, connection)

        return val if key not in cls._FROM_DICT_MAP else constructor()

    def to_dict(self, camel_case=True):

        hidden_keys = [
            '_fetched_attributes', '_altered_properties', '_connection', 'connection', '_type'
        ]
        cleaned_dict = self.__dict__.copy()
        properties = set(
            (elem[0]
             for elem in inspect.getmembers(self.__class__, lambda x: isinstance(x, property))))
        for prop in properties:
            to_be_deleted = '_' + prop
            cleaned_dict[prop] = cleaned_dict.pop(to_be_deleted, None)
        result = {
            key: self._obj_to_dict(key, val, camel_case)
            for key, val in cleaned_dict.items()
            if key not in hidden_keys
        }

        result = delete_none_values(result)
        result = {key: result[key] for key in sorted(result, key=sort_object_properties)}
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls: T, source: Dict[str, Any], connection: Optional["Connection"] = None,
                  to_snake_case: bool = True) -> T:
        object_source = camel_to_snake(source) if to_snake_case else source
        if connection is not None:
            object_source["connection"] = connection

        args = {
            key: cls._dict_to_obj(connection, val, key)
            for key, val in object_source.items()
            if key in cls.__init__.__code__.co_varnames
        }
        obj = cls(**args)  # type: ignore
        return obj
