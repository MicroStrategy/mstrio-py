"""This is the demo script to show how to manage privileges and security roles for users and user groups.

In the first part privilege retrieval is presented, and in the second security role operations.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

# Privileges
from mstrio.access_and_security.privilege import Privilege
from mstrio.users_and_groups import list_user_groups, list_users, User, UserGroup
from mstrio.access_and_security.security_role import list_security_roles, SecurityRole
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
PRIVILEGE_NAME = $privilege_name  # Insert name of edited privilege here
PRIVILEGE_ID = $privilege_id  # Insert ID of edited privilege here

# get Privilege object by name
priv = Privilege(conn, name=PRIVILEGE_NAME)
# get Privilege object by id
priv = Privilege(conn, id=PRIVILEGE_ID)

# List Privileges and return objects or display in DataFrame
Privilege.list_privileges(conn, to_dataframe=True, is_project_level_privilege='True')
priv = Privilege.list_privileges(conn, id=[PRIVILEGE_ID])
for p in priv:
    print(p.id)
priv[0].list_properties()

# Define variables which can be later used in a script
USER_NAME = $user_name
USER_GROUP_NAME = $user_group_name
SECURITY_ROLE_NAME = $security_role_name  # Insert name of newly created or accessed security role
SECURITY_ROLE_DESCRIPTION = $security_role_description  # Insert description of newly created or accessed security role
SECURITY_ROLE_ID = $security_role_id
NEW_SECURITY_ROLE_NAME = $new_security_role_name
NEW_SECURITY_ROLE_DESCRIPTION = $new_security_role_description
NEW_SECURITY_ROLE_OWNER = $new_security_role_owner

# SecurityRoles
# List SecurityRoles and store the Objects
all_roles = list_security_roles(conn)
list_security_roles(conn, to_dataframe=True) # If True, return SecurityRoles as pandas DataFrame.
# List SecurityRoles by User
user = User(connection=conn, name=USER_NAME)
print(user.security_roles)
# List SecurityRoles by UserGroup
user_group = UserGroup(connection=conn, name=USER_GROUP_NAME)
print(UserGroup.security_roles)
# Get SecurityRole by name
security_role = SecurityRole(connection=conn, name=SECURITY_ROLE_NAME)
# also you can get SecurityRole by ID
security_role = SecurityRole(connection=conn, id=SECURITY_ROLE_ID)
# Create new SecurityRole
new_role = SecurityRole.create(
    conn,
    name=SECURITY_ROLE_NAME,
    description=SECURITY_ROLE_DESCRIPTION,
    privileges=[PRIVILEGE_ID, PRIVILEGE_NAME]
)
# Initialize SecurityRole object by ID
role = SecurityRole(conn, id=SECURITY_ROLE_ID)
# Initialize SecurityRole by name
role_by_name = SecurityRole(conn, name=SECURITY_ROLE_NAME)

# Alter SecurityRole. Change security role's name, description, or owner
role.alter(
    conn,
    name=NEW_SECURITY_ROLE_NAME,
    description=NEW_SECURITY_ROLE_DESCRIPTION,
    owner=NEW_SECURITY_ROLE_OWNER
)

# List SecurityRole members
role.list_members(project_name=PROJECT_NAME)

# Delete SecurityRole
security_role.delete(force=True) # If True, then no additional prompt will be shown before deleting.

# Define variables which can be later used in a script
USERNAME = $username  # Insert name of user to be assigned or revoked security role
USER_GROUP_NAME = $user_group_name  # Insert name of user group to be assigned or revoked security role

# Grant/Revoke Security Role to users/usergroups
user = User(conn, name=USERNAME)
users = list_users(conn)
group = UserGroup(conn, name=USER_GROUP_NAME)
groups = list_user_groups(conn)

# Grant/Revoke for Users
role.grant_to(members=user, project=PROJECT_NAME)
role.revoke_from(members=user, project=PROJECT_NAME)
role.grant_to(members=users, project=PROJECT_NAME)
role.revoke_from(members=users, project=PROJECT_NAME)

# Grant/Revoke for UserGroups
role.grant_to(members=group, project=PROJECT_NAME)
role.revoke_from(members=group, project=PROJECT_NAME)

# List Privileges
role.list_privileges()
role.list_privileges(to_dataframe=True)

# Grant/ Revoke privileges to Security Role
role.grant_privilege(privilege=[PRIVILEGE_ID])
role.revoke_privilege([PRIVILEGE_ID])
privs = list(role.list_privileges().keys())
role.revoke_all_privileges()
role.grant_privilege(privilege=privs)
