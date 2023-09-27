from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error getting Gateways.")
def get_gateways(
    connection: Connection,
    error_msg: str | None = None,
):
    """Get information for all gateways.

    Args:
        connection: MicroStrategy REST API connection object
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """

    return connection.get(
        endpoint='/api/gateways',
    )


@ErrorHandler(err_msg='Error getting Gateway with ID {id}')
def get_gateway(connection: Connection, id: str, error_msg: str | None = None):
    """Get gateway by a specific ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the gateway
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f'/api/gateways/{id}',
    )
