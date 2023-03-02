from enum import auto, Enum
import functools
from itertools import filterfalse
import logging
import sys
from textwrap import dedent
from typing import Optional, Union

from packaging.version import Version

from .exceptions import NotSupportedError
from .. import __version__, config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stderr)  # NOSONAR

current_version = Version(__version__)


class WipLevels(Enum):
    SILENT = auto()
    PREVIEW = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


def _wiplevel_error(level):
    raise ValueError(f'Unrecognised WipLevel {level}.')


message_templates = {
    WipLevels.PREVIEW: (
        "In a current version, {}is available as "
        "a Functionality Preview. It is subject to change until it is released "
        "as Generally Available."
    ),
    WipLevels.INFO: "This {}functionality is a work-in-progress. It may change in future updates.",
    WipLevels.WARNING: (
        "This {}functionality is a work-in-progress. Use it only if you understand"
        " the underlying code. It may change in future updates."
    ),
    WipLevels.ERROR: (
        "This {}functionality is a work-in-progress. It has been deemed unsafe to use"
        " and is currently blocked."
    ),
}
release_info_template = " It is currently scheduled for {} release."
docstring_prefix_template = dedent(
    """\
    ------------------ WORK IN PROGRESS ------------------

    {}

    ------------------------------------------------------

"""
)


def _get_message_template(level: WipLevels = WipLevels.WARNING):
    if level in message_templates.keys():
        return message_templates[level]
    else:
        return message_templates[WipLevels.INFO]


def _construct_message(
    name: Optional[str] = None,
    target_release: Optional[Union[Version, str]] = None,
    level: WipLevels = WipLevels.WARNING
):
    template = _get_message_template(level)
    if name is None:
        message = template.format("")
    else:
        message = template.format(f"({name}) ")
    if target_release is not None:
        message += release_info_template.format(target_release)
    return message


def _emit(
    name: Optional[str] = None,
    target_release: Optional[Union[Version, str]] = None,
    level: WipLevels = WipLevels.WARNING,
    message: Optional[str] = None
):
    if level == WipLevels.SILENT or not config.wip_warnings_enabled:
        return None

    if message is None:
        message = _construct_message(name, target_release, level)

    if level == WipLevels.INFO or level == WipLevels.PREVIEW:
        logger.info(message)
    elif level == WipLevels.WARNING:
        logger.warning(message)
    elif level == WipLevels.ERROR:
        raise NotSupportedError(message)
    else:
        _wiplevel_error(level)


def wip(
    target_release: Optional[Union[Version, str]] = None,
    level: WipLevels = WipLevels.WARNING,
    message: Optional[str] = None,
    prefix_doc: Union[bool, str] = True,
    mark_attr: bool = True
):
    """Work-In-Progress wrapper

    Note:
        This is a decorator generator, which accepts arguments and returns the
        actual decorator, so even when not providing arguments and letting it
        choose the defaults it should be used like `@wip()`, not plain `@wip`.

    Args:
        target_release: The target release when the functionality is scheduled
            to be production-ready.
        level: The severity level of the warning emitted when the functionality
            is loaded or used.
            SILENT: no warning will be emitted
            PREVIEW: a warning will be dispatched
            INFO: a disclaimer will be printed to stderr
            WARNING: a warning will be dispatched
            ERROR: an error will be raised
        message: A custom message to replace the one standard to the given level
        prefix_doc: Whether to prefix the docstring with a WIP warning.
            Accepts bool values or a custom string to replace standard prefix.
        mark_attr: Marks the wrapped function via adding the `_wip` attribute,
            which is checked by `is_wip`.
    """
    if target_release is not None:
        if not isinstance(target_release, Version):
            target_release = Version(target_release)
        if target_release <= current_version:
            raise ValueError(
                "WIP wrapper called with target_release equal to"
                " or lower than current release."
            )
    if level not in WipLevels:
        _wiplevel_error(level)

    def wrap_func(f):

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            _emit(wrapped.__name__, target_release, level, message)
            return f(*args, **kwargs)

        if mark_attr:
            wrapped._wip = True  # This makes it trivial to programmatically check.
        if prefix_doc:
            if not wrapped.__doc__:
                wrapped.__doc__ = ""
            if isinstance(prefix_doc, str):
                wrapped.__doc__ = prefix_doc + wrapped.__doc__
            else:
                if message is not None:
                    docstring_prefix = docstring_prefix_template.format(message)
                else:
                    msg = _construct_message(target_release=target_release, level=level)
                    docstring_prefix = docstring_prefix_template.format(msg)
                wrapped.__doc__ = docstring_prefix + wrapped.__doc__
        return wrapped

    return wrap_func


def module_wip(
    module_globals: dict,
    target_release: Optional[Union[Version, str]] = None,
    level: WipLevels = WipLevels.WARNING,
    message: Optional[str] = None,
    prefix_doc: Union[bool, str] = True,
    mark_attr: bool = True
):
    """Emit the WIP warning/error/info when the module is loaded."""
    if mark_attr:
        module_globals["_wip"] = True
    if prefix_doc:
        if not module_globals["__doc__"]:
            module_globals["__doc__"] = ""
        if isinstance(prefix_doc, str):
            module_globals["__doc__"] = prefix_doc + module_globals["__doc__"]
        else:
            if message is not None:
                docstring_prefix = docstring_prefix_template.format(message)
            else:
                msg = _construct_message(target_release=target_release, level=level)
                docstring_prefix = docstring_prefix_template.format(msg)
            module_globals["__doc__"] = docstring_prefix + module_globals["__doc__"]
    _emit(f"module {module_globals['__name__']}", target_release, level, message)


def pause_wip_warnings():
    previous_setting = config.wip_warnings_enabled
    config.wip_warnings_enabled = False
    return previous_setting


def resume_wip_warnings(previous_setting: bool):
    config.wip_warnings_enabled = previous_setting


def is_wip(obj) -> bool:
    return getattr(obj, "_wip", False)


def is_module_wip(module_globals: dict) -> bool:
    return module_globals.get("_wip", False)


def filter_wip(iterable, return_wip: bool = False):
    """Return a generator containing only non-WIP elements
        (or only WIP elements, depending on `return_wip` parameter.).

    Args:
        iterable: Any iterable containing elements that may or may not be WIP.
        return_wip: Whether to return only WIP results or the opposite.
            Default `False` (return only non-WIP).
    """
    if return_wip:
        return filter(is_wip, iterable)
    return filterfalse(is_wip, iterable)


def filter_wip_dict(dict: dict, return_wip: bool = False) -> dict:
    """Return a dict containing only non-WIP elements
        (or only WIP elements, depending on `return_wip` parameter.).

    Args:
        dict: Any dict containing elements that may or may not be WIP.
        return_wip: Whether to return only WIP results or the opposite.
            Default `False` (return only non-WIP).
    """
    if return_wip:
        return {key: val for key, val in dict.items() if is_wip(val)}
    return {key: val for key, val in dict.items() if not is_wip(val)}
