from typing import Any

from requests import Response

from mstrio.api import documentation as documentation_api
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.api_helpers import add_property_to_patch_operations


def get_documentation(connection: Connection, id: str) -> dict[str, Any]:
    """Get a single documentation item as parsed JSON."""
    documentations = get_documentation_list(
        connection=connection,
        id=id,
    )
    return documentations[0] if documentations else {}


def get_documentation_list(
    connection: Connection,
    id: str | None = None,
    documentation_name: str | None = None,
    sort_by: str | None = None,
    documentation_definition_id: str | None = None,
    project_id: str | None = None,
    owner_id: str | None = None,
    status: str | None = None,
    date_created: str | None = None,
    size: str | None = None,
    fields: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Get unpacked list of documentation items."""
    documentations = helper.fetch_objects(
        connection=connection,
        api=documentation_api.get_documentation_list,
        limit=limit,
        filters={},
        dict_unpack_value='documentation',
        id=id,
        documentation_name=documentation_name,
        sort_by=sort_by,
        documentation_definition_id=documentation_definition_id,
        project_id=project_id,
        owner_id=owner_id,
        status=status,
        date_created=date_created,
        size=size,
        fields=fields,
        offset=offset,
    )

    return [
        helper.normalize_owner_payload(documentation)
        for documentation in documentations
    ]


def create_documentation(
    connection: Connection,
    documentation_definition_id: str,
) -> dict[str, Any]:
    """Create a documentation job and return parsed JSON response."""
    response = documentation_api.create_documentation(
        connection=connection,
        documentation_definition_id=documentation_definition_id,
    ).json()

    if 'documentationId' in response:
        response['id'] = response.pop('documentationId')

    return response


def delete_documentation(
    connection: Connection,
    id: str,
) -> 'Response':
    """Delete documentation job by ID."""
    return documentation_api.delete_documentation(
        connection=connection,
        id=id,
    )


def update_documentation(
    connection: Connection,
    id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Update documentation job and return parsed JSON response."""
    body = add_property_to_patch_operations(
        body=body,
        property_name='id',
        property_value=id,
    )
    return documentation_api.update_documentation(
        connection=connection,
        id=id,
        body=body,
    ).json()


def get_documentation_resource(
    connection: Connection,
    id: str,
    resource_id: str,
    fields: str | None = None,
) -> dict[str, Any]:
    """Get documentation resource payload as parsed JSON."""
    return documentation_api.get_documentation_resource(
        connection=connection,
        id=id,
        resource_id=resource_id,
        fields=fields,
    ).json()


def export_documentation(
    connection: Connection,
    id: str,
    export_format: str | None = None,
) -> dict[str, Any]:
    """Export documentation and return binary with response metadata."""
    response = documentation_api.export_documentation(
        connection=connection,
        id=id,
        export_format=export_format,
    )

    content_disposition = response.headers.get('Content-Disposition', '')
    filename = content_disposition.partition('filename=')[2].split(';')[0].strip('"')

    if not filename:
        extension = {
            'csv': '.csv',
            'json': '.json',
            'excel': '.xlsx',
        }.get(export_format, '.bin')
        filename = f"{id}{extension}"

    return {
        'filename': filename,
        'file_binary': response.content,
    }


def get_documentation_status(
    connection: Connection,
    documentation_ids: str | None = None,
) -> list[dict[str, Any]]:
    """Get documentation job status payload as parsed JSON."""
    response = documentation_api.get_documentation_status(
        connection=connection,
        documentation_ids=documentation_ids,
    ).json()
    return response.get('documentationStatuses', [])


def get_documentation_objects(
    connection: Connection,
    id: str,
    documentation_object_name: str | None = None,
    object_type: str | None = None,
    sort_by: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
) -> list[dict[str, Any]]:
    """Get unpacked list of documentation objects."""
    return helper.fetch_objects(
        connection=connection,
        api=documentation_api.get_documentation_objects,
        limit=limit,
        filters={},
        dict_unpack_value='objects',
        id=id,
        documentation_object_name=documentation_object_name,
        object_type=object_type,
        sort_by=sort_by,
        offset=offset,
        fields=fields,
    )
