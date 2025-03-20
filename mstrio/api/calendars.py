from requests import Response

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

# These endpoints concern calendars, which are configuration-level objects.
# Project ID must be still provided. In this case an empty string is passed.


@unpack_information
@ErrorHandler(err_msg="Error getting calendars.")
def list_calendars(
    connection: Connection,
    subtype: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a list of calendars.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        subtype (str, optional): Subtype of the calendar to get. If skipped,
            all calendars are returned.
            Possible values: 'calendar_custom', 'calendar_system'
        offset (int, optional): Starting point within the collection of
            returned results. Used to control paging behavior.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Custom error message for error handling

    Returns:
        Complete HTTP response object. 200 on success.
    """
    return connection.get(
        endpoint='/api/model/calendars',
        headers={'X-MSTR-ProjectID': ''},
        params={
            'information.subType': subtype,
            'offset': offset,
            'limit': limit,
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating calendar.")
def create_calendar(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Create a new calendar.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new calendar
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    with changeset_manager(
        connection, project_id='', schema_edit=False
    ) as changeset_id:
        return connection.post(
            endpoint='/api/model/calendars',
            json=body,
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@unpack_information
@ErrorHandler(err_msg="Error getting calendar with ID: {id}")
def get_calendar(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a calendar by its identifier.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): Identifier of the calendar to get
        changeset_id (str, optional): Identifier of the changeset to get the
            calendar from
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/model/calendars/{id}',
        headers={'X-MSTR-ProjectID': '', 'X-MSTR-MS-Changeset': changeset_id},
    )


@unpack_information
@ErrorHandler(err_msg="Error updating calendar with ID: {id}")
def update_calendar(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update an existing calendar.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): Identifier of the calendar to update
        body (dict): JSON-formatted body of the updated calendar
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    with changeset_manager(
        connection, project_id='', schema_edit=False
    ) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/calendars/{id}',
            json=body,
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
