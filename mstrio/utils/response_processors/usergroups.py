from mstrio.api import usergroups as usergroups_api


def update_user_group_info(connection, id, body):
    """Update user group by a specified ID.

    Args:
        connection: MicroStrategy REST API connection object
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
