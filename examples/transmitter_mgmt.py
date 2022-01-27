"""This is the demo script to show how to manage transmitters.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services import (
    EmailTransmitterProperties, list_transmitters, RecipientFieldType, Transmitter,
    TransmitterDeliveryType
)

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# create email transmitter properties object
# which is used when creating transmitter
etp = EmailTransmitterProperties(
    sender_display_name='sender - display name',
    sender_email_address='sender - email address',
    reply_to_display_name='reply to - display name',
    reply_to_email_address='reply to - email address',
    recipient_field_type=RecipientFieldType.TO,
    save_message_to_file=False,
    send_message_to_file=False,
    send_message_via_smtp=False,
    save_file_path=None,
    notify_on_success=False,
    notify_on_failure=False,
    notification_email_address=None,
)

# create a transmitter with delivery type as `email` (when type is `email` then
# it is mandatory to provide `email_transmitter_properties`). Delivery type
# can be also passed as a string and `email_transmitter_properties` can be
# passed as a dictionary
new_t = Transmitter.create(
    connection=conn,
    name='Name of transmitter',
    delivery_type=TransmitterDeliveryType.EMAIL,
    description='Description of transmitter',
    email_transmitter_properties=etp,
)

# alter email transmitter and its properties
etp.notify_on_success = True
etp.notify_on_failure = True
etp.notification_email_address = 'notification - email address'
etp.save_message_to_file = True
new_t.alter(
    name='New name of transmitter',
    description='New description of transmitter',
    email_transmitter_properties=etp,
)

# create file transmitter
new_file_t = Transmitter.create(
    connection=conn,
    name='Name of file transmitter',
    delivery_type=TransmitterDeliveryType.FILE,
    description='Description of file transmitter',
)

# alter file transmitter
new_file_t.alter(name='New file transmitter name', description='New file description')

# create ipad transmitter
new_ipad_t = Transmitter.create(
    connection=conn,
    name='Name of ipad transmitter',
    delivery_type=TransmitterDeliveryType.IPAD,
    description="Description of ipad transmitter",
)

# alter ipad transmitter
new_ipad_t.alter(name='New ipad transmitter name', description='New ipad description')

# create iphone transmitter
new_iphone_t = Transmitter.create(
    connection=conn,
    name='Name of iphone transmitter',
    delivery_type=TransmitterDeliveryType.IPHONE,
    description="Description of iphone transmitter",
)

# alter iphone transmitter
new_iphone_t.alter(name='New iphone transmitter name', description='New iphone description')

# create print transmitter
new_print_t = Transmitter.create(
    connection=conn,
    name='Name of print transmitter',
    delivery_type=TransmitterDeliveryType.PRINT,
    description="Description of print transmitter",
)

# alter print transmitter
new_print_t.alter(name='New print transmitter name', description='New print description')

# get list of transmitters
transmitters = list_transmitters(conn)

# get transmitter by ID. Transmitter can be also found by its name.
t = Transmitter(conn, id='transmitter id')
t_by_name = Transmitter(conn, name='Name of transmitter')

# list properties for transmitter
t.list_properties()

# Delete transmitter. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
t.delete(force=True)
