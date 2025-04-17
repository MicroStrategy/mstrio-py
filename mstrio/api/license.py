from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting license information.")
def get_license(
    connection: Connection, node_name: str, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license information for the authenticated user.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to get license information
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error getting license activation information.")
def get_license_activation_info(
    connection: Connection, node_name: str, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license activation information for the authenticated user.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to get license activation
            information
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}/activation'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error updating license information.")
def update_license_information(
    connection: Connection, node_name: str, operations: list, error_msg=None
) -> Response:
    """Update the license information using operations list.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to update license
            information
        operations (list): List of operations to perform on the license
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}'
    body = {'operationList': operations}

    return connection.patch(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error updating license activation information.")
def update_license_activation(
    connection: Connection, node_name: str, operations: list, error_msg=None
) -> Response:
    """Update the license activation information.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to update the license
            activation information
        operations (list): List of activation operations to be performed
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}/activation'
    body = {'operationList': operations}

    return connection.patch(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error getting license activation XML file.")
def get_activation_xml_file(
    connection: Connection, node_name: str, fields: str | None = None, error_msg=None
) -> Response:
    """Get the activation XML file for the authenticated user.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to get activation XML file
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}/activation/xmlFile'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)
