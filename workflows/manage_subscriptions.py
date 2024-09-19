"""
Manage subscriptions.
Create, modify and execute various types of subscriptions such as
Email Subscription, File Subscription etc.

1. Connect to the environment using data from the workstation
2. Get 2 schedules based on provided IDs
3. Create and execute an email subscription for a document
4. Modify a file subscription for a document with bursting option ON
5. Create and execute a history list subscription for an OLAP cube
6. Create and execute a mobile subscription for a document
7. Get a subscription based on provided id and list its dependent dashboards
8. Select a dashboard, find all subscriptions using it and print them
"""

from mstrio.connection import get_connection

from mstrio.distribution_services.subscription.email_subscription import (
    EmailSubscription,
)
from mstrio.distribution_services.subscription.content import Content
from mstrio.distribution_services.schedule.schedule import Schedule
from mstrio.distribution_services.subscription.file_subscription import FileSubscription
from mstrio.distribution_services.subscription.history_list_subscription import (
    HistoryListSubscription,
)
from mstrio.distribution_services.subscription.mobile_subscription import (
    MobileSubscription,
)
from mstrio.distribution_services.subscription.delivery import ClientType
from mstrio.distribution_services.subscription.subscription_manager import (
    list_subscriptions,
)
from mstrio.project_objects.dashboard import Dashboard


conn = get_connection(workstationData, 'MicroStrategy Tutorial')

example_schedule1 = Schedule(conn, id="987DF6464625F087CCC67FA9DB53097D")
example_schedule2 = Schedule(conn, id="FF7BB3B311D501F0C00051916B98494F")

example_user_id = 'E96A7BE711D4BBCE10004694316DE8A4'


# Create and execute an Email Subscription for a Document
email_sub = EmailSubscription.create(
    connection=conn,
    name='<Name of the email subscription>',
    project_name='MicroStrategy Tutorial',
    contents=Content(
        id='C68851F14333D950BC37EC9D8DF3FDCA',
        type=Content.Type.DOCUMENT,
        personalization=Content.Properties(
            format_type=Content.Properties.FormatType.HTML
        ),
    ),
    schedules=[example_schedule1, example_schedule2],
    recipients=[example_user_id],
    email_subject="<Subject of the email>",
)
email_sub.execute()


# Modify a File Subscription for a Document with Bursting option on
example_file_sub = FileSubscription(conn, id="<ID of the subscription>")
file_sub_content: Content = example_file_sub.contents[0]
file_sub_content.personalization.bursting = Content.Properties.Bursting(
    slicing_attributes=['<Attribute ID>', '<Attribute ID>'],
)
example_file_sub.alter(content=file_sub_content)


# Create and execute a History List subscription for an OLAP Cube
example_hl_sub = HistoryListSubscription.create(
    connection=conn,
    name='<Name of the history list subscription>',
    contents=Content(
        id='C68851F14333D950BC37EC9D8DF3FDCA',
        type=Content.Type.CUBE,
        personalization=Content.Properties(
            format_type=Content.Properties.FormatType.HTML
        ),
    ),
    schedules=[example_schedule1, example_schedule2],
    recipients=[example_user_id],
    allow_delivery_changes=False,
    allow_personalization_changes=False,
    allow_unsubscribe=False,
)
example_hl_sub.execute()

# Create and execute a Mobile Subscription for a Document
example_mobile_sub = MobileSubscription.create(
    connection=conn,
    name='<Name of the mobile subscription>',
    contents=Content(
        id='C68851F14333D950BC37EC9D8DF3FDCA',
        type=Content.Type.DOCUMENT,
        personalization=Content.Properties(
            format_type=Content.Properties.FormatType.HTML
        ),
    ),
    schedules=[example_schedule1, example_schedule2],
    recipients=[example_user_id],
    mobile_client_type=ClientType.PHONE,
    device_id='E206C75BABC441C5B13B60C5D956F605',
    do_not_create_update_caches=True,
    overwrite_older_version=False,
    re_run_hl=True,
)
example_mobile_sub.execute()


# Select a Subscription and list its dependent Dashboards
example_subscription = HistoryListSubscription(
    connection=conn, id="7138EE3011EA0FD26B470080EF752E56"
)
all_contents = example_subscription.contents
dashboard_contents = [
    content for content in all_contents if content.type == Content.Type.DASHBOARD
]

dashboard_ids = [content.id for content in dashboard_contents]
print("Dashboard IDs:")
print(dashboard_ids)

dashboards_objects = [Dashboard(conn, id) for id in dashboard_ids]
print(dashboards_objects)


# Select a Dashboard and find all Subscriptions using it. This step requires
# filtering a list of Subscriptions with Python list operations,
# as Document/Dashboard query responses do not backlink to Subscriptions.
all_subscriptions = list_subscriptions(conn)
dashboard_id = "<ID of the Dashboard>"

subscriptions_using_dashboard = [
    sub
    for sub in all_subscriptions
    if any(content.id == dashboard_id for content in sub.contents)
]
print("Subscriptions using the Dashboard:")
print(subscriptions_using_dashboard)
