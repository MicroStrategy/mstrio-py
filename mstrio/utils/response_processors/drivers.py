from mstrio.connection import Connection
from mstrio.api import drivers as drivers_api
from mstrio.utils.helper import rename_dict_keys


REST_ATTRIBUTES_MAP = {'enabled': 'isEnabled'}


def get_all(connection: Connection) -> list[dict]:
    """Get information for all drivers.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        list of dict representing driver objects
    """
    drivers = drivers_api.get_drivers(connection).json()['drivers'].values()
    return [rename_dict_keys(item, REST_ATTRIBUTES_MAP) for item in drivers]


def get(connection: Connection, id: str) -> dict:
    """Get driver by a specific ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the driver

    Returns:
        dict representing driver object
    """
    data = drivers_api.get_driver(connection, id).json()
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)


def update(
    connection: Connection,
    id: str,
    body: dict,
) -> dict:
    """Update a driver.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the driver
        body: Driver update info.

    Returns:
        dict representing driver object
    """
    data = drivers_api.update_driver(connection, id, body).json()
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)
