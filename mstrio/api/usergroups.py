from typing import List, Optional, TYPE_CHECKING, Union

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession

    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error getting user groups privileges for a group with ID {id}')
def get_privileges(connection, id, privilege_level=None, project_id=None, error_msg=None):
    """Get user group's privileges of a project including the source of the
    privileges.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        privilege_level (string, optional) [server, project]: String
            representing level of privileges required
        project_id (string, optional): Project id string
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}/privileges',
        headers={'X-MSTR-ProjectID': None},
        params={
            'privilege.level': privilege_level,
            'projectId': project_id
        },
    )


@ErrorHandler(err_msg='Error getting user groups memberships for a group with ID {id}')
def get_memberships(connection, id, error_msg=None):
    """Get information for the user group that is the direct parent of a
    specific user group.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required memberships
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}/memberships',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg='Error getting user groups members for a group with ID {id}')
def get_members(connection, id, include_access=False, offset=0, limit=-1, error_msg=None):
    """Get member information for a specific user group.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        include_access (bool, optional): Specifies whether to return access for
            members
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}/members',
        headers={'X-MSTR-ProjectID': None},
        params={
            'includeAccess': include_access,
            'offset': offset,
            'limit': limit
        },
    )


@ErrorHandler(err_msg='Error getting user group settings for a group with ID {id}')
def get_settings(connection, id, include_access=False, offset=0, limit=-1, error_msg=None):
    """Update the governing setting of the user group id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        include_access (bool, optional): Specifies whether to return access for
            members
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}/settings',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg='Error getting user groups top level.')
def get_top_level(connection, error_msg=None):
    """Get information for all of the user groups that exist at the level of
    the MicroStrategy Everyone user group.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/topLevel',
        headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error updating user group info with ID {id}')
def update_user_group_info(connection, id, body, error_msg=None):
    """Update specific information for a specific user group.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        body (JSON): Body.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object
    """

    return connection.patch(
        url=f'{connection.base_url}/api/usergroups/{id}',
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )


@ErrorHandler(err_msg='Error deleting user group with ID {id}')
def delete_user_group(connection, id, error_msg=None):
    """Delete user group for specific user group id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object
    """

    return connection.delete(
        url=f'{connection.base_url}/api/usergroups/{id}',
        headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error overwriting user group info for a group with ID {id}')
def replace_user_group_info(connection, id, error_msg=None):
    """Update all of the information for a specific user group.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object
    """

    return connection.put(
        url=f'{connection.base_url}/api/usergroups/{id}',
        headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error getting information for a set of user groups.')
def get_info_all_user_groups(connection, name_begins, offset=0, limit=1000, fields=None,
                             error_msg=None):
    """Get information for a specific set of user groups or all user groups.
    You can refine the set of user groups that are returned with a query
    parameter that specifies the characters that the user group name must begin
    with; if you omit the nameBegins query parameter, all user groups are
    returned. You can limit the results that are returned with two query
    parameters. The offset parameter specifies the location in the list of
    users groups to begin returning results and the limit parameter specifies
    the maximum number of matching user groups that can be returned; if you set
    the limit parameter to -1, all results are returned (subject to Governing
    settings). The total count of results returned is included in the response
    header as "x-mstr-total-count". You obtain the authorization token needed
    to execute the request using POST /auth/login; you pass the authorization
    token in the request header.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins (string): only user groups with given beginning of name will
            be retrieved
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    return connection.get(
        f'{connection.base_url}/api/usergroups/',
        headers={'X-MSTR-ProjectID': None},
        params={
            'nameBegins': name_begins,
            'offset': offset,
            'limit': limit,
            'fields': fields
        },
    )


def get_info_all_user_groups_async(future_session: "FuturesSession", connection, name_begins,
                                   offset=0, limit=-1, fields=None):
    """Get information for a set of users asynchronously.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        name_begins(string): Characters that the user name must begin with.
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
        'offset': offset,
        'limit': limit,
        'fields': fields,
    }
    url = f'{connection.base_url}/api/usergroups/'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


@ErrorHandler(err_msg='Error creating a new user group.')
def create_user_group(connection, body):
    """Create a new user group. The response includes the user group ID, which
    other endpoints use as a request parameter to specify the user group to
    perform an action on. You obtain the authorization token needed to execute
    the request using POST /auth/login; you pass the authorization token in the
    request header. You provide the information to create the.

    User group in the body parameter of the request - including the name and
    description of the user group, the IDs of parent user groups, and the IDs
    of child users or user groups.

    Args:
        connection: MicroStrategy REST API connection object
        body(JSON):{"name": "string",
                    "description": "string",
                    "memberships": ["string"],
                    "members": ["string"]}
    Returns:
        Complete HTTP response object
    """
    return connection.post(
        url=f'{connection.base_url}/api/usergroups/',
        json=body
    )


@ErrorHandler(err_msg='Error getting user group information for a group with ID {id}')
def get_user_group_info(connection, id, error_msg=None):
    """Get information for a specific user group.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}',
        headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error getting user group security roles for a group with ID {id}')
def get_security_roles(connection, id, project_id=None, error_msg=None):
    """Get security roles for a specific user group in a specific project.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of user group containing your required privileges
        project_id (string, optional): Project id string
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/usergroups/{id}/securityRoles',
        headers={'X-MSTR-ProjectID': None},
        params={'projectId': project_id},
    )


@ErrorHandler(err_msg='Error getting security filters for user with ID {id}.')
def get_security_filters(connection: "Connection", id: str,
                         projects: Optional[Union[str, List[str]]] = None, offset: int = 0,
                         limit: int = -1, error_msg: Optional[str] = None):
    """Get each project level security filter and its corresponding inherited
    security filters for the user group with given ID.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): User group ID
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
    url = f"{connection.base_url}/api/usergroups/{id}/securityFilters"
    projects = (
        ','.join(projects if isinstance(projects, list) else [projects])) if projects else projects
    params = {'projects.id': projects, 'offset': offset, 'limit': limit}
    return connection.get(url=url, params=params)
