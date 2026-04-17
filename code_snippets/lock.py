"""This is the demo script to show how to manage project and configuration
locks. Its basic goal is to present what can be done with this module
and to ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server.lock import ConfigurationLock, LockType
from mstrio.server.project import Project, ProjectLock

conn = get_connection(workstationData)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project to interact with

# Retrieve project lock and configuration lock objects
project = Project(conn, name=PROJECT_NAME)
project_lock = project.project_lock
# OR
project_lock = ProjectLock(project)

configuration_lock = ConfigurationLock(conn)

# Get lock status
print(project_lock.status)
print(configuration_lock.status)

# Locking and unlocking target
configuration_lock.lock(LockType.PERMANENT_INDIVIDUAL, "my lock id")
print(configuration_lock.status)

configuration_lock.unlock(LockType.PERMANENT_INDIVIDUAL, "my lock id")
print(configuration_lock.status)

# Fetching lock status from the server
# This is useful when handling multiple lock objects tracking the same target
configuration_lock.fetch()
