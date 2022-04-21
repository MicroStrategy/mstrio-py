from typing import Optional

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error getting tables.')
def get_tables(connection: Connection, changeset_id: Optional[str] = None, project_id: str = None,
               limit=None, offset=0):
    """Get a list describing all available logical tables

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id: ID of a changeset
        project_id: Id of a project
        limit: limit the number of elements returned. If `None` (default),
            all elements are returned
        offset: Offset of the elements returned

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/tables', headers={
            'X-MSTR-MS-Changeset': changeset_id,
            'X-MSTR-ProjectID': project_id
        }, params={
            'limit': limit,
            'offset': offset
        })


@ErrorHandler(err_msg=f'Error getting table {id}.')
def get_table(connection: Connection, id: str, changeset_id: Optional[str] = None,
              project_id: str = None, fields=None):
    """Get a list descrbing all available logical tables

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id: ID of a changeset
        project_id: Id of a project
        limit: limit the number of elements returned. If `None` (default),
            all elements are returned
        offset: Offset of the elements returned

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/tables/{id}', headers={
            'X-MSTR-MS-Changeset': changeset_id,
            'X-MSTR-ProjectID': project_id
        }, params={'fields': fields})