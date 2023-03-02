"""This is the demo script to show how administrator can manage users and
user groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
import csv
from code_snippets.document import USER_ID

from mstrio.users_and_groups import (
    create_users_from_csv, list_user_groups, list_users, User, UserGroup
)

from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

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
NAME_BEGINS = $name_begins  # beginning of the full name to look for in listing users
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

# create a single user with password already defined
User.create(connection=conn, username=USERNAME_7, full_name=FULLNAME_7, password=PASSWORD_7)

# Define a variable which can be later used in a script
USER_GROUP_NAME = $user_group_name  # name of a User Group to create and add users
USER_GROUP_ID = $user_group_id
USER_ID = $user_id

# get all user groups (you can also add additional filters as for users) and
# create a new one
user_groups_list = list_user_groups(connection=conn)
UserGroup.create(connection=conn, name=USER_GROUP_NAME)

# get user by name
user = User(connection=conn, name=FULLNAME_6)
# get user by id
user = User(connection=conn, id=USER_ID)

# get user group by name
user_group = UserGroup(connection=conn, name=USER_GROUP_NAME)
# get user group by id
user_group = UserGroup(connection=conn, id=USER_GROUP_ID)
# add user to user_group
user_group.add_users(users=[user.id])

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

# delete a user and a user group
user.delete()
user_group.delete()

# Addresses
ADDRESS_NAME = $address_name
ADDRESS = $address
user_john = User(connection=conn, name=FULLNAME_6)
# The user's addresses list is lazily loaded upon first accessing the property
johns_addresses = user_john.addresses
# MicroStrategy allows having multiple addresses marked as default
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
