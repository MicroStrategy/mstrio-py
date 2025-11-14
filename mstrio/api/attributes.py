from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@unpack_information
@ErrorHandler(err_msg="Error creating an attribute")
def create_attribute(
    connection: Connection,
    body: dict,
    show_expression_as: list[str] | None = None,
    show_potential_tables: str | None = None,
    show_fields: str | None = None,
    fields: str | None = None,
):
    """Create a new attribute in the changeset,
    based on the definition provided in request body.

    Args:
        connection: Strategy One REST API connection object
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
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint='/api/model/attributes',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showPotentialTables': show_potential_tables,
                'showFields': show_fields,
                'fields': fields,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(err_msg="Error getting attribute with ID: {id}")
def get_attribute(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_potential_tables: str | None = None,
    show_fields: str | None = None,
    fields: str | None = None,
):
    """Get definition of a single attribute by id

    Args:
        connection: Strategy One REST API connection object
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
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/model/attributes/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': show_potential_tables,
            'showFields': show_fields,
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error updating attribute with ID: {id}")
def update_attribute(
    connection: Connection,
    id: str,
    body: dict,
    show_expression_as: list[str] | None = None,
    show_potential_tables: str | None = None,
    show_fields: str | None = None,
    fields: str | None = None,
    remove_invalid_fields: str | None = None,
):
    """Update a specific attribute in the changeset
    This endpoint replaces the attribute's top-level fields
    with the new definition provided in the request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of an attribute
        body: Attribute update data
        show_expression_as: Specifies the format in which the expressions
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
    with changeset_manager(connection) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/attributes/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showPotentialTables': show_potential_tables,
                'showFields': show_fields,
                'fields': fields,
                'removeInvalidFields': remove_invalid_fields,
            },
            json=body,
        )


@ErrorHandler(err_msg="Error getting attribute with ID: {id}")
def get_attribute_elements(
    connection: Connection,
    id: str,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
):
    """Get definition of a single attribute by ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of an attribute.
        offset: Block to begin with. Default is None. If None, the API will use
            its default (1, the first block).
        limit: Number of blocks to include (0-based). Default is None. If None,
            the API will use its default (50). -1 means to include all blocks.
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """

    params = {}
    if offset is not None:
        params['offset'] = offset
    if limit is not None:
        params['limit'] = limit
    if fields is not None:
        params['fields'] = fields
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/attributes/{id}/elements',
        params=params,
    )
