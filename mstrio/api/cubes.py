from packaging import version
from mstrio.utils.helper import response_handler

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mstrio.connection import Connection
    from requests_futures.sessions import FuturesSession

CUBE_FIELDS = '-data.metricValues.extras,-data.metricValues.formatted'


def cube_definition(connection: "Connection", id: str):
    """Get the definition of a specific cube, including attributes and metrics.
    The cube can be either an Intelligent Cube or a Direct Data Access
    (DDA)/MDX cube. The in-memory cube definition provides information about
    all available objects without actually running any data query/report. The
    results can be used by other requests to help filter large datasets and
    retrieve values dynamically, helping with performance and scalability.

    Args:
        connection: MicroStrategy REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    connection._validate_application_selected()
    response = connection.session.get(url=connection.base_url + '/api/v2/cubes/' + id)

    if not response.ok:
        response_handler(response, "Error getting cube definition. Check Cube ID.")
    return response


def cube_info(connection: "Connection", id: str):
    """Get information for specific cubes in a specific project. The cubes can
    be either Intelligent cubes or Direct Data Access (DDA)/MDX cubes. This
    request returns the cube name, ID, size, status, path, last modification
    date, and owner name and ID.

    Args:
        connection: MicroStrategy REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.get(url=connection.base_url + '/api/cubes/?id=' + id)

    if not response.ok:
        response_handler(response, "Error getting cube metadata information. Check Cube ID.")
    return response


def get_cube_status(connection: "Connection", id: str):
    """Get the status of a specific cube in a specific project.

    Args:
        connection: MicroStrategy REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    response = connection.session.head(url=connection.base_url + '/api/cubes/' + id)

    if not response.ok:
        response_handler(response, "Error getting cube metadata information. Check Cube ID.")
    return response


def cube_instance(connection: "Connection", cube_id: str, body: dict = {}, offset: int = 0,
                  limit: int = 5000):
    """Create a new instance of a specific cube. This in-memory instance can be
    used by other requests.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        offset (int, optional): Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As an
            example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.

    Returns:
        Complete HTTP response object.
    """
    params = {'offset': offset, 'limit': limit}
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    response = connection.session.post(
        url=connection.base_url + '/api/v2/cubes/' + cube_id + '/instances',
        json=body,
        params=params,
    )
    if not response.ok:
        response_handler(response, "Error creating a new cube instance.")
    return response


def cube_instance_id(connection: "Connection", cube_id: str, instance_id: str, offset: int = 0,
                     limit: int = 5000):
    """Get the results of a previously created instance for a specific cube,
    using the in-memory instance created by cube_instance().

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        instance_id (str): Unique ID of the in-memory instance of a published
            cube.
        offset (int, optional): Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As an
            example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.

    Returns:
        Complete HTTP response object.
    """
    params = {'offset': offset, 'limit': limit}
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    response = connection.session.get(
        url=connection.base_url + '/api/v2/cubes/' + cube_id + '/instances/' + instance_id,
        params=params,
    )
    if not response.ok:
        response_handler(response, "Error getting cube contents.")
    return response


def cube_instance_id_coroutine(future_session: "FuturesSession", connection: "Connection",
                               cube_id: str, instance_id: str, offset: int = 0, limit: int = 5000):
    """Get the future of a previously created instance for a specific cube
    asynchronously, using the in-memory instance created by cube_instance().

    Returns:
        Complete Future object.
    """
    params = {'offset': offset, 'limit': limit}
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    url = connection.base_url + '/api/v2/cubes/' + cube_id + '/instances/' + instance_id
    future = future_session.get(url, params=params)
    return future


def cube_single_attribute_elements(connection: "Connection", cube_id: str, attribute_id: str,
                                   offset: int = 0, limit: int = 200000):
    """Get elements of a specific attribute of a specific cube.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        attribute_id (str): Unique ID of the attribute in the cube.

    Returns:
        Complete HTTP response object.
    """

    response = connection.session.get(
        url=connection.base_url + '/api/cubes/' + cube_id + '/attributes/' + attribute_id
        + '/elements',
        params={
            'offset': offset,
            'limit': limit
        },
    )
    if not response.ok:
        response_handler(response, "Error getting attribute " + attribute_id + " elements")
    return response


def cube_single_attribute_elements_coroutine(future_session: "FuturesSession",
                                             connection: "Connection", cube_id: str,
                                             attribute_id: str, offset: int = 0,
                                             limit: int = 200000):
    """Get elements of a specific attribute of a specific cube.

    Returns:
        Complete Future object.
    """
    url = (connection.base_url + '/api/cubes/' + cube_id + '/attributes/' + attribute_id
           + '/elements')
    future = future_session.get(url, params={'offset': offset, 'limit': limit})
    return future


def publish(connection: "Connection", cube_id: str):
    """Publish a specific cube in a specific project.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to publish.

    Returns:
        Complete HTTP response object.
    """

    response = connection.session.post(url=connection.base_url + '/api/cubes/' + cube_id)
    if not response.ok:
        response_handler(response, "Error sending request to publish cube.")
    return response


def status(connection: "Connection", cube_id: str, throw_error: bool = True):
    """Get the status of a specific cube in a specific project. The status is
    returned in HEADER X-MSTR-CubeStatus with a value from EnumDSSCubeStates,
    which is a bit vector.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        throw_error (bool, optional): Flag indicates if the error should be
            thrown.

    Returns:
        Complete HTTP response object.
    """

    response = connection.session.head(url=connection.base_url + '/api/cubes/' + cube_id)
    if not response.ok:
        response_handler(response, "Error getting cube status.", throw_error)
    return response


def create(connection: "Connection", name: str, folder_id: str, overwrite: bool = None,
           description: str = None, definition: dict = None):
    """
    Create an intelligent cube.
    POST /api/v2/cubes
    """
    connection._validate_application_selected()

    body = {
        'name': name,
        'description': description,
        'folderId': folder_id,
        'overwrite': overwrite,
        'definition': definition
    }
    params = {'X-MSTR-ProjectID': connection.application_id}

    response = connection.session.post(url=connection.base_url + '/api/v2/cubes', json=body,
                                       params=params)
    if not response.ok:
        response_handler(response, "Error creating cube definition.")
    return response


def update(connection: "Connection", cube_id: str, definition: dict = None):
    """
    Update an intelligent cube.
    PUT /api/v2/cubes/{cube_id}
    """
    connection._validate_application_selected()

    body = {'definition': definition}
    params = {'X-MSTR-ProjectID': connection.application_id}

    response = connection.session.put(url=f"{connection.base_url}/api/v2/cubes/{cube_id}",
                                      json=body, params=params)
    if not response.ok:
        response_handler(response, "Error updating cube definition.")
    return response


def get_sql_view(connection: "Connection", cube_id: str, project_id: str = None):
    """
    Get the sql view of cube.
    GET /api/v2/cubes/{cube_id}/sqlView
    """
    if not project_id:
        connection._validate_application_selected()
        project_id = connection.application_id

    response = connection.session.get(url=f"{connection.base_url}/api/v2/cubes/{cube_id}/sqlView",
                                      params={'X-MSTR-projectID': project_id})
    if not response.ok:
        response_handler(response, "Error getting sql view of cube.")
    return response
