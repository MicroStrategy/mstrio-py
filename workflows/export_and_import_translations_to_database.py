"""This is the demo script to show how to export translations to database
and import them back. This script will not work without replacing parameters
with real values. Its basic goal is to present what can be done with this
module and to ease its usage.

1. Connect to the environment using data from workstation
2. Search for first ten metrics with "Revenue" in their name
3. Define export destination datasource (in this case "Tutorial Postgres")
4. Export translations to database without extra parameters
5. Import translations from database standard way
6. Export translations to database with specific languages only
7. Import translations from database with removing translations
   and auto matching target's ids
8. Export translations to database with extra columns
9. Import translations from database standard way
"""

from mstrio.connection import get_connection
from mstrio.datasources import DatasourceInstance
from mstrio.object_management import Translation
from mstrio.server import Language
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectTypes

# Define a variable which can be later used in a script
PROJECT_NAME = 'MicroStrategy Tutorial'  # Project to connect to


# Create connection based on workstation data
CONN = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
LANG_ID = '000004104F95EF3956E52781700C1E7A'
LANG_2_ID = '0000041D4F95EF3956E52781700C1E7A'
LANGUAGE_OBJECT = Language(connection=CONN, id=LANG_ID)
LANGUAGE_OBJECT_2 = Language(connection=CONN, id=LANG_2_ID)

# Search for first ten metrics with 'Revenue' in their name
search_result = full_search(
    connection=CONN,
    project=CONN.project_id,
    type=ObjectTypes.METRIC,
    name='Revenue',
    to_dictionary=False,
    limit=10,
)

# Export translations to database
# The flag force=True will be used in the examples
# That flag means no confirmation will be asked before overwriting the specified table
# If the flag is not used, the user will be asked for confirmation before overwriting

# First we need to define export destination datasource
# In this case it would be "Tutorial Postgres"
DATASOURCE = DatasourceInstance(connection=CONN, id='A23BBC514D336D5B4FCE919FE19661A3')

# Export translations to database without extra parameters
Translation.to_database_from_list(
    connection=CONN,
    object_list=search_result,
    table_name='test_table',
    datasource=DATASOURCE,
    force=True,
)

# Import translations from database standard way
Translation.add_translations_from_database(
    connection=CONN, table_name='test_table', datasource=DATASOURCE
)

# Export translations to database with specific languages only
Translation.to_database_from_list(
    connection=CONN,
    object_list=search_result,
    table_name='test_table',
    datasource=DATASOURCE,
    languages=[LANG_ID, LANG_2_ID],
    force=True,
)

# Import translations from database with removing translations and automatching target_ids
Translation.add_translations_from_database(
    connection=CONN,
    table_name='test_table',
    datasource=DATASOURCE,
    delete=True,
    automatch_target_ids=True,
)

# Export translations to database with extra columns
Translation.to_database_from_list(
    connection=CONN,
    object_list=search_result,
    table_name='test_table',
    datasource=DATASOURCE,
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
    force=True,
)

# Import translations from database standard way
Translation.add_translations_from_database(
    connection=CONN, table_name='test_table', datasource=DATASOURCE
)
