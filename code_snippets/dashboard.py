"""This is the demo script to show how to manage dashboards. Its basic goal is
to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.dashboard import (
    Dashboard,
    list_dashboards,
    list_dashboards_across_projects
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define variables which can be later used in a script
PROJECT_ID = $project_id # Insert project ID here
DASHBOARD_NAME = $dashboard_name  # Insert name of the Dashboard here

# Dashboard management
# List dashboards with different conditions
list_of_all_dashboards = list_dashboards(connection=conn)
print(list_of_all_dashboards)
list_of_all_dashboards_as_dicts = list_dashboards(connection=conn, to_dictionary=True)
print(list_of_all_dashboards_as_dicts)
list_of_all_dashboards_as_dataframes = list_dashboards(connection=conn, to_dataframe=True)
print(list_of_all_dashboards_as_dataframes)
list_of_dashboards_by_project_id = list_dashboards(connection=conn, project_id=PROJECT_ID)
print(list_of_dashboards_by_project_id)
list_of_dashboards_by_name = list_dashboards(connection=conn, name=DASHBOARD_NAME)
print(list_of_dashboards_by_name)

# List of dashboards across projects, with examples of different conditions
list_of_dashboards_across_projects = list_dashboards_across_projects(connection=conn)
print(list_of_dashboards_across_projects)
list_of_dashboards_across_projects_as_dicts = list_dashboards_across_projects(
    connection=conn, to_dictionary=True
)
print(list_of_dashboards_across_projects_as_dicts)
list_of_dashboards_across_projects_as_dataframe = list_dashboards_across_projects(
    connection=conn, to_dataframe=True
)
print(list_of_dashboards_across_projects_as_dataframe)

# Define a variable which can be later used in a script
DASHBOARD_ID = $dashboard_id  # Insert ID of Dashboard on which you want to perform actions

# Get single dashboard by its id
dashboard = Dashboard(connection=conn, id=DASHBOARD_ID)

# List dashboard properties
properties = dashboard.list_properties()
print(properties)

# Delete dashboard without prompt
dashboard.delete(force=True)

# Define variables which can be later used in a script
NEW_DASHBOARD_NAME = $new_dashboard_name  # Insert new name of edited dashboard here
NEW_DASHBOARD_DESCRIPTION = $new_dashboard_description  # Insert new description of edited dashboard here
FOLDER_ID = $folder_id  # Insert folder ID here

# Alter dashboard
dashboard.alter(name=NEW_DASHBOARD_NAME)
dashboard.alter(description=NEW_DASHBOARD_DESCRIPTION)
dashboard.alter(folder_id=FOLDER_ID)

# Define a variable which can be later used in a script
USER_ID = $user_id  # Insert user ID here

# Publish and unpublish dashboard
dashboard.publish()
dashboard.publish(recipients=USER_ID)
dashboard.unpublish()

# Share dashboard with given user
dashboard.share_to(users=USER_ID)

# List dashboard schedules
schedules = dashboard.list_available_schedules()
print(schedules)
schedules_as_dicts = dashboard.list_available_schedules(to_dictionary=True)
print(schedules_as_dicts)

# List connected cubes
cubes = dashboard.get_connected_cubes()
print(cubes)

# Get list of dashboard cache, with examples of different conditions
list_of_all_dashboard_cache = Dashboard.list_caches(connection=conn)
print(list_of_all_dashboard_cache)
list_of_limited_dashboard_cache = Dashboard.list_caches(connection=conn, limit=5)
print(list_of_limited_dashboard_cache)

# Define a variable which can be later used in a script
CACHE_ID = $cache_id  # Insert ID of cache on which you want to perform actions

list_of_dashboard_cache_by_id = Dashboard.list_caches(connection=conn, id=CACHE_ID)
print(list_of_dashboard_cache_by_id)
list_of_all_dashboard_caches_as_dicts = Dashboard.list_caches(connection=conn, to_dictionary=True)
print(list_of_all_dashboard_caches_as_dicts)

# Helper function to list all cache status
def show_caches_status():
    caches = Dashboard.list_caches(conn)
    for cache in caches:
        print(f'Cache ID: {cache.id}, {cache.status}')


# List cache properties
cache = Dashboard.list_caches(connection=conn)[0]
properties = cache.list_properties()
print(properties)

# Define a variable which can be later used in a script
OTHER_CACHE_ID = $other_cache_id  # Insert ID of cache on which you want to perform actions

# Unload multiple dashboard caches
Dashboard.unload_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Define variables which can be later used in a script
CACHE_STATUS = $cache_status # Insert cache status here
USER_NAME = $user_name # Insert user name here

# Unload all dashboard caches with filter examples
Dashboard.unload_all_caches(connection=conn)
show_caches_status()
Dashboard.unload_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Dashboard.unload_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Load multiple dashboard caches
Dashboard.load_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID])
show_caches_status()

# Load all dashboard caches with filter examples
Dashboard.load_all_caches(connection=conn)
show_caches_status()
Dashboard.load_all_caches(connection=conn, owner=USER_NAME)
show_caches_status()
Dashboard.load_all_caches(connection=conn, status=CACHE_STATUS)
show_caches_status()

# Invalidating specific caches for dashboards
Dashboard.invalidate_caches(connection=conn, ids=[CACHE_ID])

# Delete multiple dashboard caches
Dashboard.delete_caches(connection=conn, cache_ids=[CACHE_ID, OTHER_CACHE_ID], force=True)

# Delete all dashboard caches with filter examples
Dashboard.delete_all_caches(connection=conn, force=True)
Dashboard.delete_all_caches(connection=conn, owner=USER_NAME, force=True)
Dashboard.delete_all_caches(connection=conn, status=CACHE_STATUS, force=True)
