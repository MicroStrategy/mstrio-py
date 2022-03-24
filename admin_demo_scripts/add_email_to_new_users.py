from typing import List

from mstrio.connection import Connection
from mstrio.users_and_groups import list_users, User


def add_email_to_new_users(connection: "Connection", domain="microstrategy.com") -> List["User"]:
    """Add email address with a form `{username}@microstrategy.com`
    to every user which is enabled but doesn't have an email address.
    For each successfully added email address a message will be printed.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        domain: name of the domain in the email address (it should be
            provided without '@' symbol). Default value is "microstrategy.com".

    Returns:
        list of users to which email addresses where added
    """

    # get all users that are enabled
    all_users = list_users(connection=connection)
    users = [u for u in all_users if u.enabled]
    modified_users = []
    for usr in users:
        # add email address only for those users which don't have one
        if not usr.addresses:
            email_address = usr.username + '@' + domain
            usr.add_address(name=usr.username, address=email_address)
            modified_users.append(usr)

    return modified_users
