from requests import Response

from mstrio.connection import Connection
from mstrio.utils.api_helpers import add_comment_to_dict
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting Runtimes.")
def list_runtimes(
    connection: Connection, fields: str | None = None, error_msg: str | None = None
) -> Response:
    """Get list of runtimes.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy REST server.
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
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new runtime
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy REST server.
    """

    return connection.post(
        endpoint='/api/runtimes', json=body, params={'fields': fields}
    )


@ErrorHandler(err_msg="Error getting Runtime with ID: {id}")
def get_runtime(
    connection: Connection,
    id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a runtime by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of the runtime
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy REST server.
    """

    return connection.get(endpoint=f'/api/runtimes/{id}', params={'fields': fields})


@ErrorHandler(err_msg="Error updating Runtime with ID: {id}")
def update_runtime(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update a runtime by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of the runtime
        body (dict): JSON-formatted runtime properties to update
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy REST server.
    """

    return connection.patch(endpoint=f'/api/runtimes/{id}', json=body)


@ErrorHandler(err_msg="Error deleting Runtime with ID: {id}")
def delete_runtime(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
    journal_comment: str | None = None,
) -> Response:
    """Delete a runtime.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of the runtime to be deleted
        error_msg (str, optional): Custom Error Message for Error Handling
        journal_comment (str, optional): Comment that will be added to the
            runtime's change journal entry

    Returns:
        HTTP response object returned by the Strategy REST server.
    """

    params = add_comment_to_dict(journal_comment=journal_comment)
    if params:
        return connection.delete(endpoint=f'/api/runtimes/{id}', params=params)
    return connection.delete(endpoint=f'/api/runtimes/{id}')


@ErrorHandler(err_msg="Error getting Runtime versions.")
def get_runtime_versions(
    connection: Connection,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get available runtime versions.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy REST server.
    """

    return connection.get(endpoint='/api/runtimes/versions', params={'fields': fields})
