"""
Facilitate user management operations such as changing owner,
Distinguished Name (DN) manipulation.

1. Connect to the environment using data from the workstation
2. Get first user group object based on provided name ('Second Factor Exempt')
3. Get second user group object based on provided name ('TransactionServer')
4. Move users from the first user group to the second user group
5. Change owner for all users to administrator
6. Get user group object based on provided name ('Second Factor Exempt')
7. Change/add LDAP Distinguished Name (DN) on target user group
"""

from mstrio.connection import get_connection
from mstrio.users_and_groups.user import User, list_users
from mstrio.users_and_groups.user_group import UserGroup

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# Move users from one user group to another
user_group_1 = UserGroup(conn, name='Second Factor Exempt')
user_group_2 = UserGroup(conn, name='TransactionServer')
user_group_2.add_users([user['id'] for user in user_group_1.members])
user_group_1.remove_all_users()

# change owner for all the users to Administrator
for user in list_users(conn):
    user.alter(owner=User(conn, name='Administrator'))

# change/add LDAP Distinguished Name (DN) on target user group
user_group = UserGroup(conn, name='Second Factor Exempt')
user_group.alter(ldapdn='CN=Users,DC=domain,DC=com')
