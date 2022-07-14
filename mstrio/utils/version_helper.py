from functools import wraps
from inspect import getattr_static, getmembers

from mstrio.api.exceptions import VersionException
from mstrio.connection import Connection


def method_version_handler(version):
    """
    Decorator which can be applied to a function.
    When applied, validates the iServer version of the existing connection
    (retrieved from kwargs, args or `connection` property from self)
    and compares it with the `version` provided in the arguments -
    version at which the functionality becomes applicable.
    """

    def wrapper(function):

        @wraps(function)
        def inner(*args, **kwargs):
            if conn := kwargs.get("connection"):
                connection_obj = conn
            elif conn := list(filter(lambda arg: isinstance(arg, Connection), args)):
                connection_obj = conn[0]
            else:
                connection_obj = (
                    getattr(args[0], 'connection', None) or getattr(args[0], '_connection')
                )

            if connection_obj._iserver_version < version:
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
        for name, method in getmembers(cls):
            if name in cls.__dict__ and callable(method) and not isinstance(
                    getattr_static(cls, name), staticmethod):
                setattr(cls, name, decorator(method))
        return cls

    return wrapper
