"""This is the demo script to show how to manage contact groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

# create contact group with one member represented as an object (it can be more
# and they can be also represented as dictionaries). User linked to the contact
# group can be passed as a `User` object or just its ID.

from mstrio.distribution_services import (
    ContactGroup, ContactGroupMember, ContactGroupMemberType
)
from mstrio.users_and_groups import User
from mstrio.connection import get_connection
from production.mstrio.distribution_services.contact.contact import Contact
from production.mstrio.distribution_services.contact_group.contact_group import list_contact_groups

PROJECT_NAME = '<Project_name>' # Insert project name here
MEMBER_NAME = '<Username>' # here insert member name
MEMBER_ID = '<Member_ID>'# Insert member ID
USER_NAME = '<Username>' # name of user to link to the contact group
CONTACT_GROUP_NAME = '<Contact_group_name>' # Name of contact group
CONTACT_GROUP_DESCRIPTION = '<Contact_group_desc>' # Description of newly created contact group
CONTACT_GROUP_ID = '<Contact_group_ID>' # Insert your contact group ID here
CONTACT_GROUP_NEW_NAME = '<Contact_group_name>' # Insert new name of contact group
CONTACT_GROUP_NEW_DESCRIPTION = '<Contact_group_desc>' # Insert new description of contact group
OTHER_USER_NAME = '<Username>' # Insert new user for contact group
CONTACT_NAME = '<Contact_name>' # Insert contact name here
OTHER_CONTACT_GROUP_NAME = '<Contact_group_name>' # Insert name of another contact group here


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
    linked_user=User(conn, username=USER_NAME),
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
    linked_user=User(conn, username=OTHER_USER_NAME),
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
