from mstrio.api import datasources as datasources_api
from mstrio.connection import Connection
from mstrio.utils import helper


def get_mappings(
    connection: Connection,
    project_id: str | None = None,
    limit: int | None = None,
    default_connection_map: bool = False,
    filters: str = None,
):
    helper.validate_param_value('limit', limit, int, min_val=1, special_values=[None])
    response = datasources_api.get_datasource_mappings(
        connection=connection,
        default_connection_map=default_connection_map,
        project_id=project_id,
    )
    if response.ok:
        response = response.json()
        for mapping in response['mappings']:
            if 'locale' not in mapping:
                mapping['locale'] = {'name': '', 'id': ''}
        mappings = helper._prepare_objects(response, filters, 'mappings')
        if limit:
            mappings = mappings[:limit]
        return mappings
    else:
        return []


def update_project_datasources(connection: Connection, id: str, body: dict):
    return (
        datasources_api.update_project_datasources(
            connection=connection, id=id, body=body
        )
        .json()
        .get('datasources')
    )
