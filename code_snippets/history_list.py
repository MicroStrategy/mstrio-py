"""This is the demo script to show how to manage history list messages.

Its basic goal is to present what can be done with this module and to
ease its usage.

=== [WIP Disclaimer] ===
This module is not implemented fully yet. It currently contains only
functionalities related to deleting all history list messages from all users.
"""

from mstrio.connection import get_connection
from mstrio.server.history_list import (
    delete_all_history_list_messages,
    list_history_list_messages,
)

# Create connection to the environment
conn = get_connection(connectionData)

# list all history list messages for all users as dictionaries of data
messages = list_history_list_messages(conn)
print(messages)

# Delete all history list messages for all users
delete_all_history_list_messages(conn)
# The functionality will confirm whether the process failed or partially failed
# by leaving a warning.
