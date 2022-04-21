import logging
import sys
import warnings

from pandas import options

verbose = True  # Controls the amount of feedback from the I-Server
fetch_on_init = True  # Controls if object will fetch basic data from server on init
progress_bar = True  # Controls whether progress bar will be shown during long fetch operations
debug = False  # Lets the program run in debugging mode
# Sets number of rows displayed for pandas DataFrame
options.display.max_rows = max(250, options.display.max_rows)
options.display.max_colwidth = max(100, options.display.max_colwidth)
# Warning settings: "error", "ignore", "always", "default", "module", "once"
print_warnings = 'always'
module_path = 'mstrio.*'
save_responses = False  # Used to save REST API responses for mocking
wip_warnings_enabled = True  # Controls whether warnings/errors about WIP functionality are emitted


def custom_formatwarning(msg, category, *args, **kwargs):
    # ignore everything except the message
    return str(category.__name__) + ': ' + str(msg) + '\n'


warnings.formatwarning = custom_formatwarning
warnings.filterwarnings(action=print_warnings, module=module_path)
warnings.filterwarnings(action=print_warnings, category=DeprecationWarning, module=module_path)
warnings.filterwarnings(action='default', category=UserWarning, module=module_path)


logging_level = logging.DEBUG if debug else logging.INFO
logger_stream_handler = logging.StreamHandler(stream=sys.stdout)

# warns issued by the warnings module will be redirected to the logging.warning
logging.captureWarnings(True)

logger = logging.getLogger()
warnings_logger = logging.getLogger("py.warnings")

logger.addHandler(logger_stream_handler)
logger.setLevel(logging_level)
