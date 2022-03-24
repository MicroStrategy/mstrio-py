"""List names and IDs of empty user groups."""

from typing import List

from mstrio.connection import Connection, get_connection
from mstrio.users_and_groups import list_user_groups, UserGroup


def list_empty_user_groups(connection: "Connection") -> List["UserGroup"]:
    """List empty user groups.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    """
    all_user_groups = list_user_groups(connection=connection)
    return [user_group_ for user_group_ in all_user_groups if not user_group_.list_members()]


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# get empty user groups
empty_user_groups = list_empty_user_groups(conn)

# print empty user groups
print('Empty user groups:', flush=True)
for ug in empty_user_groups:
    print(f"{ug.name} ({ug.id}) ", flush=True)
