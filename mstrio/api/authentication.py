from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(
    err_msg="Authentication error. Check user credentials or REST API URL and try again"
)
def login(connection: 'Connection') -> 'Response':
    """Authenticate a user and create an HTTP session on the web server where
    the user's Strategy One sessions are stored.

    This request returns an authorization token (X-MSTR-AuthToken) which will be
    submitted with subsequent requests. The body of the request contains
    the information needed to create the session. The loginMode parameter in
    the body specifies the authentication mode to use. You can authenticate with
    one of the following authentication modes: Standard (1), Anonymous (8),
    LDAP (16) or API Token (4096). Authentication modes can be enabled through
    System Administration REST APIs, if they are supported by the deployment.

    Args:
        connection (Connection): Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """

    ENDPOINT = '/api/auth/login'
    APPLICATION_TYPE = 35

    auth_data = {
        'loginMode': connection.login_mode,
        'applicationType': APPLICATION_TYPE,
    }

    if app_id := connection.application_id:
        auth_data['applicationId'] = app_id

    if connection.login_mode == 4096:
        auth_data['username'] = connection.api_token
        return connection.post(
            skip_expiration_check=True, endpoint=ENDPOINT, json=auth_data
        )

    auth_data.update(
        {
            'username': connection.username,
            'password': connection._Connection__password,
        }
    )

    return connection.post(
        skip_expiration_check=True, endpoint=ENDPOINT, data=auth_data
    )


@ErrorHandler(err_msg="Failed to logout.")
def logout(connection, error_msg=None, whitelist=None):
    """Close all existing sessions for the authenticated user.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        skip_expiration_check=True,
        endpoint='/api/auth/logout',
        headers={'X-MSTR-ProjectID': None},
    )


def session_renew(connection):
    """Extends the HTTP and Intelligence Server sessions by resetting the
    timeouts.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.put(
        skip_expiration_check=True,
        endpoint='/api/sessions',
        headers={'X-MSTR-ProjectID': None},
        timeout=2.0,
    )


def session_status(connection):
    """Checks Intelligence Server session status.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        skip_expiration_check=True,
        endpoint='/api/sessions',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Could not get identity token.")
def identity_token(connection):
    """Create a new identity token.

    An identity token is used to share an existing session with another
    project, based on the authorization token for the existing
    session.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        endpoint='/api/auth/identityToken',
    )


@ErrorHandler(err_msg="Could not get API token.")
def api_token(connection):
    """Create a new API token.

    An API token is used to authenticate a user via login mode 4096.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        endpoint='/api/auth/apiTokens',
    )


def validate_identity_token(connection, identity_token):
    """Validate an identity token.

    Args:
        connection: Strategy One REST API connection object
        identity_token: Identity token

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        endpoint='/api/auth/identityToken',
        headers={'X-MSTR-IdentityToken': identity_token},
    )


@ErrorHandler(
    err_msg="Error creating a new Web server session that shares an existing IServer "
    "session."
)
def delegate(connection, identity_token, whitelist=None):
    """Returns authentication token and cookies from given X-MSTR-
    IdentityToken.

    Args:
        connection: Strategy One REST API connection object
        identity_token: Identity token
        whitelist: list of errors for which we skip printing error messages

    Returns:
        Complete HTTP response object.
    """
    return connection.post(
        skip_expiration_check=True,
        endpoint='/api/auth/delegate',
        json={'loginMode': "-1", 'identityToken': identity_token},
    )


@ErrorHandler(err_msg="Error getting privileges list.")
def user_privileges(connection):
    """Get the list of privileges for the authenticated user.

    The response includes the name, ID, and description of each
    privilege and specifies which projects the privileges are valid for.

    Args:
        connection: Strategy One REST API connection object

    Returns:
        Complete HTTP response object.
    """
    return connection.get(endpoint='/api/sessions/privileges')


@ErrorHandler(err_msg="Error getting info for authenticated user.")
def get_info_for_authenticated_user(connection, error_msg=None):
    """Get information for the authenticated user.

    Args:
        connection: Strategy One REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    return connection.get(endpoint='/api/sessions/userInfo')
