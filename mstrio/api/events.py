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
