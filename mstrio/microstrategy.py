import warnings

from mstrio import connection

Connection = connection.Connection
warnings.simplefilter('always', DeprecationWarning)
warning_text = """Connection class has been moved to connection module in mstrio-py 11.2.2. 
Support for microstrategy.connection will be dropped in the future versions."
"""

warnings.warn(warning_text, DeprecationWarning)
