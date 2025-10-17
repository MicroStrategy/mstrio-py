"""This is the demo script to show how to manage Search Objects. Its basic goal
is to present what can be done with the SearchObject class, its related methods
and to ease its usage.

This script will not work without replacing parameters with real values.
"""

from mstrio.connection import get_connection
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_operations import (
    DateQuery,
    SearchObject,
    list_search_objects,
)
from mstrio.types import ObjectTypes

# Define variables which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to
FOLDER_ID = $folder_id  # ID of the folder where the Search Object will be created
FOLDER_QUERY_LISTING = $folder_query_listing  # ID of the folder where the Search Object listing will be narrowed down to
NAME_QUERY_1 = $name_query_1  # Object name to search for
NAME_QUERY_2 = $name_query_2  # Object name to search for (after update)
FOLDER_QUERY_1 = $folder_query_1  # Root folder to search in
FOLDER_QUERY_2 = $folder_query_2  # Root folder to search in (after update)


# Connect to the Strategy One environment
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List all Search Objects
search_objects = list_search_objects(conn)
print(f"Found {len(search_objects)} search objects.")

# List Search Objects in a given folder
search_objects = list_search_objects(conn, folder_id=FOLDER_QUERY_LISTING)
print(f"Found {len(search_objects)} search objects in folder.")

# Create a Search Object
new_so = SearchObject.create(
    conn,
    name='New Search Object',
    destination_folder=FOLDER_ID,
    project_name=PROJECT_NAME,
    name_query=NAME_QUERY_1,
    root_folder_query=FOLDER_QUERY_1,
    include_subfolders=True,
)

# List properties of the Search Object
properties = new_so.list_properties()
print(properties)

# Run search based on parameters stored in the Search Object
results = new_so.run(project_name=PROJECT_NAME)
print(f"Search returned {len(results)} results.")

# Update the Search Object
new_so.alter(
    name='Updated Search Object',
    description='This is an updated description',
    name_query=NAME_QUERY_2,
    root_folder_query=FOLDER_QUERY_2,
)

# Delete the Search Object
new_so.delete(force=True)
