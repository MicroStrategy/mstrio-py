"""Delete all subscription in all projects which owners are departed users.
For which project message about successful (or not) deletion will be printed.

1. Connect to the environment using data from workstation
2. Get all projects that the authenticated user has access to
3. Get all disabled users
4. For each project for each user get the list of subscriptions and delete them
5. For each deletion process message is displayed informing about the result
"""

from mstrio.api.projects import get_projects
from mstrio.connection import Connection, get_connection
from mstrio.distribution_services import SubscriptionManager
from mstrio.users_and_groups import list_users


def delete_subscriptions_of_departed_users(connection: "Connection") -> None:
    """Delete all subscription in all projects which owners are departed users.

    Args:
        Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
    """

    # get all projects that the authenticated user has access to
    response = get_projects(connection, whitelist=[('ERR014', 403)])
    projects_ = response.json() if response.ok else []
    # get all disabled users
    all_users = list_users(connection=connection)
    disabled_users = [u for u in all_users if not u.enabled]

    for project_ in projects_:
        project_id = project_['id']
        sub_manager = SubscriptionManager(connection=connection, project_id=project_id)
        for user_ in disabled_users:
            subs = sub_manager.list_subscriptions(owner={'id': user_.id})
            msg = f"subscriptions of user with ID: {user_.id}"
            msg += f" in project {project_['name']} with ID: {project_['id']}"
            # call of the function below returns True if all passed
            # subscriptions were deleted
            if sub_manager.delete(subscriptions=subs, force=True):
                print("All " + msg + " were deleted.", flush=True)
            else:
                print(
                    "Not all " + msg + " were deleted or there was no subscriptions.",
                    flush=True,
                )


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# execute deletion of addresses from departed users
delete_subscriptions_of_departed_users(conn)
