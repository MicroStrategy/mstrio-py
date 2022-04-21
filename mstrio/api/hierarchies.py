from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_decorator
from mstrio.utils.error_handlers import ErrorHandler


@changeset_decorator
@ErrorHandler(err_msg='Error getting attribute {id} relationship.')
def get_attribute_relationships(connection: Connection, id: str, changeset_id: str,
                                project_id: str):
    """Get relationship(s) of an attribute

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a attribute
        changeset_id: ID of a changeset
        project_id: Id of a project

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/systemHierarchy/attributes/{id}/relationships',
        headers={
            'X-MSTR-MS-Changeset': changeset_id,
            'X-MSTR-ProjectID': project_id
        })


@changeset_decorator
@ErrorHandler(err_msg='Error updating attribute {id} relationship.')
def update_attribute_relationships(
    connection: Connection,
    id: str,
    changeset_id: str,
    body: dict,
):
    """Update relationship(s) of an attribute

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a attribute
        changeset_id: ID of a changeset
        body: JSON-formatted definition of the attribute relationships

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.put(
        url=f'{connection.base_url}/api/model/systemHierarchy/attributes/{id}/relationships',
        headers={'X-MSTR-MS-Changeset': changeset_id}, json=body)
