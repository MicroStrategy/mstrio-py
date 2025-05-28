from mstrio.api import migration as migrations_api
from mstrio.connection import Connection
from mstrio.utils.helper import rename_dict_keys

REST_ATTRIBUTES_MAP = {
    'packageInfo': 'package_info',
    'importInfo': 'import_info',
}


def get(connection: Connection, id: str) -> dict:
    """Get migration by a specific ID.

    Args:
        connection: Strategy One REST API connection object
        id: ID of the Migration

    Returns:
        dict representing a migration object
    """
    data = migrations_api.get_migration(
        connection, migration_id=id, show_content='default'
    ).json()
    renamed_data = rename_dict_keys(data, REST_ATTRIBUTES_MAP)
    renamed_data['name'] = renamed_data['package_info']['name']
    return renamed_data
