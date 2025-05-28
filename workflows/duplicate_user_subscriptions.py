"""
Duplicate user subscriptions across all projects.

1. Connect to the environment using data from workstation
2. Get user with the given id
2. Get all projects that the authenticated user has access to
4. For each project get all subscriptions of the user which was earlier
   retrieved
5. Duplicate each received subscription and change its name by adding " Copy" at
   the end and specify new owner by providing some other id
"""

from mstrio.api.projects import get_projects
from mstrio.api.subscriptions import create_subscription
from mstrio.connection import Connection, get_connection
from mstrio.distribution_services import list_subscriptions
from mstrio.users_and_groups import User


def duplicate_user_subscriptions(connection: Connection, owner: str | User) -> None:
    """Duplicate user subscriptions across all projects.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        owner (str, User): The owner of the subscriptions to duplicate.
    """

    # get all projects that the authenticated user has access to
    response = get_projects(connection, whitelist=[('ERR014', 403)])
    projects = response.json() if response.ok else []

    owner_id = owner.id if isinstance(owner, User) else owner

    for project in projects:
        project_id = project['id']
        subscriptions = list_subscriptions(
            connection=connection,
            project_id=project_id,
            owner={'id': owner_id},
        )
        for subscription in subscriptions:
            subscription_dict = subscription.to_dict()
            # Update subscription name and owner
            subscription_dict.update(
                name=f'{subscription_dict["name"]} Copy',
                owner={'id': '51F189429A439FAA734550A753978285'},
            )
            create_subscription(
                connection, project_id=project_id, body=subscription_dict
            )


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

user = User(connection=conn, id='7FC05A65473CE2FD845CE6A1D3F13233')
duplicate_user_subscriptions(conn, user)
