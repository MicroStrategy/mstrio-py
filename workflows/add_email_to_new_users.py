"""Add email address with a form `{username}@microstrategy.com` to every user
which is enabled but doesn't have an email address. For each successfully added
email address a message will be printed.

1. Connect to the environment using data from workstation
2. Get list of all users that are enabled
3. Add email address to every user which doesn't have one (it is created with username
   of the user and the domain provided in the function)
"""

from typing import List

from mstrio.connection import Connection, get_connection
from mstrio.users_and_groups import list_users, User


def add_email_to_new_users(
    connection: "Connection", domain="microstrategy.com"
) -> List["User"]:
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
    users_ = [u for u in all_users if u.enabled]
    modified_users_ = []
    for user_ in users_:
        # add email address only for those users which don't have one
        if not user_.addresses:
            email_address = user_.username + '@' + domain
            user_.add_address(name=user_.username, address=email_address)
            modified_users_.append(user_)

    return modified_users_


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# execute adding email to new users
# if needed provide some domain - default is 'microstrategy.com'
add_email_to_new_users(conn)
