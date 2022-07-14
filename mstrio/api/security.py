from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error getting privileges.')
def get_privileges(connection, error_msg=None):
    """Get the set of available privileges for the platform.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/iserver/privileges', headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error getting privilege categories.')
def get_privilege_categories(connection, error_msg=None):
    """Get the set of available privilege categories for the platform.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/iserver/privileges/categories',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg='Error getting information for set of security roles.')
def get_security_roles(connection, fields=None, error_msg=None):
    """Get information for all security roles. A security role describes the
    ability to do something, such as create, edit, add, delete, view, manage,
    save, search, share, export, and so on. A security role has a name, a
    description, and a privilege.

    Args:
        connection: MicroStrategy REST API connection object
        fields: top-level field whitelist which allows client to selectively
            retrieve part of the response model
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/securityRoles',
        headers={'X-MSTR-ProjectID': None},
        params={'fields': fields}
    )


@ErrorHandler(err_msg='Error creating new security role.')
def create_security_role(connection, body, error_msg=None):
    """Create a new security role.

    Args:
        connection: MicroStrategy REST API connection object
        body: JSON-formatted definition of the dataset. Generated by
            `utils.formjson()`.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        url=f'{connection.base_url}/api/securityRoles',
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )


@ErrorHandler(err_msg='Error getting security role {id} information.')
def get_security_role(connection, id, error_msg=None):
    """Get information for a security role with security role Id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Security role ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/securityRoles/{id}', headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error deleting security role with ID {id}.')
def delete_security_role(connection, id, error_msg=None):
    """Delete info for a security role with given Id.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Security role ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.delete(
        url=f'{connection.base_url}/api/securityRoles/{id}', headers={'X-MSTR-ProjectID': None}
    )


@ErrorHandler(err_msg='Error updating security role with ID {id}')
def update_security_role(connection, id, body, error_msg=None):
    """Update information for a specific security role.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Security role ID
        body: JSON-formatted definition of the dataset. Generated by
            `utils.formjson()`.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.patch(
        url=f'{connection.base_url}/api/securityRoles/{id}',
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )


@ErrorHandler(err_msg='Error getting security role with ID {id} for project with ID {project_id}')
def get_security_role_for_project(connection, id, project_id, error_msg=None):
    """Get all users and user groups that are linked to a specific security
    role.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): Security role ID
        project_id (string, optional): Project id string
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/securityRoles/{id}/projects/{project_id}/members',
        headers={'X-MSTR-ProjectID': None},
    )
