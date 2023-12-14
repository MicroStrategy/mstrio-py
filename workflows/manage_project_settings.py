from mstrio.connection import get_connection
from mstrio.server import Project

conn = get_connection(workstationData, 'MicroStrategy Tutorial')

project = Project(connection=conn, id='B3FEE61A11E696C8BD0F0080EFC58F44')
test_project = Project(connection=conn, id='B7CA92F04B9FAE8D941C3E9B7E0CD754')

# Change single setting for a project
# You can get a list of all available settings by calling:
# project.settings.list_properties()
project.settings.maxMstrFileSize = 50
project.settings.update()

# Apply all settings from one project to another
project.settings.alter(**test_project.settings.list_properties(show_names=False))
project.settings.update()

# Or export settings to a CSV file and import them to another project
settings_file_name = 'settings.csv'
test_project.settings.to_csv(settings_file_name)
project.settings.import_from(settings_file_name)
project.settings.update()

# Export settings to a CSV file with their descriptions
project.settings.to_csv('settings_file_name', show_description=True)
