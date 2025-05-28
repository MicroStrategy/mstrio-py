from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting color palettes.")
def list_palettes(
    connection: Connection,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a list of color palettes.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str, optional): Project ID.
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Custom error message for error handling

    Returns:
        Complete HTTP response object. 200 on success.
    """
    return connection.get(
        endpoint='/api/palettes',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error creating the color palette.")
def create_palette(
    connection: Connection,
    body: dict,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create a new color palette.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str, optional): Project ID.
        body (dict): JSON-formatted body describing the new palette
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.post(
        endpoint='/api/palettes',
        json=body,
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting a palette with ID: {id}")
def get_palette(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a color palette by ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str, optional): Project ID.
        id (str): ID of the palette to get
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/palettes/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating the palette with ID: {id}")
def update_palette(
    connection: Connection,
    id: str,
    body: dict,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Update an existing color palette.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str, optional): Project ID.
        id (str): ID of the palette to update
        body (dict): JSON-formatted body describing the updated palette
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.put(
        endpoint=f'/api/palettes/{id}',
        json=body,
        headers={'X-MSTR-ProjectID': project_id},
    )
