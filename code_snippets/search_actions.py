"""This is the demo script to show how to search for items using mstrio-py with
limited data available.

This script will not work without replacing parameters with real values.
"""

from mstrio.connection import get_connection
from mstrio.object_management.search_operations import find_objects_with_id

# Define variables which can be later used in a script
OBJECT_ID = $object_id  # ID of an object to search for
SEARCH_PROJECT_ID1 = $search_project_id1
SEARCH_PROJECT_ID2 = $search_project_id2

# Connect to the Strategy One environment
conn = get_connection(workstationData)

# There might be many cases where you have access to an ID of an object but not
# to its type, project or projects (if any) where it is.
#
# mstrio-py has a method to find the object(s) in such cases and you can use it
# as follows:
elements = find_objects_with_id(conn, OBJECT_ID)

# [DISCLAIMER]
# Have in mind this is a very resource intensive method and should be used for
# debugging purposes and not in a production code unless necessary.

# The returned `elements` is a list of objects with a provided `OBJECT_ID` in
# a particular shape:
#
# [
#   {"project_id": <str>, "object_data": <Entity-based-object>},
#   ...
# ]
#
# If an object is a configuration-level object (for example a `User`),
# the returned list would look like this (notice `project_id` being `None` for
# configuration-level objects):
#
# [
#     {
#         "project_id": None,
#         "object_data": User(conn, id=OBJECT_ID),
#     }
# ]
#
# If an object is a project-level object (for example a `Folder`), all instances
# of it will be found and the list may look like this:
#
# [
#   {"project_id": "B3FEE61A11E696...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
#   {"project_id": "4BAE16A340B995...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
#   {"project_id": "0DDDDEC8C94B32...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
#   {"project_id": "B7CA92F04B9FAE...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
#   {"project_id": "4C09350211E697...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
#   {"project_id": "CE52831411E696...",
#    "object_data": Folder(conn, id=OBJECT_ID)},
# ]

# If you know that a particular ID can be found only in at least one of specific
# places, you can provide additional parameters to the method to narrow the
# search.
#
# If you know that the object is a configuration-level object:
elements = find_objects_with_id(
    conn, OBJECT_ID, config_level_only=True
)

# If you know that the object is only within at most a set of
# particular Projects:
elements = find_objects_with_id(
    conn, OBJECT_ID, projects=[SEARCH_PROJECT_ID1, SEARCH_PROJECT_ID2]
)

# Additionally, if you wish to receive only a raw dictionary of data for each
# found object instead of an initialized mstrio-py's module, you can provide
# a flag to do so:
elements = find_objects_with_id(conn, OBJECT_ID, to_dictionary=True)
