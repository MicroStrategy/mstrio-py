from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.helper import exception_handler, response_handler
from mstrio.utils.version_helper import is_server_min_version

if TYPE_CHECKING:
    from concurrent.futures import Future

    from mstrio.connection import Connection
    from mstrio.utils.sessions import FuturesSessionWithRenewal


@ErrorHandler(err_msg="Error getting subscription list.")
def list_subscriptions(
    connection: 'Connection',
    project_id: str,
    fields: str | None = None,
    offset: int = 0,
    limit: int = -1,
    last_run: bool = False,
    error_msg: str | None = None,
) -> 'Response':
    """Get a list of subscriptions.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        last_run (bool, optional): If True, adds the last time that
            the subscription ran.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """

    params = {'offset': offset, 'limit': limit, 'fields': fields}

    if is_server_min_version(connection, '11.4.0600'):
        params['lastRun'] = last_run

    response = connection.get(
        endpoint='/api/subscriptions',
        params=params,
        headers={'X-MSTR-ProjectID': project_id},
    )

    return response


def list_subscriptions_async(
    future_session: 'FuturesSessionWithRenewal',
    project_id: str,
    fields: str | None = None,
    offset: int = 0,
    limit: int = -1,
    last_run: bool = False,
) -> 'Future':
    """Get a list of subscriptions asynchronously.

    Args:
        future_session: Future Session object to call Strategy One REST
            Server asynchronously
        project_id (str): ID of the project
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        last_run (bool, optional): If True, adds the last time that
            the subscription ran.

    Returns:
        Complete Future object.
    """
    params = {'offset': offset, 'limit': limit, 'fields': fields}
    if is_server_min_version(future_session.connection, '11.4.0600'):
        params['lastRun'] = last_run

    endpoint = '/api/subscriptions'
    headers = {'X-MSTR-ProjectID': project_id}

    return future_session.get(endpoint=endpoint, headers=headers, params=params)


@ErrorHandler(err_msg="Error getting Dynamic Recipient List list.")
def list_dynamic_recipient_lists(
    connection: 'Connection',
    project_id: str,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get a list of Dynamic Recipient Lists.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint='/api/dynamicRecipientLists',
        params={'offset': offset, 'limit': limit, 'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )


def list_dynamic_recipient_lists_async(
    future_session: 'FuturesSessionWithRenewal',
    project_id: str,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
) -> 'Future':
    """Get a list of Dynamic Recipient Lists asynchronously.

    Args:
        future_session: Future Session object to call Strategy One REST
            Server asynchronously
        project_id (str): ID of the project
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Returns:
        Complete Future object.
    """
    return future_session.get(
        endpoint='/api/dynamicRecipientLists',
        headers={'X-MSTR-ProjectID': project_id},
        params={'offset': offset, 'limit': limit, 'fields': fields},
    )


@ErrorHandler(err_msg="Error getting subscription {subscription_id} information.")
def get_subscription(
    connection: 'Connection',
    subscription_id: str,
    project_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get information of a specific subscription for a given project.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        subscription_id (str): ID of the subscription
        project_id (str): ID of the project
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(
        endpoint=f'/api/subscriptions/{subscription_id}',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting Dynamic Recipient List {list_id} information.")
def get_dynamic_recipient_list(
    connection: 'Connection',
    id: str,
    project_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get information of a specific Dynamic Recipient List for a given project.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        id (str): ID of the Dynamic Recipient List
        project_id (str): ID of the project
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(
        endpoint=f'/api/dynamicRecipientLists/{id}',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error creating new subscription.")
def create_subscription(
    connection: 'Connection',
    project_id: str,
    body: dict,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Create a new subscription.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project
        body: JSON-formatted body of the new subscription
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.post(
        endpoint='/api/subscriptions',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error creating new Dynamic Recipient List.")
def create_dynamic_recipient_list(
    connection: 'Connection',
    project_id: str,
    body: dict,
    fields: list[str] | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Create a new subscription.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        project_id (str): ID of the project
        body: JSON-formatted body of the new subscription
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.post(
        endpoint='/api/dynamicRecipientLists',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


def remove_subscription(
    connection: 'Connection',
    subscription_id: str,
    project_id: str,
    error_msg: str | None = None,
    exception_type: type[Exception] | None = None,
) -> 'Response':
    """Remove (Unsubscribe) the subscription using subscription id.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        subscription_id (str): ID of the subscription
        project_id (str): ID of the project
        error_msg (str, optional): Customized error message.
        exception_type (Exception): Instance of Exception or Warning class

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    response = connection.delete(
        endpoint=f'/api/subscriptions/{subscription_id}',
        headers={'X-MSTR-ProjectID': project_id},
    )
    if not response.ok:
        if error_msg is None:
            error_msg = f"Error unsubscribing Subscription {subscription_id}"
        if exception_type is None:
            response_handler(response, error_msg)
        else:
            exception_handler(error_msg, exception_type)
    return response


@ErrorHandler(err_msg="Error deleting Dynamic Recipient List ID: {id}.")
def remove_dynamic_recipient_list(
    connection: 'Connection', id: str, project_id: str, error_msg: str | None = None
) -> 'Response':
    """Delete a Dynamic Recipient List.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        id (str): ID of the Dynamic Recipient List
        project_id (str): ID of the project
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.delete(
        endpoint=f'/api/dynamicRecipientLists/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating subscription {subscription_id}")
def update_subscription(
    connection: 'Connection',
    subscription_id: str,
    project_id: str,
    body: dict,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Updates a subscription.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        subscription_id (str): ID of the subscription
        project_id (str): ID of the project
        body (dict): JSON-formatted body of the subscription
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.put(
        endpoint=f'/api/subscriptions/{subscription_id}',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error updating Dynamic Recipient List {list_id}")
def update_dynamic_recipient_list(
    connection: 'Connection',
    id: str,
    project_id: str,
    body: dict,
    fields: list[str] | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Updates a Dynamic Recipient List.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        id (str): ID of the Dynamic Recipient List
        project_id (str): ID of the project
        body (dict): JSON-formatted body of the new subscription
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.put(
        endpoint=f'/api/dynamicRecipientLists/{id}',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error getting recipients list.")
def available_recipients(
    connection: 'Connection',
    project_id: str,
    body: dict,
    delivery_type: str,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get a list of available recipients in shared list, for a given content
    and delivery type, within a given project.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        body (json): {
                    "contents": [
                        {
                        "id": "string",
                        "type": "REPORT"
                        }
                    ]
                    }
        delivery_type (str): Type of the delivery [EMAIL / FILE / PRINTER /
            HISTORY_LIST / CACHE / MOBILE / FTP]
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.


    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.post(
        endpoint='/api/subscriptions/recipients/results',
        params={
            'fields': fields,
            'deliveryType': delivery_type,
            'offset': offset,
            'limit': limit,
        },
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error getting available bursting attributes list.")
def bursting_attributes(
    connection: 'Connection',
    project_id: str,
    content_id: str,
    content_type: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get a list of available attributes for bursting feature, for a given
    content, within a given project. This endpoint returns the name, ID, and
    other information about available attributes.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        content_id (str): ID of the content
        content_type (str): Type of the content [REPORT, DOCUMENT]
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(
        endpoint='/api/subscriptions/bursting',
        params={'fields': fields, 'contentId': content_id, 'contentType': content_type},
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error sending subscription {subscription_id}")
def send_subscription(
    connection: 'Connection',
    subscription_id: str,
    project_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Send the existing subscription immediately.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        subscription_id (str): ID of subscription
        project_id (str): ID of the project
        fields (list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.post(
        endpoint=f'/api/v2/subscriptions/{subscription_id}/send',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting status for subscription {id}")
def get_subscription_status(
    connection: 'Connection',
    id: str,
    error_msg: str | None = None,
    whitelist: list | None = None,
) -> 'Response':
    """Get the status of the existing subscription.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of subscription
        error_msg (str, optional): Customized error message.
        whitelist(list, optional): list of tuples of I-Server Error and HTTP
            errors codes respectively, which will not be handled
            i.e. whitelist = [('ERR001', 500),('ERR004', 404)]

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(endpoint=f'/api/subscriptions/{id}/status')


@ErrorHandler(err_msg="Error getting dependent subscriptions for object {object_id}.")
def get_dependent_subscriptions(
    connection: 'Connection',
    object_id: str,
    object_type: str,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """List dependent subscriptions of an object.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        object_id (str): ID of the object.
        object_type (str): Type of the object.
        project_id (str, optional): ID of the project.
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint='/api/dependentSubscriptions',
        params={'objectId': object_id, 'type': object_type, 'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error getting subscription prompts.")
def get_subscription_prompts(
    connection: 'Connection',
    subscription_id: str,
    project_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """List prompt definitions and answers customized for the given subscription
    or the child subscription identifier.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`.
        subscription_id (str): ID of the subscription.
        project_id (str): ID of the project.
        error_msg (str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(
        endpoint=f'/api/subscriptions/{subscription_id}/prompts',
        headers={'X-MSTR-ProjectID': project_id},
    )
