import warnings
from pandas import options


verbose = True      # Controls the amount of feedback from the I-Server
progress_bar = True  # Controls whether progress bar will be shown during long fetch operations
debug = False     # Lets the program run in debugging mode
options.display.max_rows = max(250, options.display.max_rows)  # Sets number of rows displayed for pandas DataFrame
options.display.max_colwidth = max(100, options.display.max_colwidth)
print_warnings = 'always'   # Warning setting, one of "error", "ignore", "always", "default", "module", or "once"
save_responses = False      # Used to save REST API responses for mocking


def custom_formatwarning(msg, category, *args, **kwargs):
    # ignore everything except the message
    return str(category.__name__) + ': ' + str(msg) + '\n'


warnings.formatwarning = custom_formatwarning
warnings.filterwarnings(action=print_warnings, module='mstrio.*')
warnings.filterwarnings(action='always', category=DeprecationWarning, module='mstrio.*')
warnings.filterwarnings(action='default', category=UserWarning, module='mstrio.*')
