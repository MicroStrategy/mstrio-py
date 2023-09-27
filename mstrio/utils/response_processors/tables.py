from mstrio.api import tables as tables_api
from mstrio.connection import Connection


def update_structure(
    connection: Connection,
    id: str,
    column_merge_option: str | None = None,
    ignore_table_prefix: bool | None = None,
):
    data = tables_api.update_structure(
        connection, id, column_merge_option, ignore_table_prefix
    ).json()

    data.update(data.pop('information', {}))
    data.update({'id': data.pop('objectId', None)})

    return data
