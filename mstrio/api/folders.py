from typing import TYPE_CHECKING

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.utils.sessions import FuturesSessionWithRenewal


@ErrorHandler(err_msg="Error while creating the folder.")
def create_folder(
    connection: Connection,
    name: str,
    parent_id: str,
    description: str | None = None,
    project_id: str | None = None,
):
    """Create a folder.

    Note:
        When `project_id` is provided then folder will be created in this
        project. Otherwise it will be created in a project selected within
        `connection` object.

    Args:
        connection: MicroStrategy REST API connection object
        name (string): name of folder to create
        parent_id (string): id of folder in which new folder will be created
        description (string, optional): description of folder to create
        project_id (string, optional): id of project

    Returns:
        Complete HTTP response object.
    """
    project_id = project_id if project_id is not None else connection.project_id
    body = {'name': name, 'description': description, 'parent': parent_id}
    return connection.post(
        endpoint='/api/folders', headers={'X-MSTR-ProjectID': project_id}, json=body
    )


@ErrorHandler(err_msg="Error while deleting folder with ID: {id}.")
def delete_folder(connection: Connection, id: str, project_id: str | None = None):
    """Delete complete folder.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of folder
        project_id (string, optional): id of project

    Returns:
        Complete Future object.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.delete(
        endpoint=f'/api/folders/{id}', headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg="Error while listing folders.")
def list_folders(
    connection: Connection,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
    error_msg: str | None = None,
):
    """Get a list of folders.

    Args:
        connection: MicroStrategy REST API connection object
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        endpoint='/api/folders',
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit},
    )


def list_folders_async(
    future_session: 'FuturesSessionWithRenewal',
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
):
    """Get a list of folders asynchronously.

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            MicroStrategy REST Server asynchronously
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete Future object.
    """
    endpoint = '/api/folders'
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(endpoint=endpoint, headers=headers, params=params)


@ErrorHandler(err_msg="Error while getting contents of a folder with ID: {id}.")
def get_folder_contents(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
    error_msg: str | None = None,
):
    """Get contents of a folder.

    Args:
        connection: MicroStrategy REST API connection object
        id (string): ID of folder
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete HTTP response object.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        endpoint=f'/api/folders/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit},
    )


def get_folder_contents_async(
    future_session: 'FuturesSessionWithRenewal',
    id: str,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
):
    """Get contents of a folder asynchronously.

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            MicroStrategy REST Server asynchronously
        id (string): ID of folder
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete Future object.
    """
    project_id = (
        project_id if project_id is not None else future_session.connection.project_id
    )
    endpoint = f'/api/folders/{id}'
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(endpoint=endpoint, headers=headers, params=params)


@ErrorHandler(err_msg="Error while getting contents of a pre-defined folder.")
def get_predefined_folder_contents(
    connection: Connection,
    folder_type: int,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
    error_msg: str | None = None,
):
    """Get contents of a pre-defined folder.

    Args:
        connection: MicroStrategy REST API connection object
        folder_type (int): predefined folder type, from `EnumDSSXMLFolderNames`
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete HTTP response object.
    """
    return connection.get(
        endpoint=f'/api/folders/preDefined/{folder_type}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit},
    )


def get_predefined_folder_contents_async(
    future_session: 'FuturesSessionWithRenewal',
    folder_type: int,
    project_id: str | None = None,
    offset: int = 0,
    limit: int = 5000,
):
    """Get contents of a pre-defined folder.

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            MicroStrategy REST Server asynchronously
        folder_type (int): predefined folder type, from `EnumDSSXMLFolderNames`
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete Future object.
    """
    endpoint = f'/api/folders/preDefined/{folder_type}'
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(endpoint=endpoint, headers=headers, params=params)


@ErrorHandler(err_msg="Error while getting contents of My Personal Objects folder.")
def get_my_personal_objects_contents(
    connection: Connection, project_id: str | None = None
):
    """Get contents of My Personal Objects folder.

    Args:
        connection: MicroStrategy REST API connection object
        project_id (string, optional): id of project

    Returns:
         Complete HTTP response object.
    """
    return connection.get(
        endpoint='/api/folders/myPersonalObjects',
        headers={'X-MSTR-ProjectID': project_id},
    )
