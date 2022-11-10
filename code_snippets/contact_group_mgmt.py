"""This is the demo script to show how to manage contact groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

# create contact group with one member represented as an object (it can be more
# and they can be also represented as dictionaries). User linked to the contact
# group can be passed as a `User` object or just its ID.

from mstrio.connection import get_connection
from mstrio.users_and_groups import (
    Contact, ContactGroup, ContactGroupMember, ContactGroupMemberType, list_contact_groups, User
)

PROJECT_NAME = $project_name  # Insert project name here
MEMBER_NAME = $member_name  # here insert member name
MEMBER_ID = $member_id  # Insert member ID
USERNAME = $username  # name of user to link to the contact group
CONTACT_GROUP_NAME = $contact_group_name  # Name of contact group
CONTACT_GROUP_DESCRIPTION = $contact_group_description  # Description of newly created contact group
CONTACT_GROUP_ID = $contact_group_id  # Insert your contact group ID here
CONTACT_GROUP_NEW_NAME = $contact_group_new_name  # Insert new name of contact group
CONTACT_GROUP_NEW_DESCRIPTION = $contact_group_new_description  # Insert new description of contact group
OTHER_USERNAME = $other_username  # Insert new user for contact group
CONTACT_NAME = $contact_name  # Insert contact name here
OTHER_CONTACT_GROUP_NAME = $other_contact_group_name  # Insert name of another contact group here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

member1 = ContactGroupMember(
    name=MEMBER_NAME,
    type=ContactGroupMemberType.CONTACT,  # it can be also ContactGroupMemberType.CONTACT_GROUP
    id=MEMBER_ID,
    enabled=True,
)
new_cg = ContactGroup.create(
    connection=conn,
    name=CONTACT_GROUP_NAME,
    linked_user=User(conn, username=USERNAME),
    members=[member1],
    description=CONTACT_GROUP_DESCRIPTION,
    enabled=True,
)

# list all contact groups
contact_groups = list_contact_groups(conn)

# get contact group by ID. Contact group can be also found by its name
cg = ContactGroup(conn, id=CONTACT_GROUP_ID)
cg_by_name = ContactGroup(conn, name=CONTACT_GROUP_NAME)

# get properties of contact group
cg_name = cg.name
cg_description = cg.description
cg_lined_user = cg.linked_user
cg_members = cg.members
cg_enabled = cg.enabled

# alter contact group
cg.alter(
    name=CONTACT_GROUP_NEW_NAME,
    description=CONTACT_GROUP_NEW_DESCRIPTION,
    linked_user=User(conn, username=OTHER_USERNAME),
    enabled=False,
)

# add members to contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
contact = Contact(conn, name=CONTACT_NAME)
cg.add_members(members=[contact])  # add contact
cg.add_members(members=[new_cg])  # add contact group

# remove members from contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
contact_group = ContactGroup(conn, name=OTHER_CONTACT_GROUP_NAME)
cg.remove_members(members=[contact])  # remove contact
cg.remove_members(members=[contact_group])  # remove contact group

# Delete contact group. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
cg.delete(force=True)
