from typing import TYPE_CHECKING

from mstrio.api import scripts as scripts_api
from mstrio.utils.helper import delete_none_values

if TYPE_CHECKING:
    from mstrio.connection import Connection


def get_info_data(connection: 'Connection', script_id: str) -> dict:
    """Returns dict with data about a specific Script.

    Requires `connection` to have selected project.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script.

    Returns:
        dict: Dictionary with Script information.
    """
    return scripts_api.get_info(
        connection=connection,
        project_id=connection.project_id,
        id=script_id,
    ).json()


def create_script(
    connection: 'Connection',
    name: str,
    runtime_id: str,
    encoded_code: str,
    script_type: str,
    folder_id: str,
    description: str | None = None,
    variables: list[dict] | None = None,
    script_usage_type: str | None = None,
    script_result_type: str | None = None,
) -> str:
    """Creates a new Script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        name (str): Name of the Script.
        runtime_id (str): ID of the Script runtime.
        encoded_code (str): Base64 encoded content of the Script.
        script_type (str): Type of the Script.
        folder_id (str): ID of the folder where the Script will be created.
        description (str, optional): Description of the Script.
        variables (list[dict], optional): List of variables associated with the
            Script. Defaults to None.
        script_usage_type (str, optional): Usage type of the Script.
            Defaults to None, which means `commandManager` on I-Server.
        script_result_type (str, optional): Result type of the Script.
            Defaults to None which means "no result" on I-Server.

    Returns:
        str: ID of the created Script.
    """
    assert " " not in encoded_code, "Provided `encoded_code` is not b64-encoded."

    body = {
        "name": name,
        "description": description,
        "scriptRuntimeId": runtime_id,
        "scriptContent": encoded_code,
        "variables": variables,
        "scriptType": script_type,
        "scriptUsageType": script_usage_type,
        "scriptResultType": script_result_type,
        "folderId": folder_id,
    }
    body = delete_none_values(body, recursion=False)

    return scripts_api.create_script(
        connection,
        project_id=connection.project_id,
        body=body,
    ).json()["id"]


def update_script(
    connection: 'Connection',
    script_id: str,
    name: str | None = None,
    description: str | None = None,
    runtime_id: str | None = None,
    encoded_code: str | None = None,
    variables: list[dict] | None = None,
    script_type: str | None = None,
    script_usage_type: str | None = None,
    script_result_type: str | None = None,
    folder_id: str | None = None,
) -> bool:
    """Updates an existing Script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script to be updated.
        name (str, optional): New name of the Script.
        description (str, optional): New description of the Script.
        runtime_id (str, optional): New ID of the Script runtime.
        encoded_code (str, optional): New base64 encoded content of the Script.
        variables (list[dict], optional): New list of variables associated with
            the Script.
        script_type (str, optional): New type of the Script.
        script_usage_type (str, optional): New usage type of the Script.
        script_result_type (str, optional): New result type of the Script.
        folder_id (str, optional): New ID of the folder where the Script is
            located.

    Returns:
        bool: True if the Script was successfully updated, False otherwise.
    """
    body = {
        "name": name,
        "description": description,
        "scriptRuntimeId": runtime_id,
        "scriptContent": encoded_code,
        "variables": variables,
        "scriptType": script_type,
        "scriptUsageType": script_usage_type,
        "scriptResultType": script_result_type,
        "folderId": folder_id,
    }
    body = delete_none_values(body, recursion=False)

    if not body:
        return False

    return scripts_api.update_script(
        connection,
        project_id=connection.project_id,
        id=script_id,
        body=body,
    ).ok


def delete_script(
    connection: 'Connection',
    script_id: str,
) -> bool:
    """Deletes a Script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script to be deleted.

    Returns:
        bool: True if the Script was successfully deleted, False otherwise.
    """
    return scripts_api.delete_script(
        connection,
        project_id=connection.project_id,
        id=script_id,
    ).ok


def start_run(
    connection: 'Connection',
    script_id: str | None = None,
    encoded_code: str | None = None,
    runtime_id: str | None = None,
    variables_data: list[dict] | None = None,
) -> str:
    """Runs a Script or Code.

    Requires a set of parameters for either running script or running code,
    but not both. Those are either:
    - `script_id` + optional `variables_data`, or
    - `encoded_code` + `runtime_id` + optional `variables_data`.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str, optional): ID of the Script to be run.
        encoded_code (str, optional): Base64 encoded content of the Script to be
            run.
        runtime_id (str, optional): ID of the Script runtime.
        variables_data (list[dict], optional): List of variables data to be used
            when running the Script.

    Returns:
        str: evaluation ID of the Script/Code execution job.
    """

    want_script: bool = script_id is not None
    want_code: bool = encoded_code is not None and runtime_id is not None

    assert want_script ^ want_code, (
        "Incorrect set of parameters. Either (`script_id`) or (`encoded_code` "
        "and `runtime_id`) must be provided but not neither nor both."
    )

    if want_script:
        return scripts_api.run_existing_script(
            connection,
            project_id=connection.project_id,
            id=script_id,
            variables_data=variables_data,
        ).json()["evaluationId"]

    return scripts_api.run_python_code(
        connection,
        code=encoded_code,
        script_runtime_id=runtime_id,
        variables_data=variables_data,
    ).json()["evaluationId"]


def get_run_result(
    connection: 'Connection',
    evaluation_id: str,
) -> dict:
    """Gets results of a Script/Code execution.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        evaluation_id (str): Evaluation ID of the Script/Code execution job.

    Returns:
        dict: Dictionary with results of the execution.
    """
    return scripts_api.get_run_result(
        connection,
        evaluation_id=evaluation_id,
    ).json()


def stop_run(
    connection: 'Connection',
    evaluation_id: str,
) -> bool:
    """Stops a running Script/Code execution.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        evaluation_id (str): Evaluation ID of the Script/Code execution job.

    Returns:
        bool: True if the stop request was successful, False otherwise.
    """
    return scripts_api.stop_script_or_code_execution(
        connection,
        evaluation_id=evaluation_id,
    ).ok
