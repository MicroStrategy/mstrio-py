import mstrio.config as config
from mstrio.utils.helper import response_handler, exception_handler


def list_subscriptions(connection, project_id, fields=None, offset=0, limit=-1, error_msg=None):
    """Get list of a subscriptions.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        project_id(str): ID of the project
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(url=connection.base_url + '/api/subscriptions',
                                      params={'fields': fields},
                                      headers={'X-MSTR-ProjectID': project_id})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting subscription list."
        response_handler(response, error_msg)
    return response


def get_subscription(connection, subscription_id, project_id, fields=None, error_msg=None):
    """Get information of a specific subscription for a given project.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        subscription_id(str): ID of the subscription
        project_id(str): ID of the project
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(
        url=connection.base_url + '/api/subscriptions/' + subscription_id,
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )

    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting subscription information."
        response_handler(response, error_msg)
    return response


def create_subscription(connection, project_id, body, fields=None, error_msg=None):
    """Create a new subscription.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        project_id(str): ID of the project
        body: JSON-formatted doby of the new subscription, example;
        {"name": "My new subscription",
        "allowDeliveryChanges": false,
        "allowPersonalizationChanges": false,
        "allowUnsubscribe": false,
        "sendNow": false,
        "schedules": [
            {
            "id": "string"
            }
        ],
        "contents": [
            {
            "id": "string",
            "type": "report",
            "personalization": {
                "compressed": false,
                "formatMode": "DEFAULT",
                "viewMode": "DEFAULT",
                "formatType": "PLAIN_TEXT",
                "delimiter": "string",
                "bursting": {
                "slicingAttributes": [
                    "string"
                ],
                "addressAttributeId": "string",
                "deviceId": "string",
                "formId": "string"
                },
                "prompt": {
                "enabled": false,
                "instanceId": "string"
                }
            }
            }
        ],
        "recipients": [
            {
            "id": "string",
            "includeType": "TO"
            }
        ],
        "delivery": {
            "mode": "EMAIL",
            "expiration": "2020-09-21T10:35:01.911Z",
            "contactSecurity": true,
            "email": {
            "subject": "string",
            "message": "string",
            "filename": "string",
            "spaceDelimiter": "string",
            "includeLink": true,
            "includeData": true,
            "sendToInbox": true,
            "overwriteOlderVersion": true,
            "zip": {
                "filename": "string",
                "password": "string",
                "passwordProtect": true
            }
            },
            "file": {
            "filename": "string",
            "spaceDelimiter": "string",
            "burstSubFolder": "string",
            "zip": {
                "filename": "string",
                "password": "string",
                "passwordProtect": true
            }
            },
            "printer": {
            "copies": 0,
            "rangeStart": 0,
            "rangeEnd": 0,
            "collated": true,
            "orientation": "PORTRAIT",
            "usePrintRange": true
            },
            "ftp": {
            "spaceDelimiter": "string",
            "filename": "string",
            "zip": {
                "filename": "string",
                "password": "string",
                "passwordProtect": true
            }
            },
            "cache": {
            "cacheType": "RESERVED",
            "shortcutCacheFormat": "RESERVED"
            },
            "mobile": {
            "clientType": "RESERVED",
            "deviceId": "string",
            "doNotCreateUpdateCaches": true,
            "overwriteOlderVersion": true,
            "reRunHl": true
            },
            "historyList": {
            "deviceId": "string",
            "doNotCreateUpdateCaches": true,
            "overwriteOlderVersion": true,
            "reRunHl": true
            },
            "iserverExpiration": "string"
        }
        }
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.post(
        url=connection.base_url + '/api/subscriptions',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating new subscription."
        response_handler(response, error_msg)
    return response


def remove_subscription(connection, subscription_id, project_id, error_msg=None,
                        exception_type=None):
    """Remove (Unsubscribe) the subscription using subscription id.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        subscription_id(str): ID of the subscription
        project_id(str): ID of the project
        error_msg(str, optional): Customized error message.
        exception_type (Exception): Instance of Exception or Warning class

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.delete(
        url=connection.base_url + '/api/subscriptions/' + subscription_id,
        headers={'X-MSTR-ProjectID': project_id},
    )
    if config.debug:
        print(response.url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error unsubscribing Subscription {}".format(subscription_id)
        if exception_type is None:
            response_handler(response, error_msg)
        else:
            exception_handler(error_msg, exception_type)
    return response


def update_subscription(connection, subscription_id, project_id, body, fields=None,
                        error_msg=None):
    """Updates a subscription.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        subscription_id(str): ID of the subscription
        project_id(str): ID of the project
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.put(
        url=connection.base_url + '/api/subscriptions/' + subscription_id,
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error updating subscription '{}'".format(subscription_id)
        response_handler(response, error_msg)
    return response


def available_recipients(connection, project_id, body, delivery_type, offset=0, limit=-1,
                         fields=None, error_msg=None):
    """Get a list of available recipients in shared list, for a given content
    and delivery type, within a given project.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id(str): ID of the project
        body(json): {
                    "contents": [
                        {
                        "id": "string",
                        "type": "REPORT"
                        }
                    ]
                    }
        delivery_type(str): Type of the delivery [EMAIL / FILE / PRINTER /
            HISTORY_LIST / CACHE / MOBILE / FTP]
        offset (integer, optional): Starting point within the collection of
            returned search results. Used to control paging behavior.
        limit (integer, optional): Maximum number of items returned for a single
            search request. Used to control paging behavior. Use -1 for no limit
            (subject to governing settings).
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.


    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.post(
        url=connection.base_url + '/api/subscriptions/recipients/results',
        params={
            'fields': fields,
            'deliveryType': delivery_type,
            'offset': offset,
            'limit': limit
        },
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting recipients list."
        response_handler(response, error_msg)
    return response


def bursting_attributes(connection, project_id, content_id, content_type, fields=None,
                        error_msg=None):
    """Get a list of available attributes for bursting feature, for a given
    content, within a given project. This endpoint returns the name, ID, and
    other information about available attributes.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id(str): ID of the project
        content_id(str): ID of the content
        content_type(str): Type of the content [REPORT, DOCUMENT]
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(
        url=connection.base_url + '/api/subscriptions/bursting',
        params={
            'fields': fields,
            'contentId': content_id,
            'contentType': content_type
        },
        headers={'X-MSTR-ProjectID': project_id},
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting available bursting attributes list."
        response_handler(response, error_msg)
    return response


def send_subscription(connection, subscription_id, project_id, body, fields=None, error_msg=None):
    """Send the existing subscription immediately.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`
        subscription_id(str): ID of subscription
        project_id(str): ID of the project
        body (dict): body of the request
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(
        url=connection.base_url + '/api/subscriptions/' + subscription_id + '/send',
        params={'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )
    if not response.ok:
        if error_msg is None:
            error_msg = "Error sending subscription."
        response_handler(response, error_msg)
    return response
