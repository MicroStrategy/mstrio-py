from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error creating Contact.")
def create_contact(connection: Connection, body: dict, error_msg: str | None = None):
    """Create a new contact.

    Args:
        connection: MicroStrategy REST API connection object
        body: Contact creation info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    endpoint = '/api/contacts/'
    return connection.post(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error getting Contact with ID {id}")
def get_contact(connection: Connection, id: str, error_msg: str | None = None):
    """Get contact by a specific id.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the contact
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    endpoint = f'/api/contacts/{id}'
    return connection.get(endpoint=endpoint)


@ErrorHandler(err_msg="Error deleting Contact with ID {id}")
def delete_contact(connection: Connection, id: str, error_msg: str | None = None):
    """Delete a contact.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the contact
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    endpoint = f'/api/contacts/{id}'
    return connection.delete(endpoint=endpoint)


@ErrorHandler(err_msg="Error updating Contact with ID {id}")
def update_contact(
    connection: Connection, id: str, body: dict, error_msg: str | None = None
):
    """Update a contact.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the contact
        body: Contact update info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    endpoint = f'/api/contacts/{id}'
    return connection.put(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error getting Contacts.")
def get_contacts(
    connection: Connection,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Get information for all contacts.

    Args:
        connection: MicroStrategy REST API connection object
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    endpoint = '/api/contacts/'
    params = {'fields': fields, 'offset': offset, 'limit': limit}
    return connection.get(endpoint=endpoint, params=params)
