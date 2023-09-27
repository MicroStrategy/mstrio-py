from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error listing Transmitters.")
def get_transmitters(connection: 'Connection', error_msg: str | None = None):
    """Get a list of all transmitters that the authenticated user has access
    to.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(endpoint='/api/transmitters')


@ErrorHandler(err_msg="Error creating Transmitter.")
def create_transmitter(connection: 'Connection', body, error_msg: str | None = None):
    """Create a new transmitter.

    Args:
        connection: MicroStrategy REST API connection object
        body: Transmitter creation body
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    return connection.post(endpoint='/api/transmitters', json=body)


@ErrorHandler(err_msg="Error getting Transmitter with ID {id}")
def get_transmitter(connection: 'Connection', id: str, error_msg: str | None = None):
    """Get transmitter by a specific id.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the transmitter
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(endpoint=f'/api/transmitters/{id}')


@ErrorHandler(err_msg="Error updating Transmitter with ID {id}")
def update_transmitter(
    connection: 'Connection', id: str, body: dict, error_msg: str | None = None
):
    """Update a transmitter.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the transmitter
        body: Transmitter update info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.put(endpoint=f'/api/transmitters/{id}', json=body)


@ErrorHandler(err_msg="Error deleting Transmitter with ID {id}")
def delete_transmitter(connection: 'Connection', id: str, error_msg: str | None = None):
    """Delete a transmitter.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the transmitter
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(endpoint=f'/api/transmitters/{id}')
