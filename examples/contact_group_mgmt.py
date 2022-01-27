"""This is the demo script to show how to manage contact groups.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services import (
    Contact, ContactGroup, ContactGroupMember, ContactGroupMemberType, list_contact_groups
)
from mstrio.users_and_groups import User

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# create contact group with one member represented as an object (it can be more
# and they can be also represented as dictionaries). User linked to the contact
# group can be passed as a `User` object or just its ID.
member1 = ContactGroupMember(
    name='member name',
    type=ContactGroupMemberType.CONTACT,  # it can be also ContactGroupMemberType.CONTACT_GROUP
    id='member_id',
    enabled=True,
)
new_cg = ContactGroup.create(
    connection=conn,
    name='Name of contact group',
    linked_user=User(conn, username='some username'),
    members=[member1],
    description="Description of contact group",
    enabled=True,
)

# list all contact groups
contact_groups = list_contact_groups(conn)

# get contact group by ID. Contact group can be also found by its name
cg = ContactGroup(conn, id=new_cg.id)
cg_by_name = ContactGroup(conn, name='Name of contact group')

# get properties of contact group
cg_name = cg.name
cg_description = cg.description
cg_lined_user = cg.linked_user
cg_members = cg.members
cg_enabled = cg.enabled

# alter contact group
cg.alter(
    name='New name of contact group',
    description='New description of contact group',
    linked_user=User(conn, username='other username'),
    enabled=False,
)

# add members to contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
contact = Contact(conn, name='contact name')
cg.add_members(members=[contact])  # add contact
cg.add_members(members=[new_cg])  # add contact group

# remove members from contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
contact_group = ContactGroup(conn, name='contact group name')
cg.remove_members(members=[contact])  # remove contact
cg.remove_members(members=[contact_group])  # remove contact group

# Delete contact group. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
cg.delete(force=True)
