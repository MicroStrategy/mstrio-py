from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error getting Applications list.')
def get_applications(
    connection: Connection,
    output_flag: list[str] | None = None,
    fields: str | None = None,
) -> Response:
    """Get list of available Applications.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        output_flag (list, optional): Flag that specifies what should be
            included or filtered out of the application output
            Possible values:
                -DEFAULT
                -FILTER_AUTH_MODES
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    if output_flag is None:
        output_flag = ['DEFAULT']
    return connection.get(
        endpoint='/api/v2/applications',
        params={'outputFlag': output_flag, 'fields': fields},
    )


@ErrorHandler(err_msg='Error getting Application with ID: {id}.')
def get_application(
    connection: Connection,
    id: str,
    output_flag: list[str] | None = None,
    fields: str | None = None,
) -> Response:
    """Get an Application by its ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the application to get
        output_flag (list, optional): Flag that specifies what should be
            included or filtered out of the application output
            Possible values:
                -DEFAULT
                -INCLUDE_LOCALE
                -INCLUDE_ACL
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    if output_flag is None:
        output_flag = ['INCLUDE_LOCALE', 'INCLUDE_ACL']
    return connection.get(
        endpoint=f'/api/v2/applications/{id}',
        params={'outputFlag': output_flag, 'fields': fields},
    )


@ErrorHandler(err_msg='Error creating an Application.')
def create_application(
    connection: Connection,
    body: dict,
) -> Response:
    """Create a new Application.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new application

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.post(
        endpoint='/api/v2/applications',
        json=body,
    )


@ErrorHandler(err_msg='Error updating Application with ID: {id}.')
def update_application(
    connection: Connection,
    id: str,
    body: dict,
) -> Response:
    """Update an Application.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the application to update
        body (dict): JSON-formatted body of the updated application

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.put(
        endpoint=f'/api/v2/applications/{id}',
        json=body,
    )


@ErrorHandler(err_msg='Error deleting Application with ID: {id}.')
def delete_application(
    connection: Connection,
    id: str,
) -> Response:
    """Delete an Application.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the application to delete

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.delete(
        endpoint=f'/api/v2/applications/{id}',
    )
