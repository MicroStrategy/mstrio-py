from mstrio.users_and_groups.user import list_users
from mstrio.api.projects import get_projects
from mstrio.distribution_services.subscription.subscription_manager import SubscriptionManager
from mstrio.connection import Connection


def delete_subscriptions_of_departed_users(connection: "Connection") -> None:
    """Delete all subscription in all projects which owners are departed users.

    Args:
        Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
    """

    # get all projects that the authenticated user has access to
    response = get_projects(connection, whitelist=[('ERR014', 403)])
    prjcts = response.json() if response.ok else []
    # get all disabled users
    all_usrs = list_users(connection=connection)
    dsbld_usrs = [u for u in all_usrs if not u.enabled]

    for prjct in prjcts:
        app_id = prjct['id']
        sub_mngr = SubscriptionManager(connection=connection, application_id=app_id)
        for usr in dsbld_usrs:
            subs = sub_mngr.list_subscriptions(owner={'id': usr.id})
            msg = f"subscriptions of user with ID: {usr.id}"
            msg += f" in project {prjct.name} with ID: {prjct.id}"
            # call of the function below returns True if all passed
            # subscriptions were deleted
            if sub_mngr.delete(subscriptions=subs, force=True):
                print("All " + msg + " were deleted.")
            else:
                print("Not all " + msg + " were deleted or there was no subsscriptions.")
