"""
Change password for one or more users.

1. Connect to the environment using data from workstation
2. Change password for all users which name begins with 'User_S'
3. Change password for only first user which name begins with 'User_S'
4. Change password for only first user which name begins with 'User_S' and
   require new password on the next login
5. Change password for all users which name begins with 'User_S' and require
   new password on the next login
"""

from mstrio.connection import get_connection
from mstrio.users_and_groups.user import list_users

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# change password for all users
for user in list_users(conn, name_begins='User_S'):
    user.alter(password='new_password')

# change user password
user = list_users(conn, name_begins='User_S')[0]
user.alter(password='new_password')

# change user password with option require_new_password
user.alter(password='new_password', require_new_password=True)

# change password for all users with option require_new_password
for user in list_users(conn, name_begins='User_S'):
    user.alter(password='new_password', require_new_password=True)
