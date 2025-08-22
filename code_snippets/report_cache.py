"""This is the demo script to show how to manage report caches.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import ContentCache, Report
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name # Insert project ID here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get the project ID
PROJECT_ID = conn.project_id

# List all report caches for a given project
# This can be done in two ways
# Listing it through the Report class
Report.list_caches(connection=conn, project_id=PROJECT_ID)

# Listing it through the ContentCache class
# We have to specify the type of the cache we want to list in this case
ContentCache.list_caches(connection=conn, project_id=PROJECT_ID, type='report')

# Define a variable which can be later used in a script
REPORT_CACHE_ID = $cache_id # Insert ID of cache that you want to perform your actions upon

# Initializing the cache
REPORT_CACHE = ContentCache(connection=conn, id=REPORT_CACHE_ID)

# Listing properties of a cache
REPORT_CACHE.list_properties()

# Invalidating specific caches for reports
Report.invalidate_caches(connection=conn, ids=[REPORT_CACHE_ID])

# Deleting all caches for all reports
Report.delete_all_caches(connection=conn, force=True)

# Deleting a specific cache
REPORT_CACHE.delete(force=True)

# Deleting all caches from a specific warehouse table
WAREHOUSE_TABLE = $warehouse_table # Insert warehouse table name here
cache_ids = [cache.id for cache in Report.list_caches(connection=conn, project_id=PROJECT_ID, wh_tables=WAREHOUSE_TABLE)]
ContentCache.delete_caches(connection=conn, cache_ids=cache_ids, force=True)

# Loading and unloading all caches in a project
cache_ids = [cache.id for cache in Report.list_caches(connection=conn, project_id=PROJECT_ID)]
ContentCache.load_caches(connection=conn, cache_ids=cache_ids)
ContentCache.unload_caches(connection=conn, cache_ids=cache_ids)

# Deleting invalid caches from a project
cache_ids = [cache.id for cache in Report.list_caches(connection=conn, project_id=PROJECT_ID, status='invalid')]
ContentCache.delete_caches(connection=conn, cache_ids=cache_ids, force=True)

# Deleting invalid caches from multiple projects
PROJECT_ID_2 = $project_id_2 # Insert project ID here
PROJECTS = [PROJECT_ID, PROJECT_ID_2]
for project in PROJECTS:
    cache_ids = [cache.id for cache in Report.list_caches(connection=conn, project_id=project, status='invalid')]
    ContentCache.delete_caches(connection=conn, cache_ids=cache_ids, force=True)
