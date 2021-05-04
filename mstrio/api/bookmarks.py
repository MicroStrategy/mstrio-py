from typing import List

from mstrio.utils.helper import response_handler


def get_bookmarks_from_shortcut(connection, shortcut_id, error_msg=None):
    """Get a Bookmark list from a Shortcut Object.

    Args:
        connection: MicroStrategy REST API connection object
        shortcut_id (string): Shortcut  ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = connection.base_url + f"/api/shortcuts/{shortcut_id}/bookmarks"
    response = connection.session.get(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error getting bookmarks from shortcut {shortcut_id}"
        response_handler(response, error_msg)
    return response


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
    response = connection.session.patch(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error updating information for shortcut {shortcut_id}"
        response_handler(response, error_msg)
    return response


def refresh_document_instance(connection, error_msg=None):
    """Add a new bookmark into current shortcut object.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    url = connection.base_url + "​/api​/bookmarks"
    response = connection.session.put(url=url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error adding a new bookmark"
        response_handler(response, error_msg)
    return response


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
    url = connection.base_url + "/api/bookmarks"
    response = connection.session.delete(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error deleting bookmarks"
        response_handler(response, error_msg)
    return response


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
    url = connection.base_url + f"/api/bookmarks/{bookmark_id}"
    response = connection.session.delete(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error deleting bookmark {bookmark_id}"
        response_handler(response, error_msg)
    return response


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
    url = connection.base_url + f"/api/bookmarks/{bookmark_id}"
    response = connection.session.put(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error updating bookmark {bookmark_id}"
        response_handler(response, error_msg)
    return response


def add_bookmark(connection, bookmark_name, instance_id, shortcut_id,
                 error_msg=None):  # shortcut needs to be created to add a bookmark!
    """Update a bookmark.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    body = {"name": bookmark_name, "instanceId": instance_id}
    url = connection.base_url + "/api/bookmarks"
    response = connection.session.post(url=url, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error adding bookmark"
        response_handler(response, error_msg)
    return response


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
    response = connection.session.get(connection.base_url + endpoint_url)
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error getting shortcuts for document {document_id}"
        response_handler(response, error_msg)
    return response
