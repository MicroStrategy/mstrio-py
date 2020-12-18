import mstrio.utils.helper as helper
from mstrio import connection

Connection = connection.Connection
warning_text = """Connection class has been moved to connection module in mstrio-py 11.2.2.
Support for microstrategy.connection will be dropped in the future versions."
"""
helper.exception_handler(warning_text, exception_type=DeprecationWarning)
