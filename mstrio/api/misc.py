from requests.exceptions import SSLError

from mstrio.utils.helper import exception_handler, response_handler


def server_status(connection):
    """
     Args:
        connection: MicroStrategy REST API connection object
    Returns:
        Complete HTTP response object
    """

    try:
        response = connection.get(
            skip_expiration_check=True,
            url=connection.base_url + '/api/status'
        )
    except SSLError:
        exception_handler(
            ("SSL certificate error.\nPlease double check that the link you "
             "are using comes from a trusted source. If you trust the URL "
             "provided please specify parameter 'ssl_verify' to 'False' in the "
             "'Connection' class.\n\nCheck readme for more details."),
            SSLError)

    if not response.ok:
        response_handler(response, "Failed to check server status")
    return response
