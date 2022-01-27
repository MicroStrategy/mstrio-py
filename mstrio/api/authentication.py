from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Authentication error. Check user credentials or REST API URL and try again')
def login(connection):
    """Authenticate a user and create an HTTP session on the web server where
    the user's MicroStrategy sessions are stored.

    This request returns an authorization token (X-MSTR-AuthToken) which will be
    submitted with subsequent requests. The body of the request contains
    the information needed to create the session. The loginMode parameter in
    the body specifies the authentication mode to use. You can authenticate with
    one of the following authentication modes: Standard (1), Anonymous (8),
    or LDAP (16). Authentication modes can be enabled through the System
    Administration REST APIs, if they are supported by the deployment.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """

    return connection.post(
        skip_expiration_check=True,
        url=f'{connection.base_url}/api/auth/login',
        data={
            'username': connection.username,
            'password': connection._Connection__password,
            'loginMode': connection.login_mode,
            'applicationType': 35,
        },
    )


@ErrorHandler(err_msg="Failed to logout.")
def logout(connection, error_msg=None, whitelist=None):
    """Close all existing sessions for the authenticated user.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        skip_expiration_check=True,
        url=f'{connection.base_url}/api/auth/logout',
        headers={'X-MSTR-ProjectID': None},
    )


def session_renew(connection):
    """Extends the HTTP and Intelligence Server sessions by resetting the
    timeouts.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.put(
        skip_expiration_check=True,
        url=f'{connection.base_url}/api/sessions',
        headers={'X-MSTR-ProjectID': None},
    )


def session_status(connection):
    """Checks Intelligence Server session status.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        skip_expiration_check=True,
        url=f'{connection.base_url}/api/sessions',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg='Could not get identity token.')
def identity_token(connection):
    """Create a new identity token.

    An identity token is used to share an existing session with another
    project, based on the authorization token for the existing
    session.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        url=f'{connection.base_url}/api/auth/identityToken',
    )


def validate_identity_token(connection, identity_token):
    """Validate an identity token.

    Args:
        connection: MicroStrategy REST API connection object
        identity_token: Identity token

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        url=f'{connection.base_url}/api/auth/identityToken',
        headers={'X-MSTR-IdentityToken': identity_token},
    )


@ErrorHandler(
    err_msg='Error creating a new Web server session that shares an existing IServer session.')
def delegate(connection, identity_token, whitelist=None):
    """Returns authentication token and cookies from given X-MSTR-
    IdentityToken.

    Args:
        connection: MicroStrategy REST API connection object
        identity_token: Identity token
        whitelist: list of errors for which we skip printing error messages

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        skip_expiration_check=True,
        url=f'{connection.base_url}/api/auth/delegate',
        json={
            'loginMode': "-1",
            'identityToken': identity_token
        },
    )


@ErrorHandler(err_msg='Error getting privileges list.')
def user_privileges(connection):
    """Get the list of privileges for the authenticated user.

    The response includes the name, ID, and description of each
    privilege and specifies which projects the privileges are valid for.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.get(url=f"{connection.base_url}/api/sessions/privileges")


@ErrorHandler(err_msg='Error getting info for authenticated user.')
def get_info_for_authenticated_user(connection, error_msg=None):
    """Get information for the authenticated user.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f'{connection.base_url}/api/sessions/userInfo'
    return connection.get(url=url)
