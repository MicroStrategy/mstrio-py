"""This is the demo script to show how to manage applications.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.applications import Application, list_applications

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert name of project here

conn = get_connection(workstationData, project_id=PROJECT_ID)


# Define variables which can be later used in a script
LIMIT = $limit
NAME_FILTER = $name_filter

# list applications with different conditions
# Note: No Applications exist in a default environment
list_of_all_apps = list_applications(connection=conn)
list_of_several_apps = list_applications(connection=conn, limit=LIMIT)
list_of_apps_name_filtered = list_applications(connection=conn, name=NAME_FILTER)
list_of_all_apps_as_dicts = list_applications(connection=conn, to_dictionary=True)

# Define variables which can be later used in a script
APP_NAME = $app_name
APP_DESCRIPTION = $app_description
APP_HOME_SCREEN_MODE = $app_home_screen_mode
APP_HOME_DOCUMENT_URL = $app_home_document_url
APP_HOME_DOCUMENT_TYPE = $app_home_document_type
APP_HOME_ICON = $app_home_icon
APP_HOME_TOOLBAR_MODE = $app_home_toolbar_mode
APP_HOME_LIBRARY_CONTENT_BUNDLE_ID = $app_home_library_content_bundle_id
APP_HOME_LIBRARY_SIDEBAR = $app_home_library_sidebar

# Create an Application
app = Application.create(
    connection=conn,
    name='Application Validation Scripts',
    description='This is a demo application created by the validation script.',
    home_screen=Application.HomeSettings(
        mode=APP_HOME_SCREEN_MODE,
        home_document=Application.HomeSettings.HomeDocument(
            url=APP_HOME_DOCUMENT_URL,
            home_document_type=APP_HOME_DOCUMENT_TYPE,
            icons=[APP_HOME_ICON],
            toolbar_mode=APP_HOME_TOOLBAR_MODE,
            toolbar_enabled=True,
        ),
        home_library=Application.HomeSettings.HomeLibrary(
            content_bundle_ids=[APP_HOME_LIBRARY_CONTENT_BUNDLE_ID],
            show_all_contents=False,
            icons=[APP_HOME_ICON],
            toolbar_mode=APP_HOME_TOOLBAR_MODE,
            sidebars=[APP_HOME_LIBRARY_SIDEBAR],
            toolbar_enabled=True,
        ),
    )
)

# Define variables which can be later used in a script
APP_ID = $app_id
APP_NEW_NAME = $app_new_name

# Get an Application by it's id or name
app = Application(connection=conn, id=APP_ID)
app = Application(connection=conn, name=APP_NAME)

# Alter an Application
app.alter(
    home_screen=app.home_screen,
    name=APP_NEW_NAME,
    general=app.general,
    email_settings=app.email_settings,
    ai_settings=app.ai_settings,
    auth_modes=app.auth_modes,
)

# Delete an Application without prompt
app.delete(force=True)
