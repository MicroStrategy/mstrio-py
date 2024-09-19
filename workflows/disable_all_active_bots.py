"""
Disable all active bots in a project.

1. Provide name of the project to connect to
2. Connect to the environment using data from workstation
3. Get a list of all bots in the project
4. Disable every active bot on the list
"""

from mstrio.connection import get_connection
from mstrio.project_objects.bots import list_bots

# Define project to connect to
PROJECT_NAME = 'MicroStrategy Tutorial'

# Connect to environment without providing user credentials
# Variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get a list of bots in the project
bots = list_bots(connection=conn)

# Disable every active bot
for bot in bots:
    if bot.status == 'enabled':
        bot.disable()
