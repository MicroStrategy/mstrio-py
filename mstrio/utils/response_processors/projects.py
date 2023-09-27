from mstrio.api import projects as projects_api
from mstrio.connection import Connection


def get_project_languages(connection: Connection, id: str):
    """Get languages of the project.

    Args:
        connection (Connection): MicroStrategy REST API connection object
        id (string): Project ID

    Returns:
        List of languages in form of a single dictionary.
    """
    return (
        projects_api.get_project_languages(connection=connection, id=id)
        .json()
        .get('metadata')
        .get('languages')
    )
