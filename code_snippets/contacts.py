"""This is the demo script to show how administrator can manage contacts
 and contact addresses.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.distribution_services import Device
from mstrio.users_and_groups import (
    Contact, ContactAddress, ContactDeliveryType, ContactGroup, list_contacts, User
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# get list of all contacts
contacts = list_contacts(conn)

# get limited number of contacts
contacts = list_contacts(conn, limit=1)

# Define variables which can be later used in a script
CONTACT_ID = $contact_id  # Insert your contact ID here
CONTACT_NAME = $contact_name  # Insert your contact name here

# get contact by id
contact = Contact(conn, id=CONTACT_ID)

# get contact by name
contact = Contact(conn, name=CONTACT_NAME)

# Define variables which can be later used in a script
CONTACT_ADDRESS_NAME = $contact_address_name  # Insert your contact address name here
PHYSICAL_ADDRESS = $physical_address  # Insert physical address of created contact here
DEVICE_ID = $device_id  # Insert device used for contact here
CONTACT_DESCRIPTION = $contact_description  # Insert  description for new contact here
USERNAME = $username  # Insert name of user to link to the contact

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
    linked_user=User(conn, name=USERNAME),
    description=CONTACT_DESCRIPTION,
    enabled=True,
    contact_addresses=[contact_address] # list of `ContactAddress` objects
)

# list properties for contact
contact.list_properties()

# Define variables which can be later used in a script
NEW_CONTACT_NAME = $new_contact_name  # Insert new contact name here
CONTACT_NEW_DESCRIPTION = $contact_new_description  #Insert new description for contact here

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

# Define a variable which can be later used in a script
CONTACT_GROUP_NAME = $contact_group_name  # Insert name of contact group here

# get contact group
contact_group = ContactGroup(conn, name=CONTACT_GROUP_NAME)

# add contact to contact group
contact.add_to_contact_group(contact_group)

# remove contact from contact group
contact.remove_from_contact_group(contact_group)

# delete contact without a prompt
contact.delete(force=True)
