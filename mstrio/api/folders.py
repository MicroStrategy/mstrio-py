from typing import Optional, TYPE_CHECKING

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession


@ErrorHandler(err_msg='Error while creating the folder.')
def create_folder(connection: Connection, name: str, parent_id: str,
                  description: Optional[str] = None, project_id: Optional[str] = None):
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
    body = {
        "name": name,
        "description": description,
        "parent": parent_id,
    }
    return connection.post(
        url=connection.base_url + '/api/folders',
        headers={'X-MSTR-ProjectID': project_id},
        json=body
    )


@ErrorHandler(err_msg='Error while deleting folder with ID: {id}.')
def delete_folder(connection: Connection, id: str, project_id: Optional[str] = None):
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
        url=f"{connection.base_url}/api/folders/{id}",
        headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg='Error while listing folders.')
def list_folders(connection: Connection, project_id: Optional[str] = None, offset: int = 0,
                 limit: int = 5000, error_msg: Optional[str] = None):
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
        url=f"{connection.base_url}/api/folders",
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'offset': offset,
            'limit': limit
        }
    )


def list_folders_async(future_session: "FuturesSession", connection: Connection,
                       project_id: Optional[str] = None, offset: int = 0, limit: int = 5000):
    """Get a list of folders asynchronously.

    Args:
        future_session(object): `FuturesSession` object to call MicroStrategy
            REST Server asynchronously
        connection: MicroStrategy REST API connection object
        project_id (string, optional): id of project
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 5000.

    Returns:
        Complete Future object.
    """
    url = f"{connection.base_url}/api/folders"
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(url=url, headers=headers, params=params)


@ErrorHandler(err_msg='Error while getting contents of a folder with ID: {id}.')
def get_folder_contents(connection: Connection, id: str, project_id: Optional[str] = None,
                        offset: int = 0, limit: int = 5000, error_msg: Optional[str] = None):
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
        url=f"{connection.base_url}/api/folders/{id}",
        headers={'X-MSTR-ProjectID': connection.project_id},
        params={
            'offset': offset,
            'limit': limit
        }
    )


def get_folder_contents_async(future_session: "FuturesSession", connection: Connection, id: str,
                              project_id: Optional[str] = None, offset: int = 0,
                              limit: int = 5000):
    """Get contents of a folder asynchronously.

    Args:
        future_session(object): `FuturesSession` object to call MicroStrategy
            REST Server asynchronously
        connection: MicroStrategy REST API connection object
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
    project_id = project_id if project_id is not None else connection.project_id
    url = f"{connection.base_url}/api/folders/{id}"
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(url=url, headers=headers, params=params)


@ErrorHandler(err_msg='Error while getting contents of a pre-defined folder.')
def get_predefined_folder_contents(connection: Connection, folder_type: int,
                                   project_id: Optional[str] = None, offset: int = 0,
                                   limit: int = 5000, error_msg: Optional[str] = None):
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
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/folders/preDefined/{folder_type}",
        headers={'X-MSTR-ProjectID': project_id}, params={
            'offset': offset,
            'limit': limit
        }
    )


def get_predefined_folder_contents_async(future_session: "FuturesSession", connection: Connection,
                                         folder_type: int, project_id: Optional[str] = None,
                                         offset: int = 0, limit: int = 5000):
    """Get contents of a pre-defined folder.

    Args:
        future_session(object): `FuturesSession` object to call MicroStrategy
            REST Server asynchronously
        connection: MicroStrategy REST API connection object
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
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    url = f"{connection.base_url}/api/folders/preDefined/{folder_type}"
    headers = {'X-MSTR-ProjectID': project_id}
    params = {'offset': offset, 'limit': limit}
    return future_session.get(url=url, headers=headers, params=params)


@ErrorHandler(err_msg='Error while getting contents of My Personal Objects folder.')
def get_my_personal_objects_contents(connection: Connection, project_id: Optional[str] = None):
    """Get contents of My Personal Objects folder.

    Args:
        connection: MicroStrategy REST API connection object
        project_id (string, optional): id of project

    Returns:
         Complete HTTP response object.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/folders/myPersonalObjects",
        headers={'X-MSTR-ProjectID': project_id}
    )
