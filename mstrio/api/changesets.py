from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error creating a new changeset.')
def create_changeset(connection: "Connection", project_id: str = None, schema_edit: bool = False,
                     error_msg: str = None):
    """Create a new changeset for modelling manipulations."""
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(url=f"{connection.base_url}/api/model/changesets",
                           headers={'X-MSTR-ProjectID': project_id},
                           params={'schemaEdit': str(schema_edit).lower()})


@ErrorHandler(err_msg='Error committing changeset {id} changes to the metadata.')
def commit_changeset_changes(connection: "Connection", id: str, error_msg: str = None,
                             throw_error=True):
    """Commit the changeset changes to metadata."""
    return connection.post(url=f"{connection.base_url}/api/model/changesets/{id}/commit",
                           headers={'X-MSTR-MSChanget': id}, params={'changesetId': id})


@ErrorHandler(err_msg='Error deleting the changeset with ID {id}')
def delete_changeset(connection: "Connection", id: str, error_msg: str = None):
    """Delete the changeset."""
    return connection.delete(url=f"{connection.base_url}/api/model/changesets/{id}",
                             headers={'X-MSTR-MSChanget': id}, params={'changesetId': id})
