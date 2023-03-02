"""This is the demo script to show how to manage dossiers. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.dossier import (
    Dossier,
    list_dossiers,
    list_dossiers_across_projects
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define variables which can be later used in a script
PROJECT_ID = $project_id # Insert project ID here
DOSSIER_NAME = $dossier_name  # Insert name of the Dossier here

# Dossier management
# List dossiers with different conditions
list_of_all_dossiers = list_dossiers(connection=conn)
print(list_of_all_dossiers)
list_of_all_dossiers_as_dicts = list_dossiers(connection=conn, to_dictionary=True)
print(list_of_all_dossiers_as_dicts)
list_of_all_dossiers_as_dataframes = list_dossiers(connection=conn, to_dataframe=True)
print(list_of_all_dossiers_as_dataframes)
list_of_dossiers_by_project_id = list_dossiers(connection=conn, project_id=PROJECT_ID)
print(list_of_dossiers_by_project_id)
list_of_dossiers_by_name = list_dossiers(connection=conn, name=DOSSIER_NAME)
print(list_of_dossiers_by_name)

# List of dossiers across projects, with examples of different conditions
list_of_dossiers_across_projects = list_dossiers_across_projects(connection=conn)
print(list_of_dossiers_across_projects)
list_of_dossiers_across_projects_as_dicts = list_dossiers_across_projects(
    connection=conn, to_dictionary=True
)
print(list_of_dossiers_across_projects_as_dicts)
list_of_dossiers_across_projects_as_dataframe = list_dossiers_across_projects(
    connection=conn, to_dataframe=True
)
print(list_of_dossiers_across_projects_as_dataframe)

# Define a variable which can be later used in a script
DOSSIER_ID = $dossier_id  # Insert ID of Dossier on which you want to perform actions

# Get single dossier by its id
dossier = Dossier(connection=conn, id=DOSSIER_ID)

# List dossier properties
properties = dossier.list_properties()
print(properties)

# Delete dossier without prompt
dossier.delete(force=True)

# Define variables which can be later used in a script
NEW_DOSSIER_NAME = $new_dossier_name  # Insert new name of edited dossier here
NEW_DOSSIER_DESCRIPTION = $new_dossier_description  # Insert new description of edited dossier here
FOLDER_ID = $folder_id  # Insert folder ID here

# Alter dossier
dossier.alter(name=NEW_DOSSIER_NAME)
dossier.alter(description=NEW_DOSSIER_DESCRIPTION)
dossier.alter(folder_id=FOLDER_ID)

# Define a variable which can be later used in a script
USER_ID = $user_id  # Insert user ID here

# Publish and unpublish dossier
dossier.publish()
dossier.publish(recipients=USER_ID)
dossier.unpublish()

# Share dossier with given user
dossier.share_to(users=USER_ID)

# List dossier schedules
schedules = dossier.list_available_schedules()
print(schedules)
schedules_as_dicts = dossier.list_available_schedules(to_dictionary=True)
print(schedules_as_dicts)

# List connected cubes
cubes = dossier.get_connected_cubes()
print(cubes)

# Get list of dossier cache, with examples of different conditions
list_of_all_dossier_cache = Dossier.list_caches(connection=conn)
print(list_of_all_dossier_cache)
list_of_limited_dossier_cache = Dossier.list_caches(connection=conn, limit=5)
print(list_of_limited_dossier_cache)

# Define a variable which can be later used in a script
CACHE_ID = $cache_id  # Insert ID of cache on which you want to perform actions

list_of_dossier_cache_by_id = Dossier.list_caches(connection=conn, id=CACHE_ID)
print(list_of_dossier_cache_by_id)
list_of_all_dossier_caches_as_dicts = Dossier.list_caches(connection=conn, to_dictionary=True)
print(list_of_all_dossier_caches_as_dicts)

# Helper function to list all cache status
def show_caches_status():
    caches = Dossier.list_caches(conn)
    for cache in caches:
        print(f'Cache ID: {cache.id}, {cache.status}')


# List cache properties
cache = Dossier.list_caches(connection=conn)[0]
properties = cache.list_properties()
print(properties)

# Define a variable which can be later used in a script
OTHER_CACHE_ID = $other_cache_id  # Insert ID of cache on which you want to perform actions

# Unload multiple dossier caches
Dossier.unload_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Define variables which can be later used in a script
CACHE_STATUS = $cache_status # Insert cache status here
USER_NAME = $user_name # Insert user name here

# Unload all dossier caches with filter examples
Dossier.unload_all_caches(connection=conn)
show_caches_status()
Dossier.unload_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Dossier.unload_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Load multiple dossier caches
Dossier.load_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Load all dossier caches with filter examples
Dossier.load_all_caches(connection=conn)
show_caches_status()
Dossier.load_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Dossier.load_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Delete multiple dossier caches
Dossier.delete_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID], force=True)

# Delete all dossier caches with filter examples
Dossier.delete_all_caches(connection=conn, force=True)
Dossier.delete_all_caches(connection=conn, owner=USER_NAME, force=True)
Dossier.delete_all_caches(connection=conn, status=CACHE_STATUS, force=True)
