from mstrio.users_and_groups import UserGroup, list_user_groups
from mstrio.connection import Connection

from typing import List


def list_empty_user_groups(connection: "Connection") -> List["UserGroup"]:
    """List empty user groups.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    """
    all_user_groups = list_user_groups(connection=connection)
    return [user_group_ for user_group_ in all_user_groups if not user_group_.list_members()]
