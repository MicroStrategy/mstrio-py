from typing import Optional

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@unpack_information
@ErrorHandler(err_msg='Error getting transformation with ID: {id}')
def get_transformation(connection: Connection, id: str, changeset_id: Optional[str] = None,
                       show_expression_as: Optional[list[str]] = None):
    """Get definition of a single transformation by id

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of an transformation
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
           are returned in response
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(url=f'{connection.base_url}/api/model/transformations/{id}',
                          headers={'X-MSTR-MS-Changeset': changeset_id},
                          params={'showExpressionAs': show_expression_as})


@unpack_information
@ErrorHandler(err_msg='Error creating a transformation')
def create_transformation(connection: Connection, body: dict,
                          show_expression_as: Optional[list[str]] = None):

    """Create a new transformation in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        body: Transformation creation data
        show_expression_as: Specifies the format in which the expressions are
           returned in response
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.

    Return:
        HTTP response object. Expected status: 200
    """
    with changeset_manager(connection) as changeset_id:
        return connection.post(url=f'{connection.base_url}/api/model/transformations',
                               headers={'X-MSTR-MS-Changeset': changeset_id},
                               params={'showExpressionAs': show_expression_as}, json=body)


@unpack_information
@ErrorHandler(err_msg='Error updating transformation with ID: {id}')
def update_transformation(connection: Connection, id: str, body: dict,
                          show_expression_as: Optional[list[str]] = None):
    """Update a specific transformation in the changeset,
    based on the definition provided in the request body.
    It returns the transformation's updated definition in the changeset.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a Transformation
        body: Transformation update data
        show_expression_as: Specifies the format in which the expressions
           are returned in response.
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.

    Return:
        HTTP response object. Expected status: 200
    """
    with changeset_manager(connection) as changeset_id:
        return connection.patch(url=f'{connection.base_url}/api/model/transformations/{id}',
                                headers={'X-MSTR-MS-Changeset': changeset_id},
                                params={'showExpressionAs': show_expression_as}, json=body)
