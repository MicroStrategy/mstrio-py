"""This is the demo script to show how administrator can manage schema.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.modeling.schema import SchemaManagement, SchemaLockType, SchemaUpdateType

from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# create an object to manage the schema
schema_mgmt = SchemaManagement(conn)

# get lock type of the schema
lock_t = schema_mgmt.lock_type

# unlock schema and get its status
schema_mgmt.unlock()
lock_st = schema_mgmt.get_lock_status()

# Lock schema and get its status. Schema can be locked also with type
# `ABSOLUTE_CONSTITUENT` or `EXCLUSIVE_CONSTITUENT`.
# Available values for SchemaLockType enum are in modeling/schema/schema_management.py
schema_mgmt.lock(SchemaLockType.ABSOLUTE_INDIVIDUAL)
lock_st = schema_mgmt.get_lock_status()

# Reload schema. It is allowed not to provide an update type. Except for
# types below `TABLE_KEY` or `LOGICAL_SIZE` are also available.
# When schema is reloaded asynchronously then task is returned.
# Available values for SchemaLockType enum are in modeling/schema/schema_management.py
task = schema_mgmt.reload(
    update_types=[SchemaUpdateType.CLEAR_ELEMENT_CACHE, SchemaUpdateType.ENTRY_LEVEL]
)

# get list of tasks which are stored within schema management object (tasks
# are saved when `reload` is performed asyncronously)
tasks = schema_mgmt.tasks

# get all details about the first task which is stored within schema management
# object
task = schema_mgmt.get_task(task_index=0)

# get all details about the last task which is stored within schema management
# object
task_st = schema_mgmt.get_task(task_index=-1)

# unlock schema and get its status
schema_mgmt.unlock()
lock_st = schema_mgmt.get_lock_status()
