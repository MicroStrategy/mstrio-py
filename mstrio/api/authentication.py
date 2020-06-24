from mstrio.utils.helper import response_handler


def login(connection, verbose=False):
    """
    Authenticate a user and create an HTTP session on the web server where the user’s MicroStrategy sessions are
    stored.

    This request returns an authorization token (X-MSTR-AuthToken) which will be submitted with subsequent requests.
    The body of the request contains the information needed to create the session. The loginMode parameter in the body
    specifies the authentication mode to use. You can authenticate with one of the following authentication modes:
    Standard (1), Anonymous (8), or LDAP (16). Authentication modes can be enabled through the System Administration
    REST APIs, if they are supported by the deployment.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    response = connection.session.post(url=connection.base_url + '/api/auth/login',
                                       data={'username': connection.username,
                                             'password': connection.password,
                                             'loginMode': connection.login_mode,
                                             'applicationType': 64})
    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Authentication error. Check user credentials or REST API URL and try again.")
    return response


def logout(connection, verbose=False):
    """
    Close all existing sessions for the authenticated user.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = connection.session.post(url=connection.base_url + '/api/auth/logout',
                                       headers={'X-MSTR-ProjectID': None})
    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Failed to logout.")
    return response


def session_renew(connection, verbose=False):
    """
    Extends the HTTP and Intelligence Server sessions by resetting the timeouts.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = connection.session.put(url=connection.base_url + '/api/sessions',
                                      headers={'X-MSTR-ProjectID': None})
    if verbose:
        print(response.url)
    return response


def session_status(connection, verbose=False):
    """
    Checks Intelligence Server session status.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = connection.session.get(url=connection.base_url + '/api/sessions',
                                      headers={'X-MSTR-ProjectID': None})
    if verbose:
        print(response.url)
    # if not response.ok:
    #     response_handler(response, "Session expired. Please reconnect to MicroStrategy.")
    return response


def identity_token(connection, verbose=False):
    """
    Create a new identity token. An identity token is used to share an existing session with another application,
    based on the authorization token for the existing session
    """
    response = connection.session.post(url=connection.base_url+'/api/auth/identityToken',
                                       headers={"X-MSTR-AuthToken": connection.session.headers['X-MSTR-AuthToken']})
    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Could not get identity token.")
    return response


def validate_identity_token(connection, identity_token, verbose=False):
    """
    Validate an identity token.

    """
    response = connection.session.get(url=connection.base_url+'/api/auth/identityToken',
                                      headers={'X-MSTR-IdentityToken': identity_token})

    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Could not validate identity token.")
    return response


def delegate(connection, identity_token, verbose=False):
    """
    Returns authentication token and cookies from given X-MSTR-IdentityToken

    """
    response = connection.session.post(url=connection.base_url + '/api/auth/delegate',
                                       json={'loginMode': "-1",
                                             'identityToken': identity_token})

    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Error creating a new Web server session that shares an existing IServer session.")
    return response
