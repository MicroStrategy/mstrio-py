"""Create a mobile subscription for a selected dashboard and schedule.
1. Connect to the environment using data from workstation
2. List Dashboards and select one that will be used as Content for the subscription
3. List Schedules and select one that will be used for the subscription
4. Define the user that will receive the subscription
5. Create Mobile Subscription with expiration date
6. Execute created mobile subscription
"""

from mstrio.connection import get_connection
from mstrio.distribution_services.schedule.schedule import list_schedules
from mstrio.distribution_services.subscription import Content, MobileSubscription
from mstrio.project_objects import list_dashboards
from mstrio.users_and_groups import list_users

PROJECT_NAME = 'MicroStrategy Tutorial'  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# List Dashboards and select one that will be used as Content for the subscription
dashboards = list_dashboards(conn)
selected_dashboard = dashboards[0]

# List Schedules and select one that will be used for the subscription
# It will be 'At Close of Business (Weekday)' in our example here
schedules = list_schedules(conn)
selected_schedule = schedules[1]
print(selected_schedule)

# Define the user that will receive the subscription
# It will be 'Administrator' in our example here
users = list_users(conn, 'Administrator')
selected_user = users[0]
print(selected_user)

# Create Mobile Subscription
mobile_sub = MobileSubscription.create(
    connection=conn,
    name='<Name of the subscription>',
    schedules=[selected_schedule],
    contents=Content(
        id=selected_dashboard.id,
        type=Content.Type.DASHBOARD,
        personalization=Content.Properties(
            format_type=Content.Properties.FormatType.HTML
        ),
    ),
    recipients=[selected_user.id],
    delivery_expiration_date='2024-12-31',
    delivery_expiration_timezone='Europe/London',
)

# Execute the subscription
mobile_sub.execute()
