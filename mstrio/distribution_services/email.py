import logging

from mstrio import config
from mstrio.api import emails
from mstrio.connection import Connection
from mstrio.users_and_groups import User

logger = logging.getLogger(__name__)


def send_email(
    connection: 'Connection',
    users: list[str | User],
    subject: str,
    content: str,
    is_html: bool | None = None,
) -> None:
    """Send an email to specified recipients.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        users(list[str | User]): List of user IDs or User objects to send
            the email to
        subject (str): Subject of the email
        content (str): Content of the email
        is_html (bool, optional): Whether the email content is HTML-formatted
    """
    if not subject or not content:
        raise ValueError("Both `subject` and `content` must be provided.")

    body = {
        'notificationType': 'USER_CREATION',
        'userIds': [
            user_id.id if isinstance(user_id, User) else user_id for user_id in users
        ],
        'subject': subject,
        'content': content,
        'isHTML': is_html,
    }

    emails.send_email(connection=connection, body=body)
    if config.verbose:
        logger.info(f"Email sent with the subject: {subject}")
