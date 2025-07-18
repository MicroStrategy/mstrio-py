"""
Sample script showing how to duplicate a project.

This script uses MicroStrategy Tutorial project. Please replace its values
to use it with your own project.

1. Connect to the environment using data from the workstation
2. Define the name of the project to duplicate
3. Select project languages for duplication
4. Define non default duplication settings
5. Perform project duplication
6. Wait for the duplication to finish
7. Print the status of the duplication

"""

from mstrio.connection import get_connection
from mstrio.server import DuplicationConfig, Project, list_languages

conn = get_connection(workstationData)


PROJECT_NAME = 'MicroStrategy Tutorial' # Insert the name of project to duplicate
base_project = Project(connection=conn, name=PROJECT_NAME)

# Insert name of duplicated project
DUPLICATION_NAME = 'MicroStrategy Tutorial duplication 1'

# Duplicate the project with no default settings
# List languages to select from in duplication settings
langs = list_languages(conn)

selected_langs = langs[:5]  # Select first 5 languages for duplication
selected_default_project_lang= langs[0].lcid  # Select first language as default locale

# Create a list of import locales consisting from lcids of selected languages

selected_langs = [lang.lcid for lang in selected_langs]

# Define not default duplication settings
duplication_config= DuplicationConfig(schema_objects_only=False,
                                      skip_empty_profile_folders=False,
                                      include_user_subscriptions=False,
                                      include_contact_subscriptions=False,
                                      import_description="test duplication with languages",
                                      import_default_locale=selected_default_project_lang,
                                      import_locales=selected_langs)

# Perform duplication
# Target name should be unique, otherwise request will fail
duplication = base_project.duplicate(
    target_name=DUPLICATION_NAME, duplication_config=duplication_config
)

duplication.wait_for_stable_status()

print(
    f"Project duplication '{DUPLICATION_NAME}' (ID: {duplication.id}) has finished with status: {duplication.status.value}"
)
