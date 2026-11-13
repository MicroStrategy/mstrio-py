import logging

from mstrio import config
from mstrio.api import emails
from mstrio.connection import Connection
from mstrio.users_and_groups import User

logger = logging.getLogger(__name__)


def send_email(
    connection: 'Connection',
    users: list[str | User] | str | User,
    subject: str,
    content: str,
    is_html: bool | None = None,
) -> None:
    """Send an email to specified recipients.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        users(list[str | User] | str | User): User IDs, User objects, or raw
            email addresses to send the email to. Using raw email addresses
            requires a configured SmartHost email device in the target Strategy
            environment.
        subject (str): Subject of the email
        content (str): Content of the email
        is_html (bool, optional): Whether the email content is HTML-formatted
    """
    if not subject or not content:
        raise ValueError("Both `subject` and `content` must be provided.")

    recipients = [users] if isinstance(users, (str, User)) else users
    user_ids = []
    email_addresses = []
    for recipient in recipients:
        if isinstance(recipient, User):
            user_ids.append(recipient.id)
        elif isinstance(recipient, str) and '@' in recipient:
            email_addresses.append(recipient)
        else:
            user_ids.append(recipient)

    if user_ids or not email_addresses:
        emails.send_email(
            connection=connection,
            body={
                'notificationType': 'USER_CREATION',
                'userIds': user_ids,
                'subject': subject,
                'content': content,
                'isHTML': is_html,
            },
        )

    if email_addresses:
        emails.send_email_v2(
            connection=connection,
            body={
                'recipients': email_addresses,
                'subject': subject,
                'content': content,
            },
        )

    if config.verbose:
        logger.info(f"Email sent with the subject: {subject}")
