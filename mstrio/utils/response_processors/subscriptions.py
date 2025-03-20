from mstrio.api import subscriptions as subscriptions_api
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.utils.version_helper import is_server_min_version


def get_subscription_status(connection: Connection, id: str):
    response = subscriptions_api.get_subscription_status(
        connection=connection, id=id, whitelist=[('ERR002', 500)]
    )
    res = response.json()
    server_msg = res.get('message')

    if not server_msg:
        return {'status': res}

    if (
        'No status for the subscription' in server_msg
        or 'This endpoint is disabled' in server_msg
    ):
        return {'status': None}

    server_code = res.get('code')
    ticket_id = res.get('ticketId')
    raise IServerError(
        message=f"{server_msg}; code: '{server_code}', ticket_id: '{ticket_id}'",
        http_code=response.status_code,
    )


def get_subscription_last_run(connection: Connection, id: str, project_id: str):
    if not is_server_min_version(connection, '11.4.0600'):
        return None

    response = subscriptions_api.list_subscriptions(
        connection=connection, project_id=project_id, last_run=True
    ).json()['subscriptions']
    sub = next(sub for sub in response if sub['id'] == id).get('lastRun')

    return {'last_run': sub}
