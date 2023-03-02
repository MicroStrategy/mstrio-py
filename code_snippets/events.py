"""This is the demo script to show how to manage events.
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import Event, list_events
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List all events
all_events = list_events(conn)

# Define variables which can be later used in a script
EVENT_ID = $event_id  # id for Event object
EVENT_NAME = $event_name  # name for Event object

# Get event by id
sample_event = Event(conn, id=EVENT_ID)

# Get event by name
sample_event = Event(conn, name=EVENT_NAME)

# list the Event's properties
sample_event.list_properties()

# Define a variable which can be later used in a script
EVENT_DESCRIPTION = $event_description

# Create event with description
db_load_event = Event.create(conn, name=EVENT_NAME, description=EVENT_DESCRIPTION)

# Trigger the event
db_load_event.trigger()

# Rename the event via alter
db_load_event.alter(name=EVENT_NAME, description=EVENT_DESCRIPTION)

# Delete the event
# Please note that when argument `force` is set to `False` (default value),
# deletion must be confirmed by selecting the appropriate prompt value.
# Do also note that the Event object stored in the `db_load_event` variable is
# still valid after the rename above, as it internally references the event
# by ID, not name.
db_load_event.delete(force=True)
