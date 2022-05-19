from typing import Optional

from mstrio.utils.api_helpers import changeset_decorator, unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.connection import Connection


@unpack_information
@ErrorHandler(err_msg='Error reading fact with ID: {id}.')
def read_fact(connection: "Connection", id: str, project_id: str = None, changeset_id: str = None,
              show_expression_as: Optional[str] = None, show_potential_tables: bool = False,
              show_fields: Optional[str] = None):
    project_id = project_id if project_id is not None else connection.project_id
    spt = str(show_potential_tables).lower() if show_potential_tables is not None else None
    return connection.get(
        url=f"{connection.base_url}/api/model/facts/{id}",
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
@changeset_decorator
@ErrorHandler(err_msg='Error creating a fact.')
def create_fact(connection: "Connection", changeset_id: str, body: dict,
                show_expression_as: Optional[str] = None, show_potential_tables: bool = False):
    spt = str(show_potential_tables).lower() if show_potential_tables is not None else None
    return connection.post(
        url=f"{connection.base_url}/api/model/facts",
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': spt,
        },
        json=body,
    )


@unpack_information
@changeset_decorator
@ErrorHandler(err_msg='Error updating fact with ID: {id}.')
def update_fact(connection: "Connection", changeset_id: str, id: str, body: dict,
                show_expression_as: Optional[str] = None, show_potential_tables: bool = False):
    spt = str(show_potential_tables).lower() if show_potential_tables is not None else None
    return connection.put(
        url=f"{connection.base_url}/api/model/facts/{id}",
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showPotentialTables': spt,
        },
        json=body,
    )
