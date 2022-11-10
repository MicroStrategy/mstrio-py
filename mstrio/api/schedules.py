import json
from typing import Optional

from requests.adapters import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg='Error getting schedules list.')
def list_schedules(connection, fields=None, error_msg=None):
    """Get list of a schedules.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    response = connection.get(
        url=f'{connection.base_url}/api/schedules', params={'fields': fields}
    )
    if response.ok:
        # Fix for incorrect 'eventId' (expecting 'id')
        event_based_in_list = False
        response_json = response.json()
        for schedule in response_json['schedules']:
            if 'event' in schedule.keys():
                schedule['event']['id'] = schedule['event'].pop('eventId')
                event_based_in_list = True
        if event_based_in_list:
            response.encoding, response._content = 'utf-8', json.dumps(response_json).encode(
                'utf-8')

    return response


@ErrorHandler(err_msg='Error getting schedule {id} information.')
def get_schedule(connection, id, fields=None, error_msg=None):
    """Get information of a specific schedule by `schedule_id`.

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

    response = connection.get(
        url=f'{connection.base_url}/api/schedules/{id}', params={'fields': fields}
    )
    if response.ok:
        # Fix for incorrect 'eventId' (expecting 'id')
        response_json = response.json()
        if 'event' in response_json.keys():
            response_json['event']['id'] = response_json['event'].pop('eventId')
            response.encoding, response._content = 'utf-8', json.dumps(response_json).encode(
                'utf-8')

    return response


@ErrorHandler(err_msg='Error getting schedule information.')
def create_schedule(connection, body, fields=None, error_msg=None):
    """Create a new schedule using data from `body`.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        body(dict): Dictionary containing data used for creating schedule.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    # id to eventId conversion - API Problem
    if 'event' in body.keys():
        body['event']['eventId'] = body['event'].pop('id')

    response = connection.post(
        url=f'{connection.base_url}/api/schedules', json=body, params={'fields': fields}
    )
    if response.ok:
        # Fix for incorrect 'eventId' (expecting 'id')
        response_json = response.json()
        if 'event' in response_json.keys():
            response_json['event']['id'] = response_json['event'].pop('eventId')
            response.encoding, response._content = 'utf-8', json.dumps(response_json).encode(
                'utf-8')

    return response


@ErrorHandler(err_msg='Error getting schedule {id} information.')
def update_schedule(connection, id, body, fields=None, error_msg=None):
    """Alter a schedule specified by `schedule_id`, using data from `body`.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        schedule_id(str): ID of the schedule
        body(dict): Dictionary containing data used for replacing schedule.
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """

    # id to eventId conversion - API Problem
    if 'event' in body.keys():
        body['event']['eventId'] = body['event'].pop('id')

    response = connection.put(
        url=f'{connection.base_url}/api/schedules/{id}', json=body, params={'fields': fields}
    )
    if response.ok:
        # Fix for incorrect 'eventId' (expecting 'id')
        response_json = response.json()
        if 'event' in response_json.keys():
            response_json['event']['id'] = response_json['event'].pop('eventId')
        response.encoding, response._content = 'utf-8', json.dumps(response_json).encode('utf-8')

    return response


@ErrorHandler(err_msg='Error getting schedule {id} information.')
def delete_schedule(connection, id, fields=None, error_msg=None):
    """Delete a schedule specified by `schedule_id`.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        id(str): ID of the schedule
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        error_msg(str, optional): Customized error message.
    Returns:
        HTTP response object returned by the MicroStrategy REST server
    """
    return connection.delete(
        url=f'{connection.base_url}/api/schedules/{id}', params={'fields': fields}
    )


@ErrorHandler(err_msg='Error getting schedule information')
def get_contents_schedule(
        connection: "Connection",
        project_id: str,
        body: dict,
        fields: Optional[str] = None
) -> Response:
    """Get a list of available schedules for a list of contents within a given
        project.

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`.
        project_id(str): Field to filter on project id (exact match),
        body: List of contents
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.post(
        url=f'{connection.base_url}/api/schedules/results',
        headers={'X-MSTR-ProjectID': project_id},
        params={'fields': fields},
        json=body
    )
