from typing import List

from mstrio.connection import Connection
from mstrio.users_and_groups import list_users


def list_active_user_privileges(connection: "Connection") -> List[dict]:
    """List user privileges for all active users.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`

    Returns:
        list of dicts where eac of them is in given form:
        {
            'id' - id of user
            'name' - name of user
            'username' - username of user
            'privileges' - list of privileges of user
        }
    """
    all_users = list_users(connection=connection)
    active_users = [u for u in all_users if u.enabled]
    list_privileges = []
    for usr in active_users:
        p = {
            'id': usr.id,
            'name': usr.name,
            'username': usr.username,
            'privileges': usr.privileges
        }
        list_privileges.append(p)
    return list_privileges
