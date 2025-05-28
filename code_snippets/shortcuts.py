"""This is the demo script to show how administrator can manage shortcuts.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling.metric import Metric
from mstrio.object_management.shortcut import list_shortcuts


# Create connection based on workstation data
PROJECT_NAME = $project_name  # Project to connect to
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Create a shortcut for an existing object, e.g. a metric
METRIC_ID = $metric_id
metric_object = Metric(conn, id=METRIC_ID)

TARGET_FOLDER_ID = $target_folder_id
shortcut = metric_object.create_shortcut(target_folder_id=TARGET_FOLDER_ID)

# List shortcuts
shortcuts = list_shortcuts(conn)
for sc in shortcuts:
    print(sc)

# list properties for a shortcut
properties = shortcut.list_properties()
for prop_name, prop_value in properties.items():
    print(f"{prop_name}: {prop_value}")

# alter properties of a shortcut
SHORTCUT_NEW_NAME = $shortcut_new_name
shortcut.alter(name=SHORTCUT_NEW_NAME)

# delete a shortcut
shortcut.delete(force=True)
