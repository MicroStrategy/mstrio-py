"""This is the demo script to show how an administrator can manage
Object Telemetry operations for the Strategy One environment.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server import Environment

conn = get_connection(connectionData)
env = Environment(connection=conn)

# get reference to Object Telemetry handler
telemetry = env.object_telemetry

# get current telemetry pipeline status
status = telemetry.get_status()
print(status)

# trigger an immediate Load Metadata Object Telemetry for ALL PROJECTS
success = telemetry.trigger_load()
print(f"Telemetry load triggered (all projects): {success}")
