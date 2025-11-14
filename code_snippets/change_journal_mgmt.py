"""This is the demo script to show how to review and manage change journal
entries via mstrio-py.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from datetime import datetime
from pprint import pprint
from time import sleep

from mstrio.connection import get_connection
from mstrio.modeling import Metric
from mstrio.server import (
    Environment,
    Project,
    list_change_journal_entries,
    purge_change_journal_entries,
)


# Define a variable which will be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

SELECTED_PROJECT_ID = $selected_project_id

# List change journal properties across all projects in the environment
# This operation can take a long time depending on the amount of data
entries_all = list_change_journal_entries(conn)
print(len(entries_all))

# List change journal properties for configuration project only
CONFIGURATION_PROJECT_ID = $configuration_project_id
entries_configuration_proj = list_change_journal_entries(
    conn, affected_projects=CONFIGURATION_PROJECT_ID
)
print(len(entries_configuration_proj))

# List change journal properties for specified project
entries_selected = list_change_journal_entries(
    conn, affected_projects=SELECTED_PROJECT_ID
)
print(len(entries_selected))

# List change journal entries for specified user
USER_ID = $user_id

entries_user = list_change_journal_entries(conn, users=USER_ID)
print(len(entries_user))

# List change journal entries from defined time period you can
# use both string or datetime object as begin_time and end_time
begin_time = '10/01/2022 12:00:00 AM'
end_time = datetime(2025, 10, 24, 23, 59, 59)

entries_time_period = list_change_journal_entries(
    conn, begin_time=begin_time, end_time=end_time
)
print(len(entries_time_period))


# Get change journal entries for specific objects
OBJECT_ID_1 = $object_id_1
OBJECT_ID_2 = $object_id_2

entries_object = list_change_journal_entries(conn, affected_objects=[OBJECT_ID_1, OBJECT_ID_2])
print(len(entries_object))

# Get change journal entries for specific object by its property
selected_object = Metric(conn, id=OBJECT_ID_1)
change_journals = selected_object.change_journal
print(change_journals[0])

# Fetch change journal entries for specific object
selected_object.fetch_all_change_journal_entries()

# Purge change journal entries for selected project before specific time
PURGE_TIME = $purge_time
entries_before = list_change_journal_entries(
    conn, affected_projects=SELECTED_PROJECT_ID
)
print(f'Entries before purge: {len(entries_before)}')
selected_project = Project(connection=conn, id=SELECTED_PROJECT_ID)
selected_project.purge_change_journals(
    comment=f'Purging old entries before {PURGE_TIME}', timestamp=PURGE_TIME
)
entries_after = list_change_journal_entries(conn, affected_projects=SELECTED_PROJECT_ID)
print(f'Entries after purge: {len(entries_after)}')

# Purge configuration change journal entries before specific time
entries_before = list_change_journal_entries(
    conn, affected_projects=CONFIGURATION_PROJECT_ID
)
print(f'Configuration entries before purge: {len(entries_before)}')
env = Environment(connection=conn)
env.purge_configuration_change_journals(
    comment=f'Purging old configuration entries before {PURGE_TIME}',
    timestamp=PURGE_TIME,
)
sleep(5)  # wait for the purge to be processed
entries_after = list_change_journal_entries(
    conn, affected_projects=CONFIGURATION_PROJECT_ID
)
print(f'Configuration entries after purge: {len(entries_after)}')

# Purge change journal entries for specified user before specific time for provided projects
# When leaving projects param as None, entries will be purged for all loaded projects
SECOND_PROJECT_ID = $second_project_id
purge_change_journal_entries(
    conn,
    projects=[SELECTED_PROJECT_ID, SECOND_PROJECT_ID],
    comment=f'Purging old entries before {PURGE_TIME}',
    timestamp=PURGE_TIME,
)

# Purge change journal entries before specific time for all projects
# existing in the environment including configuration change journal entries
entries_before = list_change_journal_entries(conn)
print(f'All entries before purge: {len(entries_before)}')
conn.environment.purge_all_change_journals(
    comment=f'Purging all old entries before {PURGE_TIME}', timestamp=PURGE_TIME
)
sleep(10)  # wait for the purge to be processed
entries_after = list_change_journal_entries(conn)
print(f'All entries after purge: {len(entries_after)}')
