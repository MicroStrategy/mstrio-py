from mstrio.utils.helper import response_handler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mstrio.connection import Connection


def create_changeset(connection: "Connection", project_id: str = None, schema_edit: bool = False,
                     error_msg: str = None):
    """Create a new changeset for modelling manipulations."""
    if project_id is None:
        connection._validate_application_selected()
        project_id = connection.application_id
    response = connection.session.post(url=f"{connection.base_url}/api/model/changesets",
                                       headers={'X-MSTR-ProjectID': project_id},
                                       params={'schemaEdit': str(schema_edit).lower()})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating a new changeset."
        response_handler(response, error_msg)
    return response


def commit_changeset_changes(connection: "Connection", id: str, error_msg: str = None,
                             throw_error=True):
    """Commit the changeset changes to metadata."""
    response = connection.session.post(
        url=f"{connection.base_url}/api/model/changesets/{id}/commit",
        headers={'X-MSTR-MSChanget': id}, params={'changesetId': id})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error commiting changeset changes to the metadata."
        response_handler(response, error_msg, throw_error)
    return response


def delete_changeset(connection: "Connection", id: str, error_msg: str = None):
    """Delete the changeset."""
    response = connection.session.delete(url=f"{connection.base_url}/api/model/changesets/{id}",
                                         headers={'X-MSTR-MSChanget': id},
                                         params={'changesetId': id})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error deleting the changeset."
        response_handler(response, error_msg)
    return response
