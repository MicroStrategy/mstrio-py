"""This is the demo script to show how administrator can manage contacts
 and contact addresses.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import (
    Contact, ContactAddress, ContactDeliveryType, ContactGroup, Device, list_contacts
)
from mstrio.users_and_groups import User
from mstrio.connection import get_connection

PROJECT_NAME='<Project_name>' # Insert project name here
CONTACT_ID='<Contact_ID>' # Insert your contact ID here
CONTACT_NAME='<Contact_name>' # Insert your contact name here
CONTACT_ADDRESS_NAME = '<Contact_adress_name>' # Insert your contact address name here
PHYSICAL_ADDRESS = '<Adress>' # Insert physical address of created contact here
DEVICE_ID = '<Device_ID>' #Insert device used for contact here
NEW_CONTACT_NAME = '<Contact_name>' # Insert new contact name here
CONTACT_DESCRIPTION = '<Contact_desc>' #Insert  description for new contact here
CONTACT_NEW_DESCRIPTION = '<Contact_desc>' #Insert new description for contact here

USER_NAME= '<Username>' # Insert name of user to link to the contact
NEW_CONTACT_DESCRIPTION = '<Contact_desc>' # Description of newly created contact 

CONTACT_GROUP_NAME = '<Contact_group_name>' # Insert name of contact group here


conn = get_connection(workstationData, project_name=PROJECT_NAME)

contacts = list_contacts(conn)

# get limited number of contacts
contacts = list_contacts(conn, limit=1)

# get contact by id
contact = Contact(conn, id=CONTACT_ID)

# get contact by name
contact = Contact(conn, name=CONTACT_NAME)

# create contact address by providing device object
contact_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    # the ContactDeliveryType values can be found in distribution_services/contact/contact.py
    delivery_type=ContactDeliveryType.EMAIL,
    device=Device(conn, id=DEVICE_ID),
    is_default=True
)

# create contact address by providing device id
contact_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    # the ContactDeliveryType values can be found in distribution_services/contact/contact.py
    delivery_type=ContactDeliveryType.EMAIL,
    device=DEVICE_ID,
    is_default=True,
    connection=conn
)

# create contact
new_contact = Contact.create(
    connection=conn,
    name=CONTACT_NAME,
    linked_user=User(conn, name=USER_NAME),
    description=CONTACT_DESCRIPTION,
    enabled=True,
    contact_addresses=[contact_address]
)

# list properties for contact
contact.list_properties()

# alter contact
contact.alter(name=NEW_CONTACT_NAME)
contact.alter(description=CONTACT_NEW_DESCRIPTION)


# add new contact address to contact:
# 1. create a contact address
new_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    # the ContactDeliveryType values can be found in distribution_services/contact/contact.py
    delivery_type=ContactDeliveryType.EMAIL,
    device=DEVICE_ID,
    connection=conn
)
# 2. create new list of contact addresses
# combining list of existing contact addresses with a new one
new_address_list = contact.contact_addresses + [new_address]
# 3. update contact with a new list of contact addresses
contact.alter(contact_addresses=new_address_list)


# get contact group
contact_group = ContactGroup(conn, name=CONTACT_GROUP_NAME)

# add contact to contact group
contact.add_to_contact_group(contact_group)

# remove contact from contact group
contact.remove_from_contact_group(contact_group)

# delete contact without a prompt
contact.delete(force=True)
