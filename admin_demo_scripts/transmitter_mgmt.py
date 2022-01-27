from mstrio.connection import get_connection
from mstrio.distribution_services import (
    EmailTransmitterProperties, list_transmitters, RecipientFieldType, Transmitter,
    TransmitterDeliveryType
)

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

DISPLAY_NAME = 'MicroStrategy Distribution Services'
EMAIL_ADDRESS = 'DistributionServices@MicroStrategy.com'

# create email transmitter properties object
# which is used when creating transmitter
etp = EmailTransmitterProperties(
    sender_display_name=DISPLAY_NAME,
    sender_email_address=EMAIL_ADDRESS,
    reply_to_display_name=DISPLAY_NAME,
    reply_to_email_address=EMAIL_ADDRESS,
    recipient_field_type=RecipientFieldType.TO,
    save_message_to_file=False,
    send_message_to_file=False,
    send_message_via_smtp=False,
    save_file_path=None,
    notify_on_success=False,
    notify_on_failure=False,
    notification_email_address=None,
)

# get list of transmitters
print(list_transmitters(conn))

# create a transmitter with delivery type as `email` (when type is `email` then
# it is mandatory to provide `email_transmitter_properties`)
new_t = Transmitter.create(
    connection=conn,
    name='Tmp Transmitter Name',
    delivery_type=TransmitterDeliveryType.EMAIL,
    description="Description of new transmitter",
    email_transmitter_properties=etp,
)

# get transmitter by id
t = Transmitter(conn, id=new_t.id)
print(t)

# print name, description and properties of email transmitter
print(t.name)
print(t.description)
print(t.email_transmitter_properties.to_dict())

# alter email transmitter and its properties
etp.notify_on_success = True
etp.notify_on_failure = True
etp.notification_email_address = EMAIL_ADDRESS
t.alter(
    name='Tmp Transmitter Name (altered)',
    description='Transmitter was altered',
    email_transmitter_properties=etp,
)

# print name, description and properties of email transmitter after altering
print(t.name)
print(t.description)
print(t.email_transmitter_properties.to_dict())

# delete transmitter without prompt
t.delete(force=True)
