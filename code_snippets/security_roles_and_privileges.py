# Privileges
from mstrio.access_and_security.privilege import Privilege
from mstrio.users_and_groups import list_user_groups, list_users, User, UserGroup
from mstrio.access_and_security.security_role import list_security_roles, SecurityRole
from mstrio.connection import get_connection

PROJECT_NAME = '<Project_name>' # Insert name of project here
PRIVILEGE_NAME = '<Privilege_name>' # Insert name of edited privilege here
PRIVILEGE_ID = '<Privilege_ID>' # Insert ID of edited privilege here
# Following strings are for Security Roles edition
SECURITY_ROLE_NAME = '<Security_Role_name>' # Insert name of newly created or accesed security role
SECURITY_ROLE_DESCRIPTION = '<Security_Role_desc>' # Insert description of newly created or accesed security role
USER_NAME = '<Username>' # Insert name of user to be assigned or revoked security role
USER_GROUP_NAME ='<User_group_name>' # Insert name of user group to be assigned or revoked security role

conn = get_connection(workstationData, project_name=PROJECT_NAME)


# Create Privilege object by name or ID
priv = Privilege(conn, name=PRIVILEGE_NAME)
priv = Privilege(conn, id=PRIVILEGE_ID)

# List Privileges and return objects or display in DataFrame
Privilege.list_privileges(conn, to_dataframe=True, is_project_level_privilege='True')
priv = Privilege.list_privileges(conn,id=[PRIVILEGE_ID])
for p in priv:
    print(p.id)
priv[0].list_properties()


# SecurityRoles
# Create new SecurityRole
new_role = SecurityRole.create(conn,
 name=SECURITY_ROLE_NAME,
 description=SECURITY_ROLE_DESCRIPTION,
 privileges=[PRIVILEGE_ID, PRIVILEGE_NAME])

# List SecurityRoles and store the Objects
all_roles = list_security_roles(conn)
list_security_roles(conn, to_dataframe=True)

# Create SecurityRole object by name or ID
role = SecurityRole(conn, id=all_roles[0].id)
SecurityRole(conn, id=all_roles[0].id)
role = SecurityRole(conn, name=all_roles[0].name)
SecurityRole(conn, name=all_roles[0].name)
SecurityRole(connection=conn, name=SECURITY_ROLE_NAME)

# List SecurityRole members
role.list_members(project_name=PROJECT_NAME)

# Grant/Revoke Security Role to users/usergroups
user = User(conn, name=USER_NAME)
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
