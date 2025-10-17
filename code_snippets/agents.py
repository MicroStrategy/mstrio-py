"""This is the demo script to show how to manage agents. Its basic goal
is to present what can be done with this module and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.agents import Agent, list_agents

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

# Get connection to the environment
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List all agents
agents = list_agents(connection=conn)
# List all agents as dictionaries
agents_as_dicts = list_agents(connection=conn, to_dictionary=True)

# Define a variable which can be later used in a script
AGENT_ID = $agent_id

# Initialize an agent
test_agent = Agent(connection=conn, id=AGENT_ID)

# Define variables which can be later used in a script
NEW_NAME = $new_name
NEW_DESCRIPTION = $new_description
NEW_ABBREVIATION = $new_abbreviation
NEW_HIDDEN = $new_hidden == 'True'
NEW_STATUS = $new_status
NEW_COMMENTS = $new_comments

# Alter the agent's properties
test_agent.alter(
    name=NEW_NAME,
    description=NEW_DESCRIPTION,
    abbreviation=NEW_ABBREVIATION,
    hidden=NEW_HIDDEN,
    status=NEW_STATUS,
    comments=NEW_COMMENTS,
)

# Disable and enable an agent
test_agent.disable()
test_agent.enable()

# Delete an agent
test_agent.delete(force=True)
