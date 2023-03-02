"""This is the demo script to show how to manage transmitters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.distribution_services import (
    EmailTransmitterProperties,
    list_transmitters,
    RecipientFieldType,
    Transmitter,
    TransmitterDeliveryType
)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
SENDER_DISPLAY_NAME = $sender_display_name  # name of a sender
SENDER_EMAIL_ADDRESS = $sender_email_address  # address of a sender
REPLY_TO_DISPLAY_NAME = $reply_to_display_name  # name for destination for replies
REPLY_TO_EMAIL_ADDRESS = $reply_to_email_address  # address for destination for replies

# get list of transmitters
transmitters = list_transmitters(conn)

# Define variables which can be later used in a script
TRANSMITTER_ID = $transmitter_id
TRANSMITTER_NAME = $transmitter_name

# get transmitter by id
transmitter = Transmitter(conn, id=TRANSMITTER_ID)

# get transmitter by name
transmitter = Transmitter(conn, name=TRANSMITTER_NAME)

# list properties for transmitter
transmitter.list_properties()

# create email transmitter properties object
# which is used when creating transmitter
etp = EmailTransmitterProperties(
    sender_display_name=SENDER_DISPLAY_NAME,
    sender_email_address=SENDER_EMAIL_ADDRESS,
    reply_to_display_name=REPLY_TO_DISPLAY_NAME,
    reply_to_email_address=REPLY_TO_EMAIL_ADDRESS,
    # see distribution_services/transmitter/transmitter.py - RecipientFieldType
    # for available values
    recipient_field_type=RecipientFieldType.TO,
    save_message_to_file=False,
    send_message_to_file=False,
    send_message_via_smtp=False,
    save_file_path=None,
    notify_on_success=False,
    notify_on_failure=False,
    notification_email_address=None,
)

# Define variables which can be later used in a script
TRANSMITTER_DESCRIPTION = $transmitter_description
NOTIFICATION_EMAIL_ADDRESS = $notification_email_address

# create a transmitter with delivery type as `email` (when type is `email` then
# it is mandatory to provide `email_transmitter_properties`). Delivery type
# can be also passed as a string and `email_transmitter_properties` can be
# passed as a dictionary
new_t = Transmitter.create(
    connection=conn,
    name=TRANSMITTER_NAME,
    delivery_type=TransmitterDeliveryType.EMAIL,
    description=TRANSMITTER_DESCRIPTION,
    email_transmitter_properties=etp,
)

# alter email transmitter and its properties
etp.notify_on_success = True
etp.notify_on_failure = True
etp.notification_email_address = NOTIFICATION_EMAIL_ADDRESS
etp.save_message_to_file = True
new_t.alter(
    name=TRANSMITTER_NAME,
    description=TRANSMITTER_DESCRIPTION,
    email_transmitter_properties=etp,
)

# create file transmitter
new_file_t = Transmitter.create(
    connection=conn,
    name=TRANSMITTER_NAME,
    delivery_type=TransmitterDeliveryType.FILE,
    description=TRANSMITTER_DESCRIPTION,
)

# Define variables which can be later used in a script
TRANSMITTER_NEW_NAME = $transmitter_new_name
TRANSMITTER_NEW_DESCRIPTION = $transmitter_new_description

# alter file transmitter
new_file_t.alter(name=TRANSMITTER_NEW_NAME, description=TRANSMITTER_NEW_DESCRIPTION)

# create ipad transmitter
new_ipad_t = Transmitter.create(
    connection=conn,
    name=TRANSMITTER_NAME,
    delivery_type=TransmitterDeliveryType.IPAD,
    description=TRANSMITTER_DESCRIPTION,
)

# alter ipad transmitter
new_ipad_t.alter(name=TRANSMITTER_NEW_NAME, description=TRANSMITTER_NEW_DESCRIPTION)

# create iphone transmitter
new_iphone_t = Transmitter.create(
    connection=conn,
    name=TRANSMITTER_NAME,
    delivery_type=TransmitterDeliveryType.IPHONE,
    description=TRANSMITTER_DESCRIPTION,
)

# alter iphone transmitter
new_iphone_t.alter(name=TRANSMITTER_NEW_NAME, description=TRANSMITTER_NEW_DESCRIPTION)

# create print transmitter
new_print_t = Transmitter.create(
    connection=conn,
    name=TRANSMITTER_NAME,
    delivery_type=TransmitterDeliveryType.PRINT,
    description=TRANSMITTER_DESCRIPTION,
)

# alter print transmitter
new_print_t.alter(name=TRANSMITTER_NEW_NAME, description=TRANSMITTER_NEW_DESCRIPTION)

# Delete transmitter. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
transmitter.delete(force=True)
