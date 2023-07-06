from mstrio.api import languages as languages_api
from mstrio.connection import Connection
from mstrio.utils.helper import fetch_objects


def get(connection: Connection, id: str) -> dict:
    """Get language by a specified ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the language

    Returns:
        dict representing language object
    """
    return languages_api.get_language(connection=connection, id=id).json()


def get_all(connection: Connection, limit: int, filters) -> list[dict]:
    """Get list of languages.

    Args:
        connection: MicroStrategy REST API connection object
        limit: limit of languages to list
        filters: filters

    Returns:
        list of dicts representing languages"""
    return fetch_objects(
        connection=connection,
        api=languages_api.list_languages,
        limit=limit,
        filters=filters,
        dict_unpack_value="languages",
    )


def get_interface_languages(connection: Connection) -> list[dict]:
    """Get list of interface languages.

    Args:
        connection: MicroStrategy REST API connection object

    Returns:
        list of dicts representing interface languages"""
    return (
        languages_api.list_interface_languages(connection=connection)
        .json()
        .get('interfaceLanguages')
    )


def get_formatting_settings(connection: Connection, id: str) -> dict:
    """Get formatting settings for a language with specified ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the language

    Returns:
        dict representing language object formatting settings
    """
    return (
        languages_api.get_language_formatting_settings(connection=connection, id=id)
        .json()
        .get('formattingSettings')
        .get('timeInterval')
    )


def update_formatting_settings(connection: Connection, id: str, body: dict) -> dict:
    """Update formatting settings for a language with specified ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the language
        body: json body for the request

    Returns:
        dict representing language object formatting settings
    """
    return (
        languages_api.update_language_formatting_settings(
            connection=connection, id=id, body=body
        )
        .json()
        .get('formattingSettings')
        .get('timeInterval')
    )


def create(connection: Connection, body: dict) -> dict:
    """Create a language based on provided body.

    Args:
        connection: MicroStrategy REST API connection object
        body: dictionary with language details

    Returns:
        dict representing language object"""
    return languages_api.create_language(connection=connection, body=body).json()


def update(connection: Connection, id: str, body: dict) -> dict:
    """Update a language with specified ID.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the language
        body: json body for the request

    Returns:
        dict representing language object
    """
    return languages_api.update_language(connection=connection, id=id, body=body).json()
