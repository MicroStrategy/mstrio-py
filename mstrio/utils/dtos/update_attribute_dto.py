from dataclasses import dataclass


@dataclass
class UpdateAttributeDto:
    """DTO for updating an attribute

    Args:
        id: ID of the attribute to update
        body: Dictionary containing updated attribute data
        show_expression_as: Specifies the format in which the expressions are
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
        remove_invalid_fields: Specifies whether to remove invalid fields before updating.
    """

    id: str
    body: dict
    show_expression_as: list[str] | None = None
    show_potential_tables: str | None = None
    show_fields: str | None = None
    fields: str | None = None
    remove_invalid_fields: str | None = None
