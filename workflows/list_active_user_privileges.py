"""List user privileges for all active users.

1. Connect to the environment using data from workstation
2. Get all active users
3. For each of retrieved users prepare dictionary with user's id, name,
   username and list of privileges and save it to table
4. For each of retrieved users print user's name, username and each of its
   privileges' name
"""

from typing import List

from mstrio.connection import Connection, get_connection
from mstrio.users_and_groups import list_users


def list_active_user_privileges(connection: "Connection") -> List[dict]:
    """List user privileges for all active users.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`

    Returns:
        list of dicts where each of them is in given form:
        {
            'id' - id of user
            'name' - name of user
            'username' - username of user
            'privileges' - list of privileges of user
        }
    """
    all_users = list_users(connection=connection)
    active_users = [u for u in all_users if u.enabled]
    privileges_list = []
    for usr in active_users:
        p = {
            'id': usr.id,
            'name': usr.name,
            'username': usr.username,
            'privileges': usr.privileges,
        }
        print(f"{p['name']} ({p['username']}) ", flush=True)
        for prvlg in p['privileges']:
            print("\t" + prvlg['privilege']['name'], flush=True)
        privileges_list.append(p)
    return privileges_list


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# list privileges for all enabled users
list_active_user_privileges(conn)
