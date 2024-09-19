from mstrio.connection import get_connection
from mstrio.project_objects.content_group import ContentGroup
from mstrio.project_objects.applications import Application
from mstrio.project_objects.dashboard import Dashboard
from mstrio.users_and_groups import User, UserGroup

conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# Create a Content Group
cg = ContentGroup.create(
    connection=conn,
    name='Content Group for Application',
    color='#ffe4e1',
    opacity=100,
    email_enabled=True,
    recipients=[
        User(connection=conn, id='0870757440D0FEB7CDC449AAE6C18AFF'),
        UserGroup(connection=conn, id='E96685CD4E60068559F7DFAC7C2AA851'),
    ],
)

# Add some contents to the Content Group
# Add Contents to a Content Group
cg.update_contents(
    content_to_add=[
        Dashboard(connection=conn, id='F6252B9211E7B348312C0080EF55DB6A'),
        Dashboard(connection=conn, id='27BB740E11E7A7B40A650080EF856B88'),
    ]
)

# Create an Application
# To limit the Application to only the specified group, pass the
# ContentGroup ID in the content_bundle_ids of the home_library settings
# And make sure to set show_all_contents to False

# Only the necessary variables are defined here
app = Application.create(
    connection=conn,
    name='Application Workflow Showcase',
    description='This is a demo application created for content group.',
    home_screen=Application.HomeSettings(
        mode=0,
        home_library=Application.HomeSettings.HomeLibrary(
            content_bundle_ids=[cg.id],
            show_all_contents=False,
        ),
    ),
)
