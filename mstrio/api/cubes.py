from typing import TYPE_CHECKING

from mstrio.modeling.expression import ExpressionFormat
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.helper import get_enum_val
from mstrio.utils.version_helper import is_server_min_version

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.utils.sessions import FuturesSessionWithRenewal

CUBE_FIELDS = '-data.metricValues.extras,-data.metricValues.formatted'


@ErrorHandler(err_msg="Error getting cube {id} definition.")
def cube_definition(connection: 'Connection', id: str):
    """Get the definition of a specific cube, including attributes and metrics.
    The cube can be either an Intelligent Cube or a Direct Data Access
    (DDA)/MDX cube. The in-memory cube definition provides information about
    all available objects without actually running any data query/report. The
    results can be used by other requests to help filter large datasets and
    retrieve values dynamically, helping with performance and scalability.

    Args:
        connection: Strategy One REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    return connection.get(endpoint=f'/api/v2/cubes/{id}')


@ErrorHandler(err_msg="Error getting cube {id} metadata information.")
def cube_info(connection: 'Connection', id: str):
    """Get information for specific cubes in a specific project. The cubes can
    be either Intelligent cubes or Direct Data Access (DDA)/MDX cubes. This
    request returns the cube name, ID, size, status, path, last modification
    date, and owner name and ID.

    Args:
        connection: Strategy One REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    return connection.get(endpoint=f'/api/cubes/?id={id}')


@ErrorHandler(err_msg="Error getting cube {id} metadata information.")
def get_cube_status(connection: 'Connection', id: str):
    """Get the status of a specific cube in a specific project.

    Args:
        connection: Strategy One REST API connection object.
        id (str): Unique ID of the cube you wish to extract information
            from.

    Returns:
        Complete HTTP response object.
    """
    return connection.head(endpoint=f'/api/cubes/{id}')


@ErrorHandler(err_msg="Error creating a new cube instance with ID {cube_id}.")
def cube_instance(
    connection: 'Connection',
    cube_id: str,
    body: dict = None,
    offset: int = 0,
    limit: int = 5000,
):
    """Create a new instance of a specific cube. This in-memory instance can be
    used by other requests.

    Args:
        connection: Strategy One REST API connection object.
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
    body = body or {}
    params = {'offset': offset, 'limit': limit}
    if is_server_min_version(connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS

    return connection.post(
        endpoint=f'/api/v2/cubes/{cube_id}/instances', json=body, params=params
    )


@ErrorHandler(err_msg="Error getting cube {cube_id} contents.")
def cube_instance_id(
    connection: 'Connection',
    cube_id: str,
    instance_id: str,
    offset: int = 0,
    limit: int = 5000,
):
    """Get the results of a previously created instance for a specific cube,
    using the in-memory instance created by cube_instance().

    Args:
        connection: Strategy One REST API connection object.
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
    if is_server_min_version(connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS

    return connection.get(
        endpoint=f'/api/v2/cubes/{cube_id}/instances/{instance_id}', params=params
    )


def cube_instance_id_coroutine(
    future_session: 'FuturesSessionWithRenewal',
    cube_id: str,
    instance_id: str,
    offset: int = 0,
    limit: int = 5000,
):
    """Get the future of a previously created instance for a specific cube
    asynchronously, using the in-memory instance created by cube_instance().

    Returns:
        Complete Future object.
    """
    params = {'offset': offset, 'limit': limit}
    if is_server_min_version(future_session.connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS

    endpoint = f'/api/v2/cubes/{cube_id}/instances/{instance_id}'
    return future_session.get(endpoint=endpoint, params=params)


@ErrorHandler(
    err_msg="Error getting attribute {attribute_id} elements within cube {cube_id}"
)
def cube_single_attribute_elements(
    connection: 'Connection',
    cube_id: str,
    attribute_id: str,
    offset: int = 0,
    limit: int = 200000,
):
    """Get elements of a specific attribute of a specific cube.

    Args:
        connection: Strategy One REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        attribute_id (str): Unique ID of the attribute in the cube.

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        endpoint=f'/api/cubes/{cube_id}/attributes/{attribute_id}/elements',
        params={'offset': offset, 'limit': limit},
    )


def cube_single_attribute_elements_coroutine(
    future_session: 'FuturesSessionWithRenewal',
    cube_id: str,
    attribute_id: str,
    offset: int = 0,
    limit: int = 200000,
):
    """Get elements of a specific attribute of a specific cube.

    Returns:
        Complete Future object.
    """
    endpoint = f'/api/cubes/{cube_id}/attributes/{attribute_id}/elements'
    return future_session.get(
        endpoint=endpoint, params={'offset': offset, 'limit': limit}
    )


@ErrorHandler(err_msg="Error sending request to publish cube with ID {cube_id}")
def publish(connection: 'Connection', cube_id: str):
    """Publish a specific cube in a specific project.

    Args:
        connection: Strategy One REST API connection object.
        cube_id (str): Unique ID of the cube you wish to publish.

    Returns:
        Complete HTTP response object.
    """

    return connection.post(endpoint=f'/api/v2/cubes/{cube_id}')


@ErrorHandler(err_msg="Error getting cube {cube_id} status.")
def status(connection: 'Connection', cube_id: str, throw_error: bool = True):
    """Get the status of a specific cube in a specific project. The status is
    returned in HEADER X-MSTR-CubeStatus with a value from EnumDSSCubeStates,
    which is a bit vector.

    Args:
        connection: Strategy One REST API connection object.
        cube_id (str): Unique ID of the cube you wish to extract information
            from.
        throw_error (bool, optional): Flag indicates if the error should be
            thrown.

    Returns:
        Complete HTTP response object.
    """

    return connection.head(endpoint=f'/api/cubes/{cube_id}')


@ErrorHandler(err_msg="Error creating cube {name} definition.")
def create(
    connection: 'Connection',
    name: str,
    folder_id: str,
    overwrite: bool = None,
    description: str = None,
    definition: dict = None,
):
    """
    Create an intelligent cube.
    POST /api/v2/cubes
    """
    connection._validate_project_selected()

    body = {
        'name': name,
        'description': description,
        'folderId': folder_id,
        'overwrite': overwrite,
        'definition': definition,
    }
    params = {'X-MSTR-ProjectID': connection.project_id}

    return connection.post(endpoint='/api/v2/cubes', json=body, params=params)


@ErrorHandler(err_msg="Error updating cube {cube_id} definition.")
def update(connection: 'Connection', cube_id: str, definition: dict = None):
    """
    Update an intelligent cube.
    PUT /api/v2/cubes/{cube_id}
    """
    connection._validate_project_selected()

    body = {'definition': definition}
    params = {'X-MSTR-ProjectID': connection.project_id}

    return connection.put(endpoint=f'/api/v2/cubes/{cube_id}', json=body, params=params)


@ErrorHandler(err_msg="Error getting sql view of cube with ID {cube_id}")
def get_sql_view(connection: 'Connection', cube_id: str, project_id: str = None):
    """
    Get the sql view of cube.
    GET /api/v2/cubes/{cube_id}/sqlView
    """
    if not project_id:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/v2/cubes/{cube_id}/sqlView',
        params={'X-MSTR-projectID': project_id},
    )


@ErrorHandler(err_msg="Error creating cube {name}.")
def create_cube(
    connection: 'Connection',
    body: dict,
    project_id: str | None = None,
    cube_template_id: str | None = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = True,
):
    """Create a new cube.

    Args:
        connection (Connection): Strategy One REST API connection object.
        body (dict): JSON-formatted data used to create cube.
        project_id (str, optional): Project ID.
        cube_template_id (str, optional): If specified, new created cube will
            inherit 'template' of given by ID cube.
        show_expression_as (ExpressionFormat, str, optional): Specify how
            expressions should be presented, default 'ExpressionFormat.TREE'.
            Available values:
            - None.
                (expression is returned in 'text' format)
            - `ExpressionFormat.TREE` or `tree`.
                (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`.
                (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool, optional): Specify whether 'filter'
            is returned in 'tokens' format, along with `text` and `tree`
            formats, default False.
            - If omitted or False, only `text` and `tree` formats are returned.
            - If True, all `text`, 'tree' and `tokens` formats are returned.
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties. If omitted or false, nothing
            will be returned for the advanced properties, default True.

    Returns:
        HTTP response object. Expected status: 200.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    params = {
        'cubeTemplateId': cube_template_id,
        'showExpressionAs': get_enum_val(show_expression_as, ExpressionFormat),
        'showFilterTokens': str(show_filter_tokens).lower(),
        'showAdvancedProperties': str(show_advanced_properties).lower(),
    }

    return connection.post(
        endpoint='/api/model/cubes',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
        params=params,
    )


@ErrorHandler(err_msg="Error getting cube with ID {id}")
def get_cube(
    connection: 'Connection',
    id: str,
    project_id: str | None = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = True,
):
    """Get cube by specific ID.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Cube ID.
        project_id (str, optional): Project ID.
        show_expression_as (ExpressionFormat, str, optional): Specify how
            expressions should be presented, default 'ExpressionFormat.TREE'.
            Available values:
            - None.
                (expression is returned in 'text' format)
            - `ExpressionFormat.TREE` or `tree`.
                (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`.
                (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool, optional): Specify whether 'filter'
            is returned in 'tokens' format, along with `text` and `tree`
            formats, default False.
            - If omitted or False, only `text` and `tree` formats are returned.
            - If True, all `text`, 'tree' and `tokens` formats are returned.
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties. If omitted or false, nothing
            will be returned for the advanced properties, default True.

    Returns:
        HTTP response object. Expected status: 200.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    params = {
        'showExpressionAs': get_enum_val(show_expression_as, ExpressionFormat),
        'showFilterTokens': str(show_filter_tokens).lower(),
        'showAdvancedProperties': str(show_advanced_properties).lower(),
    }

    return connection.get(
        endpoint=f'/api/model/cubes/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params=params,
    )


@ErrorHandler(err_msg="Error updating cube with ID {id}")
def update_cube(
    connection: 'Connection',
    id: str,
    body: dict,
    project_id: str | None = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = False,
):
    """Update cube specified by ID.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Cube ID.
        body (dict): JSON-formatted data used to update cube.
        project_id (str, optional): Project ID.
        show_expression_as (ExpressionFormat, str, optional): Specify how
            expressions should be presented, default 'ExpressionFormat.TREE'.
            Available values:
            - None.
                (expression is returned in 'text' format)
            - `ExpressionFormat.TREE` or `tree`.
                (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`.
                (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool, optional): Specify whether 'filter'
            is returned in 'tokens' format, along with `text` and `tree`
            formats, default False.
            - If omitted or False, only `text` and `tree` formats are returned.
            - If True, all `text`, 'tree' and `tokens` formats are returned.
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties. If omitted or false, nothing
            will be returned for the advanced properties, default False.

    Returns:
        HTTP response object. Expected status: 200.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    params = {
        'showExpressionAs': get_enum_val(show_expression_as, ExpressionFormat),
        'showFilterTokens': str(show_filter_tokens).lower(),
        'showAdvancedProperties': str(show_advanced_properties).lower(),
    }

    return connection.put(
        endpoint=f'/api/model/cubes/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
        params=params,
    )


@ErrorHandler(err_msg="Error getting metadata of VLDB settings for cube with ID {id}")
def get_applicable_vldb_settings(
    connection: 'Connection', id: str, project_id: str | None = None
):
    """Get metadata of advanced VLDB settings for cube.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Cube ID.
        project_id (str, optional): Project ID.

    Returns:
        HTTP response object. Expected status: 200.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/model/cubes/{id}/applicableVldbProperties',
        headers={'X-MSTR-ProjectID': project_id},
    )
