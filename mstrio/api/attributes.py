from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.dtos.create_attribute_dto import CreateAttributeDto
from mstrio.utils.dtos.update_attribute_dto import UpdateAttributeDto
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
    changeset_id: str | None = None
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
        changeset_id: Specifies an existing changeset ID. If omitted, a new
            changeset is created.

    Return:
        HTTP response object. Expected status: 201
    """
    if not changeset_id:
        with changeset_manager(connection) as changeset_id:
            return _create_attribute(connection, body, changeset_id, show_expression_as, show_potential_tables, show_fields, fields)

    return _create_attribute(connection, body, changeset_id, show_expression_as, show_potential_tables, show_fields, fields)

   
@unpack_information
@ErrorHandler(err_msg="Error creating attributes")
def create_attributes(
    connection: Connection,
    create_attribute_dtos: list[CreateAttributeDto],
    changeset_id: str | None = None
):
    """Create multiple attributes in the changeset,
    based on the definitions provided in request bodies.

    Args:
        connection: MicroStrategy REST API connection object
        create_attribute_dtos: List of attribute creation data
        changeset_id: Specifies an existing changeset ID. If omitted, a new
            changeset is created.

    Return:
        HTTP response object. Expected status: 201
    """
    if not changeset_id:
        with changeset_manager(connection) as changeset_id:
            responses = [_create_attribute(connection, create_attribute_dto.body, changeset_id,
                                           create_attribute_dto.show_expression_as, create_attribute_dto.show_potential_tables,
                                           create_attribute_dto.show_fields, create_attribute_dto.fields)
                         for create_attribute_dto in create_attribute_dtos]
            return responses
        
    responses = [_create_attribute(connection, create_attribute_dto.body, changeset_id,
                                   create_attribute_dto.show_expression_as, create_attribute_dto.show_potential_tables,
                                   create_attribute_dto.show_fields, create_attribute_dto.fields)
                 for create_attribute_dto in create_attribute_dtos]
    return responses


def _create_attribute(
    connection: Connection,
    body: dict,
    changeset_id: str,
    show_expression_as: list[str] | None = None,
    show_potential_tables: str | None = None,
    show_fields: str | None = None,
    fields: str | None = None,
):
    """Helper function to create a single attribute."""
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
    fields: str | None = None,
):
    """Get definition of a single attribute by ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of an attribute
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/attributes/{id}/elements',
        params={
            'fields': fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error updating attributes")
def update_attributes(
    connection: Connection,
    update_attribute_dtos: list[UpdateAttributeDto],
    changeset_id: str | None = None
):
    """Update multiple attributes at once.

    Args:
        connection: MicroStrategy connection object
        update_attribute_dtos: List of update attribute DTOs containing update data
        changeset_id: ID of the changeset to apply updates in. If not provided,
                   a new changeset will be created
    Returns:
        List of HTTP response objects with updated attribute data
    """
    if not changeset_id:
        with changeset_manager(connection) as changeset_id:
            responses = [_update_attribute(connection, dto.id, dto.body, changeset_id,
                                       dto.show_expression_as, dto.show_potential_tables,
                                       dto.show_fields, dto.fields, dto.remove_invalid_fields)
                        for dto in update_attribute_dtos]
            return responses

    responses = [_update_attribute(connection, dto.id, dto.body, changeset_id,
                                dto.show_expression_as, dto.show_potential_tables,
                                dto.show_fields, dto.fields, dto.remove_invalid_fields)
                for dto in update_attribute_dtos]
    return responses

def _update_attribute(
    connection: Connection,
    id: str,
    body: dict,
    changeset_id: str,
    show_expression_as: list[str] | None = None,
    show_potential_tables: str | None = None,
    show_fields: str | None = None,
    fields: str | None = None,
    remove_invalid_fields: str | None = None
):
    """Helper function to update a single attribute."""
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