from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting license information.")
def get_license(
    connection: Connection, node_name: str, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license information.

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
    """Get the license activation information.

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
    """Get the activation XML file.

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


@ErrorHandler(err_msg="Error getting license history.")
def get_license_history(
    connection: Connection, node_name: str, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license history.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to get license history
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}/history'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error getting license audit.")
def get_audit(
    connection: Connection, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license audit.

    Args:
        connection (Connection): Strategy One REST API connection object
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = '/api/license/iServer/audit/result'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error getting compliance check results.")
def get_compliance_check(
    connection: Connection, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license compliance check results.

    Args:
        connection (Connection): Strategy One REST API connection object
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = '/api/license/iServer/compliance/result'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error getting license compliance check status.")
def get_compliance_check_status(
    connection: Connection, fields: str | None = None, error_msg=None
) -> Response:
    """Get the license compliance check status.

    Args:
        connection (Connection): Strategy One REST API connection object
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = '/api/license/iServer/compliance/status'
    params = {}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)


@ErrorHandler(err_msg="Error running license audit.")
def run_audit(connection: Connection, error_msg=None) -> Response:
    """Run the license audit.
    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to run the license audit
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 201.
    """
    endpoint = '/api/license/iServer/audit'
    return connection.post(endpoint=endpoint)


@ErrorHandler(err_msg="Error running license compliance check.")
def run_compliance_check(connection: Connection, error_msg=None) -> Response:
    """Run the license compliance check.

    Args:
        connection (Connection): Strategy One REST API connection object
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 201.
    """
    endpoint = '/api/license/iServer/compliance'
    return connection.post(endpoint=endpoint)


@ErrorHandler(err_msg="Error getting license entitlements.")
def get_license_entitlements(
    connection: Connection,
    node_name: str,
    license_key: str,
    fields: str | None = None,
    error_msg=None,
) -> Response:
    """Get the license entitlements for a specific license key.

    Args:
        connection (Connection): Strategy One REST API connection object
        node_name (str): Name of the node for which to get license entitlements
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        license_key (str): License key for which to get entitlements
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/iServer/nodes/{node_name}/entitlements'
    params = {}
    headers = {'licenseKey': license_key}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, headers=headers, params=params)


@ErrorHandler(err_msg="Error getting license privileges for user with ID:{id}.")
def get_privileges_for_user(
    connection: Connection,
    id: str,
    license_product: str,
    fields: str | None = None,
    error_msg=None,
) -> Response:
    """Get the license privileges for selected user.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (str): User ID for which to get license privileges
        license_product (str): License product for which to get privileges
        fields (str | None, optional): Comma-separated list of fields to return
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    endpoint = f'/api/license/privileges/{id}'
    params = {'licenseProduct': license_product}

    if fields:
        params['fields'] = fields

    return connection.get(endpoint=endpoint, params=params)
