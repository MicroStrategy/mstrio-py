"""
Manage Pre-/Post-execution SQL statements with Subscription execution.
Check the ETL flag in the database, run Subscription,
and send an email to the Administrator.

1. Connect to environment using data from workstation
2. Get datasource instance base on provided name ('Tutorial Postgres')
3. Get project object based on provided name ('MicroStrategy Tutorial')
4. Steps below describe the process of managing email subscription for the given
   project and datasource instance
5. Prepare query to select the ETL flag 
6. Execute the query and store the result
7. If the ETL flag is present, get the email subscription object by an id
   and execute it
8. If the ETL flag is missing, send an email to the administrator
9. Steps below describe the process of managing mobile subscription for the given
   project and datasource instance
10. Get the mobile subscription object by an id
11. Execute the mobile subscription and wait for its completion checking the status
12. Prepare SQL query to insert status of the mobile subscription into the table
13. Execute the query
14. Calculate the success rate of the mobile subscription
15. Prepare email content with the results of the mobile subscription's execution
    and send it to the administrator
"""

import time

from mstrio.connection import Connection, get_connection
from mstrio.datasources import DatasourceInstance
from mstrio.distribution_services import EmailSubscription, MobileSubscription
from mstrio.distribution_services.email import send_email
from mstrio.server import Project
from mstrio.users_and_groups import User


def send_email_to_administrator(connection: Connection, subject: str, content: str):
    """Send an email to the Administrator.

    Args:
        connection: Strategy One connection object.
        subject: Email subject.
        content: Email content.
    """
    administrator = User(connection=connection, name="Administrator")
    send_email(
        connection=connection,
        subject=subject,
        content=content,
        users=[administrator],
        is_html=True,
    )


def manage_email_subscription(
    connection: 'Connection',
    datasource_instance: 'DatasourceInstance',
    project: 'Project',
):
    """Manage the Email Subscription.

    Args:
        connection: Strategy One connection object.
        datasource_instance: Datasource instance object.
        project: Project object.
    """
    # SQL query to select the ETL flag
    select_query = 'SELECT <ETL_FLAG> FROM <TABLE_NAME>'
    # Execute the SQL query
    sql_result = datasource_instance.execute_query(
        project_id=project.id,
        query=select_query,
        max_retries=10,
        retry_delay=10,
    )
    # If the ETL flag is present, run the Email Subscription
    if sql_result and sql_result.get('results'):
        print('ETL flag is present. Running the Email Subscription.')
        email_subscription = EmailSubscription(
            connection=conn, id="7138EE3011EA0FD26B470080EF752E56"
        )
        email_subscription.execute()
    # If the ETL flag is missing, send an email to the Administrator
    else:
        print("The ETL flag is missing. Sending an email to the Administrator.")
        send_email_to_administrator(
            connection=connection,
            subject="ETL Flag Missing",
            content="The ETL flag is missing. Please check the ETL process.",
        )


def manage_mobile_subscription(
    connection: 'Connection',
    datasource_instance: 'DatasourceInstance',
    project: 'Project',
):
    """Manage the Mobile Subscription.

    Args:
        connection: Strategy One connection object.
        datasource_instance: Datasource instance object.
        project: Project object.
    """
    # Table name to save the Mobile Subscription status
    TABLE_NAME = "<TABLE_NAME>"

    mobile_subscription = MobileSubscription(
        connection=connection, id="EBC6F6D7F3413F546285B091B746FC69"
    )
    mobile_subscription.execute()

    # Wait for the Mobile Subscription to complete
    for _ in range(10):
        if mobile_subscription.status is None:
            print("Mobile Subscription is still running. Waiting for completion.")
            time.sleep(10)
        break

    mobile_subscription_status = mobile_subscription.status.to_dict(False).values()

    # Convert each item in the list to a string
    # and replace single quotes with double quotes
    str_mobile_subscription_status = [
        str(x).replace("'", '"') for x in mobile_subscription_status
    ]

    # SQL query to insert the Mobile Subscription status into the table
    insert_query = f"""
    INSERT INTO {TABLE_NAME}
    VALUES
        ({", ".join([f"'{x}'" for x in str_mobile_subscription_status])});
    """

    # Execute the SQL query
    datasource_instance.execute_query(
        project_id=project.id,
        query=insert_query,
    )

    # Calculate the success rate of the Mobile Subscription
    result = sum(
        1 for status in mobile_subscription.status.statuses if status.error is None
    )
    success_rate = (result / mobile_subscription.status.total) * 100 if result else 0

    email_content = f"""
    <html>
        <body>
            <h1>Subscription with name: {mobile_subscription.name} was executed</h1>
            <p>Total number of successful deliveries: {result}</p>
            <p>Total number of deliveries: {mobile_subscription.status.total}</p>
            <p>Successful rate: {success_rate}% </p>
            <p>All details were saved to the table {TABLE_NAME}</p>
        </body>
    </html>
    """

    send_email_to_administrator(
        connection=connection, subject="Mobile Subscription", content=email_content
    )


def manage_execution(connection: 'Connection'):
    """Manage Pre-/Post-execution SQL statements with Subscription execution.

    Args:
        connection: Strategy One connection object.
    """
    datasource_instance = DatasourceInstance(
        connection=connection, name='Tutorial Postgres'
    )
    project = Project(connection=connection, name='MicroStrategy Tutorial')
    manage_email_subscription(connection, datasource_instance, project)
    manage_mobile_subscription(connection, datasource_instance, project)


# Create connection based on workstation data
conn = get_connection(workstationData, 'MicroStrategy Tutorial')
manage_execution(conn)
