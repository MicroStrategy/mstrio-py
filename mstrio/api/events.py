from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error triggering event {id}")
def trigger_event(connection, id, fields=None, error_msg=None):
    """Trigger an event.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id(str): ID of the event
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    endpoint = f'/api/events/{id}/trigger'
    return connection.post(endpoint=endpoint, params={'fields': fields})


@ErrorHandler(err_msg="Error getting events list.")
def list_events(connection, fields=None, error_msg=None):
    """Get list of events.

    Args:
        connection(object): Strategy One connection object returned by
                `connection.Connection()`.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    return connection.get(endpoint='/api/events', params={'fields': fields})


@ErrorHandler(err_msg="Error getting event {id} information.")
def get_event(connection, id, fields=None, error_msg=None):
    """Get information of a specific event

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id(str): ID of the event
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.

    Returns:
        HTTP response object returned by the Strategy One REST server
    """
    return connection.get(
        endpoint=f'/api/events/{id}',
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error creating event")
def create_event(connection, body, fields=None, error_msg=None):
    """Create an event.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        body: JSON-formatted body of the new event
        fields:  Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    endpoint = '/api/events'
    return connection.post(endpoint=endpoint, params={'fields': fields}, json=body)


@ErrorHandler(err_msg="Error updating event {id}")
def update_event(connection, id, body, fields=None, error_msg=None):
    """Update an event.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        body: JSON-formatted body of the updated event
        fields:  Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    endpoint = f'/api/events/{id}'
    return connection.put(endpoint=endpoint, params={'fields': fields}, json=body)


@ErrorHandler(err_msg="Error deleting event {id}")
def delete_event(connection, id, error_msg=None):
    """Delete an event.

    Args:
        connection(object): Strategy One connection object returned by
            `connection.Connection()`.
        id: ID of the event to be deleted
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    endpoint = f'/api/events/{id}'
    return connection.delete(endpoint=endpoint)
