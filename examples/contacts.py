"""This is the demo script to show how administrator can manage contacts
 and contact addresses.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services.contact import (
    Contact, ContactAddress,ContactDeliveryType, list_contacts
)
from mstrio.distribution_services.contact_group import ContactGroup
from mstrio.distribution_services.device import Device
from mstrio.users_and_groups.user import User


base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

CONTACT_ADDRESS_NAME = 'Contact address name'
PHYSICAL_ADDRESS = 'physical address'

# get list of contacts
contacts = list_contacts(conn)

# get limited number of contacts
contacts = list_contacts(conn, limit=1)

# get contact by id
contact = Contact(conn, id='contact_id')

# get contact by name
contact = Contact(conn, name='contact_name')

# create contact address by providing device object
contact_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    delivery_type=ContactDeliveryType.EMAIL,
    device=Device(conn, id='device_id'),
    is_default=True
)

# create contact address by providing device id
contact_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    delivery_type=ContactDeliveryType.EMAIL,
    device='device_id',
    is_default=True,
    connection=conn
)

# create contact
new_contact = Contact.create(
    connection=conn,
    name="Contact's name",
    linked_user=User(conn, id='user_id'),
    description="Contact's description",
    enabled=True,
    contact_addresses=[contact_address]
)

# list properties for contact
contact.list_properties()

# alter contact
contact.alter(name='new name')
contact.alter(description='new description')


# add new contact address to contact:

# 1. create a contact address
new_address = ContactAddress(
    name=CONTACT_ADDRESS_NAME,
    physical_address=PHYSICAL_ADDRESS,
    delivery_type=ContactDeliveryType.EMAIL,
    device='device_id',
    is_default=True,
    connection=conn
)

# 2. create new list of contact addresses
# combining list of existing contact addresses with a new one
new_address_list = contact.contact_addresses + [new_address]

# 3. update contact with a new list of contact addresses
contact.alter(contact_addresses=new_address_list)


# get contact group
contact_group = ContactGroup(conn, id='contact_group_id')

# add contact to contact group
contact.add_to_contact_group(contact_group)

# remove contact from contact group
contact.remove_from_contact_group(contact_group)

# delete contact with a Y/N prompt
contact.delete()

# delete contact without a prompt
contact.delete(force=True)
