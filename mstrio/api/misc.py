import requests
from mstrio.utils.helper import response_handler


def server_status(connection, verbose=False):
    """
     Args:
        connection: MicroStrategy REST API connection object
        verbose (bool, optional): Verbosity of server responses; defaults to False.
    Returns:
        Complete HTTP response object
    """

    response = requests.get(url=connection.base_url + '/api/status',
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)

    if verbose:
        print(response.url)
    if not response.ok:
        response_handler(response, "Failed to check server status")
    return response
