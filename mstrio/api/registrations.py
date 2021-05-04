from mstrio.utils.helper import response_handler


def get_nodes(connection, error_msg=None):
    """Obtain the list of registered nodes from the MicroStrategy deployment.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    response = connection.session.get(url=connection.base_url + '/api/registrations/nodes')

    if not response.ok:
        if error_msg is None:
            error_msg = ("Error obtaining the list of registered nodes from the MicroStrategy "
                         "deployment")
        response_handler(response, error_msg)
    return response


def get_services(connection, error_msg=None):
    """Obtain the list of registered services available from the MicroStrategy
    deployment.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    response = connection.session.get(url=connection.base_url + '/api/registrations/services')

    if not response.ok:
        if error_msg is None:
            error_msg = ("Error obtaining the list of registered services available from the "
                         "MicroStrategy deployment")
        response_handler(response, error_msg)
    return response


def get_services_metadata(connection, error_msg=None):
    """Obtain the metadata information for the registered services available
    from the MicroStrategy deployment.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    response = connection.session.get(url=connection.base_url
                                      + '/api/registrations/services/metadata')

    if not response.ok:
        if error_msg is None:
            error_msg = ("Error obtaining the metadata information for the registered services "
                         "available from the MicroStrategy deployment")
        response_handler(response, error_msg)
    return response


def start_stop_service(connection, login, password, name, id, address, action="START",
                       error_msg=None):
    """Start or stop registered service.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection()
        login (string): login for SSH operation
        password (string): password for SSH operation
        name(string): name of the service
        id(string): name of the service
        action(string): one of "START" or "STOP"
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        Complete HTTP response object.
    """

    body = {
        "name": name,
        "id": id,
        "action": action,
        "address": address,
        "login": login,
        "password": password
    }

    response = connection.session.post(
        url=connection.base_url + '/api/registrations/services/control', json=body)
    return response
