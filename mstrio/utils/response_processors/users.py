from time import sleep, time

from requests import JSONDecodeError

from mstrio.api import devices
from mstrio.api import usergroups as usergroups_api
from mstrio.api import users as users_api
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.utils.helper import deprecation_warning, fetch_objects, fetch_objects_async
from mstrio.utils.version_helper import method_version_handler

TIMEOUT = 60
TIMEOUT_INCREMENT = 0.25


def get(connection: Connection, id: str):
    """Get user by a specified ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing user object
    """
    return users_api.get_user_info(connection=connection, id=id).json()


def get_addresses(connection: Connection, id: str):
    """Get addresses for a specified user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing user addresses
    """
    return users_api.get_addresses_v2(connection=connection, id=id).json()


def get_security_roles(connection: Connection, id: str):
    """Get security roles for a specified user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing user security roles
    """
    return users_api.get_user_security_roles(connection=connection, id=id).json()


def get_settings(connection: Connection, id: str):
    """Get settings for a specified user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing user security roles
    """
    return users_api.get_settings(connection=connection, id=id).json()


def get_privileges(connection: Connection, id: str):
    """Get privileges for a specified user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing user privileges
    """
    return users_api.get_user_privileges(connection=connection, id=id).json()


def update(connection: Connection, id: str, body: dict):
    """Update info for a specified user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        body: body of the request

    Returns:
        dict representing user object
    """
    return users_api.update_user_info(connection=connection, id=id, body=body).json()


def create(connection: Connection, body: dict, username: str):
    """Create a user.

    Args:
        connection: Strategy One REST API connection object
        body: body of the request
        username: name of the user, for error purposes only

    Returns:
        dict representing user object
    """
    return users_api.create_user(
        connection=connection, body=body, username=username
    ).json()


def get_all(
    connection: Connection,
    limit: int,
    msg: str,
    name_begins: str,
    abbreviation_begins: str,
    filters: dict,
):
    """Get list of users.

    Args:
        connection: Strategy One REST API connection object
        limit: limit of users to list
        msg: optional error message,
        name_begins: optional filter for name beginning with
        abbreviation_begins: optional filter for abbreviation beginning with
        filters: filters

    Returns:
        list of dicts representing users
    """
    if filters.get('initials'):
        deprecation_warning(
            deprecated="possibility of providing 'initials' as a filter",
            new="New options to filter on 'full_name' and 'enabled' fields instead",
            version="11.3.13.101",
            module=False,
        )
        return fetch_objects_async(
            connection=connection,
            api=users_api.get_users_info,
            async_api=users_api.get_users_info_async,
            limit=limit,
            chunk_size=1000,
            error_msg=msg,
            name_begins=name_begins,
            abbreviation_begins=abbreviation_begins,
            filters=filters,
        )
    if filters.get('name') or name_begins:
        name_begins_filter = ('starts', name_begins) if name_begins else None

        filters['name'] = filters.get('name') or name_begins_filter

    if filters.get('abbreviation') or abbreviation_begins:
        abbreviation_begins_filter = (
            ('starts', abbreviation_begins) if abbreviation_begins else None
        )
        filters['abbreviation'] = (
            filters.get('abbreviation') or abbreviation_begins_filter
        )
    # Getting information from members of 'Everyone' user group
    return fetch_objects(
        connection=connection,
        api=usergroups_api.get_members,
        limit=limit,
        error_msg=msg,
        filters=filters,
        id='C82C6B1011D2894CC0009D9F29718E4F',
    )


def create_address(connection: Connection, id: str, body: dict):
    """Create an email user address.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        body: body of the request

    Returns:
    created address dictionary
    """
    return users_api.create_address(connection=connection, id=id, body=body).json()


def create_address_v2(connection: Connection, id: str, body: dict):
    """Create a non-email user address.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        body: body of the request

    Returns:
        dict representing user addresses
    """
    return users_api.create_address_v2(connection=connection, id=id, body=body).json()


def update_address(connection: Connection, id: str, address_id: str, body: dict):
    """Update a user address.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        address_id: ID of the address
        body: body of the request

    Returns:
        True if successfully updated, False otherwise
    """
    return users_api.update_address_v2(
        connection=connection, id=id, address_id=address_id, body=body
    ).ok


def delete_address(connection: Connection, id: str, address_id: str):
    """Delete a user address.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        address_id: ID of the address

    Returns:
        True if successfully deleted, False otherwise
    """
    return users_api.delete_address(
        connection=connection, id=id, address_id=address_id
    ).ok


def get_security_filters(connection: Connection, id: str, projects: str | list[str]):
    """Get security filters for a user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user
        projects: IDs of the projects

    Returns:
        list of user security filters
    """
    return users_api.get_security_filters(
        connection=connection, id=id, projects=projects
    ).json()


@method_version_handler('11.3.0700')
def update_user_settings(connection: Connection, id: str, body: str):
    """Update user settings.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        True if successfully updated, False otherwise
    """
    response = users_api.update_user_settings(connection=connection, id=id, json=body)
    if response.ok:
        # Body is returned as endpoint returns 204 with empty response, which
        # would fail when using response.json() .
        # In order to alter user correctly, we return body to reflect changes
        return body
    return response


def get_user_last_login(connection: Connection, id: str):
    # Call the telemetry endpoint. Retry if the user is not found.
    # This is required because the user appears in the Telemetry Service
    # with a slight delay after the user is created.

    # The endpoint returns 404 in two cases, differentiated by error message:
    # if the user does not exist (may be due to a delay) and
    # if the user exists but does not have any login records.

    no_login_date_msg = 'No login found for the given user'
    no_user_msg = 'User not found'

    end_time = time() + TIMEOUT

    while time() < end_time:
        response = users_api.get_user_last_login(
            connection=connection,
            id=id,
            whitelist=[(404, 404)],
            throw_error=False,
            verbose=False,
        )
        try:
            res = response.json()
        except JSONDecodeError:
            if no_user_msg in response.text:
                sleep(TIMEOUT_INCREMENT)
                continue
            elif no_login_date_msg in response.text:
                return None
            raise response.raise_for_status()

        error = res.get('errors', [None])[0]

        if error:
            if no_user_msg in error.get('message'):
                sleep(TIMEOUT_INCREMENT)
                continue

            if no_login_date_msg in error.get('message'):
                return None

            server_code = error.get('code')
            ticket_id = error.get('ticketId')
            server_msg = error.get('message')

            raise IServerError(
                message=f"{server_msg}; code: '{server_code}', "
                f"ticket_id: '{ticket_id}'",
                http_code=response.status_code,
            )

        return res

    raise ValueError(f"There is no user with ID {id}. Timeout exceeded")


def get_default_email_device(connection: Connection, id: str) -> dict | None:
    """Get default email device for a user.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user

    Returns:
        dict representing default email device
    """

    addresses = get_addresses(connection=connection, id=id).get('addresses')
    default_email_device_id = next(
        (
            address.get('deviceId')
            for address in addresses
            if address.get('isDefault') and address.get('deliveryType') == 'email'
        ),
        None,
    )
    if default_email_device_id is None:
        return None
    device = devices.get_device(connection, id=default_email_device_id).json()

    return {'email_device': device}
