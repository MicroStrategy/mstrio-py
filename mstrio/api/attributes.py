from typing import List, Optional

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_decorator, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error creating an attribute')
def create_attribute(connection: Connection, changeset_id: str, body: dict,
                     show_expression_as: Optional[List[str]] = None,
                     show_potential_tables: Optional[str] = None,
                     show_fields: Optional[str] = None, fields: Optional[str] = None):
    """Create a new attribute in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id: ID of a changeset
        body: Attribute creation data
        show_expession_as: Specifies the format in which the expressions are
           returned in response
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.
        show_potential_tables: Specifies whether to return the potential tables
            that the expressions can be applied to.
            Available values: 'true', 'false'
            If 'true', the 'potentialTables' field returns for each attribute
                expression, in the form of a list of tables.
            If 'false' or omitted, the 'potentialTables' field is omitted.
        show_fields: Specifies what additional information to return.
            Only 'acl' is supported.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 201
    """
    return connection.post(
        url=f'{connection.base_url}/api/model/attributes',
        headers={'X-MSTR-MS-Changeset': changeset_id}, params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': show_potential_tables,
            'showFields': show_fields,
            'fields': fields
        }, json=body)


@unpack_information
@ErrorHandler(err_msg='Error getting attribute with ID: {id}')
def get_attribute(connection: Connection, id: str, changeset_id: Optional[str] = None,
                  show_expression_as: Optional[List[str]] = None,
                  show_potential_tables: Optional[str] = None, show_fields: Optional[str] = None,
                  fields: Optional[str] = None):
    """Get definition of a single attribute by id

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of an attribute
        changeset_id: ID of a changeset
        show_expession_as: Specifies the format in which the expressions
           are returned in response
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.
        show_potential_tables: Specifies whether to return the potential tables
            that the expressions can be applied to.
            Available values: 'true', 'false'
            If 'true', the 'potentialTables' field returns for each
                attribute expression, in the form of a list of tables.
            If 'false' or omitted, the 'potentialTables' field is omitted.
        show_fields: Specifies what additional information to return.
            Only 'acl' is supported.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/attributes/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id}, params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': show_potential_tables,
            'showFields': show_fields,
            'fields': fields
        })


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error updating attribute with ID: {id}')
def update_attribute(connection: Connection, id: str, changeset_id: str, body: dict,
                     show_expression_as: Optional[List[str]] = None,
                     show_potential_tables: Optional[str] = None,
                     show_fields: Optional[str] = None, fields: Optional[str] = None,
                     remove_invalid_fields: Optional[str] = None):
    """Update a specific attribute in the changeset
    This endpoint replaces the attribute's top-level fields
    with the new definition provided in the request body.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of an attribute
        changeset_id: ID of a changeset
        body: Attribute update data
        show_expession_as: Specifies the format in which the expressions
           are returned in response.
           Available values: 'tokens', 'tree'
           If omitted, the expression is returned in 'text' format
           If 'tree', the expression is returned in 'text' and 'tree' formats.
           If 'tokens', the expression is returned in 'text' and 'tokens'
           formats.
        show_potential_tables: Specifies whether to return the potential tables
            that the expressions can be applied to.
            Available values: 'true', 'false'
            If 'true', the 'potentialTables' field returns for each
                attribute expression, in the form of a list of tables.
            If 'false' or omitted, the 'potentialTables' field is omitted.
        show_fields: Specifies what additional information to return.
            Only 'acl' is supported.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
        remove_invalid_fields: Specifies whether to check and remove the invalid
            fields caused by changes related to key form within the request.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.patch(
        url=f'{connection.base_url}/api/model/attributes/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id}, params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': show_potential_tables,
            'showFields': show_fields,
            'fields': fields,
            'removeInvalidFields': remove_invalid_fields
        }, json=body)
