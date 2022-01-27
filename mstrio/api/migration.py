from typing import Optional

import requests

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error while creating the package holder')
def create_package_holder(connection: Connection, project_id: Optional[str] = None,
                          error_msg: Optional[str] = None) -> requests.Response:
    """Create a new in-memory metadata package holder.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.post(
        url=f'{connection.base_url}/api/packages',
        headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg='Error while updating the package holder with id: {id}')
def update_package_holder(connection: Connection, body: dict, id: str,
                          project_id: Optional[str] = None, prefer: str = "respond-async",
                          error_msg: Optional[str] = None) -> requests.Response:
    """Fill the content of the in-memory metadata package holder per supplied
    specification. Currently, it's only supported when the holder is empty.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        body (dict): dictionarized PackageConfig object (with `to_dict()`)
        id (str): ID of the package to be updated
        prefer (str, optional): API currently just supports asynchronous mode,
        not support synchronous mode, so header parameter ‘Prefer’ must be set
        to ‘respond-async’ in your request. Defaults to "respond-async".
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.put(
        url=f'{connection.base_url}/api/packages/{id}',
        headers={
            'X-MSTR-ProjectID': project_id,
            'Prefer': prefer
        },
        json=body
    )


@ErrorHandler(err_msg='Error while downloading the package with id: {id}')
def download_package(connection: Connection, id: str, project_id: Optional[str] = None,
                     error_msg: Optional[str] = None) -> requests.Response:
    """Download a package binary.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): ID of the package to be downloaded.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        url=f'{connection.base_url}/api/packages/{id}/binary',
        headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg='Error while uploading the package with id: {id}')
def upload_package(connection: Connection, id: str, file: bytes, project_id: Optional[str] = None,
                   error_msg: Optional[str] = None) -> requests.Response:
    """Upload package to sandbox directly.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): ID of the package to be uploaded.
        file (bytes): package in a format of a binary string.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.put(
        url=f'{connection.base_url}/api/packages/{id}/binary',
        headers={'X-MSTR-ProjectID': project_id},
        files={'file': file}
    )


@ErrorHandler(err_msg='Error while getting the package holder with id: {id}')
def get_package_holder(connection: Connection, id: str, project_id: Optional[str] = None,
                       show_content: bool = True,
                       error_msg: Optional[str] = None) -> requests.Response:
    """Get definition of a package, including package status and its detail
    content.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): ID of the package to be retrieved.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        show_content (bool, optional): Show package content or not. Defaults to
        False.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id

    return connection.get(
        url=f'{connection.base_url}/api/packages/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'showContent': show_content}
    )


@ErrorHandler(err_msg='Error while deleting the package holder with id: {id}')
def delete_package_holder(connection: Connection, id: str, project_id: Optional[str] = None,
                          prefer: str = 'respond-async',
                          error_msg: Optional[str] = None) -> requests.Response:
    """Delete the in-memory metadata package holder, releasing associated
    Intelligence Server resources.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): ID of the package to be deleted.
        prefer (str, optional): API currently just supports asynchronous mode,
        not support synchronous mode, so header parameter ‘Prefer’ must be set
        to ‘respond-async’ in your request. Defaults to "respond-async".
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """

    project_id = project_id if project_id is not None else connection.project_id
    return connection.delete(
        url=f'{connection.base_url}/api/packages/{id}',
        headers={
            'X-MSTR-ProjectID': project_id,
            'Prefer': prefer
        }
    )


@ErrorHandler(err_msg='Error while creating the import for package holder with id: {id}')
def create_import(connection: Connection, id: str, project_id: Optional[str] = None,
                  generate_undo: bool = False,
                  error_msg: Optional[str] = None) -> requests.Response:
    """Create a package import process.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): ID of the package for which import process will be
        created.
        generate_undo (bool, optional): Generate undo package or not. Defaults
        to False.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """

    # TODO: Change to a parameter when any other values are supported
    prefer = 'respond-async'

    project_id = project_id if project_id is not None else connection.project_id
    return connection.post(
        url=f'{connection.base_url}/api/packages/imports',
        headers={
            'X-MSTR-ProjectID': project_id,
            'Prefer': prefer
        },
        params={
            'packageId': id,
            'generateUndo': generate_undo
        },
    )


@ErrorHandler(err_msg='Error while getting the import with id: {id}')
def get_import(connection: Connection, id: str, project_id: Optional[str] = None,
               error_msg: Optional[str] = None) -> requests.Response:
    """Get result of a package import process.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): Import process ID.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        url=f'{connection.base_url}/api/packages/imports/{id}',
        headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg='Error while deleting the import with id: {id}')
def delete_import(connection: Connection, id: str, project_id: Optional[str] = None,
                  error_msg: Optional[str] = None) -> requests.Response:
    """Closes an existing import process previously created.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): Import process ID.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    # TODO: Change to a parameter when any other values are supported
    prefer = 'respond-async'

    project_id = project_id if project_id is not None else connection.project_id
    return connection.delete(
        url=f'{connection.base_url}/api/packages/imports/{id}',
        headers={
            'X-MSTR-ProjectID': project_id,
            'Prefer': prefer
        }
    )


@ErrorHandler(err_msg='Error while creating the undo for import with id: {id}')
def create_undo(connection: Connection, id: str, project_id: Optional[str] = None,
                error_msg: Optional[str] = None) -> requests.Response:
    """Download undo package binary for this import process.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server.
        id (str): Import process ID.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    project_id = project_id if project_id is not None else connection.project_id
    return connection.get(
        url=f'{connection.base_url}/api/packages/imports/{id}/undoPackage/binary',
        headers={'X-MSTR-ProjectID': project_id}
    )
