from mstrio.users_and_groups import list_users
from mstrio.connection import Connection

from typing import List


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
    all_usrs = list_users(connection=connection)
    active_usrs = [u for u in all_usrs if u.enabled]
    lst_prvlgs = []
    for usr in active_usrs:
        p = {
            'id': usr.id,
            'name': usr.name,
            'username': usr.username,
            'privileges': usr.privileges
        }
        lst_prvlgs.append(p)
    return lst_prvlgs
