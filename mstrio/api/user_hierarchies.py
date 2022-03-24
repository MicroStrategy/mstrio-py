from typing import Optional, TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_decorator, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error listing Hierarchies.')
def get_user_hierarchies(connection: "Connection", project_id: Optional[str] = None,
                         changeset_id: Optional[str] = None, limit: int = 1000, offset: int = 0,
                         error_msg: Optional[str] = None):
    """Get a list of all user hierarchies.
    The project ID is required to return all user hierarchy definitions
    in metadata. The changeset ID is required to return all user hierarchy
    definitions within a specific changeset. To execute the request,
    provide either the project ID or changeset ID.
    If you provide both, only the changeset ID is used.

    Args:
        connection: MicroStrategy REST API connection object
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 1000.
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/model/hierarchies",
        headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-MS-Changeset': changeset_id,
        },
        params={
            'limit': limit,
            'offset': offset,
        }
    )


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error creating the user hierarchy.')
def create_user_hierarchy(connection: "Connection", body: dict, changeset_id: str,
                          error_msg: Optional[str] = None):
    """Creates a new user hierarchy in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id (str): Changeset ID
        body: User hierarchy creation body
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    return connection.post(
        url=f"{connection.base_url}/api/model/hierarchies",
        headers={'X-MSTR-MS-Changeset': changeset_id},
        json=body
    )


@unpack_information
@ErrorHandler(err_msg='Error getting the user hierarchy with ID: {id}.')
def get_user_hierarchy(connection: "Connection", id: str, project_id: Optional[str] = None,
                       changeset_id: Optional[str] = None, error_msg: Optional[str] = None):
    """Get the definition of a user hierarchy.
    The project ID is required to return a user hierarchy's definition
    in metadata. The changeset ID is required to return a user hierarchy's
    definition within a specific changeset. To execute the request, provide
    either the project ID or changeset ID.
    If both are provided, only the changeset ID is used.

    Args:
        connection: MicroStrategy REST API connection object
        hierarchy_id (str): Hierarchy ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/model/hierarchies/{id}",
        headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-MS-Changeset': changeset_id
        },
    )


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error updating the user hierarchy with ID: {id}.')
def update_user_hierarchy(connection: "Connection", changeset_id: str, id: str,
                          body: dict, error_msg: Optional[str] = None):
    """Updates a specific user hierarchy in the changeset,
    based on the definition provided in the request body.

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id (str, optional): Changeset ID
        hierarchy_id (str): Hierarchy ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        body: User hierarchy update info
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        url=f"{connection.base_url}/api/model/hierarchies/{id}",
        headers={'X-MSTR-MS-Changeset': changeset_id},
        json=body
    )


@changeset_decorator
@ErrorHandler(err_msg='Error deleting the user hierarchy with ID: {id}.')
def delete_user_hierarchy(connection: "Connection", id: str, changeset_id: str,
                          error_msg: Optional[str] = None):
    """Delete a specific user hierarchy

    Args:
        connection: MicroStrategy REST API connection object
        hierarchy_id (str): Hierarchy ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        changeset_id (str): Changeset ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """

    return connection.delete(
        url=f"{connection.base_url}/api/model/hierarchies/{id}",
        headers={
            'X-MSTR-MS-Changeset': changeset_id
        },
    )
