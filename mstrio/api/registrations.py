from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(
    err_msg="Error obtaining the list of registered nodes from the Strategy One "
    "deployment."
)
def get_nodes(connection, error_msg=None):
    """Obtain the list of registered nodes from the Strategy One deployment.

    Args:
        connection(object): Strategy One connection object returned by
            'connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    return connection.get(endpoint='/api/registrations/nodes')


@ErrorHandler(
    err_msg="Error obtaining the list of registered services available from "
    "the Strategy One deployment"
)
def get_services(connection, error_msg=None):
    """Obtain the list of registered services available from the Strategy One
    deployment.

    Args:
        connection(object): Strategy One connection object returned by
            'connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    return connection.get(endpoint='/api/registrations/services')


@ErrorHandler(
    err_msg="Error obtaining the metadata information for the registered services"
    " available from the Strategy One deployment."
)
def get_services_metadata(connection, error_msg=None):
    """Obtain the metadata information for the registered services available
    from the Strategy One deployment.

    Args:
        connection(object): Strategy One connection object returned by
            "connection.Connection().
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    return connection.get(endpoint='/api/registrations/services/metadata')


@ErrorHandler(err_msg="Error to start/stop service")
def start_stop_service(
    connection, login, password, name, id, address, action='START', error_msg=None
):
    """Start or stop registered service.

    Args:
        connection(object): Strategy One connection object returned by
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
        "password": password,
    }
    endpoint = '/api/registrations/services/control'
    return connection.post(endpoint=endpoint, json=body)
