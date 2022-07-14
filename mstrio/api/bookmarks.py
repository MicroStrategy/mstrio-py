from typing import List

from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error getting bookmarks from shortcut {shortcut_id}')
def get_bookmarks_from_shortcut(connection, shortcut_id, error_msg=None):
    """Get a Bookmark list from a Shortcut Object.

    Args:
        connection: MicroStrategy REST API connection object
        shortcut_id (string): Shortcut  ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/shortcuts/{shortcut_id}/bookmarks"
    return connection.get(url=url)


@ErrorHandler(err_msg='Error updating information for shortcut {shortcut_id}')
def update_information_for_shortcut(connection, shortcut_id, body, error_msg=None):
    """Update info for a shortcut.

    Args:
        connection: MicroStrategy REST API connection object
        shortcut_id (string): The ID of the document shortcut to execute
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = connection.base_url + f"​/api/shortcuts/{shortcut_id}"
    return connection.patch(url=url, json=body)


@ErrorHandler(err_msg='Error adding a new bookmark.')
def refresh_document_instance(connection, error_msg=None):
    """Add a new bookmark into current shortcut object.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = connection.base_url + "​/api​/bookmarks"
    return connection.put(url=url)


@ErrorHandler(err_msg='Error deleting bookmarks.')
def delete_bookmarks(connection, shortcut_id: str, bookmark_ids: List, error_msg=None):
    """Bulk deletion of bookmarks.

    Args:
        connection: MicroStrategy REST API connection object
        shortcut_id: Shortcut ID
        bookmark_ids: IDs of bookmarks to be deleted
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    body = {"shortcutId": shortcut_id, "bookmarkIds": bookmark_ids}
    url = f'{connection.base_url}/api/bookmarks'
    return connection.delete(url=url, json=body)


@ErrorHandler(err_msg='Error deleting bookmark with ID {bookmark_id}')
def delete_single_bookmark(connection, shortcut_id: str, bookmark_id: str, error_msg=None):
    """Delete a bookmark.

    Args:
        connection: MicroStrategy REST API connection object
        shortcut_id: Shortcut ID
        bookmark_id (string): Bookmark ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    body = {"shortcutId": shortcut_id}
    url = f'{connection.base_url}/api/bookmarks/{bookmark_id}'
    return connection.delete(url=url, json=body)


@ErrorHandler(err_msg='Error updating bookmark {bookmark_id}')
def update_bookmark(connection, bookmark_id, body, error_msg=None):
    """Update a bookmark.

    Args:
        connection: MicroStrategy REST API connection object
        bookmark_id (string): Bookmark ID
        body: JSON-formatted information used to format the document
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = f"{connection.base_url}/api/bookmarks/{bookmark_id}"
    return connection.put(url=url, json=body)


@ErrorHandler(err_msg='Error adding bookmark {bookmark_name}')
def add_bookmark(
    connection, bookmark_name, instance_id, shortcut_id, error_msg=None
):  # shortcut needs to be created to add a bookmark!
    """Update a bookmark.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    body = {"name": bookmark_name, "instanceId": instance_id}
    url = f'{connection.base_url}/api/bookmarks'
    return connection.post(url=url, json=body)


@ErrorHandler(err_msg='Error getting shortcuts for document {document_id}')
def get_document_shortcut(connection, document_id, instance_id, error_msg=None):
    """Retrieve a published shortcut from the document definition.

    Args:
        connection: MicroStrategy REST API connection object
        document_id (string): Document  ID
        instance_id (string): Instance  ID
        error_msg (string, optional): Custom Error Message for Error Handling


    Returns:
        Complete HTTP response object.
    """
    endpoint_url = f'/api/documents/{document_id}/instances/{instance_id}/shortcut'
    return connection.get(connection.base_url + endpoint_url)
