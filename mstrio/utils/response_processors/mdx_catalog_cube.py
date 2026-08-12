from typing import TYPE_CHECKING, Any

from mstrio.api import datasources as datasources_api
from mstrio.api import mdx_data_sources as mdx_api
from mstrio.connection import Connection
from mstrio.utils.helper import delete_none_values, get_response_json, is_valid_str_id

if TYPE_CHECKING:
    from mstrio.datasources.datasource_instance import DatasourceInstance

MDX_DATABASE_TYPES = ['microsoft_as', 'essbase', 'tm1', 'sap', 'ess_base']


def list_mdx_datasources(connection: Connection) -> list[dict[str, Any]]:
    """Return all MDX datasource instances as a list of dicts."""
    response = datasources_api.get_datasource_instances(
        connection=connection,
        database_types=MDX_DATABASE_TYPES,
    )
    return get_response_json(response).get('datasources', [])


def resolve_mdx_datasource_id(
    connection: Connection,
    mdx_datasource: 'DatasourceInstance | str',
) -> str:
    """Resolve an MDX datasource object, name, or ID to datasource ID.

    Note:
        This helper is intentionally kept in the MDX catalog processor instead
        of ``mstrio.utils.resolvers`` because the lookup is scoped to
        MDX-specific datasource types only.
    """
    datasource_id = getattr(mdx_datasource, 'id', None)
    if datasource_id:
        return datasource_id

    if is_valid_str_id(mdx_datasource):
        return mdx_datasource

    datasources = list_mdx_datasources(connection)
    matches = [
        datasource
        for datasource in datasources
        if datasource.get('name') == mdx_datasource
    ]
    if not matches:
        raise ValueError(
            'Could not find an MDX datasource with the provided ID or name: '
            f"'{mdx_datasource}'."
        )
    if len(matches) > 1:
        raise ValueError(
            'Multiple MDX datasources were found with name '
            f"'{mdx_datasource}'. Please use datasource ID instead."
        )
    return matches[0]['id']


def get_mdx_catalog_payload(
    connection: Connection,
    datasource_id: str,
    project_id: str,
) -> dict[str, Any]:
    """Return raw catalog payload for the given MDX datasource."""
    response = mdx_api.get_mdx_catalog(
        connection=connection,
        id=datasource_id,
        project_id=project_id,
    )
    return get_response_json(response)


def get_catalog_rows(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract catalog cube rows from a raw catalog payload.

    Args:
        payload: Raw JSON payload from the MDX catalog endpoint.

    Returns:
        List of catalog row dicts, each annotated with an ``'imported'``
        key. In the current payload shape, rows under ``'cubes'`` are treated
        as imported. If the API starts returning sections such as
        ``'available'`` or ``'external'``, those rows should be treated as not
        imported.
    """
    return [{**row, 'imported': True} for row in payload.get('cubes', [])]


def get_mdx_catalog_cube(
    connection: Connection,
    id: str | None = None,
    name: str | None = None,
    project_id: str | None = None,
    mdx_datasource: 'DatasourceInstance | str | None' = None,
) -> dict[str, Any]:
    """Get a single imported MDX catalog cube attribute dict.

    Args:
        connection: Strategy REST API connection object.
        id: ID of the imported MDX cube object.
        name: Exact imported MDX cube name.
        project_id: Project ID to search within. If not provided,
            the currently selected project is used.
        mdx_datasource: MDX datasource object, name, or ID used to limit the
            search.

    Returns:
        Dict with ``id``, ``name``, and ``mdx_datasource`` when a matching
        imported cube is found, or an empty dict when lookup by ``id`` finds
        no match.

    Raises:
        ValueError: If neither ``id`` nor ``name`` is provided, or if lookup
            by ``name`` finds zero or more than one match.
    """
    lookup_by_id = id is not None
    if not lookup_by_id and name is None:
        raise ValueError("Specify either 'id' or 'name'.")

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    datasource_id = (
        resolve_mdx_datasource_id(connection, mdx_datasource)
        if mdx_datasource is not None
        else None
    )
    if datasource_id is not None:
        datasource_ids = [datasource_id]
    else:
        datasource_ids = [
            datasource['id'] for datasource in list_mdx_datasources(connection)
        ]

    matches = []
    for current_datasource_id in datasource_ids:
        payload = get_mdx_catalog_payload(
            connection,
            current_datasource_id,
            project_id,
        )
        for row in get_catalog_rows(payload):
            catalog_row = {
                **row,
                'mdx_datasource': {'id': current_datasource_id},
            }
            if lookup_by_id and row.get('id') == id:
                return delete_none_values(
                    {
                        'id': catalog_row.get('id'),
                        'name': catalog_row.get('name'),
                        'mdx_datasource': catalog_row.get('mdx_datasource'),
                    },
                    recursion=False,
                )

            if not lookup_by_id and row.get('name') == name:
                matches.append(catalog_row)

    if lookup_by_id:
        return {}

    if not matches:
        raise ValueError(f"There is no MDXCatalogCube with the given name: '{name}'")
    if len(matches) > 1:
        raise ValueError(
            f'There are {len(matches)} MDXCatalogCube objects with name: '
            f"'{name}'. Please initialize with ID or pass mdx_datasource."
        )

    return delete_none_values(
        {
            'id': matches[0].get('id'),
            'name': matches[0].get('name'),
            'mdx_datasource': matches[0].get('mdx_datasource'),
        },
        recursion=False,
    )
