"""List security roles for every user in a user group. It is possible to provide
either name or id of user group. Without any changes this script will be
executed for user group 'System Administrators'."""

from typing import List

from mstrio.connection import Connection, get_connection
from mstrio.users_and_groups import User, UserGroup


def list_security_roles_per_user(
    connection: "Connection",
    user_group_name: str = None,
    user_group_id: str = None,
    include_user_groups: bool = False
) -> List[dict]:
    """List security roles for every user in a user group.
    It is possible to provide either name or id of user group.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        user_group_name (str): name of the user group
        user_group_id (str): id of the user group
        include_user_groups (bool): if True also user groups, which are inside
            provided user group, will be included in the result

    Returns:
        list of dicts where each of them is in given form:
        {
            'type' - type of object (it can be `user` or `user group`)
            'id' - id of object
            'name' - name of object
            'username' - username of user (for user group it is None)
            'security_roles' - list of security roles which object has
        }
    """

    user_group_ = UserGroup(connection=connection, name=user_group_name, id=user_group_id)
    all_security_roles = []
    for member in user_group_.list_members():
        if not member.get('fullName', None):
            if not include_user_groups:
                continue
            member_type = 'user_group'
            tmp_ug = UserGroup(connection=connection, id=member['id'])
            security_roles = tmp_ug.security_roles
        else:
            member_type = 'user'
            tmp_u = User(connection=connection, id=member['id'])
            security_roles = tmp_u.security_roles
        m = {
            'type': member_type,
            'id': member['id'],
            'name': member['name'],
            'username': member.get('username', None),
            'security_roles': security_roles
        }
        print('Security roles:', flush=True)
        for project_ in m['security_roles']:
            print("\tProject: " + project_['name'], flush=True)
            for sec_role in project_['securityRoles']:
                print("\t\t" + sec_role['name'], flush=True)
        all_security_roles.append(m)
    return all_security_roles


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# list security roles per all users in user group 'System Administrators'
# change name of user group if needed
list_security_roles_per_user(conn, user_group_name='System Administrators')
