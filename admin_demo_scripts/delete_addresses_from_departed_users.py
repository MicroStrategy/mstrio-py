from mstrio.users_and_groups import list_users
from mstrio.connection import Connection

from typing import List


def delete_addresses_from_departed_users(connection: "Connection") -> List[dict]:
    """Remove each address from every departed user (those which are disabled)
    For each successfully removed address a message will be printed.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    Returns:
        removed_addresses: list - list of dictionaries with keys user_id,
            username, address
    """

    # get all users that are disabled
    all_usrs = list_users(connection=connection)
    usrs = [u for u in all_usrs if not u.enabled]
    removed_addresses = []
    for usr in usrs:
        # remove all email addresses from the given user
        if usr.addresses:
            for addr in usr.addresses:
                usr.remove_address(id=addr['id'])
                removed_addresses.append({
                    'user_id': usr.id,
                    'username': usr.username,
                    'address': addr
                })
    return removed_addresses
