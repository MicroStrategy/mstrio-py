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
save_responses = False  # Used to save REST API responses for mocking


def custom_formatwarning(msg, category, *args, **kwargs):
    # ignore everything except the message
    return str(category.__name__) + ': ' + str(msg) + '\n'


warnings.formatwarning = custom_formatwarning
warnings.filterwarnings(action=print_warnings, category=Warning, module='mstrio.*')
warnings.filterwarnings(action='always', category=DeprecationWarning, module='mstrio.*')
warnings.filterwarnings(action='default', category=UserWarning, module='mstrio.*')
