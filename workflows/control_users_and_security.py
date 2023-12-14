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
