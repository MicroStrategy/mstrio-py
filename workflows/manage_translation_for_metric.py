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
CSV_LIST = Translation.to_csv_from_list(connection=CONN, object_list=[METRIC])
CSV_LIST_IOSTRING = StringIO(CSV_LIST)

# Add translations from CSV
Translation.add_translations_from_csv(connection=CONN, csv_file=CSV_LIST_IOSTRING)
