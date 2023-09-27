from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting Drivers.")
def get_drivers(
    connection: Connection,
    error_msg: str | None = None,
):
    """Get information for all drivers.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """

    return connection.get(
        endpoint='/api/drivers',
    )


@ErrorHandler(err_msg="Error getting Driver with ID {id}")
def get_driver(connection: Connection, id: str, error_msg: str | None = None):
    """Get driver by a specific ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the driver
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f'/api/drivers/{id}',
    )


@ErrorHandler(err_msg="Error updating Driver with ID {id}")
def update_driver(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
):
    """Update a driver.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the driver
        body: Driver update info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        endpoint=f'/api/drivers/{id}',
        json=body,
    )
