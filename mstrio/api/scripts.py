from typing import TYPE_CHECKING

from requests import Response

from mstrio.object_management.search_operations import full_search
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.object_management.object import Object


def list_scripts(  # TODO: will be moved to dedicated module during dev
    connection: 'Connection', project_id: str, to_dictionary=True
) -> 'list[dict] | list[Object]':
    """Get a list of scripts.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        to_dictionary (bool, optional): If True returns dict (default),
            otherwise returns Object.

    Returns:
        List of scripts.
    """
    return full_search(
        connection, project=project_id, object_types=76, to_dictionary=to_dictionary
    )


@ErrorHandler(err_msg="Error getting information for Script with id {id}.")
def get_info(
    connection: 'Connection',
    project_id: str,
    id: str,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Get info about a script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script
        fields (list[str], optional): List of fields to return. By default
            returns all available fields.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Dict representing the script.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/scripts/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'fields': ','.join(fields) if fields else None},
    )


@ErrorHandler(
    err_msg="Error getting information for a list of Scripts with ids {script_ids}."
)
def get_info_in_bulk(
    # FYI: use `get_info` instead, if possible, as some response keys here are
    # incorrect, legacy or invalid
    connection: 'Connection',
    project_id: str,
    script_ids: list[str],
    fields: list[str] | None = None,  # TODO: Do not use until CGPY-2655 is resolved
    error_msg: str | None = None,
) -> Response:
    """Get a list of scripts.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        script_ids (list[str]): List of script IDs to filter by.
        fields (list[str], optional): List of fields to return. By default
            returns all available fields.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        List of dicts representing scripts.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    body = {
        "ids": ",".join(script_ids),
        "fields": ",".join(fields) if fields else None,
    }

    return connection.get(
        endpoint='/api/scripts',
        headers={'X-MSTR-ProjectID': project_id},
        params=body,
    )


@ErrorHandler(err_msg="Error creating Script.")
def create_script(
    connection: 'Connection',
    project_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Create a script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new script
        project_id (str): ID of the project
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.post(
        endpoint='/api/scripts',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error updating Script with ID: {id}")
def update_script(
    connection: 'Connection',
    project_id: str,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update data about a script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script to be updated
        body (dict): JSON-formatted body of the updated script
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.put(
        endpoint=f'/api/scripts/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error deleting Script with ID: {id}")
def delete_script(
    connection: 'Connection',
    project_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script to be deleted
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.delete(
        endpoint=f'/api/scripts/{id}', headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg="Error running Script with ID: {id}")
def run_existing_script(
    connection: 'Connection',
    project_id: str,
    id: str,
    variables_data: list[dict] | None = None,
    error_msg: str | None = None,
) -> Response:
    """Run an existing script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script to be run
        variables_data (list[dict], optional): List of variable data to be
            passed to the script
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    body = {"variables": variables_data} if variables_data else {}

    return connection.post(
        endpoint=f'/api/scripts/{id}/evaluation',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error running Python code.")
def run_python_code(
    connection: 'Connection',
    code: str,
    # FYI: endpoint theoretically supports also `id` as param, but when
    # provided: `code` is obsolete and works exactly as `run_existing_script`
    # with extra steps...
    script_runtime_id: str | None = None,
    variables_data: list[dict] | None = None,
    error_msg: str | None = None,
) -> Response:
    """Run Python code.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        code (str): Python code to be executed - needs to be `base64` encoded
        script_runtime_id (str, optional): ID of the script runtime to be used.
            If omitted, default runtime will be used.
        variables_data (list[dict], optional): List of variable data to be
            passed to the script

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    body = {"scriptContent": code}

    if script_runtime_id:
        body["scriptRuntimeId"] = script_runtime_id

    if variables_data:
        body["variables"] = variables_data

    return connection.post(
        endpoint='/api/scripts/evaluation',
        json=body,
    )


@ErrorHandler(err_msg="Error getting run result for Evaluation ID: {evaluation_id}")
def get_run_result(
    connection: 'Connection',
    evaluation_id: str,
    error_msg: str | None = None,
) -> Response:
    """Get result of a script execution.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        evaluation_id (str): ID of the script evaluation
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/scripts/evaluation/{evaluation_id}',
    )


@ErrorHandler(
    err_msg="Error getting last run results in bulk for Scripts with IDs: {script_ids}"
)
def get_last_run_results_in_bulk(
    connection: 'Connection',
    project_id: str,
    script_ids: list[str] | str,
    fields: list[str] | None = None,  # TODO: Do not use until CGPY-2655 is resolved
    error_msg: str | None = None,
) -> Response:
    """Get last run results for multiple scripts.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        script_ids (list[str] | str): ID or IDs of the scripts
        fields (list[str], optional): List of fields to return. By default
            returns all available fields.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    body = {
        "scriptids": ",".join(
            script_ids if isinstance(script_ids, list) else [script_ids]
        ),
    }

    if fields:
        body["fields"] = ",".join(fields)

    return connection.get(
        endpoint='/api/scripts/history',
        headers={'X-MSTR-ProjectID': project_id},
        params=body,
    )


@ErrorHandler(err_msg="Error stopping execution for Evaluation ID: {evaluation_id}")
def stop_script_or_code_execution(
    connection: 'Connection',
    evaluation_id: str,
    error_msg: str | None = None,
) -> Response:
    """Stop a running script or code execution.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        evaluation_id (str): ID of the script evaluation
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.delete(
        endpoint=f'/api/scripts/evaluation/{evaluation_id}',
    )


@ErrorHandler(err_msg="Error getting Script variables answers for Script ID: {id}")
def get_script_variables_answers(
    connection: 'Connection',
    project_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get script variables answers.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/scripts/{id}/variables/answers',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating Script variables answers for Script ID: {id}")
def update_script_variables_answers(
    connection: 'Connection',
    project_id: str,
    id: str,
    answers: list[dict],
    error_msg: str | None = None,
) -> Response:
    """Update script variables answers.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        id (str): ID of the script
        answers (list[dict]): List of dicts with answers data to update
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.post(
        endpoint=f'/api/scripts/{id}/variables/answers',
        headers={'X-MSTR-ProjectID': project_id},
        json={'answers': answers},
    )
