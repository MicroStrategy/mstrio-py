"""This is the demo script to show how administrator can manage subscriptions
and schedules.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import (
    CacheType, CacheUpdateSubscription, Content, EmailSubscription, list_schedules,
    list_subscriptions, Schedule, Subscription, SubscriptionManager
)

from mstrio.connection import get_connection

PROJECT_NAME = '<project_name>'  # Project to connect to
CONTENT_TYPE = '<content_type>'  # see distribution_services/subscription/content.py for available options
FORMAT_TYPE = '<format_type>'  # see distribution_services/subscription/content.py for available options
EMAIL_SUBSCRIPTION_NAME = '<email_subscription_name>'
EMAIL_SUBJECT = '<email_subject>'
CACHE_SUBSCRIPTION_NAME = '<cache_subscription_name>'
SCHEDULE_NAME = '<schedule_name>'
DELIVERY_EXPIRATION_DATE = '<delivery_expiration_date>'

SUBSCRIPTION_ID = '<subscription_id>'
SUBSCRIPTION_ID_2 = '<subscription_id_2>'
CONTENT_ID = '<content_id>'
PROJECT_ID = '<project_id>'
RECIPIENT_ID = '<recipient_id>'
RECIPIENT_ID_2 = '<recipient_id_2>'
REMOVED_USER_ID = '<user_to_remove_id>'
ADMIN_USER_ID = '<admin_user_id>'
SCHEDULE_ID = '<schedule_id>'
OWNER_ID = '<owner_id>'

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Initialize manager for subscriptions on a chosen project
sub_mngr = SubscriptionManager(connection=conn, project_name=PROJECT_NAME)
# get all subscriptions from the given project (it is possible in two ways)
all_subs = list_subscriptions(connection=conn, project_name=PROJECT_NAME)
all_subs = sub_mngr.list_subscriptions()

#  execute/delete subscriptions by passing theirs ids or Subscription objects
sub_mngr.execute([SUBSCRIPTION_ID, SUBSCRIPTION_ID_2])
sub_mngr.delete([SUBSCRIPTION_ID, SUBSCRIPTION_ID_2], force=True)

# list available recipients of the subscription for the given content (default
# delivery type is an email)
sub_mngr.available_recipients(content_id=CONTENT_ID,
                              content_type=CONTENT_TYPE)

# get a single subscription
sub = Subscription(connection=conn, subscription_id=SUBSCRIPTION_ID,
                   project_id=PROJECT_ID)
# list all recipients of the given subscription and all available for this
# subscription
sub.recipients
sub.available_recipients()

# add/remove recipient(s) with given id(s)
sub.add_recipient(
    recipients=[RECIPIENT_ID, RECIPIENT_ID_2])
sub.remove_recipient(
    recipients=[RECIPIENT_ID, RECIPIENT_ID_2])

# execute a given subscription
sub.execute()

# replace a user with an admin in all of its subscriptions (e.g. when user exits
# company)
for s in sub_mngr.list_subscriptions(to_dictionary=False):
    if REMOVED_USER_ID in [r['id'] for r in s.recipients]:
        s.add_recipient(recipients=ADMIN_USER_ID)
        s.remove_recipient(recipients=REMOVED_USER_ID)

# create an email subscription
EmailSubscription.create(
    connection=conn,
    name=EMAIL_SUBSCRIPTION_NAME,
    project_name=PROJECT_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=Content.Type.REPORT,  # see distribution_services/subscription/content.py for available options
        personalization=Content.Properties(format_type=FORMAT_TYPE)
    ),
    schedules=[SCHEDULE_ID],
    recipients=[RECIPIENT_ID],
    email_subject=EMAIL_SUBJECT)

# create a cache update subscription
cache_update_sub = CacheUpdateSubscription.create(
    connection=conn,
    project_name=PROJECT_NAME,
    name=CACHE_SUBSCRIPTION_NAME,
    contents=Content(
        id=CONTENT_ID,
        type=Content.Type.REPORT,  # see distribution_services/subscription/content.py for available options
        personalization=Content.Properties(format_type=Content.Properties.FormatType.EXCEL),
    ),
    schedules=[SCHEDULE_ID],
    delivery_expiration_date=DELIVERY_EXPIRATION_DATE,
    send_now=True,
    recipients=[RECIPIENT_ID],
    cache_cache_type=CacheType.RESERVED)  # see distribution_services/subscription/delivery.py for available options

# change name and owner of cache update subscription
cache_update_sub.alter(name=f"<{cache_update_sub.name}_(Altered)>",
                       owner_id=OWNER_ID)

# list all cache update subscriptions
cache_update_subs = [
    sub for sub in list_subscriptions(conn, project_name=PROJECT_NAME)
    if isinstance(sub, CacheUpdateSubscription)
]

# get list of schedules (you can filter them by for example name, id or
# description)
all_schedules = list_schedules(conn)

# get a single schedule by its id or name and then its properties
schedule = Schedule(connection=conn, name=SCHEDULE_NAME)
schedule.list_properties()
