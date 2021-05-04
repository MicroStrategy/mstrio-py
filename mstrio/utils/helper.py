from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import wraps
from json.decoder import JSONDecodeError
from math import floor
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union
import warnings

import pandas as pd
from requests_futures.sessions import FuturesSession
import stringcase

from mstrio import __version__ as mstrio_version
from mstrio.api.exceptions import MstrTimeoutError, VersionException, PromptedContentError
import mstrio.config as config

if TYPE_CHECKING:
    from mstrio.connection import Connection


def deprecation_warning(deprecated: str, new: str, version: str, module: bool = True):

    module = " module" if module else ""
    msg = (f"{deprecated}{module} is deprecated and will not be supported starting from mstrio-py "
           f"{version}. Please use {new} instead.")
    warnings.warn(DeprecationWarning(msg))


def print_url(response, *args, **kwargs):
    """Response hook to print url for debugging."""
    print(response.url)


def save_response(response, *args, **kwargs):
    """Response hook to save REST API responses to files structured by the API
    family."""
    import json
    from pathlib import Path

    if response.status_code != 204:

        # Generate file name
        base_path = Path(__file__).parents[2] / 'tests/resources/auto-api-responses/'
        url = response.url.rsplit('api/', 1)[1]
        temp_path = url.split('/')
        file_name = '-'.join(temp_path[1:]) if len(temp_path) > 1 else temp_path[0]
        file_name = f'{file_name}-{response.request.method}'
        file_path = base_path if len(temp_path) == 1 else base_path / temp_path[0]
        path = str(file_path / file_name)

        # Create target directory & all intermediate directories if don't exists
        if not os.path.exists(str(file_path)):
            os.makedirs(file_path)
            print("Directory ", file_path, " created ")
        else:
            print("Directory ", file_path, " already exists")

        # Dump the response to JSON and Pickle
        # with open(path + '.pkl', 'wb') as f:
        #     pickle.dump(response, f)
        with open(path + '.json', 'w') as f:
            try:
                json.dump(response.json(), f)
            except JSONDecodeError:
                exception_handler("Could not decode response. Skipping creating JSON file.",
                                  Warning)


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


def camel_to_snake(response: Union[dict, list]) -> Union[dict, List[dict]]:
    """Converts dictionary keys from camelCase to snake_case."""

    def convert_dict(dictionary):
        return {stringcase.snakecase(key): value for key, value in dictionary.items()}

    if type(response) == list:
        return [convert_dict(dictionary) for dictionary in response if type(dictionary) == dict]
    elif type(response) == dict:
        return convert_dict(response)
    else:
        raise ValueError("Not supported data type for camel_to_snake conversion")


def snake_to_camel(response: Union[dict, list]) -> Union[dict, List[dict]]:
    """Converts dictionary keys from snake_case to camelCase."""

    def convert_dict(dictionary):
        return {stringcase.camelcase(key): value for key, value in dictionary.items()}

    if type(response) == list:
        return [convert_dict(dictionary) for dictionary in response if type(dictionary) == dict]
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


def response_handler(response, msg, throw_error=True, verbose=True, whitelist=[]):
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
    try:
        res = response.json()
        server_code = res.get('code')
        server_msg = res.get('message')
        ticket_id = res.get('ticketId')
        iserver_code = res.get('iServerCode')
        is_whitelisted = (server_code, response.status_code) in whitelist

        if verbose and not is_whitelisted:
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
            print(msg)
            print("I-Server Error %s, %s\nTicket ID: %s\n" % (server_code, server_msg, ticket_id))
    except JSONDecodeError:
        if verbose:
            print(msg)
            print(("Could not decode the response from the I-Server. Please check if I-Server "
                   "is running correctly\n"))
            response.raise_for_status()  # raise error if I-Server response cannot be decoded
    else:
        if throw_error and not is_whitelisted:
            response.raise_for_status()


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


def make_dict_filter(param: str, expression: Union[str, int, float, dict, list]):
    """Return a filter function that takes a dictionary object as parameter.

    Once evaluated it return bool value indicating if given parameter-
    expression is True or False. This function can be used in the
    filter() method.
    """

    op = None
    if type(expression) is list:
        op = 'in'
        filter_value = expression
    elif type(expression) is str:
        # extract the operation from the expression if it exists
        if expression and expression[0] in ['<', '>', '!', '=']:
            op = expression[0]
            if expression[0] in ['<', '>', '!'] and expression[1] == '=':
                op = op + expression[1]
        filter_value = expression[len(op):] if op is not None else expression

        if filter_value.lower() == 'true':  # Support Bool values
            filter_value = True
        elif filter_value.lower() == 'false':
            filter_value = False
        op = op if op else '='
    elif type(expression) is dict:
        op = 'dict'
        filter_value = expression
    elif type(expression) in [int, float, bool]:
        op = '='
        filter_value = expression
    else:
        exception_handler(
            "'{}' filter value must be either a string, bool, int, float dict or list".format(
                param), exception_type=TypeError)

    def myfilter(dict_object):
        value = dict_object.get(param)
        allowed = [
            el for el in dict_object.keys() if type(dict_object[el]) not in [list, tuple, set]
        ]
        if param not in allowed:
            exception_handler(
                "The filter parameter '{}' is not valid. Please filter by one of: {}".format(
                    param, allowed), KeyError)
        value_type = type(value)
        try:
            if op == 'in':
                typed_filter_value = [value_type(val) for val in expression]
            elif op == 'dict':
                if value_type is not dict:
                    raise TypeError(f'"{param}" needs to be a dictionary.')
            else:
                typed_filter_value = value_type(filter_value)
        except ValueError as e:
            print("'{}' filter value is incorrect.".format(param))
            raise e
        else:
            if op == '=':
                return value == typed_filter_value
            elif op == '>':
                return value > typed_filter_value
            elif op == '<':
                return value < typed_filter_value
            elif op == '>=':
                return value >= typed_filter_value
            elif op == '<=':
                return value <= typed_filter_value
            elif op in ['!', '!=']:
                return value != typed_filter_value
            elif op == 'in':
                return value in typed_filter_value
            elif op == 'dict':
                return all(
                    (value[k] == v if k in value else False for k, v in filter_value.items()))

    return myfilter


def filter_list_of_dicts(list_of_dicts: List[dict], **filters) -> List[dict]:
    """Filter a list of dicts by any given key-value pair.

    Support simple logical operators like: '<,>,<=,>=,!'. Supports
    filtering by providing a list value i.e. openJobsCount=[0, 1, 2].
    """

    for key, value in filters.items():
        filter_function = make_dict_filter(key, value)
        list_of_dicts = list(filter(filter_function, list_of_dicts))
    return list_of_dicts


def _prepare_objects(objects: Union[dict, List[dict]], filters: dict = None,
                     dict_unpack_value: str = None):
    if type(objects) is dict and dict_unpack_value:
        objects = objects[dict_unpack_value]
    objects = camel_to_snake(objects)
    if filters:
        objects = filter_list_of_dicts(objects, **filters)  # type: ignore
    return objects


def fetch_objects_async(connection: "Connection", api: Callable, async_api: Callable,
                        limit: Optional[int], chunk_size: int, filters: dict,
                        error_msg: str = None, dict_unpack_value: str = None, **kwargs) -> list:
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
    args = api.__code__.co_varnames[:api.__code__.co_argcount]
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
        with FuturesSession(executor=ThreadPoolExecutor(max_workers=threads),
                            session=connection.session) as session:
            # Extract parameters of the api wrapper and set them using kwargs
            args = async_api.__code__.co_varnames[:async_api.__code__.co_argcount]
            param_value_dict = {
                arg: kwargs.get(arg)
                for arg in args
                if arg not in ['connection', 'limit', 'offset', 'future_session', 'error_msg']
            }
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
                  error_msg: str = None, dict_unpack_value: str = None, **kwargs) -> list:
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

    # Extract parameters of the api wrapper and set them using the kwargs
    args = api.__code__.co_varnames[:api.__code__.co_argcount]
    param_value_dict = {
        arg: kwargs.get(arg) for arg in args if arg not in ['connection', 'error_msg']
    }
    response = api(connection=connection, error_msg=error_msg, **param_value_dict)
    objects = _prepare_objects(response.json(), filters, dict_unpack_value)
    if limit:
        objects = objects[:limit]
    return objects


def sort_object_properties(dictionary: dict) -> int:
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
    return preffered_order.get(dictionary, 50)


def auto_match_args(func: Callable, obj: Any, exclude: list = [],
                    include_defaults: bool = True) -> dict:
    """Automatically match `obj` object data to function arguments.

    Handles default parameters. Extracts value from Enums. Returns matched
    arguments as dict.

    Args:
        function: function for which args will be matched
        obj: object to use for matching the function args
        exclude: set `exclude` parameter to exclude specific param-value pairs
        include_defaults: if `False` then values which have the same value as
            default will not be included in the result
    Raises:
        KeyError: could not match all required arguments
    """

    args = func.__code__.co_varnames[:func.__code__.co_argcount]
    defaults = func.__defaults__
    default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}

    param_value_dict = {}
    for arg in args:
        if arg in exclude:
            continue
        elif arg == 'type' and hasattr(obj, '_OBJECT_TYPE'):
            val = obj._OBJECT_TYPE.value
        else:
            val = obj.__dict__.get(arg, obj.__dict__.get("_" + arg, default_dict.get(arg)))
            if not include_defaults:
                if arg in default_dict and val == default_dict[arg]:
                    continue

            if isinstance(val, Enum):
                val = val.value
        param_value_dict.update({arg: val})

    return param_value_dict


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

    def validate_value(value):
        if value in special_values:
            return True
        else:
            if max_val is not None:
                if value > max_val:
                    msg = f"'{param_name}' has to be less than or equal to {max_val}"
                    exception_handler(msg, inv_val)
                    return False
            if min_val is not None:
                if value < min_val:
                    msg = f"'{param_name}' has to be greater than or equal to {min_val}"
                    exception_handler(msg, inv_val)
                    return False
            if regex is not None:
                if not re.match(regex, value):
                    pattern = valid_example if valid_example else regex
                    msg = f"'{param_name}' has to match pattern '{pattern}'"
                    exception_handler(msg, inv_val)
                    return False
            if (all(cond is None for cond in [max_val, min_val, regex]) and special_values
                    and str not in data_type):
                msg = f"'{param_name}' has to be one of {special_values}"
                exception_handler(msg, inv_val)
                return False
            else:
                return True

    if any(map(lambda x: x == param_val and isinstance(x, type(param_val)), special_values)):
        return True
    else:
        if type(param_val) not in data_type:
            msg = f"'{param_name}' needs to be of type {data_type}"
            exception_handler(msg, inv_type)
            return False
        if type(param_val) == list:
            return all([validate_value(value) for value in param_val])
        else:
            return validate_value(param_val)


def extract_all_dict_values(list_of_dicts: List[Dict]) -> List[Any]:
    """Extract list of dicts values into list."""
    all_options: List = []
    for option in list_of_dicts:
        all_options.extend(option.values())
    return all_options


def delete_none_values(dictionary: dict) -> dict:
    """Delete keys with None values from dictionary.

    Args:
        dictionary: dictionary
    """
    new_dict = {}
    for key, value in dictionary.items():
        if isinstance(value, dict):
            new_dict[key] = delete_none_values(value)
        elif value not in [[], {}, None]:
            new_dict[key] = value
    return new_dict


def list_folders(connection, name: str = None, to_dataframe: bool = False, limit: int = None,
                 **filters) -> Union[List[dict], pd.DataFrame]:
    """List folders.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        name (string, optional): exact name of a folder to filter results.
            If `None`, all folders will be retrieved.
        to_dataframe (bool, optional): determine if result of retrieval will
            be returned as a list of dicts or DataFrame.
        limit: limit the number of elements returned. If `None`, all objects are
            returned.
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
    fldrs = fetch_objects_async(
        connection,
        api=objects.get_objects,
        async_api=objects.get_objects_async,
        limit=limit,
        chunk_size=1000,
        error_msg=msg,
        filters=filters,
        search_id=search_id,
    )

    if to_dataframe:
        return pd.DataFrame(fldrs)
    else:
        return fldrs


def create_folder(connection, folder_name: str, folder_description: str = None,
                  parent_name: str = None, parent_id: str = None, error_msg=None):
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


def delete_folder(connection, id: str = None, name: str = None, error_msg=None):
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
    return objects.delete_object(connection=connection, id=id, type=FOLDER_TYPE,
                                 error_msg=error_msg)


class Dictable:
    _FROM_DICT_MAP: Dict[str, Callable] = {}  # map attributes to Enums and components
    _CONNECTION = None

    def to_dict(self, camel_case=True):

        def maybe_unpack(val):
            if isinstance(val, Enum):
                return val.value
            elif isinstance(val, Dictable):
                return val.to_dict(camel_case)
            else:
                return val

        result = {key: maybe_unpack(val) for key, val in self.__dict__.items()}
        result = delete_none_values(result)
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: "Connection" = None,
                  to_snake_case=True):
        type_mapping = cls._FROM_DICT_MAP
        object_source = camel_to_snake(source) if to_snake_case else source

        def map_val(val, key):

            def constructor():
                return type_mapping[key](val) if isinstance(
                    type_mapping[key], Enum) else type_mapping[key](val, connection)

            return val if key not in type_mapping else constructor()

        args = {
            key: map_val(val, key)
            for key, val in object_source.items()
            if key in cls.__init__.__code__.co_varnames
        }
        obj = cls(**args)  # type: ignore
        obj._CONNECTION = connection
        return obj
