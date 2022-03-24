from mstrio.api.projects import get_projects
from mstrio.connection import Connection
from mstrio.distribution_services import SubscriptionManager
from mstrio.users_and_groups import list_users


def delete_subscriptions_of_departed_users(connection: "Connection") -> None:
    """Delete all subscription in all projects which owners are departed users.

    Args:
        Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    """

    # get all projects that the authenticated user has access to
    response = get_projects(connection, whitelist=[('ERR014', 403)])
    projects = response.json() if response.ok else []
    # get all disabled users
    all_users = list_users(connection=connection)
    disabled_users = [u for u in all_users if not u.enabled]

    for project in projects:
        project_id = project['id']
        sub_mngr = SubscriptionManager(connection=connection, project_id=project_id)
        for usr in disabled_users:
            subs = sub_mngr.list_subscriptions(owner={'id': usr.id})
            msg = f"subscriptions of user with ID: {usr.id}"
            msg += f" in project {project.name} with ID: {project.id}"
            # call of the function below returns True if all passed
            # subscriptions were deleted
            if sub_mngr.delete(subscriptions=subs, force=True):
                print("All " + msg + " were deleted.")
            else:
                print("Not all " + msg + " were deleted or there was no subscriptions.")
