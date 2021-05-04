from mstrio.utils.helper import response_handler


def login(connection):
    """Authenticate a user and create an HTTP session on the web server where
    the user’s MicroStrategy sessions are stored.

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

    response = connection.session.post(
        url=connection.base_url + '/api/auth/login',
        data={
            'username': connection.username,
            'password': connection._Connection__password,
            'loginMode': connection.login_mode,
            'applicationType': 35,
        },
    )
    if not response.ok:
        response_handler(
            response,
            "Authentication error. Check user credentials or REST API URL and try again.")
    return response


def logout(connection):
    """Close all existing sessions for the authenticated user.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.post(url=connection.base_url + '/api/auth/logout',
                                       headers={'X-MSTR-ProjectID': None})
    if not response.ok:
        response_handler(response, "Failed to logout.")
    return response


def session_renew(connection):
    """Extends the HTTP and Intelligence Server sessions by resetting the
    timeouts.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.put(url=connection.base_url + '/api/sessions',
                                      headers={'X-MSTR-ProjectID': None})
    return response


def session_status(connection):
    """Checks Intelligence Server session status.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(url=connection.base_url + '/api/sessions',
                                      headers={'X-MSTR-ProjectID': None})

    return response


def identity_token(connection):
    """Create a new identity token.

    An identity token is used to share an existing session with another
    application, based on the authorization token for the existing
    session.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.post(
        url=connection.base_url + '/api/auth/identityToken',
        headers={"X-MSTR-AuthToken": connection.session.headers['X-MSTR-AuthToken']},
    )
    if not response.ok:
        response_handler(response, "Could not get identity token.")
    return response


def validate_identity_token(connection, identity_token):
    """Validate an identity token.

    Args:
        connection: MicroStrategy REST API connection object
        identity_token: Identity token

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(url=connection.base_url + '/api/auth/identityToken',
                                      headers={'X-MSTR-IdentityToken': identity_token})
    return response


def delegate(connection, identity_token, whitelist=[]):
    """Returns authentication token and cookies from given X-MSTR-
    IdentityToken.

    Args:
        connection: MicroStrategy REST API connection object
        identity_token: Identity token
        whitelist: list of errors for which we skip printing error messages

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.post(
        url=connection.base_url + '/api/auth/delegate',
        json={
            'loginMode': "-1",
            'identityToken': identity_token
        },
    )

    if not response.ok:
        response_handler(
            response,
            "Error creating a new Web server session that shares an existing IServer session.",
            whitelist=whitelist)
    return response


def user_privileges(connection):
    """Get the list of privileges for the authenticated user.

    The response includes the name, ID, and description of each
    privilege and specifies which projects the privileges are valid for.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(url=connection.base_url + '/api/sessions/privileges')

    if not response.ok:
        response_handler(response, "Error getting priviliges list")
    return response


def get_info_for_authenticated_user(connection, error_msg=None):
    """Get information for the authenticated user.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = connection.base_url + "/api/sessions/userInfo"
    token = connection.session.headers['X-MSTR-AuthToken']
    headers = {"X-MSTR-AuthToken": token}
    response = connection.session.get(url=url, headers=headers)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting info for authenticated user"
        response_handler(response, error_msg)
    return response
