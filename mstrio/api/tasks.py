from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.helper import delete_none_values

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error listing tasks.")
def list_tasks(
    connection: 'Connection',
    project_id: str | None = None,
    type: str | None = None,
    schedule_id: str | None = None,
    all_levels: bool = False,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a list of Tasks.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        type (str, optional): Type of tasks to filter by. Available values:
            "invalid", "script", "workflow". Only "script" is a working value in
            current architecture.
        schedule_id (str, optional): ID of the schedule to filter tasks by.
        all_levels (bool, optional): If True, retrieves tasks from all levels -
            both project and configuration.
        offset (int, optional): The starting point for the list of tasks.
        limit (int, optional): The maximum number of tasks to retrieve.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "type": type,
        "scheduleId": schedule_id,
        "allProjects": all_levels,
        "offset": offset,
        "limit": limit,
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.get(
        endpoint="/api/tasks",
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )


@ErrorHandler(err_msg="Error creating task.")
def create_task(
    connection: 'Connection',
    body: dict,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create new Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        body (dict): Dictionary containing data used for creating the task.
            ```
                {
                    "type": "script",
                    "scheduleId": str,
                    "name": str,
                    "content": {
                        "objectId": str,
                        "variables": [{
                            "id": str,
                            "value": str,
                            "type": str
                        }, ...]
                    },
                    "expiration": "2023-12-31",
                    "expirationTimeZone": "Europe/London",
                    "active": int
                }
            ```
        project_id (str, optional): ID of the project to associate the task
            with. If not provided, the task will be created at the
            configuration level.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.post(
        endpoint="/api/tasks",
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
        params=params,
    )


@ErrorHandler(
    err_msg=(
        "Error getting information for task with ID {id} in "
        "schedule with ID {schedule_id}."
    )
)
def get_task_info(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get information about a specific Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
        "type": "script",
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.get(
        endpoint=f"/api/tasks/{id}",
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )


@ErrorHandler(
    err_msg=(
        "Error altering information for task with ID {id} in "
        "schedule with ID {schedule_id}."
    )
)
def alter_task(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    body: dict,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Alter information for a specific Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        body (dict): Dictionary containing data used for altering the task.
            ```
                {
                    "type": "script",
                    "scheduleId": str,
                    "name": str,
                    "content": {
                        "objectId": str,
                        "variables": [{
                            "id": str,
                            "value": str,
                            "type": str
                        }, ...]
                    },
                    "expiration": "2023-12-31",
                    "expirationTimeZone": "Europe/London",
                    "active": int
                }
            ```
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.put(
        endpoint=f"/api/tasks/{id}",
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
        params=params,
    )


@ErrorHandler(
    err_msg="Error deleting task with ID {id} in schedule with ID {schedule_id}."
)
def delete_task(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Delete a specific Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
    }
    params = delete_none_values(params, recursion=False)

    return connection.delete(
        endpoint=f"/api/tasks/{id}",
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )


@ErrorHandler(
    err_msg="Error activating task with ID {id} in schedule with ID {schedule_id}."
)
def activate_task(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    body: dict | None = None,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Activate a specific Task.

    Note:
        Allows updating expiration data if optional `body` is provided.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        body (dict, optional): Dictionary containing data used for updating
            the task's expiration information. If not provided, the task will
            be activated without any changes to its expiration data.
            ```
                {
                    "expiration": "2023-12-31",
                    "expirationTimeZone": "Europe/London"
                }
            ```
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.post(
        endpoint=f"/api/tasks/{id}/activation",
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
        params=params,
    )


@ErrorHandler(
    err_msg="Error deactivating task with ID {id} in schedule with ID {schedule_id}."
)
def deactivate_task(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Deactivate a specific Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
    }
    params = delete_none_values(params, recursion=False)

    return connection.delete(
        endpoint=f"/api/tasks/{id}/activation",
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )


@ErrorHandler(
    err_msg="Error triggering task with ID {id} in schedule with ID {schedule_id}."
)
def trigger_task(
    connection: 'Connection',
    id: str,
    schedule_id: str,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Trigger a specific Task.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        id (str): ID of the task.
        schedule_id (str): ID of the schedule associated with the task.
        project_id (str, optional): ID of the project to filter tasks by.
            When not provided searches on configuration level.
        fields (str, optional): Comma-separated top-level field whitelist for
            selective retrieval.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Response: HTTP response object returned by the Strategy REST server.
    """

    params = {
        "scheduleId": schedule_id,
        "type": "script",
        "fields": fields,
    }
    params = delete_none_values(params, recursion=False)

    return connection.post(
        endpoint=f"/api/tasks/{id}/trigger",
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )
