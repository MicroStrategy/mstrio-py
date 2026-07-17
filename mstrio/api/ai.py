from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error enabling object with id {object_id} for AI.')
def enable_object_for_ai(
    connection: 'Connection',
    object_id: str,
    cube_type: str,
    error_msg: str | None = None,
) -> 'Response':
    """Trigger AI enablement for an object.

    Args:
        connection (Connection): Strategy REST API connection object.
        object_id (str): ID of object to enable for AI.
        cube_type (str): Type expected by dumpcubes endpoint.
        error_msg (str, optional): Custom Error Message for Error Handling.

    Returns:
        Complete HTTP response object.
    """
    body = {
        'cubeObjects': [
            {
                'cubeId': object_id,
                'cubeType': cube_type,
            }
        ]
    }
    return connection.post(endpoint='/api/cubes/dumpcubes', json=body)


@ErrorHandler(err_msg='Error fetching AI enablement status.')
def get_bot_cube_status(
    connection: 'Connection',
    cube_ids: list[str],
    error_msg: str | None = None,
) -> 'Response':
    """Fetch AI enablement status for a bot cube.

    Args:
        connection (Connection): Strategy REST API connection object.
        cube_ids (list[str]): IDs of objects to check AI enablement status
            for.
        error_msg (str, optional): Custom Error Message for Error Handling.

    Returns:
        Complete HTTP response object.
    """
    body = {'cubeIds': cube_ids}
    return connection.post(endpoint='/api/v2/bots/cubes/status', json=body)
