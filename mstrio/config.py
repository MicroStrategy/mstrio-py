import contextlib
import logging
import sys
import warnings

from pandas import options

with contextlib.suppress(ImportError):
    from tqdm import TqdmWarning

# FYI: when editing this file, make sure to update info in config code snippets

verbose = True
"""Controls the amount of feedback from the I-Server."""
fetch_on_init = True
"""Controls if object will fetch basic data from server on init."""
progress_bar = True
"""Controls whether progress bar will be shown during long fetch operations."""
debug = False
"""Lets the program run in debugging mode, logging more information
at each step.
"""
wip_warnings_enabled = True
"""Controls whether warnings/errors about WIP functionality are emitted"""
default_request_timeout: int | float | None = 60 * 60 * 24
"""Time (in seconds) after which every `Connection.<request_type>(...)` method
(example: `Connection.get(...)`) times out and stops waiting for response,
raising `requests.Timeout`. Default is 86400 seconds (24 hours).

It uses `requests` library's `timeout` parameter under the hood. (read more:
<https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts>)
"""

# Sets number of rows displayed for pandas DataFrame
options.display.max_rows = max(250, options.display.max_rows)
options.display.max_colwidth = max(100, options.display.max_colwidth)

# Warning settings: "error", "ignore", "always", "default", "module", "once"
print_warnings = 'always'
module_path = 'mstrio.*'
save_responses = False  # Used to save REST API responses for mocking


def _custom_formatwarning(msg, category, *args, **kwargs):
    # ignore everything except the message
    return str(category.__name__) + ': ' + str(msg) + '\n'


warnings.formatwarning = _custom_formatwarning

# filters are applied in reversed order to the order of adding them (LIFO)
if "TqdmWarning" in locals():
    warnings.filterwarnings(
        action="ignore", category=TqdmWarning, message=".*IProgress not found.*"
    )

warnings.filterwarnings(action=print_warnings, module=module_path)
warnings.filterwarnings(action='default', category=UserWarning, module=module_path)
warnings.filterwarnings(
    action=print_warnings, category=DeprecationWarning, module=module_path
)


def get_logging_level() -> int:
    """Calculate and return logging level
    to configure logger.
    """
    return logging.DEBUG if debug else logging.INFO


_logger_stream_handler = logging.StreamHandler(stream=sys.stdout)
_warn_stream_handler = logging.StreamHandler(stream=sys.stderr)

# warns issued by the warnings module will be redirected to the logging.warning
logging.captureWarnings(True)

# root logger for mstrio, all loggers in submodules will have keys of the form
# "mstrio.sub1.sub2" and have this one as its ancestor
logger = logging.getLogger("mstrio")
logger.propagate = False
logger.addHandler(_logger_stream_handler)
logger.setLevel(get_logging_level())

warnings_logger = logging.getLogger("py.warnings")
warnings_logger.addHandler(_warn_stream_handler)
warnings_logger.setLevel(logging.WARNING)


def toggle_debug_mode() -> None:
    """Toggle debug mode between INFO and DEBUG.
    It will change root logger's logging level.
    """
    global debug
    debug = not debug
    logger.setLevel(get_logging_level())


@contextlib.contextmanager
def temp_verbose_disable():
    """Temporarily disable verbose logging, with keeping current state.

    Built to be used as context with `with` statement:

        >>> with temp_verbose_disable():
        >>>     ...
    """
    global verbose
    old_verbose = verbose
    verbose = False
    try:
        yield
    finally:
        verbose = old_verbose
