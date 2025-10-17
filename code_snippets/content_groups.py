"""This is the demo script to show how to manage content groups.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.content_group import (
    ContentGroup,
    list_content_groups,
)
from mstrio.project_objects.dashboard import Dashboard
from mstrio.users_and_groups import User, UserGroup

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert name of project here

conn = get_connection(workstationData, project_id=PROJECT_ID)

# List content groups with different conditions
# Note: No Content Groups exist in a default environment
list_of_all_cgs = list_content_groups(connection=conn)
print(list_of_all_cgs)
list_of_all_cgs_as_dicts = list_content_groups(connection=conn, to_dictionary=True)
print(list_of_all_cgs_as_dicts)

# Define variables which can be later used in a script
CG_NAME = $cg_name
CG_COLOR = $cg_color
CG_OPACITY = $cg_opacity
CG_EMAIL_ENABLED = $cg_email_enabled == 'True'
CG_RECIPIENT_ID = $cg_recipient_id
CG_USER_RECIPIENT_ID = $cg_user_recipient_id
CG_USER_GROUP_RECIPIENT_ID = $cg_user_group_recipient_id

# Create a Content Group
# Recipients can be provided as a User, UserGroup, or an ID of one of them
# Color has to be provided as a hex value, e.g. '#ff2400'
cg = ContentGroup.create(
    connection=conn,
    name=CG_NAME,
    color=CG_COLOR,
    opacity=CG_OPACITY,
    email_enabled=CG_EMAIL_ENABLED,
    recipients=[
        User(connection=conn, id=CG_USER_RECIPIENT_ID),
        UserGroup(connection=conn, id=CG_USER_GROUP_RECIPIENT_ID),
        CG_RECIPIENT_ID,
    ],
)

# Define variables which can be later used in a script
CG_ID = $cg_id

# Get a Content Group by it's id or name
cg = ContentGroup(connection=conn, id=CG_ID)
cg = ContentGroup(connection=conn, name=CG_NAME)

# Define variables which can be later used in a script
DASHBOARD_ID_1 = $dashboard_id_1
DASHBOARD_ID_2 = $dashboard_id_2

# Add Contents to a Content Group
# Accepted content types are: Dashboard, Document, Report and Agent
cg.update_contents(
    content_to_add=[
        Dashboard(connection=conn, id=DASHBOARD_ID_1),
        Dashboard(connection=conn, id=DASHBOARD_ID_2),
    ]
)
# Remove Contents from a Content Group
cg.update_contents(
    content_to_remove=[
        Dashboard(connection=conn, id=DASHBOARD_ID_1),
    ]
)
# Contents can be added and removed in one call
cg.update_contents(
    content_to_add=[
        Dashboard(connection=conn, id=DASHBOARD_ID_1),
    ],
    content_to_remove=[
        Dashboard(connection=conn, id=DASHBOARD_ID_2),
    ],
)

# Get contents of a Content Group
contents = cg.get_contents(project_ids=[PROJECT_ID])

# Define variables which can be later used in a script
CG_NAME_ALTERED = $cg_name_altered
CG_COLOR_ALTERED = $cg_color_altered
CG_OPACITY_ALTERED = $cg_opacity_altered
CG_EMAIL_ENABLED_ALTERED = $cg_email_enabled_altered == 'True'
CG_RECIPIENT_ID_ALTERED = $cg_recipient_id_altered

# Alter a Content Group
cg.alter(
    name=CG_NAME_ALTERED,
    color=CG_COLOR_ALTERED,
    opacity=CG_OPACITY_ALTERED,
    email_enabled=CG_EMAIL_ENABLED_ALTERED,
    recipients=[CG_RECIPIENT_ID_ALTERED],
)

# Delete a Content Group without prompt
cg.delete(force=True)
