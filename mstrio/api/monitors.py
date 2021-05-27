from mstrio.utils.helper import response_handler, delete_none_values
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from requests_futures.sessions import FuturesSession


def get_projects(connection: "Connection", offset: int = 0, limit: int = -1,
                 error_msg: str = None):
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


def get_projects_async(future_session: "FuturesSession", connection: "Connection", offset: int = 0,
                       limit: int = -1, error_msg: str = None):
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


def get_node_info(connection: "Connection", id: str = None, node_name: str = None,
                  error_msg: str = None):
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


def update_node_properties(connection: "Connection", node_name: str, project_id: str, body: dict,
                           error_msg: str = None, whitelist: List[tuple] = []):
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


def add_node(connection: "Connection", node_name: str, error_msg: str = None,
             whitelist: List[tuple] = []):
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


def remove_node(connection: "Connection", node_name: str, error_msg: str = None,
                whitelist: List[tuple] = []):
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


def get_user_connections(connection: "Connection", node_name: str, offset: int = 0,
                         limit: int = 100, error_msg: str = None):
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


def get_user_connections_async(future_session: "FuturesSession", connection: "Connection",
                               node_name: str, offset: int = 0, limit: int = 100):
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


def delete_user_connection(connection: "Connection", id: str, error_msg: str = None,
                           bulk: bool = False):
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


def delete_user_connection_async(future_session: "FuturesSession", connection: "Connection",
                                 id: str, error_msg: str = None):
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


def delete_user_connections(connection: "Connection", ids: List[str]):
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


def get_cube_cache_info(connection: "Connection", id: str):
    """Get an single cube cache info.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): cube cache id

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(url=f"{connection.base_url}/api/monitors/caches/cubes/{id}")
    if not response.ok:
        response_handler(response, "Error getting cube cache info.")
    return response


def delete_cube_cache(connection: "Connection", id: str, throw_error: bool = True):
    """Delete an cube cache.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): cube cache id
        throw_error (bool, optional): Flag indicates if the error should be
            thrown.

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.delete(
        url=f"{connection.base_url}/api/monitors/caches/cubes/{id}")
    if not response.ok:
        response_handler(response, "Error deleting cube cache.", throw_error)
    return response


def alter_cube_cache_status(connection: "Connection", id: str, active: bool = None,
                            loaded: bool = None, throw_error: bool = True):
    """Alter an cube cache status. In one request it is possible to set either
    'active' or 'loaded', never both.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): cube cache id,
        active (bool, optional): make cube cache active (True) or inactive
            (False)
        loaded (bool, optional): load (True) or unload (False) the cube cache
        throw_error (bool, optional): Flag indicates if the error should be
            thrown.

    Returns:
        Complete HTTP response object.
    """
    if loaded is not None:
        loaded = 'loaded' if loaded else 'unloaded'
    body = {'state': {'active': active, 'loadedState': loaded}}
    body = delete_none_values(body)

    response = connection.session.patch(
        url=f"{connection.base_url}/api/monitors/caches/cubes/{id}", json=body,
        headers={'Prefer': 'respond-async'})
    if not response.ok:
        response_handler(response, "Error altering cube cache status.", throw_error)
    return response


def get_cube_caches(connection: "Connection", node: str, offset: int = 0, limit: int = 1000,
                    project_ids: str = None, loaded: bool = False, sort_by: str = None,
                    error_msg: str = None):
    """Get the list of cube caches on a specific cluster node.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        node (string): Intelligence Server cluster node name
        offset (integer, optional): Starting point within the collection of
            returned results. Used to control paging behavior. Default value: 0.
        limit (integer, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default value: 1000.
        project_ids (string, optional): project id collection which is used for
            filtering data, for example:
            'B19DEDCC11D4E0EFC000EB9495D0F6E2,A232EDCC11D4E0EFC000EB9495D0F6E2'
        loaded (bool, optional): filter field which is used to filtering loaded
            cube cache. If True then the filter will be applied. Otherwise all
            cubes will be returned.
        sort_by (string, optional): Specify sorting criteria. For example
            '+name,-size' means sorting name ascending and size descending.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    loaded = 'loaded' if loaded else None
    response = connection.session.get(
        url=f"{connection.base_url}/api/monitors/caches/cubes", params={
            'clusterNode': node,
            'offset': offset,
            'limit': limit,
            'projectIds': project_ids,
            'state.loadedState': loaded,
            'sortBy': sort_by
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting list of cube caches."
        response_handler(response, error_msg)
    return response


def get_cube_caches_async(future_session: "FuturesSession", connection: "Connection", node: str,
                          offset: int = 0, limit: int = 1000, project_ids: str = None,
                          loaded: bool = False, sort_by: str = None):
    """Get the list of cube caches on a specific cluster node asynchronously.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        node (string): Intelligence Server cluster node name
        offset (integer, optional): Starting point within the collection of
            returned results. Used to control paging behavior. Default value: 0.
        limit (integer, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default value: 1000.
        project_ids (string, optional): project id collection which is used for
            filtering data, for example:
            'B19DEDCC11D4E0EFC000EB9495D0F6E2,A232EDCC11D4E0EFC000EB9495D0F6E2'
        loaded (bool, optional): filter field which is used to filtering loaded
            cube cache. If True then the filter will be applied. Otherwise all
            cubes will be returned.
        sort_by (string, optional): Specify sorting criteria. For example
            '+name,-size' means sorting name ascending and size descending.
    Returns:
        Future with HTTP response returned by the MicroStrategy REST server as
        a result.
    """
    url = connection.base_url + '/api/monitors/caches/cubes'
    params = {
        'clusterNode': node,
        'offset': offset,
        'limit': limit,
        'projectIds': project_ids,
        'state.loadedState': loaded,
        'sortBy': sort_by
    }
    future = future_session.get(url=url, params=params)
    return future


def get_cube_cache_manipulation_status(connection: "Connection", manipulation_id: str,
                                       throw_error: bool = True):
    """Get the manipulation status of cube cache.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        manipulation_id (string): cube cache manipulation ID
        throw_error (bool, optional): In case of True (default) the error will
            be thrown when it occurs.

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(
        url=(f"{connection.base_url}/api/monitors/caches/cubes/manipulations"
             f"/{manipulation_id}/status"))
    if not response.ok:
        response_handler(response, "Error getting cube cache manipulation status.", throw_error)
    return response
