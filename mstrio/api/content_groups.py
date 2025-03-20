from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error creating Content Group.")
def create_content_group(
    connection: Connection, body: dict, fields: str | None = None
) -> Response:
    """Create a new content group.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new content group
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.post(
        endpoint='/api/contentGroups', json=body, params={'fields': fields}
    )


@ErrorHandler(err_msg="Error getting Content Group with ID: {id}.")
def get_content_group(
    connection: Connection, id: str, fields: str | None = None
) -> Response:
    """Get a content group by its ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the content group to get
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/contentGroups/{id}', params={'fields': fields}
    )


@ErrorHandler(err_msg="Error updating Content Group with ID: {id}.")
def update_content_group(
    connection: Connection, id: str, body: dict, fields: str | None = None
) -> Response:
    """Update a content group.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the content group to update
        body (dict): JSON-formatted body of the updated content group
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.patch(
        endpoint=f'/api/contentGroups/{id}', json=body, params={'fields': fields}
    )


@ErrorHandler(err_msg="Error getting Content Groups.")
def list_content_groups(connection: Connection, fields: str | None = None) -> Response:
    """Get a list of content groups.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(endpoint='/api/contentGroups', params={'fields': fields})


@ErrorHandler(err_msg="Error getting content of Content Group with ID: {id}.")
def get_content_group_contents(
    connection: Connection, id: str, project_ids: list[str], fields: str | None = None
) -> Response:
    """Get the content of a content group.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the content group to get the content of
        project_id (list[str]): ID of the project the content group belongs to
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/contentGroups/{id}/contents',
        params={'projectId': project_ids, 'fields': fields},
    )


@ErrorHandler(err_msg="Error updating content of Content Group with ID: {id}.")
def update_content_group_contents(
    connection: Connection, id: str, body: dict, fields: str | None = None
) -> Response:
    """Update the content of a content group.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the content group to update the content of
        body (dict): JSON-formatted body of the updated content group
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.patch(
        endpoint=f'/api/contentGroups/{id}/contents',
        json=body,
        params={'fields': fields},
    )
