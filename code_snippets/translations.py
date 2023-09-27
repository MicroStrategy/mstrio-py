"""This is the demo script to show how to manage translations. This script will
not work without replacing parameters with real values. Its basic goal is to
present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from io import StringIO
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

# Bulk actions using CSV files can also be performed on multiple objects at once
# Export translations to CSV
# The columns A-D in the file that is exported should not be modified for the
# import functions to work properly.
# Object list accepts both Application and Schema Objects like Metric, or 
# dictionaries containing necessary information, the object ID and object type

# Define variables which can be later used in a script
LANGUAGE_OBJECT_TYPE = $lang_object_type
PATH_FOR_CSV = $path_for_csv

# If no path is specified, the CSV file will be returned as a string
CSV_LIST = Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric, {{'id': LANG_ID, 'type': LANGUAGE_OBJECT_TYPE}}],
)

# If path is specified, CSV file will be created at the specified path
Translation.to_csv_from_list(
    connection=CONN,
    object_list=[metric, {{'id': LANG_ID, 'type': LANGUAGE_OBJECT_TYPE}}],
    path=PATH_FOR_CSV,
)

# Add translations from CSV
# If CSV is to be given as a string, it has to be converted to a StringIO type string first
CSV_LIST_IOSTRING = StringIO(CSV_LIST)
Translation.add_translations_from_csv(connection=CONN, csv_file=CSV_LIST_IOSTRING)

# Instead a path to the CSV file can be specified as well
Translation.add_translations_from_csv(connection=CONN, csv_file=PATH_FOR_CSV)
