import json
from typing import TYPE_CHECKING
from unittest.mock import Mock
from urllib.parse import quote, urlencode

from packaging import version

from mstrio.helpers import MstrException, PartialSuccess, Success
from mstrio.utils.error_handlers import ErrorHandler, bulk_operation_response_handler
from mstrio.utils.helper import (
    delete_none_values,
    filter_list_of_dicts,
    get_response_json,
    response_handler,
)
from mstrio.utils.sessions import FuturesSessionWithRenewal

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection

ISERVER_VERSION_11_3_2 = '11.3.0200'


@ErrorHandler(err_msg='Error getting list of all projects from metadata.')
def get_projects(
    connection: 'Connection',
    offset: int = 0,
    limit: int = -1,
    error_msg: str | None = None,
):
    """Get list of all projects from metadata.
    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.get(
        endpoint='/api/monitors/projects',
        headers={'X-MSTR-ProjectID': None},
        params={'offset': offset, 'limit': limit},
    )


def get_projects_async(
    future_session: 'FuturesSessionWithRenewal', offset: int = 0, limit: int = -1
):
    """Get list of all projects from metadata asynchronously.
    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            Strategy One REST Server asynchronously
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    endpoint = '/api/monitors/projects'
    headers = {'X-MSTR-ProjectID': None}
    params = {'offset': offset, 'limit': limit}
    future = future_session.get(endpoint=endpoint, headers=headers, params=params)
    return future


@ErrorHandler(
    err_msg='Error getting information about nodes in the connected Intelligence '
    'Server cluster.'
)
def get_node_info(
    connection: 'Connection',
    id: str | None = None,
    node_name: str | None = None,
    error_msg: str | None = None,
):
    """Get information about nodes in the connected Intelligence Server
    cluster.

    This includes basic information, runtime state and information of projects
    on each node. This operation requires the "Monitor cluster" privilege.

    Args:
        connection(object): Strategy One connection object returned by

        id (str, optional): Project ID
        node_name (str, optional): Node Name
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    return connection.get(
        endpoint='/api/monitors/iServer/nodes',
        headers={'X-MSTR-ProjectID': None},
        params={'projects.id': id, 'name': node_name},
    )


@ErrorHandler(
    err_msg='Error updating properties for a project {project_id} for cluster node {'
    'node_name}.'
)
def update_node_properties(
    connection: 'Connection',
    node_name: str,
    project_id: str,
    body: dict,
    error_msg: str | None = None,
    whitelist: list[tuple] | None = None,
):
    """Update properties such as project status for a specific project for
    respective cluster node. You obtain cluster node name and project id from
    GET /monitors/iServer/nodes.

    {
        'operationList': [
            {
                'op': 'replace',
                'path': '/status',
                'value': 'loaded'
            }
        ]
    }

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        project_id (string): Project ID.
        body (JSON): Body 'op' can have "value" set to "add", "replace",
            "remove"; 'path' can have pattern: /([/A-Za-z0-9~])*-* example:
            /status; 'values' for '/status'  we can choose [loaded, unloaded,
            request_idle, exec_idle, wh_exec_idle, partial_idle, full_idle]
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.patch(
        endpoint=f'/api/monitors/iServer/nodes/{node_name}/projects/{project_id}',
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )


@ErrorHandler(
    err_msg="Error getting status for project: {project_id} on cluster node "
    "{node_name}."
)
def get_project_status_on_node(
    connection: 'Connection',
    node_name: str,
    project_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Get status of a project on a specific cluster node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        project_id (string): Project ID.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/monitors/iServer/nodes/{node_name}/projects/{project_id}/status'
    )


@ErrorHandler(
    err_msg='Error adding node {node_name} to connected Intelligence Server cluster.'
)
def add_node(
    connection: 'Connection',
    node_name: str,
    error_msg: str | None = None,
    whitelist: list[tuple] | None = None,
):
    """Add a node to the connected Intelligence Server cluster. The node must
    meet I-Server clustering requirements. If the node is part of a multi-node
    cluster, all the nodes in that cluster will be added. If the node is
    already in the cluster, the operation succeeds without making any change.
    This operation requires the "Monitor cluster" and "Administer cluster"
    privilege.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling
        whitelist(list): list of tuples of I-Server Error and HTTP errors codes
            respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.put(
        endpoint=f'/api/monitors/iServer/nodes/{node_name}',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(
    err_msg='Error removing node {node_name} from the connected Intelligence Server '
    'cluster.'
)
def remove_node(
    connection: 'Connection',
    node_name: str,
    error_msg: str | None = None,
    whitelist: list[tuple] | None = None,
):
    """Remove a node from the connected Intelligence Server cluster. After a
    successful removal, some existing authorization tokens may become
    invalidated and in this case re-login is needed. You cannot remove a node
    if it's the configured default node of Library Server, or there is only one
    node in the cluster. This operation requires the "Monitor cluster" and
    "Administer cluster" privilege.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling
        whitelist(list): list of tuples of I-Server Error and HTTP errors codes
            respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    return connection.delete(
        endpoint=f'/api/monitors/iServer/nodes/{node_name}',
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg='Error getting user connections for {node_name} cluster node.')
def get_user_connections(
    connection: 'Connection',
    node_name: str,
    offset: int = 0,
    limit: int = 100,
    error_msg: str | None = None,
):
    """Get user connections information on specific intelligence server node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).
        node_name (string): Node Name.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint='/api/monitors/userConnections',
        headers={'X-MSTR-ProjectID': None},
        params={'clusterNode': node_name, 'offset': offset, 'limit': limit},
    )


def get_user_connections_async(
    future_session: 'FuturesSessionWithRenewal',
    node_name: str,
    offset: int = 0,
    limit: int = 100,
):
    """Get user connections information on specific intelligence server node.

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            Strategy One REST Server asynchronously
        node_name (string): Node Name.
        offset(int): Starting point within the collection of returned search
            results. Used to control paging behavior.
        limit(int): Maximum number of items returned for a single search
            request. Used to control paging behavior. Use -1 (default ) for no
            limit (subject to governing settings).

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    params = {'clusterNode': node_name, 'offset': offset, 'limit': limit}
    endpoint = '/api/monitors/userConnections'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.get(endpoint=endpoint, headers=headers, params=params)
    return future


def delete_user_connection(
    connection: 'Connection', id: str, error_msg: str | None = None, bulk: bool = False
):
    """Disconnect a user connection on specific intelligence server node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id (str, optional): Project ID
        error_msg (string, optional): Custom Error Message for Error Handling
        bulk(bool,optional): Whether to ignore errors when using request for
            bulk disconnect
    """
    response = connection.delete(
        endpoint=f'/api/monitors/userConnections/{id}',
        headers={'X-MSTR-ProjectID': None},
    )
    if not response.ok and bulk:
        if error_msg is None:
            error_msg = f"Error deleting user connections {id}."
        # whitelist error related to disconnecting yourself or other unallowed
        response_handler(response, error_msg, whitelist=[('ERR001', 500)])
    return response


def delete_user_connection_async(future_session: 'FuturesSessionWithRenewal', id: str):
    """Disconnect a user connection on specific intelligence server node.

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            Strategy One REST Server asynchronously
        id (str, optional): Project ID
    """

    endpoint = f'/api/monitors/userConnections/{id}'
    headers = {'X-MSTR-ProjectID': None}
    future = future_session.delete(endpoint=endpoint, headers=headers)
    return future


def delete_user_connections(connection: 'Connection', ids: list[str]):
    """Delete user connections on specific intelligence server node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        ids (list of strings): list with ids of user connections to be deleted.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    body = {'userConnectionIds': ids}
    response = connection.post(
        endpoint='/api/monitors/deleteUserConnections', json=body
    )
    return response


@ErrorHandler(err_msg='Error getting cube cache {id} info.')
def get_cube_cache_info(connection: 'Connection', id: str):
    """Get a single cube cache info.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`.
        id (string): cube cache id

    Returns:
        Complete HTTP response object.
    """
    return connection.get(endpoint=f'/api/monitors/caches/cubes/{id}')


@ErrorHandler(err_msg='Error deleting cube cache with ID {id}')
def delete_cube_cache(connection: 'Connection', id: str, throw_error: bool = True):
    """Delete a cube cache.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`.
        id (string): cube cache id
        throw_error (bool, optional): Flag indicates if the error should be
            thrown.

    Returns:
        Complete HTTP response object.
    """
    return connection.delete(endpoint=f'/api/monitors/caches/cubes/{id}')


@ErrorHandler(err_msg='Error altering cube cache {id} status.')
def alter_cube_cache_status(
    connection: 'Connection',
    id: str,
    active: bool | None = None,
    loaded: bool | None = None,
    throw_error: bool = True,
):
    """Alter a cube cache status. In one request it is possible to set either
    'active' or 'loaded', never both.

    Args:
        connection: Strategy One connection object returned by
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
    body = delete_none_values(body, recursion=True)

    return connection.patch(
        endpoint=f'/api/monitors/caches/cubes/{id}',
        headers={'Prefer': 'respond-async'},
        json=body,
    )


@ErrorHandler(err_msg='Error getting list of cube caches for node {node}.')
def get_cube_caches(
    connection: 'Connection',
    node: str,
    offset: int = 0,
    limit: int = 1000,
    project_ids: str | None = None,
    loaded: bool = False,
    sort_by: str | None = None,
    error_msg: str | None = None,
):
    """Get the list of cube caches on a specific cluster node.

    Args:
        connection: Strategy One connection object returned by
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
            cube cache. If True then the filter will be applied. Otherwise, all
            cubes will be returned.
        sort_by (string, optional): Specify sorting criteria. For example
            '+name,-size' means sorting name ascending and size descending.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    loaded = 'loaded' if loaded else None
    return connection.get(
        endpoint='/api/monitors/caches/cubes',
        params={
            'clusterNode': node,
            'offset': offset,
            'limit': limit,
            'projectIds': project_ids,
            'state.loadedState': loaded,
            'sortBy': sort_by,
        },
    )


def get_cube_caches_async(
    future_session: 'FuturesSessionWithRenewal',
    node: str,
    offset: int = 0,
    limit: int = 1000,
    project_ids: str | None = None,
    loaded: bool = False,
    sort_by: str | None = None,
):
    """Get the list of cube caches on a specific cluster node asynchronously.

    Args:
        future_session(object): Future Session object to call Strategy One REST
            Server asynchronously
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
        Future with HTTP response returned by the Strategy One REST server as
        a result.
    """
    endpoint = '/api/monitors/caches/cubes'
    loaded = 'loaded' if loaded else None
    params = {
        'clusterNode': node,
        'offset': offset,
        'limit': limit,
        'projectIds': project_ids,
        'state.loadedState': loaded,
        'sortBy': sort_by,
    }
    future = future_session.get(endpoint=endpoint, params=params)
    return future


@ErrorHandler(err_msg='Error getting cube cache manipulation {manipulation_id} status.')
def get_cube_cache_manipulation_status(
    connection: 'Connection', manipulation_id: str, throw_error: bool = True
):
    """Get the manipulation status of cube cache.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`.
        manipulation_id (string): cube cache manipulation ID
        throw_error (bool, optional): In case of True (default) the error will
            be thrown when it occurs.

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        endpoint=f'/api/monitors/caches/cubes/manipulations/{manipulation_id}/status'
    )


@ErrorHandler(
    err_msg='Error getting database connections for {nodes_names} cluster node.'
)
def get_database_connections(
    connection: 'Connection', nodes_names: str, error_msg: str | None = None
):
    """Get database connections information on specific intelligence
        server node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        nodes_names (string): Node names split by ",".
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint='/api/monitors/dbConnectionInstances',
        params={'clusterNodes': nodes_names},
    )


@ErrorHandler(err_msg='Error deleting database connections {connection_id}.')
def delete_database_connection(
    connection: 'Connection', connection_id: str, error_msg: str | None = None
):
    """Disconnect a database connection on specific intelligence server node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        connection_id (str, optional): Database Connection Id
        error_msg (string, optional): Custom Error Message for Error Handling
    """
    return connection.delete(
        endpoint=f'/api/monitors/dbConnectionInstances/{connection_id}'
    )


def delete_database_connection_async(
    future_session: 'FuturesSessionWithRenewal', connection_id: str
):
    """Disconnect a database connection on specific intelligence server node.

    Args:
        future_session: Future Session object to call Strategy One REST
            Server asynchronously
        connection_id (str, optional): Database Connection Id
    """
    endpoint = f'/api/monitors/dbConnectionInstances/{connection_id}'
    return future_session.delete(endpoint=endpoint)


def get_job(
    connection: 'Connection',
    id: str,
    node_name: str | None = None,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Get job information.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name(str, optional): Node name, if not passed list jobs
            on all nodes
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    response = Mock()  # create empty mock object to mimic REST API response

    if not node_name:
        # fetch jobs on all nodes
        nodes_response = get_node_info(connection).json()
        nodes = nodes_response['nodes']
        node_names = [node['name'] for node in nodes]

    if isinstance(node_name, str):
        node_names = [node_names]

    with FuturesSessionWithRenewal(connection=connection, max_workers=8) as session:
        futures = [
            get_jobs_async(future_session=session, node_name=node, fields=fields)
            for node in node_names
        ]
        jobs = []
        for f in futures:
            response = f.result()
            res_json = get_response_json(response, msg=error_msg, throw_error=False)
            if res_json and 'jobs' in res_json:
                jobs.extend(res_json['jobs'])

    job = filter_list_of_dicts(jobs, id=id)
    if not job:
        response.status_code = 400
        response.reason = f"Error getting job '{id}'"
        response.raise_for_status()
    elif len(job) > 1:
        response.status_code = 400
        response.reason = f"More than one job with id '{id}' was found."
        response.raise_for_status()
    else:
        job = job[0]
        job = json.dumps(job).encode('utf-8')
        response._content = job
        response.status_code = 200
        return response


@ErrorHandler(err_msg="Error getting job {id}.")
def get_job_v2(
    connection: 'Connection',
    id: str,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Get job information.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(
        endpoint=f'/api/v2/monitors/jobs/{id}',
        params={'fields': ','.join(fields) if fields else None},
    )


@ErrorHandler(err_msg="Error getting jobs list.")
def get_jobs(
    connection: 'Connection',
    node_name: str,
    project_id: str | None = None,
    status: str | None = None,
    job_type: str | None = None,
    user_full_name: str | None = None,
    object_id: str | None = None,
    sort_by: str | None = None,
    fields: list[str] | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get list of a jobs.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name(str): Node name,
        project_id(str, optional): Project id ,
        status(str, optional): Job status to filter by,
        job_type(str, optional): Job type to filter by,
        user_full_name(str, optional): User full name to filter by,
        object_id(str, optional): Object id to filter by,
        sort_by(SortBy, optional): Specifies sorting criteria to
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {
        'nodeName': node_name,  # this needs to be first to work
        'projectId': project_id,
        'status': status,
        'jobType': job_type,
        'userFullName': user_full_name,
        'objectId': object_id,
        'sortBy': sort_by,
        'fields': ','.join(fields) if fields else None,
    }

    params_delete_none = delete_none_values(params, recursion=True)
    params_encoded = urlencode(params_delete_none, True, quote_via=quote)
    return connection.get(endpoint='/api/monitors/jobs', params=params_encoded)


def get_jobs_async(
    future_session: 'FuturesSessionWithRenewal',
    node_name: str,
    project_id: str | None = None,
    status: str | None = None,
    job_type: str | None = None,
    user_full_name: str | None = None,
    object_id: str | None = None,
    sort_by: str | None = None,
    fields: list[str] | None = None,
) -> 'Response':
    """Get list of a jobs asynchronously.

    Args:
        future_session(object): Future Session object to call Strategy One REST
            Server asynchronously
        node_name(str): Node name,
        project_id(str, optional): Project id,
        status(str, optional): Job status to filter by,
        job_type(str, optional): Job type to filter by,
        user_full_name(str, optional): User full name to filter by,
        object_id(str, optional): Object id to filter by,
        sort_by(SortBy, optional): Specifies sorting criteria to
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        FuturesSessionWithRenewal object
    """
    params = {
        'nodeName': node_name,  # this needs to be first to work
        'projectId': project_id,
        'status': status,
        'jobType': job_type,
        'userFullName': user_full_name,
        'objectId': object_id,
        'sortBy': sort_by,
        'fields': ','.join(fields) if fields else None,
    }

    params_delete_none = delete_none_values(params, recursion=True)
    params_encoded = urlencode(params_delete_none, True, quote_via=quote)
    return future_session.get(endpoint='/api/monitors/jobs', params=params_encoded)


@ErrorHandler(err_msg="Error getting jobs list")
def get_jobs_v2(
    connection: 'Connection',
    node_name: str,
    user: list[str] | str | None = None,
    description: str | None = None,
    type: list[str] | str | None = None,
    status: list[str] | str | None = None,
    object_id: list[str] | None = None,
    object_type: list[str] | str | None = None,
    project_id: list[str] | str | None = None,
    project_name: list[str] | str | None = None,
    pu_name: list[str] | str | None = None,
    subscription_type: list[str] | str | None = None,
    subscription_recipient: list[str] | str | None = None,
    memory_usage: str | None = None,
    elapsed_time: str | None = None,
    sort_by: str | None = None,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Get list of a jobs.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        node_name(str): Node name,
        user(str, optional): Field to filter on job owner's full name (exact
            match),
        description(str, optional): Field to filter on job description (partial
            match),
        type(str, optional): Field to filter on job type (exact match),
        status(str, optional): Job status to filter by,
        object_id(str, optional): Field to filter on object ID of the job
            (exact match)
        object_type(str, optional): Field to filter on object type (exact match)
        project_id(str, optional): Field to filter on project id (exact
            match),
        project_name(str, optional): Field to filter on project name (exact
            match),
        pu_name(str, optional): Field to filter on processing unit name (exact
            match),
        subscription_type(str, optional): Field to filter on subscription type
            (exact match),
        subscription_recipient(str, optional): Field to filter on subscription
            recipient's full name (exact match),
        memory_usage(str, optional): Field to filter on the job elapsed time,
            for example 'gte:100' means filtering jobs with memoryUsage greater
            than or equal to 100 MB. Valid operators are:
            gte - greater than or equal
            lte - less than or equal
        elapsed_time(str, optional): Field to filter on the job elapsed time,
            for example 'gte:100' means filtering jobs with elapsedTime greater
            than or equal to 100 seconds. Valid operators are:
            gte - greater than or equal
            lte - less than or equal
        sort_by(SortBy, optional): Specify sorting criteria, for example
            '+status' means sorting status is ascending order or '-userFullName'
            means sorting userFullName in descending order. Currently, the
            server supports sorting only by single field.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {
        'nodeName': node_name,  # this needs to be first to work
        'user': user,
        'description': description,
        'type': type,
        'status': status,
        'objectId': object_id,
        'objectType': object_type,
        'projectId': project_id,
        'projectName': project_name,
        'puName': pu_name,
        'subscriptionType': subscription_type,
        'subscriptionRecipient': subscription_recipient,
        'memoryUsage': memory_usage,
        'elapsedTime': elapsed_time,
        'sortBy': sort_by,
        'fields': ','.join(fields) if fields else None,
    }

    params_delete_none = delete_none_values(params, recursion=True)
    params_encoded = urlencode(params_delete_none, True, quote_via=quote)
    return connection.get(endpoint='/api/v2/monitors/jobs', params=params_encoded)


def get_jobs_v2_async(
    future_session: 'FuturesSessionWithRenewal',
    node_name: str,
    user: list[str] | str | None = None,
    description: str | None = None,
    type: list[str] | str | None = None,
    status: list[str] | str | None = None,
    object_id: list[str] | None = None,
    object_type: list[str] | str | None = None,
    project_id: list[str] | str | None = None,
    project_name: list[str] | str | None = None,
    pu_name: list[str] | str | None = None,
    subscription_type: list[str] | str | None = None,
    subscription_recipient: list[str] | str | None = None,
    memory_usage: str | None = None,
    elapsed_time: str | None = None,
    sort_by: str | None = None,
    fields: list[str] | None = None,
) -> 'Response':
    """Get list of a jobs asynchronously.

    Args:
        future_session(object): Future Session object to call Strategy One REST
            Server asynchronously
        node_name(str): Node name,
        user(str, optional): Field to filter on job owner's full name (exact
            match),
        description(str, optional): Field to filter on job description (partial
            match),
        type(str, optional): Field to filter on job type (exact match),
        status(str, optional): Job status to filter by,
        object_id(str, optional): Field to filter on object ID of the job
            (exact match)
        object_type(str, optional): Field to filter on object type (exact match)
        project_id(str, optional): Field to filter on project id (exact
            match),
        project_name(str, optional): Field to filter on project name (exact
            match),
        pu_name(str, optional): Field to filter on processing unit name (exact
            match),
        subscription_type(str, optional): Field to filter on subscription type
            (exact match),
        subscription_recipient(str, optional): Field to filter on subscription
            recipient's full name (exact match),
        memory_usage(str, optional): Field to filter on the job elapsed time,
            for example 'gte:100' means filtering jobs with memoryUsage greater
            than or equal to 100 MB. Valid operators are:
            gte - greater than or equal
            lte - less than or equal
        elapsed_time(str, optional): Field to filter on the job elapsed time,
            for example 'gte:100' means filtering jobs with elapsedTime greater
            than or equal to 100 seconds. Valid operators are:
            gte - greater than or equal
            lte - less than or equal
        sort_by(SortBy, optional): Specify sorting criteria, for example
            '+status' means sorting status is ascending order or '-userFullName'
            means sorting userFullName in descending order. Currently, the
            server supports sorting only by single field.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        FuturesSessionWithRenewal object
    """
    params = {
        'nodeName': node_name,  # this needs to be first to work
        'user': user,
        'description': description,
        'type': type,
        'status': status,
        'objectId': object_id,
        'objectType': object_type,
        'projectId': project_id,
        'projectName': project_name,
        'puName': pu_name,
        'subscriptionType': subscription_type,
        'subscriptionRecipient': subscription_recipient,
        'memoryUsage': memory_usage,
        'elapsedTime': elapsed_time,
        'sortBy': sort_by,
        'fields': ','.join(fields) if fields else None,
    }

    params_delete_none = delete_none_values(params, recursion=True)
    params_encoded = urlencode(params_delete_none, True, quote_via=quote)
    return future_session.get(endpoint='/api/v2/monitors/jobs', params=params_encoded)


@ErrorHandler(err_msg="Error killing job {id}")
def cancel_job(
    connection: 'Connection',
    id: str,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Cancel a job specified by `id`. Use cancel_job_v1 if I-Server version
    is 11.3.2 or cancel_job_v2 otherwise.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id(str): ID of the job
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    if connection.iserver_version and version.parse(
        connection.iserver_version
    ) == version.parse(ISERVER_VERSION_11_3_2):
        return cancel_job_v1(connection, id, fields, error_msg)
    else:
        return cancel_job_v2(connection, id, fields, error_msg)


@ErrorHandler(err_msg="Error killing job {id}")
def cancel_job_v1(
    connection: 'Connection',
    id: str,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Cancel a job specified by `id`.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id(str): ID of the job
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {'fields': ','.join(fields) if fields else None}

    return connection.delete(endpoint=f'/api/monitors/jobs/{id}', params=params)


@ErrorHandler(err_msg="Error killing job {id}")
def cancel_job_v2(
    connection: 'Connection',
    id: str,
    fields: list[str] | None = None,
    error_msg: str | None = None,
):
    """Cancel a job specified by `id`.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id(str): ID of the job
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {'fields': ','.join(fields) if fields else None}

    return connection.delete(endpoint=f'/api/v2/monitors/jobs/{id}', params=params)


def cancel_jobs(
    connection: 'Connection', ids: list[str], fields: list[str] | None = None
) -> Success | PartialSuccess | MstrException:
    """Cancel jobs specified by `ids`. Use cancel_jobs_v1 if I-Server version
    is 11.3.2 or cancel_jobs_v2 otherwise.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        ids(List[str]): IDs of the jobs
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        Success: object if all jobs were killed
        PartialSuccess: if not all jobs were killed
        MstrException: otherwise
    """
    if connection.iserver_version and version.parse(
        connection.iserver_version
    ) == version.parse(ISERVER_VERSION_11_3_2):
        response = cancel_jobs_v1(connection, ids, fields)
    else:
        response = cancel_jobs_v2(connection, ids, fields)

    return bulk_operation_response_handler(response, 'jobCancellationStatus')


def cancel_jobs_v1(
    connection: 'Connection', ids: list[str], fields: list[str] | None = None
):
    """Cancel jobs specified by `ids`.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        ids(List[str]): IDs of the jobs
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {'fields': ','.join(fields) if fields else None}

    if ids:
        body = {'jobIds': ids}
        return connection.post(
            endpoint='/api/monitors/cancelJobs', params=params, json=body
        )
    else:
        raise ValueError("No ids have been passed.")


def cancel_jobs_v2(
    connection: 'Connection', ids: list[str], fields: list[str] | None = None
):
    """Cancel jobs specified by `ids`.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        ids(List[str]): IDs of the jobs
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    params = {'fields': ','.join(fields) if fields else None}

    if ids:
        body = {'jobIds': ids}
        return connection.post(
            endpoint='/api/v2/monitors/cancelJobs', params=params, json=body
        )
    else:
        raise ValueError("No ids have been passed.")


@ErrorHandler(err_msg="Error getting caches")
def get_contents_caches(
    connection: 'Connection',
    project_id: str,
    node: str,
    offset: int = 0,
    limit: int = 1000,
    status: str | None = None,
    content_type: str | None = None,
    content_format: str | None = None,
    size: str | None = None,
    owner: str | None = None,
    expiration: str | None = None,
    last_updated: str | None = None,
    hit_count: str | None = None,
    sort_by: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get cache objects

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`,
        project_id(str): Field to filter on project id (exact
            match),
        node(str): Node name,
        offset(int): Starting point within the collection of returned results.
            Used to control paging behavior. Default value = 0,
        limit(int): Maximum number of items returned for a single request.
            Used to control paging behavior. Maximum and default value: 1000,
        status(str, optional): Status of the content cache,
        content_type(str, optional): type of content,
        content_format(str, optional): Format of the content cache, intended for
            dashboard and document cache,
        size(str, optional): Size of the content cache (in KB),
        owner(str, optional): Owner of the content cache. Exact match on the
            owner's full name,
        expiration(str, optional): Expiration time of the cache,
        last_updated(str, optional): Last update of the cache,
        hit_count(str, optional): Hit count of the cache,
        sort_by(str, optional): Specify sorting criteria,
        fields(str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.
        error_msg (string, optional): Custom Error Message for Error Handling
    Returns:
        HTTP response object. Expected status 200.
    """
    params = {
        'projectId': project_id,
        'clusterNode': node,
        'offset': offset,
        'limit': limit,
        'status': status,
        'type': content_type,
        'format': content_format,
        'size': size,
        'owner': owner,
        'expiration': expiration,
        'lastUpdated': last_updated,
        'hitCount': hit_count,
        'sortBy': sort_by,
        'fields': fields,
    }
    params_delete_none = delete_none_values(params, recursion=True)
    params_encoded = urlencode(params_delete_none, True, quote_via=quote)
    return connection.get(
        endpoint='/api/monitors/caches/contents', params=params_encoded
    )


@ErrorHandler(err_msg='Error updating caches')
def update_contents_caches(
    connection: 'Connection', node: str, body: dict, fields: str | None = None
) -> 'Response':
    """Alter multiple content cache statuses or remove content caches entirely
        in multiple projects at specific node.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`,
        node(str): Node name,
        body(dict): List of contents
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        HTTP response object. Expected status 200.
    """
    return connection.patch(
        endpoint='/api/v2/monitors/caches/contents',
        params={'clusterNode': node, 'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg='Error deleting caches')
def delete_caches(connection: 'Connection', project_id: str, cache_type: str):
    """Delete element or object caches for a specific project.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`,
        project_id(str): Project id,
        cache_type(str): Cache type
            Available values:
            - 'element'
            - 'object'

    Returns:
        HTTP response object. Expected status 204.
    """

    return connection.delete(
        endpoint=f'/api/monitors/projects/{project_id}/caches/{cache_type}',
    )
