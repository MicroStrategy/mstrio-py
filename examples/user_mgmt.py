"""This is the demo script to show how administrator can manage users and
user groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
import csv

from mstrio.connection import Connection
from mstrio.users_and_groups import (
    create_users_from_csv, list_user_groups, list_users, User, UserGroup
)


base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# create multiple users
users_array = [{
    'username': 'jwilliams',
    'fullName': 'John Williams'
}, {
    'username': 'mjones',
    'fullName': 'Mark Jones'
}, {
    'username': 'sbrown',
    'fullName': 'Steve Brown'
}, {
    'username': 'jdavis',
    'fullName': 'James Davis'
}, {
    'username': 'twilson',
    'fullName': 'Thomas Wilson'
}]
for u in users_array:
    User.create(connection=conn, username=u['username'], full_name=u['fullName'])

# Also, you can create users from a CSV file
newly_created_users = create_users_from_csv(connection=conn, csv_file="path/to/file.csv")

# Or you can do it manually
with open("path/to/file.csv", "r") as f:
    users = csv.DictReader(f)

    for user in users:
        User.create(connection=conn, username=user['username'], full_name=user['full_name'])

# create a single user and get users which name begins with "John" and have
# additional filter for initials
User.create(connection=conn, username="jsmith", full_name="John Smith")
my_users = list_users(connection=conn, name_begins="John", initials="JS")

# get all user groups (you can also add additional filters as for users) and
# create a new one
user_groups_list = list_user_groups(connection=conn)
UserGroup.create(connection=conn, name="Special Users")

# get user, user group and add this user to this user group
user_ = User(connection=conn, name="John Smith")
user_group_ = UserGroup(connection=conn, name="Special Users")
user_group_.add_users(users=[user_.id])

# set custom permissions of the user for given objects
user_.set_custom_permissions(to_objects=['55AA293811EAE2F2EC7D0080EF25A592'], object_type=3,
                             execute='grant', use='deny', control='default', delete='grant',
                             write='deny', read='default', browse='grant')

# set permission of the user group for given objects
user_group_.set_permission(permission='Full Control',
                           to_objects=['55AA293811EAE2F2EC7D0080EF25A592'], object_type=3)

# delete a user and a user group
user_.delete()
user_group_.delete()


# Addresses
user_john = User(connection=conn, name="John Smith")
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
