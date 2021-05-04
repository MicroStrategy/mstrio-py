from mstrio.utils.helper import response_handler


def get_recipients(connection, search_term, search_pattern="CONTAINS_ANY_WORD", offset=0, limit=-1,
                   enabled_status='ALL'):
    """Get information for a set of recipients.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        search_term(string): The value that the search_pattern parameter is set
            to. For example, if the search search_pattern is “Begins with”,
            this parameter would be the value that the search results would
            begin with.
        search_pattern(string): Available values : NONE, CONTAINS_ANY_WORD,
            BEGINS_WITH, BEGINS_WITH_PHRASE, EXACTLY, CONTAINS, ENDS_WITH.
            Default value : CONTAINS_ANY_WORD
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        enabled_status(string): Specifies whether to return only enabled users
            or all users and user groups that match the search criteria.
            Available values : ALL, ENABLED_ONLY. Default value : ALL.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(
        url=connection.base_url + '/api/collaboration/resipients',
        params={
            'searchTerm': search_term,
            'searchPattern': search_pattern,
            'offset': offset,
            'limit': limit,
            'enabledStatus': enabled_status
        },
    )

    if not response.ok:
        response_handler(response, "Error getting information for a set of recipients.")
    return response


def get_users_info(connection, name_begins, abbreviation_begins, offset=0, limit=-1, fields=None,
                   error_msg=None):
    """Get information for a set of users.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins(string): Characters that the user name must begin with.
        abbreviation_begins(string): Characters that the user abbreviation must
            begin with.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(
        url=connection.base_url + '/api/users/',
        params={
            'nameBegins': name_begins,
            'abbreviationBegins': abbreviation_begins,
            'offset': offset,
            'limit': limit,
            'fields': fields
        },
        headers={'X-MSTR-ProjectID': None},
    )

    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting information for a set of users."
        response_handler(response, error_msg)
    return response


def get_users_info_async(future_session, connection, name_begins, abbreviation_begins, offset=0,
                         limit=-1, fields=None):
    """Get information for a set of users asynchronously.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins(string): Characters that the user name must begin with.
        abbreviation_begins(string): Characters that the user abbreviation must
            begin with.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    params = {
        'nameBegins': name_begins,
        'abbreviationBegins': abbreviation_begins,
        'offset': offset,
        'limit': limit,
        'fields': fields
    }
    url = connection.base_url + '/api/users/'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


def create_user(connection, body, fields=None):
    """Create a new user. The response includes the user ID, which other
    endpoints use as a request parameter to specify the user to perform an
    action on.

    Args:
        connection(object): MicroStrategy connection object returned by
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
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.post(
        url=connection.base_url + '/api/users',
        params={'fields': fields},
        json=body,
    )

    if not response.ok:
        response_handler(
            response,
            "Error creating a new user with username: '{}'.".format(body.get('username')))
    return response


def get_addresses(connection, id, fields=None):
    """Get all of the addresses for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.get(url=connection.base_url + '/api/users/' + id + '/addresses',
                                      params={'fields': fields})

    if not response.ok:
        response_handler(response, "Error getting addresses for a specific user.")
    return response


def create_address(connection, id, body, fields=None):
    """Create a new address for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        body: JSON-formatted addres:
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

    response = connection.session.post(
        url=connection.base_url + '/api/users/' + id + '/addresses',
        params={'fields': fields},
        json=body,
    )

    if not response.ok:
        response_handler(response, "Error creating a new address for a specific user. ")
    return response


def update_address(connection, id, address_id, fields=None):
    """Update a specific address for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        address_id(string): Address ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.put(
        url=connection.base_url + '/api/users/' + id + '/addresses' + address_id,
        params={'fields': fields},
    )

    if not response.ok:
        response_handler(response, "Error updating a specific address for a specific user. ")
    return response


def delete_address(connection, id, address_id, fields=None):
    """Delete a specific address for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        address_id(string): Address ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.delete(
        url=connection.base_url + '/api/users/' + id + '/addresses/' + address_id,
        headers={'X-MSTR-ProjectID': None},
        params={'fields': fields},
    )

    if not response.ok:
        response_handler(response, "Error deleting a specific address for a specific user. ")
    return response


def get_user_security_roles(connection, id, project_id=None):
    """Get all of the security roles for a specific user in a specific project.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): User ID

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(
        url=connection.base_url + '/api/users/' + id + '/securityRoles',
        params={'projectId': project_id},
    )

    if not response.ok:
        response_handler(
            response,
            "Error getting all of the security roles for a specific user in a specific project")
    return response


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
    response = connection.session.get(
        connection.base_url + '/api/users/' + id + '/privileges/',
        params={
            'privilege.level': privilege_level,
            'projectId': project_id
        },
    )

    if not response.ok:
        response_handler(response, "Error getting user's privileges for a project.")
    return response


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
    response = connection.session.get(connection.base_url + '/api/users/' + id + '/projects/'
                                      + project_id + '/quotas')

    if not response.ok:
        response_handler(response, "Error getting user data usage limit for the specific project.")
    return response


def get_user_info(connection, id, fields=None):
    """Get information for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.get(url=connection.base_url + '/api/users/' + id,
                                      params={'fields': fields})

    if not response.ok:
        response_handler(response, "Error getting information for a specific user.")
    return response


def delete_user(connection, id):
    """Delete user for specific user id.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.delete(url=connection.base_url + '/api/users/' + id)

    if not response.ok:
        response_handler(response, "Error deleting user.")
    return response


def update_user_info(connection, id, body, fields=None):
    """Update specific information for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
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
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.patch(
        url=connection.base_url + '/api/users/' + id,
        params={'fields': fields},
        json=body,
    )

    if not response.ok:
        response_handler(response, "Error updating specific information for a specific user.")
    return response


def get_memberships(connection, id, fields=None):
    """Get information for the direct user groups that a specific user belongs
    to.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(string): User ID.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    response = connection.session.get(
        url=connection.base_url + '/api/users/' + id + '/memberships',
        params={'fields': fields},
    )

    if not response.ok:
        response_handler(
            response,
            "Error getting information for the direct user groups that a specific user belongs to."
        )
    return response


# Deprecated
def change_password(connection, body, fields=None):
    """Change the password for a specific user.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        body (JSON): Body.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.post(
        url=connection.base_url + '/api/users/changePassword',
        params={'fields': fields},
        json=body,
    )

    if not response.ok:
        response_handler(response, "Error changing password.")
    return response
