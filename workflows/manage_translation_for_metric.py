"""This is the demo script to show how to manage translations. This script will
not work without replacing parameters with real values. Its basic goal is to
present what can be done with this module and to ease its usage.

1. Connect to the environment using data from the workstation
2. Define variables which can be later used in a script
3. Add, alter and remove translations to/from an object by using Translation
   class
4. Get list of translations for an object
5. Get metric object based on provided ID
6. Add, alter and remove translations to/from the metric object by using
   its method
7. Get list of translations for the metric object by using its method
8. Export translations to CSV file with few different options
9. Add translations from CSV file with few different options
10. Export translations to JSON file with few different options
11. Add translations from JSON file with few different options
12. Export translations to database with few different options
13. Add translations from database with few different options
14 Export translations to dataframe with few different options
15. Add translations from dataframe with few different options
"""

from mstrio.connection import get_connection
from io import StringIO
from mstrio.datasources import DatasourceInstance
from mstrio.object_management import list_translations, Translation
from mstrio.modeling.metric import Metric
from mstrio.server import Language

# Define a variable which can be later used in a script
PROJECT_NAME = 'MicroStrategy Tutorial'  # Project to connect to

# Create connection based on workstation data
CONN = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
METRIC_ID = 'F03528954D22B1C3454BC68978712F94'
OBJECT_TYPE = 4
LANG_LCID = 1040
LANG_2_LCID = 1053
LANG_ID = '000004104F95EF3956E52781700C1E7A'
LANG_2_ID = '0000041D4F95EF3956E52781700C1E7A'
LANGUAGE_OBJECT = Language(connection=CONN, id=LANG_ID)
LANGUAGE_OBJECT_2 = Language(connection=CONN, id=LANG_2_ID)
TARGET_ID = 'MTowOi1GMDM1Mjg5NTREMjJCMUMzNDU0QkM2ODk3ODcxMkY5NC00'
TRANSLATION_VALUE = 'Data dell ordine +2'
TRANSLATION_VALUE_ALTERED = 'Data dell ordine +2 altered'
TRANSLATION_VALUE_2 = 'Orderdatum +2'
TRANSLATION_VALUE_2_ALTERED = 'Orderdatum +2 altered'

# You can manage translations in 2 ways, through the Translation class that
# allows managing Translations on any object.
# Or through the translation methods added to all objects that support
# translations, that are supported by mstrio-py.

# Below are snippets on using the Translation class methods:

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
# The helper class has identical structure to the ones provided when adding
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

# Listing translations for an object
list_translations(
    connection=CONN, id=METRIC_ID, object_type=OBJECT_TYPE, project_id=CONN.project_id
)

# You can also specify a list of languages for the listing function
# The function will automatically list translations for only those languages
# For the languages you have to provide a list that contains:
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

# Translations can be managed from an object as well
METRIC = Metric(connection=CONN, id=METRIC_ID)

# Add translations to the object
# Only the list of translation helper classes needs to be provided
METRIC.add_translation(
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
METRIC.alter_translation(
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
METRIC.remove_translation(
    translations=[
        Translation.OperationData(target_language=LANG_LCID, target_id=TARGET_ID),
        Translation.OperationData(target_language=LANG_2_LCID, target_id=TARGET_ID),
    ],
)

# List translations of the object
METRIC.list_translations()

# You can specify a languages list for the object as well
METRIC.list_translations(languages=[LANG_LCID, LANG_2_ID])

# Export translations to CSV
CSV_LIST = StringIO(Translation.to_csv_from_list(connection=CONN, object_list=[METRIC]))
# Export translations to CSV with extra columns
CSV_LIST_EXTRA_COLUMNS = Translation.to_csv_from_list(
    connection=CONN,
    object_list=[METRIC],
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)
# Export translations to CSV with specific languages only
CSV_LIST_SPECIFIED_LANGUAGES = StringIO(
    Translation.to_csv_from_list(
        connection=CONN, object_list=[METRIC], languages=[LANG_ID, LANG_2_ID]
    )
)
# Export translations to CSV in denormalized format and specific separator
CSV_LIST_DENORMALIZED = Translation.to_csv_from_list(
    connection=CONN, object_list=[METRIC], denormalized_form=True, separator=','
)

# Add translations from CSV
Translation.add_translations_from_csv(connection=CONN, file_path=CSV_LIST)
# Add translations from CSV with removing translations and automatching target_ids
Translation.add_translations_from_csv(
    connection=CONN,
    file_path=CSV_LIST_SPECIFIED_LANGUAGES,
    delete=True,
    automatch_target_ids=True,
)

# Export translations to JSON
JSON_LIST = StringIO(
    Translation.to_json_from_list(connection=CONN, object_list=[METRIC])
)
# Export translations to JSON with extra columns
JSON_LIST_EXTRA_COLUMNS = Translation.to_json_from_list(
    connection=CONN,
    object_list=[METRIC],
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)
# Export translations to JSON with specific languages only
JSON_LIST_SPECIFIED_LANGUAGES = StringIO(
    Translation.to_json_from_list(
        connection=CONN, object_list=[METRIC], languages=[LANG_ID, LANG_2_ID]
    )
)
# Export translations to JSON in denormalized format
JSON_LIST_DENORMALIZED = Translation.to_json_from_list(
    connection=CONN, object_list=[METRIC], denormalized_form=True
)

# Add translations from JSON
Translation.add_translations_from_json(connection=CONN, file_path=JSON_LIST)
# Add translations from JSON with removing translations and automatching target_ids
Translation.add_translations_from_json(
    connection=CONN,
    file_path=JSON_LIST_SPECIFIED_LANGUAGES,
    delete=True,
    automatch_target_ids=True,
)

# Export translations to database
# The flag force=True will be used in the examples
# That flag means no confirmation will be asked before overwriting the specified table
# If the flag is not used, the user will be asked for confirmation before overwriting
DATASOURCE = DatasourceInstance(connection=CONN, id='A23BBC514D336D5B4FCE919FE19661A3')
Translation.to_database_from_list(
    connection=CONN,
    object_list=[METRIC],
    table_name='test_table',
    datasource=DATASOURCE,
    force=True,
)
# Export translations to database with extra columns
Translation.to_database_from_list(
    connection=CONN,
    object_list=[METRIC],
    table_name='test_table',
    datasource=DATASOURCE,
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
    force=True,
)
# Export translations to database with specific languages only
Translation.to_database_from_list(
    connection=CONN,
    object_list=[METRIC],
    table_name='test_table',
    datasource=DATASOURCE,
    languages=[LANG_ID, LANG_2_ID],
    force=True,
)
# Export translations to database in denormalized format
Translation.to_database_from_list(
    connection=CONN,
    object_list=[METRIC],
    table_name='test_table_denormalized',
    datasource=DATASOURCE,
    denormalized_form=True,
    force=True,
)

# Add translations from database
Translation.add_translations_from_database(
    connection=CONN, table_name='test_table', datasource=DATASOURCE
)
# Add translations from database with removing translations and automatching target_ids
Translation.add_translations_from_database(
    connection=CONN,
    table_name='test_table',
    datasource=DATASOURCE,
    delete=True,
    automatch_target_ids=True,
)

# Export translations to dataframe
DATAFRAME = Translation.to_dataframe_from_list(connection=CONN, object_list=[METRIC])
# Export translations to dataframe with extra columns
DATAFRAME_EXTRA_COLUMNS = Translation.to_dataframe_from_list(
    connection=CONN,
    object_list=[METRIC],
    add_object_creation_date=True,
    add_object_description=True,
    add_object_last_modified_date=True,
    add_object_path=True,
    add_object_version=True,
)
# Export translations to dataframe with specific languages only
DATAFRAME_SPECIFIED_LANGUAGES = Translation.to_dataframe_from_list(
    connection=CONN, object_list=[METRIC], languages=[LANG_ID, LANG_2_ID]
)
# Export translations to dataframe in denormalized format
DATAFRAME_DENORMALIZED = Translation.to_dataframe_from_list(
    connection=CONN, object_list=[METRIC], denormalized_form=True
)

# Add translations from dataframe
Translation.add_translations_from_dataframe(connection=CONN, dataframe=DATAFRAME)
# Add translations from dataframe with removing translations and automatching target_ids
Translation.add_translations_from_dataframe(
    connection=CONN, dataframe=DATAFRAME, delete=True, automatch_target_ids=True
)
