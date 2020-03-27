import requests
from mstrio.utils.helper import response_handler


def login(connection, verbose=False):
    """
    Authenticate a user and create an HTTP session on the web server where the user’s MicroStrategy sessions are stored.
    This request returns an authorization token (X-MSTR-AuthToken) which will be submitted with subsequent requests.
    The body of the request contains the information needed to create the session. The loginMode parameter in the body
    specifies the authentication mode to use. You can authenticate with one of the following authentication modes:
    Standard (1), Anonymous (8), or LDAP (16). Authentication modes can be enabled through the System Administration
    REST APIs, if they are supported by the deployment.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    response = requests.post(url=connection.base_url + '/api/auth/login',
                             data={'username': connection.username,
                                   'password': connection.password,
                                   'loginMode': connection.login_mode,
                                   'applicationType': connection.application_code},
                             verify=connection.ssl_verify)
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
    response = requests.post(url=connection.base_url + '/api/auth/logout',
                             headers={'X-MSTR-AuthToken': connection.auth_token},
                             cookies=connection.cookies,
                             verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Failed to logout.")
    return response


def sessions(connection, verbose=False):
    """
    Extends the HTTP and Intelligence Server sessions by resetting the timeouts.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = requests.put(url=connection.base_url + '/api/sessions',
                            headers={'X-MSTR-AuthToken': connection.auth_token},
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Session expired. Please reconnect to MicroStrategy.")
    return response
