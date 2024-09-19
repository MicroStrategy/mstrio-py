"""This is the demo script to show how to manage bots. Its basic goal
is to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.bots import Bot, list_bots

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

# Get connection to the environment
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List all bots
bots = list_bots(connection=conn)
# List all bots as dictionaries
bots_as_dicts = list_bots(connection=conn, to_dictionary=True)

# Define a variable which can be later used in a script
BOT_ID = $bot_id

# Initialize a bot
test_bot = Bot(connection=conn, id=BOT_ID)

# Define variables which can be later used in a script
NEW_NAME = $new_name
NEW_DESCRIPTION = $new_description
NEW_ABBREVIATION = $new_abbreviation
NEW_HIDDEN = $new_hidden == 'True'
NEW_STATUS = $new_status
NEW_COMMENTS = $new_comments

# Alter the bot's properties
test_bot.alter(
    name=NEW_NAME,
    description=NEW_DESCRIPTION,
    abbreviation=NEW_ABBREVIATION,
    hidden=NEW_HIDDEN,
    status=NEW_STATUS,
    comments=NEW_COMMENTS,
)

# Disable and enable a bot
test_bot.disable()
test_bot.enable()

# Delete a bot
test_bot.delete(force=True)
