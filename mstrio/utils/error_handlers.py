from functools import wraps
import inspect
import logging
from typing import Any, Callable, Union

from requests.adapters import Response

from mstrio import config
from mstrio.api.exceptions import MstrException, PartialSuccess, Success
from mstrio.utils.helper import get_default_args_from_func, response_handler


def get_args_and_bind_values(func: Callable[[Any], Any], *args, **kwargs):
    signature = inspect.signature(func)
    return signature.bind(*args, **kwargs).arguments


logger = logging.getLogger(__name__)


class ErrorHandler:
    """An easy-to-use class decorator designed to replace
    logic responsible for displaying the error message in API wrappers.

    Attributes:
        err_msg(str): error message to be displayed in case of error

    Usage:
        to replace the code below

          if not response.ok:
            if error_msg is None:
              error_msg = f'Error deleting Datasource Login with ID {id}'
            response_handler(response, error_msg)
          return response

        use the decorator in a following way

           @ErrorHandler(err_msg='Error deleting Datasource Login with ID {id}')
           def func(connection, id):
              ...

        the strings in curly braces will be replaced
        with the appropriate values if they appear in the function arguments
    """

    def __init__(self, err_msg: str):
        self._err_msg = err_msg

    def __call__(self, func: Callable[[Any], Any]):

        @wraps(func)
        def inner(*args, **kwargs):
            response = func(*args, **kwargs)
            error_msg = kwargs.get("error_msg") if kwargs.get("error_msg") else self._err_msg
            if not response.ok:
                handler_kwargs = self._get_resp_handler_kwargs(kwargs)
                error_msg = self._replace_with_values(error_msg, func, *args, **kwargs)
                response_handler(response, error_msg, **handler_kwargs)
            return response

        return inner

    @staticmethod
    def _replace_with_values(err_msg: str, func: Callable[[Any], Any], *args, **kwargs):
        all_args = get_args_and_bind_values(func, *args, **kwargs)
        for arg in all_args:
            arg_name, arg_value = arg, all_args[arg]
            err_msg = err_msg.replace(f'{{{arg_name}}}', str(arg_value))
        return err_msg

    @staticmethod
    def _get_resp_handler_kwargs(decorated_func_kwargs):
        default_args = get_default_args_from_func(response_handler)
        for arg in default_args:
            default_args[arg] = decorated_func_kwargs.get(arg, default_args[arg])
        return default_args


def bulk_operation_response_handler(
    response: Response, unpack_value: str = None
) -> Union[PartialSuccess, Success, MstrException]:
    """Handle partial success and other statuses from bulk operation."""
    response_body = response.json()
    if response.ok and unpack_value:
        response_body = response_body[unpack_value]

    if response.status_code == 200:
        err = Success(response_body)
    elif response.status_code == 207:
        err = PartialSuccess(response_body)
    else:
        err = MstrException(response_body)

    if config.verbose:
        logger.error(err)
    return err
