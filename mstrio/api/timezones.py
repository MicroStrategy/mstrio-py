from requests import Response

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

# These endpoints concern timezones, which are configuration-level objects.
# Project ID must be still provided. In this case an empty string is passed.


@unpack_information
@ErrorHandler(err_msg="Error getting timezones.")
def list_all_tzs(
    connection: Connection,
    subtype: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a list of timezones.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        subtype (str, optional): Subtype of the timezone to get. If skipped,
            all timezones are returned.
            Possible values: 'timezone_custom', 'timezone_system'
        error_msg (str, optional): Custom error message for error handling

    Returns:
        Complete HTTP response object. 200 on success.
    """
    return connection.get(
        endpoint='/api/model/timezones',
        headers={'X-MSTR-ProjectID': ''},
        params={'subType': subtype},
    )


@unpack_information
@ErrorHandler(err_msg="Error creating timezone.")
def create_tz(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Create a new timezone.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new timezone
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    with changeset_manager(
        connection, project_id='', schema_edit=False
    ) as changeset_id:
        return connection.post(
            endpoint='/api/model/timezones',
            json=body,
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )


@unpack_information
@ErrorHandler(err_msg="Error getting timezone with ID: {id}")
def get_tz(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a timezone by its identifier.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): Identifier of the timezone to get
        changeset_id (str, optional): Identifier of the changeset to get the
            timezone from
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/model/timezones/{id}',
        headers={'X-MSTR-ProjectID': '', 'X-MSTR-MS-Changeset': changeset_id},
    )


@unpack_information
@ErrorHandler(err_msg="Error updating timezone with ID: {id}")
def update_tz(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update an existing timezone.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): Identifier of the timezone to update
        body (dict): JSON-formatted body of the updated timezone
        error_msg (str, optional): Custom error message for error handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    with changeset_manager(
        connection, project_id='', schema_edit=False
    ) as changeset_id:
        # Note: This endpoint uses the PATCH method, but the request body has
        # the simple delta format, not the patch operation list format
        return connection.patch(
            endpoint=f'/api/model/timezones/{id}',
            json=body,
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
