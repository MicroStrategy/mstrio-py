"""This is a template for a script to remove all history list messages for all
users. This script will work OOTB.

This script can only be run via Workstation (and then scheduled as Task)
currently. Modify how the `conn` Connection is set if you wish to run it
outside Workstation context.
"""

from mstrio.connection import get_connection
from mstrio.server.history_list import delete_all_history_list_messages

# connect to the environment inside Workstation
conn = get_connection(connectionData)


# delete all messages across all users
delete_all_history_list_messages(conn)
