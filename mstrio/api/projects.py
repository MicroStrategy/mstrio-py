import requests


def projects(connection, verbose=False):
    """
    Args:
        connection: MicroStrategy REST API connection object
        verbose (bool, optional): Verbosity of server responses; defaults to False.
    Returns:
        Complete HTTP response object
    """

    response = requests.get(url=connection.base_url + '/projects',
                            headers={'X-MSTR-AuthToken': connection.auth_token},
                            cookies=connection.cookies, verify=connection.ssl_verify)
    if verbose:
        print(response.url)

    return response
