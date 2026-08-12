"""
[DISCLAIMERS]

(1) APIs support configuration level tasks, but those are related to unreleased,
obsolete functionality and not currently relevant architecture.

Therefore API Wrappers are raw and support this setup, but this processor file
will apply only valid current architecture logic.

(2) Planned Task is not a metadata object. It is basically an independently
stored set of properties of a schedule. That's why Task ID (even though unique)
is not enough to identify the task - Schedule ID is required.
"""

from typing import TYPE_CHECKING, Any

from mstrio.api import tasks as tasks_api
from mstrio.utils.helper import delete_none_values

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_tasks(
    connection: 'Connection',
    schedule_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """List tasks for a given project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        schedule_id (str, optional): ID of the schedule to filter tasks by.
            If not provided, all tasks for the project will be listed.
        limit (int, optional): Maximum number of tasks to return.

    Returns:
        list[dict]: A list of task dictionaries.
    """

    return (
        tasks_api.list_tasks(
            connection=connection,
            project_id=connection.project_id,
            type="script",
            schedule_id=schedule_id,
            all_levels=True,  # FYI: In current architecture should not matter
            limit=limit,
        )
        .json()
        .get("tasks", [])
    )


def create_task(
    connection: 'Connection',
    name: str,
    type: str,
    schedule_id: str,
    script_id: str,
    variables_answers: list[dict[str, str]] | None = None,
    active: int = 1,
    expiration: str | None = None,
    expiration_time_zone: str | None = None,
) -> dict[str, Any]:
    """Create a new task within a given project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        name (str): Name of the task.
        type (str): Type of the task (e.g., "script").
        schedule_id (str): ID of the schedule to associate the task with.
        script_id (str): ID of the script to be executed by the task.
        variables_answers (list[dict[str, str]], optional): List of variable
            answers for the script. Each answer should be a dictionary with
            variable id, value and type.
        active (int, optional): Whether the task is active. Defaults to 1.
        expiration (str, optional): Expiration date for the task.
        expiration_time_zone (str, optional): Time zone for the expiration date.

    Returns:
        dict[str, Any]: A dictionary containing the created task's details.
    """

    body = {
        "name": name,
        "type": type,
        "scheduleId": schedule_id,
        "content": {
            "objectId": script_id,
            "variables": variables_answers or [],
        },
        "active": active,
        "expiration": expiration,
        "expirationTimeZone": expiration_time_zone,
    }
    body = delete_none_values(body, recursion=False)

    return tasks_api.create_task(
        connection, body=body, project_id=connection.project_id
    ).json()


def get_task_info_and_last_status(
    connection: 'Connection',
    project_id: str,
    id: str,
    schedule_id: str,
) -> dict[str, Any]:
    """Get information of a specific task and its last execution status.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        id (str): ID of the task to retrieve.
        schedule_id (str): ID of the schedule associated with the task.

    Returns:
        dict[str, Any]: A dictionary containing the task's details and
            its last execution status.
    """

    return tasks_api.get_task_info(
        connection, id=id, schedule_id=schedule_id, project_id=project_id
    ).json()


def alter_task(
    connection: 'Connection',
    project_id: str,
    schedule_id: str,
    body: dict,
) -> dict[str, Any]:
    """Alter an existing task within a given project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        schedule_id (str): ID of the schedule associated with the task.
        body (dict): A dictionary containing the task properties to be
            altered. It has to contain `id`, `schedule`, and `content` keys as
            minimum.

    Returns:
        dict[str, Any]: A dictionary containing the altered task's details.
    """

    if any(body.get(key) is None for key in ("id", "content", "name", "schedule")):
        raise ValueError(
            "All of 'id', `content`, `name` and `schedule` must be provided "
            "in the body."
        )

    body["type"] = "script"
    # FYI: workaround on the fact that old schedule ID need to be always
    # provided and EntityBase `_update_properties` was not ready for it
    body["scheduleId"] = body.pop("schedule")["id"]

    return tasks_api.alter_task(
        connection,
        id=body.pop("id"),
        schedule_id=schedule_id,
        project_id=project_id,
        body=body,
    ).json()


def delete_task(
    connection: 'Connection',
    project_id: str,
    id: str,
    schedule_id: str,
) -> bool:
    """Delete a specific task within a given project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        id (str): ID of the task to delete.
        schedule_id (str): ID of the schedule associated with the task.

    Returns:
        bool: True if the task was successfully deleted, False otherwise.
    """

    return tasks_api.delete_task(
        connection, id=id, schedule_id=schedule_id, project_id=project_id
    ).ok


def activate_task(
    connection: 'Connection',
    project_id: str,
    id: str,
    schedule_id: str,
    body: dict | None = None,
) -> dict[str, Any]:
    """Activate a specific task within a given project and schedule.

    Note:
        Optionally allows updating the task's expiration data on activation.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        id (str): ID of the task to activate.
        schedule_id (str): ID of the schedule associated with the task.
        body (dict, optional): A dictionary containing the expiration data new
            values if provided for change.

    Returns:
        dict[str, Any]: A dictionary containing the activated task's
            details.
    """

    return tasks_api.activate_task(
        connection,
        id=id,
        schedule_id=schedule_id,
        body=body,
        project_id=project_id,
    ).json()


def deactivate_task(
    connection: 'Connection',
    project_id: str,
    id: str,
    schedule_id: str,
) -> bool:
    """Deactivate a specific task within a given project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        id (str): ID of the task to deactivate.
        schedule_id (str): ID of the schedule associated with the task.

    Returns:
        bool: True if the task was successfully deactivated, False
            otherwise.
    """

    return tasks_api.deactivate_task(
        connection,
        id=id,
        schedule_id=schedule_id,
        project_id=project_id,
    ).ok


def trigger_task(
    connection: 'Connection',
    project_id: str,
    id: str,
    schedule_id: str,
) -> bool:
    """Trigger immediate execution of a specific task within a given
    project and schedule.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project associated with the task.
        id (str): ID of the task to trigger.
        schedule_id (str): ID of the schedule associated with the task.

    Returns:
        bool: True if the task was successfully triggered, False
            otherwise.
    """

    return tasks_api.trigger_task(
        connection,
        id=id,
        schedule_id=schedule_id,
        project_id=project_id,
    ).ok
