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
        response = connection.session.get(url=connection.base_url + '/api/status')
    except SSLError:
        exception_handler("SSL certificate error, if you are using a self-signed certificate, copy your SSL certificate to your working directory or pass the path to the certificate to your Connection. \nOtherwise please double check that the link you are using comes from a trusted source.\n\nCheck readme for more details.",  # noqa
                          SSLError)

    if not response.ok:
        response_handler(response, "Failed to check server status")
    return response
