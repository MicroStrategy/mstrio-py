from typing import TYPE_CHECKING, Any

from mstrio.api import scripts as scripts_api
from mstrio.helpers import try_str_to_num
from mstrio.utils.encoder import Encoder
from mstrio.utils.helper import delete_none_values

if TYPE_CHECKING:
    from mstrio.connection import Connection


def _parse_variables_data_before_return(variables_data: list[dict]) -> None:
    # REST always returns value as string, even for `VariableType.NUMERICAL`
    for var in variables_data:
        if var.get('type') == 2 and isinstance(  # VariableType.NUMERICAL
            v := var.get('value'), str
        ):
            var['value'] = try_str_to_num(v)


def get_info_data(connection: 'Connection', id: str) -> dict:
    """Returns dict with data about a specific Script.

    Requires `connection` to have selected project.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        id (str): ID of the Script.

    Returns:
        dict: Dictionary with Script information.
    """
    data = scripts_api.get_info(
        connection=connection,
        project_id=connection.project_id,
        id=id,
    ).json()

    _parse_variables_data_before_return(data.get('variables', []))

    return data


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
        str: ID of the newly created Script.
    """
    assert Encoder.is_encoded(
        encoded_code
    ), "Provided `encoded_code` is not b64-encoded."

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
    body = delete_none_values(body, recursion=True)

    return scripts_api.create_script(
        connection,
        project_id=connection.project_id,
        body=body,
    ).json()['id']


def update_script(
    connection: 'Connection',
    id: str,
    body: dict,
) -> dict:
    """Updates an existing Script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        id (str): ID of the Script to be updated.
        body (dict): Dictionary with updated Script information.

    Returns:
        dict: Dictionary with updated Script information after update.
    """

    if not body:
        return {}

    # FYI: this request returns something strange... we need fresh data to
    # return, requested independently
    res = scripts_api.update_script(
        connection,
        project_id=connection.project_id,
        id=id,
        body=body,
    )

    if not res.ok:
        return res

    return get_info_data(connection, id)


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
    want_code: bool = encoded_code is not None

    assert want_script ^ want_code, (
        "Incorrect set of parameters. Either `script_id` or `encoded_code` "
        "must be provided but not neither nor both."
    )

    if want_script:
        return scripts_api.run_existing_script(
            connection,
            project_id=connection.project_id,
            id=script_id,
            variables_data=variables_data,
        ).json()["id"]

    return scripts_api.run_python_code(
        connection,
        code=encoded_code,
        script_runtime_id=runtime_id,
        variables_data=variables_data,
    ).json()["id"]


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


def get_history(
    connection: 'Connection',
    script_id: str,
) -> dict | None:
    """Gets the history of Script's last run, if any.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script.

    Returns:
        dict | None: Dictionary with data about the last run of the Script,
            or None if there is no history.
    """

    # FYI: returns only last execution details
    items = scripts_api.get_last_run_results_in_bulk(
        connection,
        project_id=connection.project_id,
        script_ids=script_id,
    ).json()['history']

    return items[0] if items else None


def get_variables_personal_answers(
    connection: 'Connection',
    script_id: str,
) -> dict[str, Any]:
    """Gets personal answers for Script variables for the current user.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script.

    Returns:
        dict[str, Any]: Dictionary mapping variable IDs to their personal
            answers for current user.
    """

    data = scripts_api.get_script_variables_personal_answers(
        connection,
        project_id=connection.project_id,
        id=script_id,
    ).json()

    _parse_variables_data_before_return(data.get('answers', []))

    return {entry['id']: entry['value'] for entry in data['answers']}


def save_variables_personal_answers(
    connection: 'Connection',
    script_id: str,
    answers: list[dict],
) -> None:
    """Saves personal answers for Script variables for the current user.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        script_id (str): ID of the Script.
        answers (list[dict]): List of dictionaries representing personal answers
            to be saved for current user.
    """

    scripts_api.update_script_variables_personal_answers(
        connection,
        project_id=connection.project_id,
        id=script_id,
        answers=answers,
    )
