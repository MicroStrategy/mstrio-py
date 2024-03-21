"""This is the demo script to show how to manage translations. This script will
not work without replacing parameters with real values. Its basic goal is to
present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from io import StringIO
from mstrio.datasources import DatasourceInstance
from mstrio.object_management import list_translations, Translation
from mstrio.modeling.metric import Metric
from mstrio.server import Language

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

# Create connection based on workstation data
CONN = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
METRIC_ID = $metric_id
OBJECT_TYPE = $metric_type
LANG_LCID = $lang_lcid
LANG_2_LCID = $lang_2_lcid
LANG_ID = $lang_id
LANG_2_ID = $lang_2_id
LANGUAGE_OBJECT = $language_object
LANGUAGE_OBJECT_2 = $language_object_2
TARGET_ID = $target_id
TRANSLATION_VALUE = $translation_value
TRANSLATION_VALUE_ALTERED = $translation_value_altered
TRANSLATION_VALUE_2 = $translation_value_2
TRANSLATION_VALUE_2_ALTERED = $translation_value_2_altered

# You can manage translations in 2 ways, through the Translation class that
# allows managing Translations on any object.
# Or through the translation methods added to all objects that support
# translations, that are supported by mstrio-py.

# Below are snippets on using the Translation class methods:

# Listing translations for an object
list_translations(
    connection=CONN, id=METRIC_ID, object_type=OBJECT_TYPE, project_id=CONN.project_id
)

# You can also specify a list of languages for the listing function
# The function will automatically list translations for only those languages
# For the languages you have to provide a list.
# To specify a language in the list you need to provide either:
# - Language class objects
# - specific Language IDs
# - specific Language lcids
# The three types of language argument can be mixed in the list
list_translations(
    connection=CONN,
    id=METRIC_ID,
    object_type=OBJECT_TYPE,
    project_id=CONN.project_id,
    languages=[LANG_LCID, LANG_2_ID],
)

# Add translations to an Object

# The translations are specified with a list of helper classes
# Each helper class has to contain the target_language, value and target_id
# For target_language you can either specify:
# - Language class object
# - specific Language ID
# - specific Language lcid

Translation.add_translation(
    connection=CONN,
    id=METRIC_ID,
    object_type=OBJECT_TYPE,
    translations=[
        Translation.OperationData(
            target_language=LANG_LCID,
            value=TRANSLATION_VALUE,
            target_id=TARGET_ID,
        ),
        Translation.OperationData(
            target_language=LANG_2_LCID,
            value=TRANSLATION_VALUE_2,
            target_id=TARGET_ID,
        ),
    ],
    project_id=CONN.project_id,
)

# Alter translations of an Object

# The translations are specified with a list of helper classes
# The helper classes have identical structure to the ones provided when adding
Translation.alter_translation(
    connection=CONN,
    id=METRIC_ID,
    object_type=OBJECT_TYPE,
    translations=[
        Translation.OperationData(
            target_language=LANG_ID,
            value=TRANSLATION_VALUE_ALTERED,
            target_id=TARGET_ID,
        ),
        Translation.OperationData(
            target_language=LANG_2_ID,
            value=TRANSLATION_VALUE_2_ALTERED,
            target_id=TARGET_ID,
        ),
    ],
    project_id=CONN.project_id,
)

# Remove translations from an Object

# The translations are specified with a list of helper classes
# The helper class for removing does not need to contain the value
Translation.remove_translation(
    connection=CONN,
    id=METRIC_ID,
    object_type=OBJECT_TYPE,
    translations=[
        Translation.OperationData(target_language=LANGUAGE_OBJECT, target_id=TARGET_ID),
        Translation.OperationData(
            target_language=LANGUAGE_OBJECT_2, target_id=TARGET_ID
        ),
    ],
    project_id=CONN.project_id,
)

# Translations can be managed from an object as well
metric = Metric(connection=CONN, id=METRIC_ID)

# List translations of the object
metric.list_translations()

# You can specify a languages list for the object as well
metric.list_translations(languages=[LANG_LCID, LANG_2_ID])

# Add translations to the object
# Only the list of translation helper classes needs to be provided
metric.add_translation(
    translations=[
        Translation.OperationData(
            target_language=LANG_LCID,
            value=TRANSLATION_VALUE,
            target_id=TARGET_ID,
        ),
        Translation.OperationData(
            target_language=LANG_2_LCID,
            value=TRANSLATION_VALUE_2,
            target_id=TARGET_ID,
        ),
    ],
)

# Alter translations of the object
# Only the list of translation helper classes needs to be provided
metric.alter_translation(
    translations=[
        Translation.OperationData(
            target_language=LANG_LCID,
            value=TRANSLATION_VALUE_ALTERED,
            target_id=TARGET_ID,
        ),
        Translation.OperationData(
            target_language=LANG_2_LCID,
            value=TRANSLATION_VALUE_2_ALTERED,
            target_id=TARGET_ID,
        ),
    ],
)

# Remove translations from the object
# Only the list of translation helper classes needs to be provided
metric.remove_translation(
    translations=[
        Translation.OperationData(target_language=LANG_LCID, target_id=TARGET_ID),
        Translation.OperationData(target_language=LANG_2_LCID, target_id=TARGET_ID),
    ],
)

# Bulk actions using CSV, JSON, SQL database or dataframes can also be
# performed on multiple objects at once

# To ensure correct import, the columns from the original file/database cannot
# be renamed. Columns can be deleted (with the exception of object ID,
# object type and target ID) but new columns cannot be added. The column
# order does not matter.

# Importing is supported from normalized file/database only

# Define variables which can be later used in a script
DATASOURCE_ID = $datasource_id
TABLE_NAME = $table_name
PATH_FOR_CSV = $path_for_csv
PATH_FOR_JSON = $path_for_json
SEPARATOR = $separator

# Exporting and importing from CSV
# If no path is specified, the CSV file will be returned as a string
CSV_LIST = Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric],
)

# If path is specified, CSV file will be created at the specified path
Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_CSV,
)

# Extra columns can be added by setting the following flags to True:
# add_object_creation_date
# add_object_description
# add_object_last_modified_date
# add_object_path
# add_object_version
Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_CSV,
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)

# Translations can be exported to CSV for specified languages only
Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_CSV,
    languages=[LANG_ID, LANG_2_ID],
)

# Translations can be exported to CSV in a denormalized format
# And with a specific separator
Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_CSV,
    denormalized_form=True,
    separator=SEPARATOR,
)

# Add translations from CSV
# If CSV is to be given as a string, it has to be converted to a StringIO type string first
CSV_LIST_IOSTRING = StringIO(CSV_LIST)
Translation.add_translations_from_csv(connection=CONN, file_path=CSV_LIST_IOSTRING)

# Instead a path to the CSV file can be specified as well
Translation.add_translations_from_csv(connection=CONN, file_path=PATH_FOR_CSV)

# A separator can be specified for the import file if a custom separator was used
Translation.add_translations_from_csv(
    connection=CONN, file_path=PATH_FOR_CSV, separator=SEPARATOR
)

# Extra flags can be enabled for the import function as well
# delete=True will make the import delete translations that are empty in the CSV
# automatch_target_ids will make the import try to match the target IDs
# that are not present in the Object on the server to ones present in the file
# based on the content of the Translation for the default project language

Translation.add_translations_from_csv(
    connection=CONN, file_path=PATH_FOR_CSV, delete=True, automatch_target_ids=True
)

# Exporting and importing from JSON
# If no path is specified, the JSON file will be returned as a string
JSON_LIST = Translation.to_json_from_list(
    connection=CONN,
    object_list=[metric],
)

# If path is specified, JSON file will be created at the specified path
Translation.to_json_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_JSON,
)

# Extra columns can be added by setting the following flags to True:
# add_object_creation_date
# add_object_description
# add_object_last_modified_date
# add_object_path
# add_object_version
Translation.to_json_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_JSON,
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)

# Translations can be exported to JSON for specified languages only
Translation.to_json_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_JSON,
    languages=[LANG_ID, LANG_2_ID],
)

# Translations can be exported to JSON in a denormalized format
Translation.to_json_from_list(
    connection=CONN,
    object_list=[metric],
    file_path=PATH_FOR_JSON,
    denormalized_form=True,
)

# Add translations from JSON
# If JSON is to be given as a string, it has to be converted to a StringIO type string first
JSON_LIST_IOSTRING = StringIO(JSON_LIST)
Translation.add_translations_from_json(connection=CONN, file_path=JSON_LIST_IOSTRING)

# Instead a path to the JSON file can be specified as well
Translation.add_translations_from_json(connection=CONN, file_path=PATH_FOR_JSON)

# Extra flags can be enabled for the import function as well
# delete=True will make the import delete translations that are empty in the JSON
# automatch_target_ids will make the import try to match the target IDs
# that are not present in the Object on the server to ones present in the file
# based on the content of the Translation for the default project language

Translation.add_translations_from_json(
    connection=CONN, file_path=PATH_FOR_JSON, delete=True, automatch_target_ids=True
)

# Exporting and importing from databases
# To interact with a database we need a DatasourceInstance object
DATASOURCE = DatasourceInstance(connection=CONN, id=DATASOURCE_ID)
Translation.to_database_from_list(
    connection=CONN,
    object_list=[metric],
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
)

# By default the method will ask if you want to overwrite the table if it already exists
# To bypass having to answer that question the flag force can be set to True
Translation.to_database_from_list(
    connection=CONN,
    object_list=[metric],
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
    force=True,
)

# Extra columns can be added by setting the following flags to True:
# add_object_creation_date
# add_object_description
# add_object_last_modified_date
# add_object_path
# add_object_version
Translation.to_database_from_list(
    connection=CONN,
    object_list=[metric],
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)

# Translations can be exported to the database for specified languages only
Translation.to_database_from_list(
    connection=CONN,
    object_list=[metric],
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
    languages=[LANG_ID, LANG_2_ID],
)

# Translations can be exported to the database in a denormalized format
Translation.to_database_from_list(
    connection=CONN,
    object_list=[metric],
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
    denormalized_form=True,
)

# Add translations from database
Translation.add_translations_from_database(
    connection=CONN, table_name=TABLE_NAME, datasource=DATASOURCE
)

# Extra flags can be enabled for the import function as well
# delete=True will make the import delete translations that are empty in the database
# automatch_target_ids will make the import try to match the target IDs
# that are not present in the Object on the server to ones present in the file
# based on the content of the Translation for the default project language

Translation.add_translations_from_database(
    connection=CONN,
    table_name=TABLE_NAME,
    datasource=DATASOURCE,
    delete=True,
    automatch_target_ids=True,
)

# Exporting and importing from dataframes
DATAFRAME = Translation.to_dataframe_from_list(
    connection=CONN,
    object_list=[metric],
)

# Extra columns can be added by setting the following flags to True:
# add_object_creation_date
# add_object_description
# add_object_last_modified_date
# add_object_path
# add_object_version
Translation.to_dataframe_from_list(
    connection=CONN,
    object_list=[metric],
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)

# Translations can be exported to the dataframe for specified languages only
Translation.to_dataframe_from_list(
    connection=CONN,
    object_list=[metric],
    languages=[LANG_ID, LANG_2_ID],
)

# Translations can be exported to the dataframe in a denormalized format
Translation.to_dataframe_from_list(
    connection=CONN,
    object_list=[metric],
    denormalized_form=True,
)

# Add translations from dataframe
Translation.add_translations_from_dataframe(connection=CONN, dataframe=DATAFRAME)

# Extra flags can be enabled for the import function as well
# delete=True will make the import delete translations that are empty in the dataframe
# automatch_target_ids will make the import try to match the target IDs
# that are not present in the Object on the server to ones present in the file
# based on the content of the Translation for the default project language

Translation.add_translations_from_dataframe(
    connection=CONN, dataframe=DATAFRAME, delete=True, automatch_target_ids=True
)
