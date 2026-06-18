"""This is a template for a script to load metadata object telemetry.
This script will work OOTB.

This script can only be run via Workstation (and then scheduled as Task)
currently. Modify how the `conn` Connection is set if you wish to run it
outside Workstation context.
"""

from mstrio.connection import get_connection
from mstrio.distribution_services.event import Event

# connect to the environment inside Workstation
conn = get_connection(connectionData)


# find and trigger dedicated event "Load Metadata Object Telemetry"
event = Event(conn, name="Load Metadata Object Telemetry")
event.trigger()
