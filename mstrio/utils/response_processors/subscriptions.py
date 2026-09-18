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


def list_subscriptions_cross_projects(
    connection: Connection,
    project_ids: list[str] | None = None,
    offset: int | None = None,
    limit: int | None = None,
    delivery_modes: int = -1,
    last_run: bool = False,
    ignore_admin_privileges: bool = False,
) -> list[dict]:
    """List subscriptions from multiple projects."""
    body = {'projectIds': project_ids} if project_ids is not None else None
    response = subscriptions_api.query_subscriptions(
        connection=connection,
        body=body,
        offset=offset,
        limit=limit,
        delivery_modes=delivery_modes,
        last_run=last_run,
        ignore_admin_privileges=ignore_admin_privileges,
    )
    return response.json().get('subscriptions', [])


def list_personal_addresses(connection: Connection, delivery_type: str) -> list[dict]:
    """List personal addresses for a delivery type."""
    response = subscriptions_api.list_personal_addresses(
        connection=connection,
        delivery_type=delivery_type,
    )
    return response.json().get('personalAddresses', [])
