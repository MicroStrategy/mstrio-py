from mstrio.utils.helper import response_handler


def trigger_event(connection, id, fields=None, error_msg=None):
    """Triggers an event.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(str): ID of the event
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.put(url=connection.base_url + '/api/events/' + id + '/trigger',
                                      params={'fields': fields})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error triggering event '{}'".format(id)
        response_handler(response, error_msg)
    return response


def list_events(connection, fields=None, error_msg=None):
    """Get list of a events.

    Args:
        connection(object): MicroStrategy connection object returned by
                `connection.Connection()`.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    response = connection.session.get(url=connection.base_url + '/api/events',
                                      params={'fields': fields})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting events list."
        response_handler(response, error_msg)
    return response


def get_event(connection, id, fields=None, error_msg=None):
    """Get information of a specific event

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(str): ID of the event
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(
        url=connection.base_url + '/api/events/' + id,
        params={'fields': fields},
    )

    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting event information."
        response_handler(response, error_msg)
    return response
