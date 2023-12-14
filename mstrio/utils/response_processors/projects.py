from mstrio.api import projects as projects_api
from mstrio.connection import Connection


def _prepare_rest_output_for_project_languages(response: dict, path: str) -> dict:
    default_key = 'defaultLanguage' if path == 'data' else 'default'
    default_language_id = response.get(default_key)
    language = response.get('languages').get(default_language_id)
    response[default_key] = {default_language_id: language}
    return response


def get_project_languages(connection: Connection, id: str, path: str):
    """Get languages of the project.

    Args:
        connection (Connection): MicroStrategy REST API connection object
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
        connection (Connection): MicroStrategy REST API connection object
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
