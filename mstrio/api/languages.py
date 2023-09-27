from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error creating a language.")
def create_language(connection: Connection, body: dict, fields: str | None = None):
    """Create a new language.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new language
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.post(
        endpoint='/api/languages',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error getting languages list.")
def list_languages(
    connection: Connection,
    acl: list[str] = None,
    hidden: bool = False,
    is_language_supported: bool = None,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Get a list of languages.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        acl (list[str]): Access control list filter, defaults to None
        hidden (bool): Whether to include hidden objects, defaults to False
        is_language_supported: Whether to filter by languages derived from a
            list of supported languages, defaults to None, treated as True
            by REST API
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.get(
        endpoint='/api/languages',
        params={
            'acl': acl,
            'hidden': str(hidden).lower(),
            'isLanguageSupported': str(is_language_supported).lower()
            if is_language_supported
            else is_language_supported,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error getting interface languages list.")
def list_interface_languages(connection: Connection, fields: str | None = None):
    """Get a list of interface languages.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.get(endpoint='/api/interfaceLanguages', params={'fields': fields})


@ErrorHandler(err_msg="Error getting language with ID: {id}")
def get_language(connection: Connection, id: str, fields: str | None = None):
    """Get a language by id.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): ID of the language to be retrieved from the server
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.get(endpoint=f'/api/languages/{id}', params={'fields': fields})


@ErrorHandler(err_msg="Error getting formatting settings for language with ID: {id}")
def get_language_formatting_settings(
    connection: Connection, id: str, fields: str | None = None
):
    """Get formatting settings for a language by id.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): ID of the language of the settings to be retrieved from the
            server
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.get(
        endpoint=f'/api/languages/{id}/formattingSettings',
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error updating formatting settings for language with ID: {id}")
def update_language_formatting_settings(
    connection: Connection, id: str, body: dict, fields: str | None = None
):
    """Update formatting settings for a language by id.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): ID of the language of the settings to be updated
        body (dict): JSON-formatted body of the settings update
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.patch(
        endpoint=f'/api/languages/{id}/formattingSettings',
        params={'fields': fields},
        json=body,
    )


@ErrorHandler(err_msg="Error updating language with ID: {id}")
def update_language(
    connection: Connection, id: str, body: dict, fields: str | None = None
):
    """Update a language by id.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): ID of the language to be updated
        body (dict): JSON-formatted body of the language update
        fields(str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model,
            defaults to None

    Returns:
        HTTP response object returned by the MicroStrategy REST server."""
    return connection.patch(
        endpoint=f'/api/languages/{id}',
        params={'fields': fields},
        json=body,
    )
