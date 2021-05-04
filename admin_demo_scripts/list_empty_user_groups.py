from mstrio.users_and_groups.user_group import list_user_groups
from mstrio.connection import Connection


def list_empty_user_groups(connection: "Connection"):
    """List empty user groups.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    """
    all_user_groups = list_user_groups(connection=connection)
    return [user_group_ for user_group_ in all_user_groups if not user_group_.list_members()]
