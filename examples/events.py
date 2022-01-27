"""This is the demo script to show how to manage events.
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services.event import list_events, Event

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# List all events
all_events = list_events(conn)
# Command Manager equivalent: LIST_ALL_EVENTS

# If you want to find a given event instead of listing all events and searching
# through them you can initialize an Event object using the name of the event,
# which will perform the search for you:
sample_event = Event(name="My Event")
# If you know the ID of the event, you can instead initialize the object using
# the ID, which will avoid any searching
sample_event = Event(id="1234567890")

# Create event with description
daily_report_event = Event.create(conn, name="My Daily Report", description="My Daily Report description")
# Command Manager equivalent: CREATE EVENT "My Daily Report" DESCRIPTION "My Daily Report description";

# Trigger the event
daily_report_event.trigger()
# Command Manager equivalent: TRIGGER EVENT "My Daily Report";


# The following example presents creation, update and deletion of an event

# Create event with description
db_load_event = Event.create(conn, name="Copy Of Database Load", description="Database Load")
# Command Manager equivalent: CREATE EVENT "Copy Of Database Load" DESCRIPTION "Database Load";

# Rename the event via alter
db_load_event.alter(name="DBMS Load")
# Command Manager equivalent: ALTER EVENT "Copy Of Database Load" NAME "DBMS Load";

# Delete the event
# Please note that when argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
# Do also note that the Event object stored in the `db_load_event` variable is
# still valid after the rename above, as it internally references the event
# by ID, not name.
db_load_event.delete(force=True)
# Command Manager equivalent: DELETE EVENT "DBMS Load";
