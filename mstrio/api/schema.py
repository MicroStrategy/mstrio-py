from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error reading lock status of the schema.")
def read_lock_status(connection: 'Connection', project_id: str | None = None):
    """Read lock status of the schema."""
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        endpoint='/api/model/schema/lock',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error placing the lock of type `{lock_type}` on the schema.")
def lock_schema(
    connection: 'Connection',
    lock_type: str,
    project_id: str | None = None,
    throw_error: bool = True,
):
    """Places a lock on the schema."""
    project_id = project_id if project_id is not None else connection.project_id
    return connection.post(
        endpoint='/api/model/schema/lock',
        headers={'X-MSTR-ProjectID': project_id},
        json={'lockType': lock_type},
    )


@ErrorHandler(err_msg="Error unlocking the schema.")
def unlock_schema(
    connection: 'Connection',
    lock_type: str | None = None,
    project_id: str | None = None,
    throw_error: bool = True,
):
    """Unlocks the schema."""
    project_id = project_id if project_id is not None else connection.project_id
    return connection.delete(
        endpoint='/api/model/schema/lock',
        headers={'X-MSTR-ProjectID': project_id},
        params={'lockType': lock_type},
    )


@ErrorHandler(err_msg="Error reloading the schema.")
def reload_schema(
    connection: 'Connection',
    project_id: str | None = None,
    update_types: list[str] | None = None,
    prefer_async: bool = False,
):
    """Reloads (updates) the schema."""
    project_id = project_id if project_id is not None else connection.project_id
    update_types = update_types if update_types else []
    prefer_async = 'respond-async' if prefer_async else None
    return connection.post(
        endpoint='/api/model/schema/reload',
        headers={
            'X-MSTR-ProjectID': project_id,
            'Prefer': prefer_async,
        },
        json={'updateTypes': update_types},
    )


@ErrorHandler(err_msg="Error reading status of the task with ID: {task_id}.")
def read_task_status(
    connection: 'Connection', task_id: str, project_id: str | None = None
):
    """Read the status of the task."""
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        endpoint=f'/api/model/tasks/{task_id}',
        headers={'X-MSTR-ProjectID': project_id},
    )
