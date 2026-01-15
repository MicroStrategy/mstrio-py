"""This is the demo script to show how administrator can manage users and
user groups.

User management is showcased in the first part of the snippet and user group management in the second.
Additionally, the final section explains alternative method for user authentication and how to manage user's addresses.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
import csv
from mstrio.connection import get_connection
from mstrio.access_and_security import Privilege, PrivilegeMode
from mstrio.users_and_groups import (
    create_users_from_csv, list_user_groups, list_users, User, UserGroup
)

# User management
# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to
PROJECT_ID = $project_id # Project id to connect to
NAME_BEGINS = $name_begins # Beginning of the full name to look for in listing users
ABBREVIATION_BEGINS = $abbreviation_begins # Beginning of the user abbreviation
USERNAME_0 = $username_0
FULLNAME_0 = $fullname_0
USER_ID_0 = $user_id_0
USER_ID_1 = $user_id_1
USER_ID_2 = $user_id_2
OWNER_1 = $owner_name

# Create connection based on workstation data
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# List users
list_users(
    connection=conn,
    name_begins=NAME_BEGINS,
    abbreviation_begins=ABBREVIATION_BEGINS,
    to_dictionary=False, # If True returns dict, by default (False) returns User objects.
    id=[USER_ID_1, USER_ID_2],  # Different filtering methods are available in the docstring.
)
# Get user by name
user = User(connection=conn, name=USERNAME_0)
# Get user by username
user = User(connection=conn, username=FULLNAME_0)
# Get user by id
user = User(connection=conn, id=USER_ID_0)

# List user properties
user_properties = user.list_properties()
print(user_properties)
# List user privileges
user.list_privileges(mode=PrivilegeMode.ALL, to_dataframe=False) # If True, return a DataFrame object containing privileges.
user.list_privileges(mode=PrivilegeMode.INHERITED, to_dataframe=True)

# Define variables which can be later used in a script
USERNAME_1 = $username_1
FULLNAME_1 = $full_name_1
USERNAME_2 = $username_2
FULLNAME_2 = $full_name_2
USERNAME_3 = $username_3
FULLNAME_3 = $full_name_3
USERNAME_4 = $username_4
FULLNAME_4 = $full_name_4
USERNAME_5 = $username_5
FULLNAME_5 = $full_name_5

# Note: To create user with no password you must set minimum password length as
# 0 in environment security settings
# create multiple users
users_array = [
    {
        'username': USERNAME_1, 'fullName': FULLNAME_1
    }, {
        'username': USERNAME_2, 'fullName': FULLNAME_2
    }, {
        'username': USERNAME_3, 'fullName': FULLNAME_3
    }, {
        'username': USERNAME_4, 'fullName': FULLNAME_4
    }, {
        'username': USERNAME_5, 'fullName': FULLNAME_5
    }
]
for u in users_array:
    User.create(connection=conn, username=u['username'], full_name=u['fullName'])

# Define a variable which can be later used in a script
CSV_FILE = $csv_file  # csv file to create user from

# Also, you can create users from a CSV file
newly_created_users = create_users_from_csv(connection=conn, csv_file=CSV_FILE)

# Note: To create user with no password you must set minimum password length as
# 0 in environment security settings
# Or you can do it manually
with open(CSV_FILE, "r") as f:
    users = csv.DictReader(f)

    for user in users:
        User.create(connection=conn, username=user['username'], full_name=user['full_name'])

# Define variables which can be later used in a script
USERNAME_6 = $username_6
FULLNAME_6 = $full_name_6
INITIALS = $initials # initials to look for in listing users

# Note: To create user with no password you must set minimum password length as
# 0 in environment security settings
# create a single user without password and get users which name begins with
# "John" and have additional filter for initials
User.create(connection=conn, username=USERNAME_6, full_name=FULLNAME_6)
my_users = list_users(connection=conn, name_begins=NAME_BEGINS, initials=INITIALS)

# Define variables which can be later used in a script
USERNAME_7 = $username_7
FULLNAME_7 = $full_name_7
PASSWORD_7 = $password_7
PRIVILEGE_NAME = $privilege_name
PRIVILEGE_ID = $privilege_id
FOLDER_ID = $folder_id
DESTINATION_FOLDER_PATH = $destination_folder_path
NEW_USERNAME = $new_username
NEW_LANGUAGE = $new_language
NEW_DEFAULT_TIMEZONE = $new_default_timezone
NEW_COMMENTS = $new_comments_for_user_object

# Create a single user with password already defined
user = User.create(connection=conn, username=USERNAME_7, full_name=FULLNAME_7, password=PASSWORD_7)
# Create profile folder for user
user.create_profile_folder(
    destination_folder=FOLDER_ID, # Folder class instance or ID as string, name as string or path as string specifying the folder where to create object can be provided.
    project=PROJECT_ID # It can be Project class instance or ID as string or name as string.
)

# Alter single user properties, for example change username, language and default timezone along with comment.
user.alter(
    username=NEW_USERNAME,
    language=NEW_LANGUAGE,
    default_timezone=NEW_DEFAULT_TIMEZONE,
    comments=NEW_COMMENTS
)
# List all possible privileges
all_privileges = Privilege.list_privileges(conn)
# Get Privilege object by name
priv = Privilege(conn, name=PRIVILEGE_NAME)
# Get Privilege object by id
priv = Privilege(conn, id=PRIVILEGE_ID)
# Grant privilege to user
user.grant_privilege(priv)
# Grant multiple privileges to user
user.grant_privilege([PRIVILEGE_ID, PRIVILEGE_NAME])
# Revoke privilege from user
user.revoke_privilege(PRIVILEGE_ID)
# Revoke multiple privileges from user
user.revoke_privilege([PRIVILEGE_ID, PRIVILEGE_NAME])

# Delete single user
user.delete(force=True, delete_profile=True)  # If delete profile is set to True, User's profile folder will be deleted as well.

# User Group Management
# Define a variable which can be later used in a script
USER_GROUP_NAME = $user_group_name  # name of a User Group to create and add users
USER_GROUP_ID = $user_group_id
USER_GROUP_1 = $user_group_1
USER_GROUP_ID_1 = $user_group_id_1
USER_GROUP_2 = $user_group_2
USER_GROUP_ID_2 = $user_group_id_2
DATE_CREATED = $date_created  # YYYY-MM-DD format
GROUP_NAME = $group_name
GROUP_DESCRIPTION = $group_description
USER_GROUP_LDAPDN = $user_group_ldapdn

# Get user group by name
user_group = UserGroup(connection=conn, name=USER_GROUP_NAME)
# also you can get user group by id
user_group = UserGroup(connection=conn, id=USER_GROUP_ID)
# Get all user groups (you can also add additional filters as for users)
user_groups_list = list_user_groups(
    connection=conn,
    name_begins=GROUP_NAME,
    description=GROUP_DESCRIPTION
)

# Get all members of group (you can also add additional filters as for users/user groups)
user_group.list_members(
    users=[user.id],
    date_created=DATE_CREATED,
)

# Get user group privileges
user_group.list_privileges(
    mode=PrivilegeMode.ALL, # Returns user group's inherited, granted or all privileges
)
# if instead of UserGroup class instance you would like to get object containing privileges, you can use to_dataframe flag
user_group.list_privileges(
    mode=PrivilegeMode.ALL,
    to_dataframe=False # # If True, return a DataFrame object containing privileges.
)
# Get user group properties
user_group_properties = user_group.list_properties()
print(user_group_properties)

# Create new user group
user_group = UserGroup.create(
    connection=conn,
    name=USER_GROUP_NAME,
    members=[USER_ID_0, USER_ID_1, USER_ID_2], # Specify members of the group
    ldapdn=USER_GROUP_LDAPDN, # Specify UserGroup ldapdn.
    description=GROUP_DESCRIPTION # Provide UserGroup description.
)
# Add user to user group
user_group.add_users(users=[user.id])
# Grant privilege to user group
user_group.grant_privilege(PRIVILEGE_ID)
# Grant multiple privileges to user group
user_group.grant_privilege([PRIVILEGE_ID, PRIVILEGE_NAME])
# Add user group to already existing groups
user_group.add_to_user_groups(groups=[USER_GROUP_ID_1, USER_GROUP_ID_2])
# also you can provide UserGroup Instances instead of IDs
user_group.add_to_user_groups(
    groups=[
        UserGroup(connection=conn, name=USER_GROUP_1),
        UserGroup(connection=conn, name=USER_GROUP_2),
    ]
)

# Revoke privilege from user group
user_group.revoke_privilege(PRIVILEGE_ID)
# Remove user group from passed groups
user_group.remove_from_user_groups(groups=[USER_GROUP_ID_1, USER_GROUP_ID_2])
# also you can provide UserGroup Instances instead of IDs
user_group.remove_from_user_groups(
    groups=[
        UserGroup(connection=conn, name=USER_GROUP_1),
        UserGroup(connection=conn, name=USER_GROUP_2),
    ]
)
# Delete a user group
user_group.delete(force=True) # If True, then no additional prompt will be shown before deleting.

# To create API Token for a specific user to log in as them
# or provide them alternative way to authenticate, you need a
# "Create and Edit Users and User Groups" privilege
# and you create the API Token by using the below method:
api_token = user.get_api_token()

# Available values for permissions are 'grant', 'deny', 'default' or None
grant_right = 'right'

# Define variables which can be later used in a script
OBJECT_ID = $object_id  # ID of an object to which permissions will be set
OBJECT_TYPE = $object_type  # type of an object to which permissions will be set;
# see ObjectTypes enum in types.py for available object type values

# set custom permissions of the user for given objects
user.set_custom_permissions(
    to_objects=[OBJECT_ID],
    object_type=OBJECT_TYPE,
    execute=grant_right,
    use=grant_right,
    control=grant_right,
    delete=grant_right,
    write=grant_right,
    read=grant_right,
    browse=grant_right
)

# Addresses
ADDRESS_NAME = $address_name
ADDRESS = $address
user_john = User(connection=conn, name=FULLNAME_6)
# The user's addresses list is lazily loaded upon first accessing the property
johns_addresses = user_john.addresses
# Strategy One allows having multiple addresses marked as default
# as long as they are assigned to different device.
# The 'default' argument is automatically set to True.
# Let's add new default address to John.
user_john.add_address(name=ADDRESS_NAME, address=ADDRESS)
# It can also be achieved by setting value of 'default' argument to True.
user_john.add_address(name=ADDRESS_NAME, address=ADDRESS, default=True)
# If the address should not be default, the 'default' should be set to False.
user_john.add_address(name=ADDRESS_NAME, address=ADDRESS, default=False)
# Let's construct a list of John's "default" addresses
johns_default_addresses = [addr for addr in johns_addresses if addr["is_default"]]
# If we just want a single address to treat as default and we're OK with
# it being just the first "default" one we can now just take the first element
# of the list
johns_default_address = johns_default_addresses[0]
# Alternatively if we don't care about any addresses besides the first
# "default one" we can use a generator expression and take its first output
# to avoid going through the entire list, increasing performance
johns_default_address = next((addr for addr in user_john.addresses if addr["is_default"]), None)
# By default, when only ADDRESS_NAME and ADDRESS are provided, an email type
# address is created. It is possible to create more address types by providing
# DEVICE_ID and DELIVERY_TYPE
ADDRESS_NAME = $address_name
ADDRESS = $address
DEVICE_ID = $device_id
DELIVERY_TYPE = $delivery_type
user_john.add_address(
    name=ADDRESS_NAME,
    address=ADDRESS,
    device_id=DEVICE_ID,
    delivery_type=DELIVERY_TYPE
)
# It is possible to make changes to an existing address
ADDRESS_ID = $address_id
NEW_ADDRESS_NAME = $new_address_name
NEW_ADDRESS = $new_address
NEW_DEVICE_ID = $new_device_id
NEW_DELIVERY_TYPE = $new_delivery_type
user_john.update_address(
    id=ADDRESS_ID,
    name=NEW_ADDRESS_NAME,
    address=NEW_ADDRESS,
    device_id=NEW_DEVICE_ID,
    delivery_type=NEW_DELIVERY_TYPE
)
# It is possible to copy address from another user
FULLNAME_8 = $full_name_8
user_with_address = User(connection=conn, name=FULLNAME_8)
user_john.add_address(contact_address=user_with_address.addresses[0])
