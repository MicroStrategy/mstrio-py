from mstrio.connection import Connection
from mstrio.api import gateways as gateways_api
from mstrio.utils.helper import rename_dict_keys


REST_ATTRIBUTES_MAP = {'type': 'gatewayType', 'certifiedAsGateway': 'isCertified'}


def get_all(connection: Connection) -> list[dict]:
    """Get information for all gateways.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        list of dict representing gateway objects
    """
    gateways = gateways_api.get_gateways(connection).json()['gateways'].values()
    return [rename_dict_keys(item, REST_ATTRIBUTES_MAP) for item in gateways]


def get(connection: Connection, id: str) -> dict:
    """Get gateway by a specific ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the gateway

    Returns:
        dict representing gateway object
    """
    data = gateways_api.get_gateway(connection, id).json()
    return rename_dict_keys(data, REST_ATTRIBUTES_MAP)
