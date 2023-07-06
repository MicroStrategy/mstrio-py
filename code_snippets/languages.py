"""This is the demo script to show how to manage languages. This script will
not work without replacing parameters with real values. Its basic goal is to
present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server.language import list_interface_languages, list_languages, Language

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

# Create connection based on workstation data
CONN = get_connection(workstationData, project_name=PROJECT_NAME)

# List languages
language_list = list_languages(connection=CONN)

# List interface languages
interface_language_list = list_interface_languages(connection=CONN)

# Define variables which can be later used in a script
LANGUAGE_NAME = $language_name
LANGUAGE_ID = $language_id
LANGUAGE_NEW_NAME = $language_new_name
BASE_LANG = $base_lang
INTERFACE_LANG_ID = $interface_lang_id
MINUTES15 = $minutes15
MINUTES30 = $minutes30
HOUR = $hour
DAY = $day
HOUR_OF_DAY = $hour_of_day
WEEK = $week
MONTH = $month
QUARTER = $quarter
YEAR = $year

# Create a language
# For base_language you can either specify:
# - Language class object
# - specific Language ID
# - specific Language lcid
lang = Language.create(
    connection=CONN,
    name=LANGUAGE_NAME,
    base_language=BASE_LANG,
    interface_language_id=INTERFACE_LANG_ID,
    formatting_settings=Language.TimeInterval(
        minutes15=MINUTES15,
        minutes30=MINUTES30,
        hour=HOUR,
        day=DAY,
        hour_of_day=HOUR_OF_DAY,
        week=WEEK,
        month=MONTH,
        quarter=QUARTER,
        year=YEAR
    )
)

# Initialise a language
# By ID
lang2 = Language(connection=CONN, id=LANGUAGE_ID)
# By name
lang2 = Language(connection=CONN, name=LANGUAGE_NAME)

# Alter a language
lang.alter(
    name = LANGUAGE_NEW_NAME,
    formatting_settings=Language.TimeInterval(
        minutes15=MINUTES15,
        minutes30=MINUTES30,
        hour=HOUR,
        day=DAY,
        hour_of_day=HOUR_OF_DAY,
        week=WEEK,
        month=MONTH,
        quarter=QUARTER,
        year=YEAR
    )
)

# Delete a language
lang.delete(force=True)
