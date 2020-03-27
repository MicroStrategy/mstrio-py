import requests
from mstrio.utils.helper import response_handler


def projects(connection, error_msg=None, verbose=False):
    """
    Args:
        connection: MicroStrategy REST API connection object
        verbose (bool, optional): Verbosity of server responses; defaults to False.
    Returns:
        Complete HTTP response object
    """

    response = requests.get(url=connection.base_url + '/api/projects',
                            headers={'X-MSTR-AuthToken': connection.auth_token},
                            cookies=connection.cookies, verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error connecting to project. Check project name and try again."
        response_handler(response, error_msg)
    return response
