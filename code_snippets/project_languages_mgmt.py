"""This is the demo script to show how administrator can manage project
languages.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
from mstrio.connection import get_connection
from mstrio.datasources import list_datasource_connections
from mstrio.server import Project
from mstrio.server.project_languages import (
    CurrentMode,
    DataLocalizationLanguage,
    SimpleLanguage,
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get project with a given name
project = Project(connection=conn, name=PROJECT_NAME)

# Get a default data language of a project
data_default = project.data_language_settings.default_language

# Get a current mode for data internationalization of a project
data_mode = project.data_language_settings.current_mode

# Get an available data languages of a project
data_languages = project.data_language_settings.languages

# Get a default display language of a project
metadata_default = project.metadata_language_settings.default

# Get an available metadata languages of a project
metadata_languages = project.metadata_language_settings.languages

# Get a list of datasource connections
# might be useful to get connection_id for data language
datasource_connections = list_datasource_connections(conn)

# Data internalization

# Define variables which can be later used in a script
DATA_LANGUAGE_ID_1 = $data_language_id_1
DATA_LANGUAGE_NAME_1 = $data_language_name_1
DATA_LANGUAGE_COLUMN_1 = $data_language_column_1
DATA_LANGUAGE_TABLE_1 = $data_language_table_1
DATA_LANGUAGE_COLUMN_1_ALTERED = $data_language_column_1_altered
# Could be one of the following: 'column', 'table', 'connectionId'
DATA_ALTER_PATH = $alter_path

DATA_LANGUAGE_ID_2 = $data_language_id_2
DATA_LANGUAGE_NAME_2 = $data_language_name_2
DATA_LANGUAGE_CONNECTION_ID_2 = $data_language_connection_id_2

# Add data languages to a project
data_languages_to_add = [
    DataLocalizationLanguage(
        id=DATA_LANGUAGE_ID_1,
        name=DATA_LANGUAGE_NAME_1,
        column=DATA_LANGUAGE_COLUMN_1,
        table=DATA_LANGUAGE_TABLE_1,
    ),
    DataLocalizationLanguage(
        id=DATA_LANGUAGE_ID_2,
        name=DATA_LANGUAGE_NAME_2,
        connection_id=DATA_LANGUAGE_CONNECTION_ID_2,
    )
]

project.data_language_settings.add_language(languages=data_languages_to_add)

# Alter data language of a project
data_language_to_alter = [
    DataLocalizationLanguage(
        id=DATA_LANGUAGE_ID_1, column=DATA_LANGUAGE_COLUMN_1_ALTERED
    )
]

project.data_language_settings.alter_language(
    languages=data_language_to_alter, path=DATA_ALTER_PATH
)

# Remove data languages from a project
data_languages_to_remove = [
    DataLocalizationLanguage(id=DATA_LANGUAGE_ID_1),
    DataLocalizationLanguage(id=DATA_LANGUAGE_ID_2)
]

project.data_language_settings.remove_language(languages=data_languages_to_remove)

# Set default data language of a project
project.data_language_settings.alter_default_language(language=DATA_LANGUAGE_ID_1)

# Set current mode of a data project
project.data_language_settings.alter_current_mode(mode=CurrentMode.NONE)

# Metadata internalization

# Define variables which can be later used in a script
META_LANGUAGE_ID_1 = $meta_language_id_1
META_LANGUAGE_NAME_1 = $meta_language_name_1

META_LANGUAGE_ID_2 = $meta_language_id_2
META_LANGUAGE_NAME_2 = $meta_language_name_2

# Add metadata languages to a project
metadata_languages_to_add = [
    SimpleLanguage(id=META_LANGUAGE_ID_1, name=META_LANGUAGE_NAME_1),
    SimpleLanguage(id=META_LANGUAGE_ID_2, name=META_LANGUAGE_NAME_2),
]

project.metadata_language_settings.add_language(languages=metadata_languages_to_add)

# Remove metadata languages from a project
metadata_languages_to_remove = [
    SimpleLanguage(id=META_LANGUAGE_ID_1),
    SimpleLanguage(id=META_LANGUAGE_ID_2),
]

project.metadata_language_settings.remove_language(languages=metadata_languages_to_remove)
