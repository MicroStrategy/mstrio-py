from mstrio.connection import Connection
from mstrio.modeling.schema import (
	SchemaManagement, SchemaLockType, SchemaUpdateType
)


def schema_workflow(conn: "Connection") -> None:

    # create object to manage the schema
    schema_mgmt = SchemaManagement(conn)
    print(schema_mgmt)

    # get lock type of the schema
    print(schema_mgmt.lock_type)

    # unlock schema and get its status
    schema_mgmt.unlock()
    lock_st = schema_mgmt.get_lock_status()
    print(lock_st)

    # Lock schema and get its status. Schema can be locked also with type
    # `ABSOLUTE_CONSTITUENT` or `EXCLUSIVE_CONSTITUENT`.
    schema_mgmt.lock(SchemaLockType.ABSOLUTE_INDIVIDUAL)
    lock_st = schema_mgmt.get_lock_status()
    print(lock_st)

    # Reload schema. It is allowed not to provide an update type. Except for
    # types below `TABLE_KEY` or `LOGICAL_SIZE` are also available.
    task = schema_mgmt.reload(
        update_types=[SchemaUpdateType.CLEAR_ELEMENT_CACHE, SchemaUpdateType.ENTRY_LEVEL])
    # print task which is returned when schema is reloaded asynchronously.
    print(task)

    # get list of tasks which are stored within schema management object (tasks
    # are saved when `reload` is performed asyncronously)
    print(schema_mgmt.tasks)

    # get all details about the first task which is stored within schema management object
    task = schema_mgmt.get_task(task_index=0)
    print(task)

    # unlock schema and get its status
    schema_mgmt.unlock()
    lock_st = schema_mgmt.get_lock_status()
    print(lock_st)
