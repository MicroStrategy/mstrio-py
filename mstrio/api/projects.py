import requests


def projects(connection, verbose=False):
    """

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")

    response = requests.get(url=connection.base_url + '/projects',
                            headers={'X-MSTR-AuthToken': connection.auth_token},
                            cookies=connection.cookies, verify=connection.ssl_verify)
    if verbose:
        print(response.url)

    return response
