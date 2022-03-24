from mstrio.connection import get_connection
from mstrio.distribution_services import (
    Contact, ContactGroup, ContactGroupMember, ContactGroupMemberType, list_contact_groups
)
from mstrio.users_and_groups import User

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# create contact group with one member
member1 = ContactGroupMember(
    name='San Francisco Music Manager',
    type=ContactGroupMemberType.CONTACT,
    id='59CCFDF44EAA434CF3B2059143278064',
    enabled=True,
)
new_cg = ContactGroup.create(
    connection=conn,
    name='Tmp Contact Group',
    linked_user=User(conn, username='mstr'),
    members=[member1],
    description="This is a contact group with name 'Tmp Contact Group'.",
    enabled=True,
)

# list all contact groups
cgs = list_contact_groups(conn)
print(cgs)

# get contact group by id
cg = ContactGroup(conn, id=new_cg.id)
print(cg)

# print name, description, linked_user and members of contact group
print(cg.name)
print(cg.description)
print(cg.linked_user)
print(cg.members)

# alter name, description and linked user of contact group. Enable contact group
# as well
cg.alter(
    name='Tmp Contact Group (altered)',
    description='Contact group was altered',
    linked_user=User(conn, username='Administrator'),
    enabled=False,
)

# print altered properties of contact group
print(cg.name)
print(cg.description)
print(cg.linked_user)
print(cg.enabled)

# add members to contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
contact = Contact(conn, name='San Francisco Movies Manager')
cg.add_members(members=[contact])
print(cg.members)

# remove members from contact group - it can be `ContactGroupMember`, `Contact`
# or `ContactGroup`
cg.remove_members(members=[contact])
print(cg.members)

# delete contact group without prompt
cg.delete(force=True)
