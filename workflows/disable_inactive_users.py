"""
Disable users who have been inactive for a certain period of time

1. Connect to the environment using data from workstation
2a. Get users who have been inactive for 90 days
2b. Get users who have been inactive for 90 days using data
    from 'Platform Analytics'
3. Get users who have been inactive for 85 days
4. Send a notification to users who have been inactive for 85 days
5. Disable users who have been inactive for 90 days
"""

from datetime import datetime, timezone

from mstrio.connection import Connection, get_connection
from mstrio.datasources import DatasourceInstance
from mstrio.distribution_services.email import send_email
from mstrio.server import Project
from mstrio.users_and_groups import User, list_users


def get_inactive_users_from_database(
    connection: Connection, days_inactive: int
) -> list[User]:
    """Get users who have been inactive for a certain period of time.

    Args:
        connection (Connection): Strategy One connection object.
        days_inactive (int): Number of days to consider a user inactive.
    """

    project = Project(connection=conn, name='Platform Analytics')
    dsi = DatasourceInstance(conn, name='Platform Analytics')

    # Action_type_id 103 corresponds to user logout event
    query = """
    SELECT B.mstr_user_guid, MAX(A.local_timestamp) as max_timestamp
    FROM fact_access_transactions_view AS A
    JOIN lu_account AS B
    ON A.account_id = B.account_id AND A.action_type_id = '103'
    GROUP BY B.mstr_user_guid
    """

    res = dsi.execute_query(project_id=project.id, query=query)['results']['data']
    # Create a dictionary mapping user IDs to their last login timestamp
    user_last_login = dict(zip(res['mstr_user_guid'], res['max_timestamp']))

    users = list_users(connection)
    inactive_users = []
    today_date = datetime.now(tz=timezone.utc)
    for user in users:
        last_login = user_last_login.get(user.id)
        if user.enabled and last_login:
            last_login = datetime.fromisoformat(last_login)
            result = today_date - last_login
            if result.days > days_inactive:
                inactive_users.append(user)
    return inactive_users


def get_inactive_users(connection: Connection, days_inactive: int) -> list[User]:
    """Get users who have been inactive for a certain period of time.

    Args:
        connection (Connection): Strategy One connection object.
        days_inactive (int): Number of days to consider a user inactive.
    """
    users = list_users(connection)
    today_date = datetime.now(tz=timezone.utc)
    inactive_users = []
    for user in users:
        if user.enabled and user.last_login:
            result = today_date - user.last_login
            if result.days > days_inactive:
                inactive_users.append(user)
    return inactive_users


def disable_inactive_users(users: list[User]) -> None:
    """Disable users who have been inactive for a certain period of time.

    Args:
        users (list[User]): List of users to disable.
    """
    for user in users:
        user.alter(enabled=False)


def send_notification_to_inactive_users(
    connection: Connection, users: list[User]
) -> None:
    """Send a notification to users who have been inactive for a certain
    period of time.

    Args:
        connection (Connection): Strategy One connection object.
        users (list[User]): List of users to send notifications to.
    """

    # Send personalized email to each user
    for user in users:
        inactive_days = datetime.now(tz=timezone.utc) - user.last_login
        send_email(
            connection=connection,
            users=[user],
            subject='Inactive Account',
            content=f'{user.username} account was inactive for {inactive_days} '
            f'and will be disabled soon. Please log in to prevent this.',
        )
    # Alternatively, send a general email to all users
    # send_email(
    #     connection,
    #     users=users,
    #     subject='Inactive Account',
    #     content='Your account was inactive and will be disabled soon. '
    #     'Please log in to prevent this.',
    # )


# Define project to connect to
PROJECT_NAME = 'MicroStrategy Tutorial'

# Connect to environment without providing user credentials
# Variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# `User.last_login` property is only available on containerized environments
# with the telemetry service enabled
inactive_users_90_days = get_inactive_users(conn, 90)
# For environments without the telemetry service, you can fetch the data from
# DatasourceInstance 'Platform Analytics'
inactive_users_90_days_db = get_inactive_users_from_database(conn, 90)
inactive_users_80_days = get_inactive_users(conn, 85)


send_notification_to_inactive_users(conn, inactive_users_80_days)
disable_inactive_users(inactive_users_90_days)
