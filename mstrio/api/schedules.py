import mstrio.config as config
from mstrio.utils.helper import response_handler


def list_schedules(connection, fields=None, error_msg=None):
    """Get list of a schedules.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(url=connection.base_url + '/api/schedules',
                                      params={'fields': fields})
    if config.debug:
        print(response.url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting schedules list."
        response_handler(response, error_msg)
    return response


def get_schedule(connection, schedule_id, fields=None, error_msg=None):
    """Get information of a specific schedule by its ID.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        schedule_id(str): ID of the schedule
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    response = connection.session.get(url=connection.base_url + '/api/schedules/' + schedule_id,
                                      params={'fields': fields})

    if config.debug:
        print(response.url)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting schedule information."
        response_handler(response, error_msg)
    return response
