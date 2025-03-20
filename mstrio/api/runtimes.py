from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting Runtimes.")
def list_runtimes(
    connection: Connection, fields: str | None = None, error_msg: str | None = None
) -> Response:
    """Get list of runtimes.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.get(endpoint='/api/runtimes', params={'fields': fields})


@ErrorHandler(err_msg="Error creating Runtime.")
def create_runtime(
    connection: Connection,
    body: dict,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create a runtime.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new runtime
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.post(
        endpoint='/api/runtimes', json=body, params={'fields': fields}
    )


@ErrorHandler(err_msg="Error deleting Runtime with ID: {id}")
def delete_runtime(
    connection: Connection, id: str, error_msg: str | None = None
) -> Response:
    """Delete a runtime.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the runtime to be deleted
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.delete(endpoint=f'/api/runtimes/{id}')
