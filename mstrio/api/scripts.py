from requests import Response

from mstrio.connection import Connection
from mstrio.object_management import Object, full_search
from mstrio.utils.error_handlers import ErrorHandler


def list_scripts(
    connection: Connection, project_id: str, to_dictionary=True
) -> list[dict] | list[Object]:
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


@ErrorHandler(err_msg="Error creating Script.")
def create_script(
    connection: Connection, project_id: str, body: dict, error_msg: str | None = None
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
    return connection.post(
        endpoint='/api/scripts',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error deleting Script with ID: {id}")
def delete_script(
    connection: Connection, id: str, project_id: str, error_msg: str | None = None
) -> Response:
    """Delete a script.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the script to be deleted
        project_id (str): ID of the project
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.delete(
        endpoint=f'/api/scripts/{id}', headers={'X-MSTR-ProjectID': project_id}
    )
