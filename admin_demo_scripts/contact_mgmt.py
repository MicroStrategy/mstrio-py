from mstrio.connection import get_connection
from mstrio.distribution_services.contact import (
    Contact, ContactAddress, ContactDeliveryType, list_contacts
)
from mstrio.distribution_services.contact_group import ContactGroup
from mstrio.distribution_services.device import (
    Device, DeviceType, EmailDeviceProperties, EmailFormat, EmailSmartHostSettings,
)
from mstrio.distribution_services.transmitter import (
    EmailTransmitterProperties, RecipientFieldType, Transmitter, TransmitterDeliveryType
)

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# get list of contacts
contacts = list_contacts(conn)
print(contacts)

# create email transmitter properties object
etp = EmailTransmitterProperties(
    sender_display_name='MicroStrategy Distribution Services',
    sender_email_address='DistributionServices@MicroStrategy.com',
    reply_to_display_name='MicroStrategy Distribution Services',
    reply_to_email_address='DistributionServices@MicroStrategy.com',
    recipient_field_type=RecipientFieldType.TO,
    save_message_to_file=False,
    send_message_to_file=False,
    send_message_via_smtp=False,
    save_file_path=None,
    notify_on_success=False,
    notify_on_failure=False,
    notification_email_address=None,
)

# create a transmitter with delivery type as `email`
transmitter = Transmitter.create(
    connection=conn,
    name='Temporary Test Transmitter Name',
    delivery_type=TransmitterDeliveryType.EMAIL,
    description="Description of new transmitter",
    email_transmitter_properties=etp,
)

print(transmitter)

smart_host_settings = EmailSmartHostSettings(server='server.com', port=22)
email_device_properties = EmailDeviceProperties(
    format=EmailFormat.UU_ENCODED,
    smart_host_settings=smart_host_settings,
)

# create device
device = Device.create(
    conn,
    name='Temporary Test device name',
    description='test device description',
    device_type=DeviceType.EMAIL,
    transmitter=transmitter,
    device_properties=email_device_properties
)

print(device)

# create contact address
contact_address = ContactAddress(
    name='Contact Address Name',
    physical_address='example@example.com',
    is_default=True,
    delivery_type=ContactDeliveryType.EMAIL,
    device=device
)

# create contact
new_contact = Contact.create(
    conn,
    name='Temporary Test Contact name',
    description='New Test description',
    enabled=True,
    linked_user=conn.user_id,
    contact_addresses=[contact_address]
)

# get contact by id
contact = Contact(conn, id=new_contact.id)
print(contact)

# print properties
print(contact.id)
print(contact.name)
print(contact.enabled)
print(contact.description)
print(contact.linked_user)
print(contact.contact_addresses)
print(contact.memberships)

# change contact name
new_name = contact.name + ' altered'
new_description = contact.description + ' altered'
contact.alter(name=new_name, description=new_description)

# get contact by id
contact = Contact(conn, id=new_contact.id)
print(contact)

# print properties after changing some of them
print(contact.id)
print(contact.name)
print(contact.enabled)
print(contact.description)
print(contact.linked_user)
print(contact.contact_addresses)
print(contact.memberships)

# create contact group
group = ContactGroup.create(
    conn,
    name='Temporary Test Contact Group Name',
    description='contact group description',
    enabled=True,
    linked_user=conn.user_id,
    members=[]
)

# add contact to a group
contact.add_to_contact_group(group)

# get contact by id
contact = Contact(conn, id=new_contact.id)
print(contact.memberships)

# get contact by id
contact = Contact(conn, id=new_contact.id)
print(contact.memberships)

# delete
group.delete(force=True)
contact.delete(force=True)
device.delete(force=True)
transmitter.delete(force=True)
