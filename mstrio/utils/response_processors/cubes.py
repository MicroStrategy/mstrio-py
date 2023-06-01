from typing import Optional

from mstrio.api import cubes as cubes_api
from mstrio.connection import Connection
from mstrio.modeling.expression import ExpressionFormat
from mstrio.utils.helper import rename_dict_keys

REST_ATTRIBUTES_MAP = {
    'objectId': 'id',
    'timeBased': 'timeBasedSettings',
}


def create(
    connection: Connection,
    body: dict,
    project_id: Optional[str] = None,
    cube_template_id: Optional[str] = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = True,
) -> dict:
    """Create cube from provided body.

    Args:
        connection (Connection): MicroStrategy REST API connection object.
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
        Dict representing created cube object.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    data = cubes_api.create_cube(
        connection,
        body,
        project_id=project_id,
        cube_template_id=cube_template_id,
        show_expression_as=show_expression_as,
        show_filter_tokens=show_filter_tokens,
        show_advanced_properties=show_advanced_properties,
    ).json()
    data = {**data, **data['information']}
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)


def get(
    connection: Connection,
    id: str,
    project_id: Optional[str] = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = True,
) -> dict:
    """Get cube by specific ID.

    Args:
        connection (Connection): MicroStrategy REST API connection object.
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
        Dict representing fetched cube object.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    data = cubes_api.get_cube(
        connection,
        id,
        project_id=project_id,
        show_expression_as=show_expression_as,
        show_filter_tokens=show_filter_tokens,
        show_advanced_properties=show_advanced_properties,
    ).json()
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)


def update(
    connection: Connection,
    id: str,
    body: dict,
    project_id: Optional[str] = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = False,
) -> dict:
    """Update cube specified by ID and with provided body.

    Args:
        connection (Connection): MicroStrategy REST API connection object.
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
        Dict representing updated cube object.

    Raises:
        AttributeError: If project ID is not provided and Connection object
            doesn't have project selected.
    """

    body['timeBased'] = body.get('timeBasedSettings', {})

    data = cubes_api.update_cube(
        connection=connection,
        id=id,
        body=body,
        project_id=project_id,
        show_expression_as=show_expression_as,
        show_filter_tokens=show_filter_tokens,
        show_advanced_properties=show_advanced_properties,
    ).json()

    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)


def get_info(connection: Connection, id: str) -> dict:
    """Get information for specific cube. This request updates
    size, status, path, owner ID and server mode of the cube.

    Args:
        connection: MicroStrategy REST API connection object.
        id (str): ID of the cube.

    Returns:
        Dict representing cube information.
    """

    data = cubes_api.cube_info(connection, id).json()['cubesInfos'][0]
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)
