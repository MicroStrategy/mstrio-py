from typing import Optional, TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession

    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error getting information for a set of recipients.')
def get_recipients(
    connection,
    search_term,
    search_pattern="CONTAINS_ANY_WORD",
    offset=0,
    limit=-1,
    enabled_status='ALL'
):
    """Get information for a set of recipients.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_term (string): The value that the search_pattern parameter is set
            to. For example, if the search search_pattern is “Begins with”,
            this parameter would be the value that the search results would
            begin with.
        search_pattern (string): Available values : NONE, CONTAINS_ANY_WORD,
            BEGINS_WITH, BEGINS_WITH_PHRASE, EXACTLY, CONTAINS, ENDS_WITH.
            Default value : CONTAINS_ANY_WORD
        offset (int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit (int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        enabled_status (string): Specifies whether to return only enabled users
            or all users and user groups that match the search criteria.
            Available values : ALL, ENABLED_ONLY. Default value : ALL.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.get(
        url=f'{connection.base_url}/api/collaboration/recipients',
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'enabledStatus': enabled_status
        },
    )


@ErrorHandler(err_msg='Error getting information for a set of users')
def get_users_info(
    connection, name_begins, abbreviation_begins, offset=0, limit=-1, fields=None, error_msg=None
):
    """Get information for a set of users.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins (string): Characters that the user name must begin with.
        abbreviation_begins (string): Characters that the user abbreviation must
            begin with.
        offset (int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit (int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.get(
        url=f'{connection.base_url}/api/users/',
        params={
            'nameBegins': name_begins,
            'abbreviationBegins': abbreviation_begins,
            'offset': offset,
            'limit': limit,
            'fields': fields
        },
        headers={'X-MSTR-ProjectID': None},
    )


def get_users_info_async(
    future_session: "FuturesSession",
    connection,
    name_begins,
    abbreviation_begins,
    offset=0,
    limit=-1,
    fields=None
):
    """Get information for a set of users asynchronously.

    Args:
        future_session: Future Session object to call MicroStrategy REST
            Server asynchronously
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins (string): Characters that the user name must begin with.
        abbreviation_begins (string): Characters that the user abbreviation must
            begin with.
        offset (int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit (int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        Complete Future object.
    """
    params = {
        'nameBegins': name_begins,
        'abbreviationBegins': abbreviation_begins,
        'offset': offset,
        'limit': limit,
        'fields': fields
    }
    url = f'{connection.base_url}/api/users/'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


@ErrorHandler(err_msg='Error creating a new user with username: {username}')
def create_user(connection, body, username, fields=None):
    """Create a new user. The response includes the user ID, which other
    endpoints use as a request parameter to specify the user to perform an
    action on.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        body: JSON formatted user data;
                {
                "username": "string",
                "fullName": "string",
                "description": "string",
                "password": "string",
                "enabled": true,
                "passwordModifiable": true,
                "passwordExpirationDate": "2020-06-15T13:26:09.616Z",
                "requireNewPassword": true,
                "standardAuth": true,
                "ldapdn": "string",
                "trustId": "string",
                "memberships": [
                    "string"
                ]
                }
        username (str): username of a user, used in error message
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.post(
        url=f'{connection.base_url}/api/users',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg='Error getting addresses for user with ID {id}')
def get_addresses(connection, id, fields=None):
    """Get all of the addresses for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.get(
        url=f'{connection.base_url}/api/users/{id}/addresses', params={'fields': fields}
    )


@ErrorHandler(err_msg='Error creating a new address for user with ID {id}')
def create_address(connection, id, body, fields=None):
    """Create a new address for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        body: JSON-formatted address:
                {
                "name": "string",
                "deliveryMode": "EMAIL",
                "device": "GENERIC_EMAIL",
                "value": "string",
                "isDefault": true,
                "default": true
                }

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.post(
        url=f'{connection.base_url}/api/users/{id}/addresses',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg='Error creating a new address for user with ID {id}')
def create_address_v2(
    connection: "Connection", id: str, body: dict, fields: Optional[str] = None
) -> Response:
    """Create a new address for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        body (JSON): JSON-formatted address:
                {
                "name": "string",
                "physicalAddress": "string",
                "deliveryType": "string",
                "deviceId": "string",
                "deviceName": "string",
                "isDefault": boolean
                }
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.post(
        url=f'{connection.base_url}/api/v2/users/{id}/addresses',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg='Error updating address with ID {address_id} for user with ID {id}')
def update_address(connection, id, address_id, body, fields=None):
    """Update a specific address for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        address_id (string): Address ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.put(
        url=f'{connection.base_url}/api/users/{id}/addresses/{address_id}',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg='Error deleting address with ID {address_id} for a user with ID {id}')
def delete_address(connection, id, address_id, fields=None):
    """Delete a specific address for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        address_id (string): Address ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.delete(
        url=f'{connection.base_url}/api/users/{id}/addresses/{address_id}',
        headers={'X-MSTR-ProjectID': None},
        params={'fields': fields},
    )


@ErrorHandler(err_msg='Error getting security roles for a user with ID {id}')
def get_user_security_roles(connection, id, project_id=None):
    """Get all of the security roles for a specific user in a specific project.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): User ID

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.get(
        url=f'{connection.base_url}/api/users/{id}/securityRoles',
        params={'projectId': project_id},
    )


@ErrorHandler(err_msg="Error getting user {id} privileges for a project")
def get_user_privileges(connection, id, project_id=None, privilege_level=None):
    """Get user's privileges of a project including the source of the
    privileges.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): User ID
        project_id (string, optional): Project ID
        privilege_level (string, optional): Project Level Privilege

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    url = f'{connection.base_url}/api/users/{id}/privileges/'
    return connection.get(
        url=url,
        params={
            'privilege.level': privilege_level, 'projectId': project_id
        },
    )


@ErrorHandler(err_msg='Error getting user data usage limit for project with ID {id}')
def get_user_data_usage_limit(connection, id, project_id):
    """Get the data usage limit for users, either all users or a specific user,
    in a specific project. A typical use case would be that an administrator
    has set a project-level limit of data, such as 10GB, for all users in a
    specific project and has also limited the data usage for specific users,
    for example to 5GB.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): User ID
        project_id (str): Project ID

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    url = f'{connection.base_url}/api/users/{id}/projects/{project_id}/quotas'
    return connection.get(url=url)


@ErrorHandler(err_msg='Error getting information for a user with ID {id}')
def get_user_info(connection, id, fields=None):
    """Get information for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.get(url=f'{connection.base_url}/api/users/{id}', params={'fields': fields})


@ErrorHandler(err_msg='Error deleting user with ID {id}')
def delete_user(connection, id):
    """Delete user for specific user id.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.delete(url=f'{connection.base_url}/api/users/{id}')


@ErrorHandler(err_msg='Error updating information for a user with ID: {id}')
def update_user_info(connection, id, body, fields=None):
    """Update specific information for a specific user.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        body (JSON):
                    Body:{
                        "operationList": [
                            {
                            "op": "replace",
                            "path": "/username",
                            "value": "john1991"
                            }
                        ]
                        }
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    return connection.patch(
        url=f'{connection.base_url}/api/users/{id}',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(
    err_msg='Error getting information for the direct user groups that '
    'a user with ID {id} belongs to.'
)
def get_memberships(connection, id, fields=None):
    """Get information for the direct user groups that a specific user belongs
    to.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): User ID.
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    return connection.get(
        url=f'{connection.base_url}/api/users/{id}/memberships',
        params={'fields': fields},
    )


@ErrorHandler(err_msg='Error getting security filters for user with ID {id}.')
def get_security_filters(
    connection: "Connection",
    id: str,
    projects: Optional[str | list[str]] = None,
    offset: int = 0,
    limit: int = -1,
    error_msg: Optional[str] = None
):
    """Get each project level security filter and its corresponding inherited
    security filters for the user with given ID.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): User ID
        projects (str or list of str, optional): collection of projects' ids
            which is used for filtering data
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is -1.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/users/{id}/securityFilters"

    projects = (
        ','.join(projects if isinstance(projects, list) else [projects])
    ) if projects else projects
    params = {'projects.id': projects, 'offset': offset, 'limit': limit}
    return connection.get(url=url, params=params)
