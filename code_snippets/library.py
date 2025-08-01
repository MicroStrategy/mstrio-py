"""This is the demo script to show how administrator can manage items as they
are published to Library.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.dashboard import Dashboard
from mstrio.project_objects.library import Library


# Create connection based on workstation data
PROJECT_NAME = $project_name  # Project to connect to
conn = get_connection(workstationData, project_name=PROJECT_NAME)

DASHBOARD_ID = $dashboard_id  # Insert ID of Dashboard on which you want to perform actions

# Get single dashboard by its id
dashboard = Dashboard(connection=conn, id=DASHBOARD_ID)

# Publish dashboard to Library
dashboard.publish()

# List all items in Library as shortcuts
library = Library(connection=conn)
shortcuts = library.list_library_shortcuts()
for shortcut in shortcuts:
    print(f"Shortcut: {shortcut.name} (ID: {shortcut.id})")
    target = shortcut.target
    print(f"  Target Name: {target['name']}, Target ID: {target['id']}")

# List all dashboards in Library
dashboards_in_lib = library.dashboards
for dash in dashboards_in_lib:
    print(f"Dashboard in Library: {dash.name} (ID: {dash.id})")
