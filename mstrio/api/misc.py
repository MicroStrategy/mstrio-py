import requests


def server_status(connection, verbose=False):
    """
     Args:
        connection: MicroStrategy REST API connection object
        verbose (bool, optional): Verbosity of server responses; defaults to False.
    Returns:
        Complete HTTP response object
    """

    response = requests.get(url=connection.base_url + '/status')

    if verbose:
        print(response.url)

    return response
