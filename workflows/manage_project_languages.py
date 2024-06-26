"""
Manage project languages.
List languages, convert them to objects. Add or remove language from project.

1. Connect to the environment using data from the workstation
2. Get project object based on provided name ('MicroStrategy Tutorial')
3. Get list of all available datasource connections
4. Get a datasource connection with a given name ('XQuery(1)') to use it for
   the data language
5. Get the list of all available languages
6. Get 3 languages needed to be added to a project: Polish, Danish and Dutch
7. Convert Polish and Danish languages to DataLocalizationLanguage objects
8. Add those 2 languages to the settings of the project
9. Convert Dutch language to SimpleLanguage object
10. Add it to the settings of the project
11. Remove those 3 languages from the settings of the project
"""

from mstrio.connection import get_connection
from mstrio.datasources import list_datasource_connections
from mstrio.server import Project, list_languages
from mstrio.server.project_languages import DataLocalizationLanguage, SimpleLanguage

PROJECT_NAME = 'MicroStrategy Tutorial'  # Project to connect to

# Create connection based on workstation data
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get project with a given name
project = Project(connection=conn, name=PROJECT_NAME)

# Get list of all available datasource connections
datasource_connections = list_datasource_connections(conn)
# Get a datasource connection with a given name to use it for the data language
xquery_datasource_connection = list_datasource_connections(conn, name='XQuery(1)')[0]

# Get a list of all available languages
languages = list_languages(connection=conn)
# Get languages needed to be added to a project
polish_language = list_languages(connection=conn, name='Polish')[0]
danish_language = list_languages(connection=conn, name='Danish (Denmark)')[0]
dutch_language = list_languages(connection=conn, name='Dutch (Netherlands)')[0]

# Convert Polish and Danish languages to DataLocalizationLanguage objects
polish_data_language = DataLocalizationLanguage(
    id=polish_language.id,
    name=polish_language.name,
    column='_pl',
    table='',
)

danish_data_language = DataLocalizationLanguage(
    id=danish_language.id,
    name=danish_language.name,
    connection_id=xquery_datasource_connection.id,
)

# Add them languages to a project
project.data_language_settings.add_language(
    languages=[polish_data_language, danish_data_language]
)

# Convert Dutch language to SimpleLanguage object
dutch_metadata_language = SimpleLanguage(
    id=dutch_language.id,
    name=dutch_language.name,
)

# Add it to a project
project.metadata_language_settings.add_language(languages=[dutch_metadata_language])

# Remove languages from the project
project.data_language_settings.remove_language(
    languages=[polish_data_language, danish_data_language]
)
project.metadata_language_settings.remove_language(languages=[dutch_metadata_language])
