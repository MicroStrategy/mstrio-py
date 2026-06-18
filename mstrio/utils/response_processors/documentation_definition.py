from typing import Any

from requests import Response

from mstrio.api import documentation_definitions as documentation_definitions_api
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.api_helpers import add_property_to_patch_operations


def get_documentation_definition(
    connection: Connection,
    id: str,
) -> dict[str, Any]:
    """Get a single documentation definition as parsed JSON.

    Flattens the nested `configuration` and `objectCategories` blocks
    from the API response into top-level keys before returning.
    Creates an owner object from ownerID and ownerName.
    """
    data = documentation_definitions_api.get_documentation_definition(
        connection=connection,
        documentation_definition_id=id,
    ).json()

    # From other endpoints we get unnested properties
    # so we unpack here to normalize
    configuration = data.pop('configuration', {}) or {}
    object_categories = configuration.pop('objectCategories', {}) or {}

    data.update(configuration)
    data.update(object_categories)

    helper.normalize_owner_payload(data)

    return data


def get_documentation_definition_list(
    connection: Connection,
    id: str | None = None,
    name: str | None = None,
    sort_by: str | None = None,
    include_embedded: bool | None = None,
    tenant_id: str | None = None,
    owner_id: str | None = None,
    project_id: str | None = None,
    date_created: str | None = None,
    last_run: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Get documentation definition list as parsed JSON."""
    return helper.fetch_objects(
        connection=connection,
        api=documentation_definitions_api.get_documentation_definition_list,
        limit=limit,
        filters={},
        dict_unpack_value='documentationDefinitions',
        id=id,
        name=name,
        sort_by=sort_by,
        include_embedded=include_embedded,
        tenant_id=tenant_id,
        owner_id=owner_id,
        project_id=project_id,
        date_created=date_created,
        last_run=last_run,
        offset=offset,
    )


def create_documentation_definition(
    connection: Connection,
    body: dict[str, Any],
) -> str:
    """Create a documentation definition and return the definition ID."""
    response = documentation_definitions_api.create_documentation_definition(
        connection=connection,
        body=body,
    ).json()
    return response.get('documentationDefinitionId', '')


def delete_documentation_definition(
    connection: Connection,
    id: str,
) -> 'Response':
    """Delete documentation definition by ID."""
    return documentation_definitions_api.delete_documentation_definition(
        connection=connection,
        documentation_definition_id=id,
    )


def update_documentation_definition(
    connection: Connection,
    id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Update documentation definition and return parsed JSON response."""
    body = add_property_to_patch_operations(
        body=body,
        property_name='id',
        property_value=id,
    )

    return documentation_definitions_api.update_documentation_definition(
        connection=connection,
        documentation_definition_id=id,
        body=body,
    ).json()
