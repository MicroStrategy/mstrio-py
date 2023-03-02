"""This is the demo script to show how administrator can manage reports.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.content_cache import ContentCache
from mstrio.project_objects.report import Report, list_reports

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Cache management
# List all report caches
cache_list = Report.list_caches(conn)

# list all reports
reports = list_reports(connection=conn)

# Define a variable which can be later used in a script
REPORT_ID = $report_id  # Insert ID of report here

# When extracting contents of a report instance, new cache is created
# (for projects where caching for the report is enabled)
Report(id=REPORT_ID, connection=conn).to_dataframe()

# List all report caches again (there is a new cache)
updated_list = Report.list_caches(conn)

# Define variables which can be later used in a script
REPORT_CACHE_ID_1 = $report_cache_id_1  # Insert ID of report cache on which you want to perform actions
REPORT_CACHE_ID_2 = $report_cache_id_2  # Insert ID of report cache on which you want to perform actions

# List report caches with different conditions
list_of_all_caches = Report.list_caches(conn)

# Define variables which can be later used in the script
PROJECT_ID = $project_id  # Insert project ID here
NODE_NAME = $node_name  # Insert name of node or list of names on which you want to perform actions

# List report caches in a project
list_of_caches_for_project = Report.list_caches(connection=conn, project_id=PROJECT_ID)

# List report caches in a node
list_of_caches_for_node = Report.list_caches(connection=conn, nodes=NODE_NAME)

# List report caches by id
list_of_one_cache = Report.list_caches(connection=conn, id=REPORT_CACHE_ID_1)

# List report caches as dictionary
list_of_caches_as_dicts = Report.list_caches(connection=conn, to_dictionary=True)

# Define variables which can be later used in a script
DB_CONNECTION_ID = $db_connection_id  # Insert ID of DB connection you want to include in your functions
DB_LOGIN_ID = $db_login_id  # Insert ID of DB login you want to include in your functions

# List report caches for database connection
list_of_caches_for_db_connection = Report.list_caches(
    connection=conn, db_connection_id=DB_CONNECTION_ID
)

# List report caches for database login
list_of_caches_for_db_login = Report.list_caches(
    connection=conn, db_login_id=DB_LOGIN_ID
)

# Define variables which can be later used in a script
USER_NAME = $user_name  # Insert name of the owner of some cache
WH_TABLE_ID = $wh_table_id  # Insert warehouse table ID that some cache is using

# List report caches by owner
list_of_caches_for_owner = Report.list_caches(connection=conn, owner=USER_NAME)

# List report caches for warehouse table
list_of_caches_for_wh_table = Report.list_caches(connection=conn, wh_tables=WH_TABLE_ID)

# List report caches by status
list_of_caches_loaded = Report.list_caches(connection=conn, status='loaded')

# Get single report cache by its id
report_cache = ContentCache(connection=conn, id=REPORT_CACHE_ID_1)

# Listing properties of content cache
properties = report_cache.list_properties()

# Unload content cache
report_cache.unload()

# Check report cache status
status = report_cache.status
print(status)

# Load content cache
report_cache.load()

# Delete content cache with confirmation prompt
report_cache.delete()

# Delete content cache without confirmation prompt
report_cache.delete(force=True)

# Refresh content cache
report_cache.fetch()

# Managing multiple specific caches
# Load multiple caches
ContentCache.load_caches(conn, cache_ids=[REPORT_CACHE_ID_1, REPORT_CACHE_ID_2])

# Unload multiple caches
ContentCache.unload_caches(conn, cache_ids=[REPORT_CACHE_ID_1, REPORT_CACHE_ID_2])

# Delete multiple caches with confirmation prompt
ContentCache.delete_caches(conn, cache_ids=[REPORT_CACHE_ID_1, REPORT_CACHE_ID_2])

# Delete multiple caches without confirmation prompt
ContentCache.delete_caches(conn, cache_ids=[REPORT_CACHE_ID_1, REPORT_CACHE_ID_2], force=True)

# Managing all caches meeting the criteria
# Load all report caches
Report.load_all_caches(conn)

# Load all report caches owned by specific user
Report.load_all_caches(connection=conn, owner=USER_NAME)

# Unload all report caches
Report.unload_all_caches(conn)

# Unload all report caches owned by specific user
Report.unload_all_caches(connection=conn, owner=USER_NAME)

# Delete all report caches
Report.delete_all_caches(conn)  # with confirmation prompt
Report.delete_all_caches(conn, force=True)  # without confirmation prompt

# Delete all report caches owned by specific user
Report.delete_all_caches(connection=conn, owner=USER_NAME)  # with confirmation prompt
Report.delete_all_caches(connection=conn, owner=USER_NAME, force=True)  # without confirmation prompt

# Delete all loaded report caches
Report.delete_all_caches(connection=conn, status='loaded')  # with confirmation prompt
Report.delete_all_caches(connection=conn, status='loaded', force=True)  # without confirmation prompt
