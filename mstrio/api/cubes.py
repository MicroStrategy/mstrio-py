import requests


def cube(connection, cube_id, verbose=False):
    """
    Get the definition of a specific cube, including attributes and metrics. The cube can be either an Intelligent Cube
    or a Direct Data Access (DDA)/MDX cube. The in-memory cube definition provides information about all available
    objects without actually running any data query/report. The results can be used by other requests to help filter
    large datasets and retrieve values dynamically, helping with performance and scalability.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        verbose (bool): Verbosity of request response; defaults to False.

    Returns:
        Complete HTTP response object
    """
    response = requests.get(url=connection.base_url + '/cubes/' + cube_id,
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def cube_info(connection, cube_id, verbose=False):
    """
    Get information for specific cubes in a specific project. The cubes can be either Intelligent cubes or Direct
    Data Access (DDA)/MDX cubes. This request returns the cube name, ID, size, status, path, last modification date,
    and owner name and ID.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        verbose (bool): Verbosity of request response; defaults to False.

    Returns:
        Complete HTTP response object.
    """
    response = requests.get(url=connection.base_url + '/cubes/?id=' + cube_id,
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def cube_single_attribute_elements(connection, cube_id, attribute_id, offset=0, limit=25000, verbose=False):
    """
    Get elements of a specific attribute of a specific cube.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        attribute_id (str): Unique ID of the attribute in the cube.
        verbose (bool): Verbosity of request response; defaults to False.

    Returns:
        Complete HTTP response object.
    """
    response = requests.get(url=connection.base_url + '/cubes/' + cube_id + '/attributes/' + attribute_id + '/elements',
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            params={'offset': offset,
                                     'limit': limit},
                            verify=connection.ssl_verify)

    if verbose:
        print(response.url)
    return response


def cube_instance(connection, cube_id, body={}, offset=0, limit=1000, verbose=False):
    """
    Create a new instance of a specific cube. This in-memory instance can be used by other requests.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        offset (int, optional): Starting point within the collection of returned results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets which have a large number of rows.
            The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
            extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit
            setting (e.g. 10,000) may reduce the total time required to extract the entire dataset.
        verbose (bool, optional): Verbosity of request response; defaults to False.

    Returns:
        Complete HTTP response object.
    """
    response = requests.post(url=connection.base_url + '/cubes/' + cube_id + '/instances',
                             headers={'X-MSTR-AuthToken': connection.auth_token,
                                      'X-MSTR-ProjectID': connection.project_id},
                             json=body,
                             cookies=connection.cookies,
                             params={'offset': offset,
                                     'limit': limit},
                             verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def cube_instance_id(connection, cube_id, instance_id, offset=0, limit=1000, verbose=False):
    """
    Get the results of a previously created instance for a specific cube, using the in-memory instance created by cube_instance().

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        instance_id (str): Unique ID of the in-memory instance of a published cube.
        offset (int, optional): Starting point within the collection of returned results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets which have a large number of rows.
            The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
            extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit
            setting (e.g. 10,000) may reduce the total time required to extract the entire dataset.
        verbose (bool, optional): Verbosity of request response; defaults to False.

    Returns:
        Complete HTTP response object.

    """
    response = requests.get(url=connection.base_url + '/cubes/' + cube_id + '/instances/' + instance_id,
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            params={'offset': offset,
                                    'limit': limit},
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def publish(connection, cube_id, verbose=False):
    """
    Publish a specific cube in a specific project.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to publish.
        verbose (bool): Verbosity of request response; defaults to False.
    
    Returns:
        Complete HTTP response object.
    """

    response = requests.post(url=connection.base_url + '/cubes/' + cube_id,
                             headers={'X-MSTR-AuthToken': connection.auth_token,
                                      'X-MSTR-ProjectID': connection.project_id},
                             cookies=connection.cookies,
                             verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def status(connection, cube_id, verbose=False):
    """
    Get the status of a specific cube in a specific project. The status is returned in 
    HEADER X-MSTR-CubeStatus with a value from EnumDSSCubeStates, which is a bit vector.

    Args:
        connection: MicroStrategy REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information from.
        verbose (bool): Verbosity of request response; defaults to False.
    
    Returns:
        Complete HTTP response object.
    """

    response = requests.head(url=connection.base_url + '/cubes/' + cube_id,
                             headers={'X-MSTR-AuthToken': connection.auth_token,
                                      'X-MSTR-ProjectID': connection.project_id},
                             cookies=connection.cookies,
                             verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response
