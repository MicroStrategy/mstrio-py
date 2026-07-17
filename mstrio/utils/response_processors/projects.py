import json

from mstrio.api import objects as objects_api
from mstrio.api import projects as projects_api
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.entity import ObjectTypes

PA_CONFIGURATION_PROJECT_ID = '38A062302D4411D28E71006008960167'
PA_CONFIGURATION_PROPERTIES_SET_ID = '03EC6B029B7D4fc260A147C8110965A3'


def _prepare_rest_output_for_project_languages(response: dict, path: str) -> dict:
    default_key = 'defaultLanguage' if path == 'data' else 'default'
    default_language_id = response.get(default_key)
    language = response.get('languages').get(default_language_id)
    response[default_key] = {default_language_id: language}
    return response


def get_project_languages(connection: Connection, id: str, path: str):
    """Get languages of the project.

    Args:
        connection (Connection): Strategy REST API connection object
        id (string): Project ID
        path (string): Path to the languages.
            Available values:
                - `data`
                - `metadata`

    Returns:
        List of languages in form of a single dictionary.
    """
    return (
        projects_api.get_project_languages(connection=connection, id=id)
        .json()
        .get(path)
        .get('languages')
    )


def get_default_language(connection: Connection, id: str, path: str):
    """Get default language of the project.

    Args:
        connection (Connection): Strategy REST API connection object
        id (string): Project ID
        path (string): Path to the languages.
            Available values:
                - `data`
                - `metadata`
    """
    return _prepare_rest_output_for_project_languages(
        projects_api.get_project_languages(connection=connection, id=id)
        .json()
        .get(path),
        path,
    ).get('defaultLanguage' if path == 'data' else 'default')


def update_project_languages(connection: Connection, id: str, body: dict, path: str):
    return (
        projects_api.update_project_languages(connection=connection, id=id, body=body)
        .json()
        .get(path)
        .get('languages')
    )


def update_current_mode(connection: Connection, id: str, body: dict):
    return (
        projects_api.update_project_languages(connection=connection, id=id, body=body)
        .json()
        .get('data')
        .get('currentMode')
    )


def update_default_language(connection: Connection, id: str, body: dict):
    return _prepare_rest_output_for_project_languages(
        projects_api.update_project_languages(connection=connection, id=id, body=body)
        .json()
        .get('data'),
        path='data',
    ).get('defaultLanguage')


def get_project_internalization(connection: Connection, id: str):
    response = projects_api.get_project_languages(connection=connection, id=id).json()

    for path in ['data', 'metadata']:
        response[path] = _prepare_rest_output_for_project_languages(
            response=response[path], path=path
        )

    return response


def get_project_lock(connection: Connection, id: str):
    return {
        'lock_status': projects_api.get_project_lock(
            connection=connection, id=id
        ).json()
    }


def _parse_pa_projects_properties(properties: list[dict]) -> list[dict]:
    """Parse Platform Analytics project metadata from property-set data."""

    global_pa_project_id: str | None = None
    tenant_pa_project_ids: set[str] = set()

    for prop in properties:
        if not isinstance(prop, dict):
            continue

        prop_id = prop.get('id')
        value = prop.get('value')

        if prop_id == 2 and isinstance(value, str) and not global_pa_project_id:
            global_pa_project_id = value

        if prop_id != 3:
            continue

        if not isinstance(value, str):
            continue

        try:
            payload = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(payload, dict):
            continue

        # If global PA project ID have not been set from prop_id = 2,
        # try to get it from the payload
        project_id = payload.get('projectID')
        if not global_pa_project_id and isinstance(project_id, str) and project_id:
            global_pa_project_id = project_id

        tenant_project_ids = payload.get('tenantProjectID')
        if isinstance(tenant_project_ids, list):
            tenant_pa_project_ids.update(
                tenant_project_id
                for tenant_project_id in tenant_project_ids
                if isinstance(tenant_project_id, str) and tenant_project_id
            )

    pa_projects: list[dict] = []
    if global_pa_project_id:
        pa_projects.append(
            {
                'id': global_pa_project_id,
                'platform_analytics': True,
            }
        )

    pa_projects.extend(
        {
            'id': tenant_project_id,
            'tenant_platform_analytics': True,
        }
        for tenant_project_id in tenant_pa_project_ids
        if tenant_project_id != global_pa_project_id
    )

    return pa_projects


def get_pa_projects(connection: Connection) -> list[dict]:
    """Retrieve and parse Platform Analytics projects metadata."""

    response = objects_api.get_property_set(
        connection=connection,
        id=PA_CONFIGURATION_PROJECT_ID,
        obj_type=ObjectTypes.CONFIGURATION.value,
        property_set_id=PA_CONFIGURATION_PROPERTIES_SET_ID,
    )

    pa_projects_data = response.json()
    if not isinstance(pa_projects_data, list):
        helper.exception_handler(
            "Could not retrieve Platform Analytics project metadata.",
            exception_type=ConnectionError,
        )
        return []

    return _parse_pa_projects_properties(pa_projects_data)


def get_project_duplications(connection: Connection, limit: int | None) -> list:
    """Get project duplications."""
    limit_per_call = 1000
    offset = 0
    duplications = []

    while True:
        batch_limit = (
            min(limit_per_call, limit - len(duplications))
            if limit is not None
            else limit_per_call
        )
        new_duplications = (
            projects_api.get_project_duplications(
                connection=connection,
                limit=batch_limit,
                offset=offset,
            )
            .json()
            .get('duplications', [])
        )
        if len(new_duplications) == 0:
            break
        duplications.extend(new_duplications)
        offset += len(new_duplications)
        if limit is not None and len(duplications) >= limit:
            duplications = duplications[:limit]
            break
        if len(new_duplications) < batch_limit:
            break

    return duplications
