from mstrio.api import usergroups as usergroups_api
from mstrio.utils.helper import camel_to_snake
from mstrio.utils.version_helper import is_server_min_version


def update_user_group_info(connection, id, body):
    """Update user group by a specified ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the user group
        body: dict with changes to be made

    Returns:
        dict with user group information
    """
    # We do not want information about members from patch as it is insufficient
    # to differentiate between users and user groups
    response = usergroups_api.update_user_group_info(
        connection=connection, id=id, body=body
    )
    result = response.json()
    if result.get('members'):
        result.pop('members')

    return result


def get_settings(
    connection, id, include_access=False, offset=0, limit=-1, error_msg=None
):
    response = usergroups_api.get_settings(
        connection=connection,
        id=id,
        include_access=include_access,
        offset=offset,
        limit=limit,
        error_msg=error_msg,
    ).json()

    if is_server_min_version(connection, '11.4.1200'):
        list_of_settings = [
            {key: value} for key, value in camel_to_snake(response).items()
        ]
        response = {'settings': list_of_settings}

    return response
