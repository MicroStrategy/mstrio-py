"""This is the demo script to show how administrator can manage users and
user groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
import csv

from mstrio.users_and_groups import (
    create_users_from_csv, list_user_groups, list_users, User, UserGroup
)

from mstrio.connection import get_connection

PROJECT_NAME = '<project_name>'  # Project to connect to

# Usernames and full names for users to create
USERNAME_1 = '<username_1>'
FULLNAME_1 = '<full_name_1>'
USERNAME_2 = '<username_2>'
FULLNAME_2 = '<full_name_2>'
USERNAME_3 = '<username_3>'
FULLNAME_3 = '<full_name_3>'
USERNAME_4 = '<username_4>'
FULLNAME_4 = '<full_name_4>'
USERNAME_5 = '<username_5>'
FULLNAME_5 = '<full_name_5>'
USERNAME_6 = '<username_6>'
FULLNAME_6 = '<full_name_6>'

NAME_BEGINS = '<name_begins>'  # beginning of the full name to look for in listing users
INITIALS = '<name_initials>'  # initials to look for in listing users
USERGROUP_NAME = '<usergroup_name>'  # name of a User Group to create and add users
CSV_FILE = '<path_to_csv_file>'  # csv file to create user from
OBJECT_ID = '<object_id>'  # ID of an object to which permissions will be set
OBJECT_TYPE = '<object_type>'  # type of an object to which permissions will be set;
# see ObjectTypes enum in types.py for available object type values
PERMISSION = '<permission_type>'  # type of permission to set;
# see Permissions enum in /utils/acl.py for available permission values

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# create multiple users
users_array = [{
    'username': USERNAME_1,
    'fullName': FULLNAME_1
}, {
    'username': USERNAME_2,
    'fullName': FULLNAME_2
}, {
    'username': USERNAME_3,
    'fullName': FULLNAME_3
}, {
    'username': USERNAME_4,
    'fullName': FULLNAME_4
}, {
    'username': USERNAME_5,
    'fullName': FULLNAME_5
}]
for u in users_array:
    User.create(connection=conn, username=u['username'], full_name=u['fullName'])

# Also, you can create users from a CSV file
newly_created_users = create_users_from_csv(connection=conn, csv_file=CSV_FILE)

# Or you can do it manually
with open(CSV_FILE, "r") as f:
    users = csv.DictReader(f)

    for user in users:
        User.create(connection=conn, username=user['username'], full_name=user['full_name'])

# create a single user and get users which name begins with "John" and have
# additional filter for initials
User.create(connection=conn, username=USERNAME_6, full_name=FULLNAME_6)
my_users = list_users(connection=conn, name_begins=NAME_BEGINS, initials=INITIALS)

# get all user groups (you can also add additional filters as for users) and
# create a new one
user_groups_list = list_user_groups(connection=conn)
UserGroup.create(connection=conn, name=USERGROUP_NAME)

# get user, user group and add this user to this user group
user_ = User(connection=conn, name=FULLNAME_6)
user_group_ = UserGroup(connection=conn, name=USERGROUP_NAME)
user_group_.add_users(users=[user_.id])

# set custom permissions of the user for given objects
user_.set_custom_permissions(
    to_objects=[OBJECT_ID],
    object_type=OBJECT_TYPE,
    execute='<permission>',  # Available values for permissions are 'grant', 'deny', 'default' or None
    use='<permission>',
    control='<permission>',
    delete='<permission>',
    write='<permission>',
    read='<permission>',
    browse='<permission>')

# set permission of the user group for given objects
user_group_.set_permission(permission=PERMISSION,
                           to_objects=[OBJECT_ID], object_type=OBJECT_TYPE)

# delete a user and a user group
user_.delete()
user_group_.delete()


# Addresses
user_john = User(connection=conn, name=FULLNAME_6)
# The user's addresses list is lazily loaded upon first accessing the property
johns_addresses = user_john.addresses
# MicroStrategy allows having multiple addresses marked as default
# so let's construct a list of John's "default" addresses
johns_default_addresses = [addr for addr in johns_addresses if addr["is_default"]]
# If we just want a single address to treat as default and we're OK with
# it being just the first "default" one we can now just take the first element
# of the list
johns_default_address = johns_default_addresses[0]
# Alternatively if we don't care about any addresses besides the first
# "default one" we can use a generator expression and take its first output
# to avoid going through the entire list, increasing performance
johns_default_address = next((addr for addr in user_john.addresses if addr["is_default"]), None)
