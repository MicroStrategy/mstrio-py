from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error creating a new changeset.")
def create_changeset(
    connection: 'Connection',
    project_id: str = None,
    schema_edit: bool = False,
    error_msg: str = None,
):
    """Create a new changeset for modelling manipulations."""
    return connection.post(
        endpoint='/api/model/changesets',
        headers={'X-MSTR-ProjectID': project_id},
        params={'schemaEdit': str(schema_edit).lower()},
    )


@ErrorHandler(err_msg="Error committing changeset {id} changes to the metadata.")
def commit_changeset_changes(
    connection: 'Connection', id: str, error_msg: str = None, throw_error=True
):
    """Commit the changeset changes to metadata."""
    return connection.post(
        endpoint=f'/api/model/changesets/{id}/commit',
        headers={'X-MSTR-MSChanget': id},
        params={'changesetId': id},
    )


@ErrorHandler(err_msg="Error deleting the changeset with ID {id}")
def delete_changeset(connection: 'Connection', id: str, error_msg: str = None):
    """Delete the changeset."""
    return connection.delete(
        endpoint=f'/api/model/changesets/{id}',
        headers={'X-MSTR-MSChanget': id},
        params={'changesetId': id},
    )
