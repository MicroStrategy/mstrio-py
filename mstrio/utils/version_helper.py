import inspect
import logging
from functools import wraps
from inspect import getattr_static, getmembers

from packaging.version import Version as PackageVersion
from packaging.version import parse as ver_parser

from mstrio.connection import Connection
from mstrio.helpers import VersionException

logger = logging.getLogger(__name__)


def meets_minimal_version(
    tested_version: str | PackageVersion | None,
    minimal_version: str | PackageVersion,
    throw_error: bool = False,
) -> bool:
    """
    Checks if tested version is greater or equal to minimal version.

    Args:
        tested_version (str | PackageVersion | None): Tested version.
        minimal_version (str | PackageVersion): Minimal version.
        throw_error (bool, optional): If True, will raise VersionException
            if tested version is None. Defaults to False.

    Returns:
        bool: True if tested version is greater or equal to minimal version.
              If tested version is `None`, True is returned as we assume
              we were not able to gather value to test.
    """
    if tested_version is None:
        if throw_error:
            raise VersionException("Version to compare not provided.")

        logger.warning(
            "Version to compare not provided. "
            f"Assuming minimal version '{minimal_version}' is met."
        )
        return True

    to_test = (
        tested_version
        if isinstance(tested_version, PackageVersion)
        else ver_parser(tested_version)
    )
    minimal = (
        minimal_version
        if isinstance(minimal_version, PackageVersion)
        else ver_parser(minimal_version)
    )

    return to_test >= minimal


def method_version_handler(version):
    """
    Decorator which can be applied to a function.
    When applied, validates the iServer version of the existing connection
    (retrieved from kwargs, args or `connection` property from self)
    and compares it with the `version` provided in the arguments -
    version at which the functionality becomes applicable.
    """

    def wrapper(function, cls=None):
        @wraps(function)
        def inner(*args, **kwargs):
            if conn := kwargs.get('connection'):
                connection_obj = conn
            elif conn := [arg for arg in args if isinstance(arg, Connection)]:
                connection_obj = conn[0]
            elif cls:
                raise TypeError(
                    f"{function.__name__}() " "missing required argument: 'connection'"
                )
            else:
                connection_obj = getattr(args[0], 'connection', None) or getattr(
                    args[0], '_connection', None
                )

            if not meets_minimal_version(connection_obj.iserver_version, version):
                raise VersionException(
                    f"Environments must run IServer version {version} or newer. "
                    "Please update your environments to use this feature."
                )
            return function(*args, **kwargs)

        return inner

    return wrapper


def class_version_handler(version):
    """
    Decorator which can be used on a class.
    It applies the `method_version_handler decorator` to all the methods
    in the decorated class that are not inherited.
    """
    decorator = method_version_handler(version)

    def wrapper(cls):
        for name, obj in getmembers(cls):
            if name in vars(cls):
                # get attribute without triggering descriptor protocol
                attr = getattr_static(cls, name)

                if inspect.isfunction(attr) and name == '__init__':
                    # if __init__ method
                    setattr(cls, name, decorator(obj, cls))
                elif inspect.isfunction(attr):
                    # if other instance method
                    setattr(cls, name, decorator(obj))
                elif (
                    isinstance(attr, staticmethod)
                    and Connection in obj.__annotations__.values()
                ):
                    # if static method with Connection in params
                    setattr(
                        cls,
                        name,
                        staticmethod(decorator(obj, cls=cls)),
                    )
                elif (
                    isinstance(attr, classmethod)
                    and Connection in obj.__annotations__.values()
                ):
                    # if class method with Connection in params
                    setattr(
                        cls,
                        name,
                        classmethod(decorator(obj.__func__, cls=cls)),
                    )
                # if static or class method without params of type Connection
                # -> skip it

        return cls

    return wrapper


def is_server_min_version(connection: 'Connection', version_str: str) -> bool:
    """Check if iServer version is greater or equal than given version.

    Args:
        connection (Connection): Strategy One REST API connection object
        version_str (str): String containing iServer version number

    Returns:
        True if iServer version is greater or equal to given version
            or if it cannot be checked.
        False if iServer version is lower than given version.
    """
    return meets_minimal_version(connection.iserver_version, version_str)
