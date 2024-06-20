"""
Import user or user group from csv.
Automate administrative tasks such as resetting password, assigning security
filters.

1. Connect to the environment using data from workstation
2. Create users from CSV file
3. Get first user group from the list of user groups
4. Set view access to the user group for all users created from CSV file
5. Reset password for all newly created users and make sure they have to change
   it at the next login
6. Import user group structure from CSV file
7. Apply security filter with name 'security_filter' to the user group with name
   'AI Users'
"""

import csv
from mstrio.connection import get_connection
from mstrio.helpers import AggregatedRights
from mstrio.modeling.security_filter.security_filter import list_security_filters
from mstrio.users_and_groups.user import User, create_users_from_csv
from mstrio.users_and_groups.user_group import UserGroup, list_user_groups

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# set correct user group access in tree view for user groups
# assumptions about CSV - csv is created from User.to_csv_from_list with at least
# two columns: username and full_name
user_list = create_users_from_csv(conn, 'users.csv')
user_group = list_user_groups(conn)[0]
user_group.acl_add(
    right=AggregatedRights.VIEW,
    trustees=user_list,
    denied=False,
    inheritable=True,
    propagate_to_children=True,
)

# reset the password for those users and check-in the option
# "User must change password at the next login"
for user in user_list:
    user.alter(password='new_password', require_new_password=True)

# import user group structure from CSV file
# assumptions - you have a prepared list CSV of two columns:
# user_name , user_group_name with headers added
with open('tree_structure.csv', encoding='utf-8') as structure:
    user_rows = csv.DictReader(structure)
    for row in user_rows:
        user_name = row['user_name']
        user_group_name = row['user_group_name']
        user = User(conn, name=user_name)
        user_group = UserGroup(conn, name=user_group_name)
        user_group.add_users(user)

# assigning correct security filter (the same name) for the user group
user_group = UserGroup(conn, name='AI Users')
security_filter = list_security_filters(conn, name='security_filter')[0]
user_group.apply_security_filter(security_filter)
