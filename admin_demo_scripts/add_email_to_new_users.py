from mstrio.users_and_groups import User, list_users
from mstrio.connection import Connection

from typing import List


def add_email_to_new_users(connection: "Connection", domain="microstrategy.com") -> List["User"]:
    """Add email address with a form `{username}@microstrategy.com`
    to every user which is enabled but doesn't have an email address.
    For each successfully added email address a messege will be printed.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        domain: name of the domain in the email address (it should be
            provided without '@' symbol). Default value is "microstrategy.com".

    Returns:
        list of users to which email addresses where added
    """

    # get all users that are enabled
    all_usrs = list_users(connection=connection)
    usrs = [u for u in all_usrs if u.enabled]
    modified_usrs = []
    for usr in usrs:
        # add email address only for those users which don't have one
        if not usr.addresses:
            email_address = usr.username + '@' + domain
            usr.add_address(name=usr.username, address=email_address)
            modified_usrs.append(usr)

    return modified_usrs
