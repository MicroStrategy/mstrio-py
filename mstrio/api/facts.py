from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@unpack_information
@ErrorHandler(err_msg="Error reading fact with ID: {id}.")
def read_fact(
    connection: 'Connection',
    id: str,
    project_id: str = None,
    changeset_id: str = None,
    show_expression_as: str | None = None,
    show_potential_tables: bool = False,
    show_fields: str | None = None,
):
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    spt = (
        str(show_potential_tables).lower()
        if show_potential_tables is not None
        else None
    )
    return connection.get(
        endpoint=f'/api/model/facts/{id}',
        headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-MS-Changeset': changeset_id,
        },
        params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': spt,
            'showFields': show_fields,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating a fact.")
def create_fact(
    connection: 'Connection',
    body: dict,
    show_expression_as: str | None = None,
    show_potential_tables: bool = False,
):
    spt = (
        str(show_potential_tables).lower()
        if show_potential_tables is not None
        else None
    )
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint='/api/model/facts',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showPotentialTables': spt,
            },
            json=body,
        )


@unpack_information
@ErrorHandler(err_msg="Error updating fact with ID: {id}.")
def update_fact(
    connection: 'Connection',
    id: str,
    body: dict,
    show_expression_as: str | None = None,
    show_potential_tables: bool = False,
):
    spt = (
        str(show_potential_tables).lower()
        if show_potential_tables is not None
        else None
    )
    with changeset_manager(connection) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/facts/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showPotentialTables': spt,
            },
            json=body,
        )
