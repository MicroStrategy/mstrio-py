import requests

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error while creating the package holder")
def create_package_holder(
    connection: Connection,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Create a new in-memory metadata package holder.

    Args:
        connection (Connection): Strategy One REST API connection object.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.post(
        endpoint='/api/packages',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error while updating the package holder with id: {id}")
def update_package_holder(
    connection: Connection,
    body: dict,
    id: str,
    project_id: str | None = None,
    prefer: str = 'respond-async',
    error_msg: str | None = None,
) -> requests.Response:
    """Fill the content of the in-memory metadata package holder per supplied
    specification. Currently, it's only supported when the holder is empty.

    Args:
        connection (Connection): Strategy One REST API connection object.
        body (dict): dictionarized PackageConfig object (with `to_dict()`)
        id (str): ID of the package to be updated
        prefer (str, optional): API currently just supports asynchronous mode,
        not support synchronous mode, so header parameter `Prefer` must be set
        to `respond-async` in your request. Defaults to "respond-async".
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.put(
        endpoint=f'/api/packages/{id}',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        json=body,
    )


@ErrorHandler(err_msg="Error while downloading the package with id: {id}")
def download_package(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Download a package binary.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): ID of the package to be downloaded.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.get(
        endpoint=f'/api/packages/{id}/binary',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error while uploading the package with id: {id}")
def upload_package(
    connection: Connection,
    id: str,
    file: bytes,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Upload package to sandbox directly.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): ID of the package to be uploaded.
        file (bytes): package in a format of a binary string.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.put(
        endpoint=f'/api/packages/{id}/binary',
        headers={'X-MSTR-ProjectID': project_id},
        files={'file': file},
    )


@ErrorHandler(err_msg="Error while getting the package holder with id: {id}")
def get_package_holder(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    show_content: bool = True,
    error_msg: str | None = None,
) -> requests.Response:
    """Get definition of a package, including package status and its detail
    content.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): ID of the package to be retrieved.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        show_content (bool, optional): Show package content or not. Defaults to
        False.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.get(
        endpoint=f'/api/packages/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'showContent': show_content},
    )


@ErrorHandler(err_msg="Error while deleting the package holder with id: {id}")
def delete_package_holder(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    prefer: str = 'respond-async',
    error_msg: str | None = None,
) -> requests.Response:
    """Delete the in-memory metadata package holder, releasing associated
    Intelligence Server resources.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): ID of the package to be deleted.
        prefer (str, optional): API currently just supports asynchronous mode,
        not support synchronous mode, so header parameter `Prefer` must be set
        to `respond-async` in your request. Defaults to "respond-async".
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.delete(
        endpoint=f'/api/packages/{id}',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
    )


@ErrorHandler(
    err_msg="Error while creating the import for package holder with id: {id}"
)
def create_import(
    connection: Connection,
    id: str,
    prefer: str = 'respond-async',
    project_id: str | None = None,
    generate_undo: bool = False,
    error_msg: str | None = None,
) -> requests.Response:
    """Create a package import process.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): ID of the package for which import process will be
            created.
        prefer (str, optional): Allow client to set preferences. Currently,
            respond-async is the only supported mode.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        generate_undo (bool, optional): Generate undo package or not. Defaults
            to False.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.post(
        endpoint='/api/packages/imports',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={'packageId': id, 'generateUndo': generate_undo},
    )


@ErrorHandler(err_msg="Error while getting the import with id: {id}")
def get_import(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Get result of a package import process.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Import process ID.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.get(
        endpoint=f'/api/packages/imports/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error while deleting the import with id: {id}")
def delete_import(
    connection: Connection,
    id: str,
    prefer: str = 'respond-async',
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Closes an existing import process previously created.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Import process ID.
        prefer (str, optional): Allow client to set preferences. Currently,
            respond-async is the only supported mode.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.delete(
        endpoint=f'/api/packages/imports/{id}',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
    )


@ErrorHandler(err_msg="Error while creating the undo for import with id: {id}")
def create_undo(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Download undo package binary for this import process.

    Args:
        connection (Connection): Strategy One REST API connection object.
        id (str): Import process ID.
        project_id (Optional[str]): Optional ID of a project. Defaults to None.
        error_msg (Optional[str]): Optional error message. Defaults to None.

    Returns:
        requests.Response: Response object containing all of the information
        returned by the server.
    """
    return connection.get(
        endpoint=f'/api/packages/imports/{id}/undoPackage/binary',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting migrations list")
def list_migrations(
    connection: Connection,
    offset: int = 0,
    limit: int = 100,
    migration_type: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Get a list of migrations.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        offset (int, optional): Starting point within the collection of returned
            results
        limit (int, optional): Maximum number of items returned for a single
            request. Maximum value: 1000
        migration_type (str, optional): The purpose of the migration package,
            the allowable values include object_migration, project_merge,
            migration_from_shared_file_store. If None it returns only
            object_migration migrations
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.get(
        endpoint='/api/migrations',
        params={
            'offset': offset,
            'limit': limit,
            'packageInfo.purpose': migration_type,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error getting migration with ID: {migration_id}")
def get_migration(
    connection: Connection,
    migration_id: str,
    show_content: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Get definition of a single metric by id

    Args:
        connection (Connection): Strategy One REST API connection object
        migration_id (str): ID of the migration object
        show_content (str, optional): The type of showing content, the allowable
            values include default, tocview, treeview, all
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    return connection.get(
        endpoint=f'/api/migrations/{migration_id}',
        params={
            'showContent': show_content,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error deleting migration package with ID: {package_id}")
def delete_migration(
    connection,
    package_id,
    error_msg: str | None = None,
    whitelist=[('ERR006', 404)],  # noqa: B006
) -> requests.Response:
    """Delete migration package specified by ID.

    Args:
        connection (Connection): Strategy One REST API connection object
        package_id (str): The ID of the migration package to be deleted
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(
        endpoint='/api/migrations',
        params={'packageId': package_id},
    )


@ErrorHandler(
    err_msg="Error downloading migration package binary with ID: {package_id}"
)
def download_migration_package(
    connection: Connection,
    package_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Get definition of a single metric by id

    Args:
        connection (Connection): Strategy One REST API connection object
        package_id (str): The ID of the migration package to be downloaded
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 200.
    """
    return connection.get(
        endpoint=f'/api/migrations/packages/{package_id}/binary',
        params={
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error while creating new migration")
def create_new_migration(
    connection: Connection,
    body: dict,
    project_id: str | None = None,
    prefer: str | None = None,
    unlock_on_start: bool | None = True,
    package_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Create total new migration or reuse existing package to create new
        migration.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server
        body (dict): Migration creation data
        project_id (str, optional): Optional ID of a project. Defaults to None
        prefer (str, optional): Prefer--allow client to set preferences.
            Currently, respond-async allows client to execute in async mode
        unlock_on_start (bool, optional): Whether unlock should be done when
            creation is started. Defaults to True.
        package_id (str, optional): ID of the migration package to be reused
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 201.
    """
    return connection.post(
        endpoint='/api/migrations',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={
            'unlockOnStart': unlock_on_start,
            'packageId': package_id,
            'fields': fields,
        },
        json=body,
    )


@ErrorHandler(err_msg="Error importing migration with ID: {migration_id}")
def start_migration(
    connection: Connection,
    prefer: str,
    migration_id: str,
    body: dict,
    project_id: str | None = None,
    generate_undo: bool | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Trigger an import process to migrate the package from the source
    environment to the target environment.

    Args:
        connection (Connection): Object representation of connection to
            MSTR Server
        prefer (str): Prefer--allow client to set preferences. Currently,
            respond-async allows client to execute in async mode
        migration_id (str): ID of the migration object
        body (dict): Information about the import process
        project_id (str, optional): Optional ID of a project. Defaults to None
        generate_undo (bool, optional): Generate undo package or not
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 201.
    """
    return connection.put(
        endpoint=f'/api/migrations/{migration_id}',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={'generateUndo': generate_undo, 'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error updating or reverting a migration with ID: {migration_id}")
def update_migration(
    connection: Connection,
    migration_id: str,
    body: dict,
    project_id: str | None = None,
    prefer: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Update a migration or trigger an undo process.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        migration_id (str): ID of the migration object to be updated or reverted
        body (dict): Migration information to be updated
        project_id (str, optional): Optional ID of a project. Defaults to None
        prefer (str): Prefer--allow client to set preferences. Currently,
            respond-async allows client to execute in async mode
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected statuses: 200, 202.
    """
    return connection.patch(
        endpoint=f'/api/migrations/{migration_id}',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={'migrationId': migration_id, 'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error editing migration with ID: {migration_id}")
def edit_migration_package(
    connection: Connection,
    prefer: str,
    migration_id: str,
    body: dict,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Edit migration package information.

    Args:
        connection (Connection): Strategy One REST API connection object
        prefer (str): Prefer--allow client to set preferences. Currently,
            respond-async allows client to execute in async mode
        migration_id (str): ID of the migration object
        body (dict): Migration information to be updated
        project_id (str, optional): Optional ID of a project. Defaults to None
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object. Expected status: 202.
    """
    return connection.put(
        endpoint=f'/api/migrations/{migration_id}/packageInfo',
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error creating file metadata.")
def storage_service_create_file_metadata(
    connection: Connection,
    body: dict,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Create a file metadata before uploading the file, which is stored in the
    storage service.

    Args:
        connection (Connection): Strategy One REST API connection object
        body (dict): {
            "name": str,
            "extension": str ("mmp"),
            "type": str ("migrations.packages"),
            "size": int,
            "sha256": str,
            "environment": {
                "id": str,
                "name": str,
            },
            "extraInfo": {
                "packageId": str (optional),
                "packageType": str
                    ("project", "project_security", "configuration"),
                "packagePurpose": str
                    ("object_migration", "project_merge", "migration_group",
                    "migration_group_child", "migration_from_shared_file_store")
            },
        }
        fields (str, optional): A comma-separated list of fields to include
                in the response. By default, all fields are returned.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. 200 on success.
    """
    return connection.post(
        endpoint='/api/mstrServices/library/storage/sharedFileStore/files',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error downloading file binary for ID {file_id}.")
def storage_service_download_file_binary(
    connection: Connection,
    file_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Upload a file binary to storage service directly.

    Args:
        connection (Connection): Strategy One REST API connection object
        file_id (str): file ID
        fields (str, optional): A comma-separated list of fields to include
                in the response. By default, all fields are returned.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. 200 on success, with MIME type
            application/octet-stream.
    """
    return connection.get(
        endpoint=(
            f'/api/mstrServices/library/storage/sharedFileStore/files/{file_id}/binary'
        ),
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error uploading file binary for ID {file_id}.")
def storage_service_upload_file_binary(
    connection: Connection,
    file_id: str,
    file: bytes,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Upload a file binary to storage service directly.

    Args:
        connection (Connection): Strategy One REST API connection object
        file_id (str): file ID
        file (bytes): file object
        fields (str, optional): A comma-separated list of fields to include
                in the response. By default, all fields are returned.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. 200 on success.
    """
    return connection.put(
        endpoint=(
            f'/api/mstrServices/library/storage/sharedFileStore/files/{file_id}/binary'
        ),
        params={'fields': fields},
        files={'file': file},
    )


@ErrorHandler(err_msg="Error deleting file binary with ID: {file_id}.")
def delete_file_binary(
    connection: Connection,
    file_id: str,
    error_msg: str | None = None,
) -> requests.Response:
    """Delete a file binary from storage service directly.

    Args:
        connection (Connection): Strategy One REST API connection object
        file_id (str): file ID to be deleted
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(
        endpoint=(f'/api/mstrServices/library/storage/sharedFileStore/files/{file_id}')
    )


@ErrorHandler(err_msg="Error getting storage files list")
def list_storage_files(
    connection: Connection,
    file_type: str,
    offset: int = 0,
    limit: int = 100,
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Get a list of storage files.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        offset (int, optional): Starting point within the collection of returned
            results
        limit (int, optional): Maximum number of items returned for a single
            request. Maximum value: 1000
        file_type (str, optional): The type of shared file which you want to
            query. Currently, only file type "migration.packages" is supported
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.get(
        endpoint='/api/mstrServices/library/storage/sharedFileStore/files',
        params={
            'offset': offset,
            'limit': limit,
            'type': file_type,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error certifying migration package with ID: {id}")
def certify_migration_package(
    connection: Connection,
    id: str,
    body: dict | None = None,
    auto_sync: bool | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Update a migration's package certification status or trigger a process
    to synchronize the status.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (str): migration package ID
        body (dict, optional): Migration package information to be updated
        auto_sync (bool, optional): Whether to trigger a process to synchronize
            the certification status with shared environment via storage service
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.patch(
        endpoint=f'/api/migrations/{id}/packageInfo/certification',
        json=body,
        params={'autoSync': auto_sync},
    )


@ErrorHandler(
    err_msg="Error triggering validation process for migration package with ID: {id}"
)
def trigger_migration_package_validation(
    connection: Connection,
    id: str,
    body: dict,
    project_id: str | None = None,
    prefer: str = 'respond-async',
    fields: str | None = None,
    error_msg: str | None = None,
) -> requests.Response:
    """Trigger a validation process

    Args:
        connection (Connection): Strategy One REST API connection object
        id (str): migration package ID
        body (dict): Validation information
        project_id (str, optional): ID of the project
        prefer (str, optional): Prefer--allow client to set preferences.
            Currently, respond-async allows client to execute in async mode
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 202.
    """
    return connection.put(
        endpoint=f'/api/migrations/{id}/validation',
        json=body,
        headers={'X-MSTR-ProjectID': project_id, 'Prefer': prefer},
        params={'fields': fields},
    )
