from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error sending an email')
def send_email(connection: 'Connection', body: dict, error_msg: str | None = None):
    """Send an email to specified recipients.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (json): JSON-formatted data used to send an email
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server."""
    return connection.post(endpoint='/api/emails', json=body)
