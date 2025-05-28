"""Remove each address from every departed user (those which are disabled).
For each successfully removed address a message will be printed.

1. Connect to the environment using data from workstation
2. Get all users that are disabled
3. For every retrieved user remove all its email addresses
4. Return list which contains information about removed addresses such as user's id,
   username and address
"""

from typing import List

from mstrio.connection import Connection, get_connection
from mstrio.users_and_groups import list_users


def delete_addresses_from_departed_users(connection: "Connection") -> List[dict]:
    """Remove each address from every departed user (those which are disabled).
    For each successfully removed address a message will be printed.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
    """

    # get all users that are disabled
    all_users = list_users(connection=connection)
    users_ = [u for u in all_users if not u.enabled]
    removed_addresses = []
    for user_ in users_:
        # remove all email addresses from the given user
        if user_.addresses:
            for address in user_.addresses:
                user_.remove_address(id=address['id'])

                removed_addresses.append(
                    {
                        'user_id': user_.id,
                        'username': user_.username,
                        'address': address,
                    }
                )
    return removed_addresses


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# execute deletion of addresses from departed users
delete_addresses_from_departed_users(conn)
