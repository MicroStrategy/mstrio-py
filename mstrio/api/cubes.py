import requests


def cube(connection, cube_id, verbose=False):
    """
    Get the definition of a specific cube, including attributes and metrics. The cube can be either an Intelligent Cube
    or a Direct Data Access (DDA)/MDX cube. The in-memory cube definition provides information about all available
    objects without actually running any data query/report. The results can be used by other requests to help filter
    large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param cube_id: Unique ID of the cube you wish to extract information from.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = requests.get(url=connection.base_url + '/cubes/' + cube_id,
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def cube_instance(connection, cube_id, offset=0, limit=1000, verbose=False):
    """
    Create a new instance of a specific cube. This in-memory instance can be used by other requests.

    :param connection: MicroStrategy REST API connection object
    :param cube_id: Unique ID of the cube you wish to extract information from.
    :param offset: Optional. Starting point within the collection of returned results. Default is 0.
    :param limit: Optional. Used to control data extract behavior on datasets which have a large number of rows.
    The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
    extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit setting
    (e.g. 10,000) may reduce the total time required to extract the entire dataset.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """
    response = requests.post(url=connection.base_url + '/cubes/' + cube_id + '/instances',
                             headers={'X-MSTR-AuthToken': connection.auth_token,
                                      'X-MSTR-ProjectID': connection.project_id},
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

    :param connection: MicroStrategy REST API connection object
    :param cube_id: Unique ID of the cube you wish to extract information from.
    :param instance_id: Unique ID of the in-memory instance of a published cube.
    :param offset: Optional. Starting point within the collection of returned results. Default is 0.
    :param limit: Optional. Used to control data extract behavior on datasets which have a large number of rows.
    The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
    extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit setting
    (e.g. 10,000) may reduce the total time required to extract the entire dataset.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
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
