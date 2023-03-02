"""This is the demo script to show how administrator can manage subscriptions.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import (
    CacheType,
    CacheUpdateSubscription,
    Content,
    EmailSubscription,
    FileSubscription,
    FTPSubscription,
    HistoryListSubscription,
    list_subscriptions,
    Subscription,
    SubscriptionManager
)
from mstrio.api.users import create_address_v2, get_addresses
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

# Create connection based on workstation data
CONN = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
EMAIL_SUBSCRIPTION_NAME = $email_subscription_name
# see distribution_services/subscription/content.py for available options
FORMAT_TYPE = $format_type
EMAIL_SUBJECT = $email_subject
SCHEDULE_ID = $schedule_id
CONTENT_ID = $content_id
# see distribution_services/subscription/content.py for available options
CONTENT_TYPE = $content_type
RECIPIENT_ID = $recipient_id
RECIPIENT_ID_2 = $recipient_id_2
RECIPIENT_ID_3 = $recipient_id_3

# Create an email subscription
EMAIL_SUB = EmailSubscription.create(
    connection=CONN,
    name=EMAIL_SUBSCRIPTION_NAME,
    project_name=PROJECT_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=CONTENT_TYPE,
        personalization=Content.Properties(format_type=FORMAT_TYPE)
    ),
    schedules=[SCHEDULE_ID],
    recipients=[RECIPIENT_ID],
    email_subject=EMAIL_SUBJECT
)

# Define variables which can be later used in a script
FILE_SUBSCRIPTION_NAME = $file_subscription_name
FILE_NAME = $file_name
ZIP_FILE_NAME = $zip_file_name
ZIP_PASSWORD = $zip_password

# Create a file subscription
FILE_SUB = FileSubscription.create(
    connection=CONN,
    name=FILE_SUBSCRIPTION_NAME,
    project_name=PROJECT_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=CONTENT_TYPE,
        personalization=Content.Properties(format_type=FORMAT_TYPE)
    ),
    schedules=[SCHEDULE_ID],
    recipients=[RECIPIENT_ID_3],
    filename=FILE_NAME,
    zip_password_protect=True,
    zip_filename=ZIP_FILE_NAME,
    zip_password=ZIP_PASSWORD
)

# Define variables which can be later used in a script
FTP_SUBSCRIPTION_NAME = $ftp_subscription_name
FTP_ADDRESS_NAME = $ftp_address_name
PHYSICAL_ADDRESS = $physical_address
DEVICE_ID = $ftp_device_id
# FTP sub needs a user with FTP Device address
# Body for FTP Device address
BODY = {
        'name': FTP_ADDRESS_NAME,
        'physicalAddress': PHYSICAL_ADDRESS,
        'deliveryType': 'FTP',
        'deviceId': DEVICE_ID,
        'isDefault': False
    }
# Create FTP address for user
create_address_v2(connection=CONN, id=RECIPIENT_ID_3, body=BODY)
# Create an ftp subscription
FTP_SUB = FTPSubscription.create(
    connection=CONN,
    name=FTP_SUBSCRIPTION_NAME,
    project_name=PROJECT_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=CONTENT_TYPE,
        personalization=Content.Properties(format_type=FORMAT_TYPE)
    ),
    schedules=[SCHEDULE_ID],
    recipients=[RECIPIENT_ID_3],
    filename=FILE_NAME,
    zip_password_protect=True,
    zip_filename=ZIP_FILE_NAME,
    zip_password=ZIP_PASSWORD
)

# Define variables which can be later used in a script
HISTORY_LIST_SUBSCRIPTION_NAME = $history_list_subscription_name

# Create a history list subscription
HL_SUB = HistoryListSubscription.create(
    connection=CONN,
    name=HISTORY_LIST_SUBSCRIPTION_NAME,
    project_name=PROJECT_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=CONTENT_TYPE,
        personalization=Content.Properties(format_type=FORMAT_TYPE)
    ),
    schedules=[SCHEDULE_ID],
    recipients=[RECIPIENT_ID_3],
    do_not_create_update_caches=True,
    overwrite_older_version=True,
    re_run_hl=True
)

# Define variables which can be later used in a script
CACHE_SUBSCRIPTION_NAME = $cache_subscription_name
DELIVERY_EXPIRATION_DATE = $delivery_expiration_date

# Create a cache update subscription
CACHE_UPDATE_SUB = CacheUpdateSubscription.create(
    connection=CONN,
    project_name=PROJECT_NAME,
    name=CACHE_SUBSCRIPTION_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=CONTENT_TYPE,
        personalization=Content.Properties(format_type=Content.Properties.FormatType.PDF),
    ),
    schedules=[SCHEDULE_ID],
    delivery_expiration_date=DELIVERY_EXPIRATION_DATE,
    send_now=True,
    recipients=[RECIPIENT_ID_3],
    cache_cache_type=CacheType.RESERVED
)  # see distribution_services/subscription/delivery.py for available options

# Define variables which can be later used in a script
CACHE_SUBSCRIPTION_NEW_NAME = $cache_subscription_new_name
OWNER_ID = $owner_id

# Change name and owner of a subscription
CACHE_UPDATE_SUB.alter(name=CACHE_SUBSCRIPTION_NEW_NAME, owner_id=OWNER_ID)

# List a particular subscription type, for example Cache Update
CACHE_UPDATE_SUBS = [
    sub for sub in list_subscriptions(CONN, project_name=PROJECT_NAME)
    if isinstance(sub, CacheUpdateSubscription)
]

# Initialize manager for subscriptions on a chosen project
sub_mngr = SubscriptionManager(connection=CONN, project_name=PROJECT_NAME)
# Get all subscriptions from the given project (it is possible in two ways)
all_subs = list_subscriptions(connection=CONN, project_name=PROJECT_NAME)
all_subs = sub_mngr.list_subscriptions()

# Execute/delete subscriptions by passing theirs ids or Subscription objects
sub_mngr.execute([EMAIL_SUB.id])
sub_mngr.delete([EMAIL_SUB, FTP_SUB, FILE_SUB, CACHE_UPDATE_SUB], force=True)

# List available recipients of the subscription for the given content (default
# delivery type is an email)
sub_mngr.available_recipients(content_id=CONTENT_ID, content_type=CONTENT_TYPE)

# Get a single subscription
sub = Subscription(connection=CONN, subscription_id=HL_SUB.id, project_name=PROJECT_NAME)
# List all recipients of the given subscription and all available for this
# subscription
sub.recipients
sub.available_recipients()

# Define variables which can be later used in a script
RECIPIENT_ID_4 = $recipient_id_4

# Add/remove recipient(s) with given id(s)
sub.add_recipient(recipients=[RECIPIENT_ID_4])
sub.remove_recipient(recipients=[RECIPIENT_ID_4])

# As an alternate to subscription manager you can execute or delete a subscription
# directly from the subscription itself
sub.execute()
sub.delete(force=True)

# Define variables which can be later used in a script
USER_TO_REMOVE_ID = $user_to_remove_id
ADMIN_USER_ID = $admin_user_id

# Replace a user with an admin in all of its subscriptions (e.g. when user exits
# company)
for s in sub_mngr.list_subscriptions(to_dictionary=False):
    if USER_TO_REMOVE_ID in [r['id'] for r in s.recipients]:
        s.add_recipient(recipients=ADMIN_USER_ID)
        s.remove_recipient(recipients=USER_TO_REMOVE_ID)
