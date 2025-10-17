"""
Disable all active agents in a project.

1. Provide name of the project to connect to
2. Connect to the environment using data from workstation
3. Get a list of all agents in the project
4. Disable every active agent on the list
"""

from mstrio.connection import get_connection
from mstrio.project_objects.agents import list_agents

# Define project to connect to
PROJECT_NAME = 'MicroStrategy Tutorial'

# Connect to environment without providing user credentials
# Variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get a list of agents in the project
agents = list_agents(connection=conn)

# Disable every active agent
for agent in agents:
    if agent.status == 'enabled':
        agent.disable()
