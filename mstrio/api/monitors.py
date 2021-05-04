from mstrio.utils.helper import response_handler


def get_projects(connection, offset=0, limit=-1, error_msg=None):
    """Get list of all projects from metadata.
    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.get(
        url=connection.base_url + '/api/monitors/projects',
        headers={'X-MSTR-ProjectID': None},
        params={
            'offset': offset,
            'limit': limit
        },
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting list of all projects from metadata."
        response_handler(response, error_msg)
    return response


def get_projects_async(future_session, connection, offset=0, limit=-1, error_msg=None):
    """Get list of all projects from metadata asynchronously.
    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    url = connection.base_url + '/api/monitors/projects'
    headers = {'X-MSTR-ProjectID': None}
    params = {'offset': offset, 'limit': limit}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


def get_node_info(connection, id=None, node_name=None, error_msg=None):
    """Get information about nodes in the connected Intelligence Server
    cluster.

    This includes basic information, runtime state and information of projects
    on each node. This operation requires the "Monitor cluster" privilege.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str, optional): Project ID
        node_name (str, optional): Node Name
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    response = connection.session.get(
        url=connection.base_url + '/api/monitors/iServer/nodes',
        headers={'X-MSTR-ProjectID': None},
        params={
            'projects.id': id,
            'name': node_name
        },
    )
    if not response.ok:
        if error_msg is None:
            error_msg = ("Error getting  information about nodes in the connected Intelligence "
                         "Server cluster.")
        response_handler(response, error_msg)
    return response


def update_node_properties(connection, node_name, project_id, body, error_msg=None, whitelist=[]):
    """Update properties such as project status for a specific project for
    respective cluster node. You obtain cluster node name and project id from
    GET /monitors/iServer/nodes.

    {
        "operationList": [
            {
                "op": "replace",
                "path": "/status",
                "value": "loaded"
            }
        ]
    }

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        project_id (string): Project ID.
        body (JSON): Body 'op' can have "value" set to "add", "replace",
            "remove"; 'path' can have pattern: /([/A-Za-z0-9~])*-* example:
            /status; 'values' for '/status'  we can choose [loaded, unloaded,
            request_idle, exec_idle, wh_exec_idle, partial_idle, full_idle]
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.patch(
        url=connection.base_url + '/api/monitors/iServer/nodes/' + node_name + '/projects/'
        + project_id,
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )
    if not response.ok:
        if error_msg is None:
            error_msg = ("Error updating properties for a specific project for respective "
                         "cluster node.")
        response_handler(response, error_msg, whitelist=whitelist)
    return response


def add_node(connection, node_name, error_msg=None, whitelist=[]):
    """Add a node to the connected Intelligence Server cluster. The node must
    meet I-Server clustering requirements. If the node is part of a multi-node
    cluster, all the nodes in that cluster will be added. If the node is
    already in the cluster, the operation succeeds without making any change.
    This operation requires the "Monitor cluster" and "Administer cluster"
    privilege.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling
        whitelist(list): list of tuples of I-Server Error and HTTP errors codes
            respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.put(
        url=connection.base_url + '/api/monitors/iServer/nodes/' + node_name,
        headers={'X-MSTR-ProjectID': None},
    )
    if not response.ok:
        if error_msg is None:
            error_msg = (f"Error adding node '{node_name}' to the connected Intelligence Server "
                         "cluster")
        response_handler(response, error_msg, whitelist=whitelist)
    return response


def remove_node(connection, node_name, error_msg=None, whitelist=[]):
    """Remove a node from the connected Intelligence Server cluster. After a
    successful removal, some existing authorization tokens may become
    invalidated and in this case re-login is needed. You cannot remove a node
    if it's the configured default node of Library Server, or there is only one
    node in the cluster. This operation requires the "Monitor cluster" and
    "Administer cluster" privilege.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling
        whitelist(list): list of tuples of I-Server Error and HTTP errors codes
            respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """

    response = connection.session.delete(
        url=connection.base_url + '/api/monitors/iServer/nodes/' + node_name,
        headers={'X-MSTR-ProjectID': None},
    )
    if not response.ok:
        if error_msg is None:
            error_msg = (f"Error removing node '{node_name}' from the connected Intelligence "
                         "Server cluster.")
        response_handler(response, error_msg, whitelist=whitelist)
    return response


def get_user_connections(connection, node_name, offset=0, limit=100, error_msg=None):
    """Get user connections information on specific intelligence server node.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(
        url=connection.base_url + '/api/monitors/userConnections',
        headers={'X-MSTR-ProjectID': None},
        params={
            'clusterNode': node_name,
            'offset': offset,
            'limit': limit
        },
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting user connections for '{}' cluster node.".format(node_name)
        response_handler(response, error_msg)
    return response


def get_user_connections_async(future_session, connection, node_name, offset=0, limit=100):
    """Get user connections information on specific intelligence server node.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    params = {'clusterNode': node_name, 'offset': offset, 'limit': limit}
    url = connection.base_url + '/api/monitors/userConnections'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.get(url=url, headers=headers, params=params)
    return future


def delete_user_connection(connection, id, error_msg=None, bulk=False):
    """Disconnect a user connection on specific intelligence server node.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling
        bulk(bool,optional): Whether to ignore errors when using request for
            bulk disconnect
    """
    response = connection.session.delete(
        url=connection.base_url + '/api/monitors/userConnections/' + id,
        headers={'X-MSTR-ProjectID': None},
    )
    if not response.ok and bulk:
        if error_msg is None:
            error_msg = "Error deleting user connections '{}'.".format(id)
        # whitelist error related to disconnecting yourself or other unallowed
        response_handler(response, error_msg, whitelist=[('ERR001', 500)])
    return response


def delete_user_connection_async(future_session, connection, id, error_msg=None):
    """Disconnect a user connection on specific intelligence server node.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str, optional): Project ID
    """

    url = connection.base_url + '/api/monitors/userConnections/' + id
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.delete(url=url, headers=headers)
    return future


def delete_user_connections(connection, ids):
    """Delete user connections on specific intelligence server node.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        ids (list of strings): list with ids of user connections to be deleted.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    body = {"userConnectionIds": ids}
    response = connection.session.post(
        url=connection.base_url + '/api/monitors/deleteUserConnections',
        json=body,
    )
    return response
