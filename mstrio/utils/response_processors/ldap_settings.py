from typing import TYPE_CHECKING

from mstrio.api import administration as admin_api
from mstrio.utils.helper import camel_to_snake, snake_to_camel

if TYPE_CHECKING:
    from mstrio.connection import Connection


def get_ldap_settings(connection: 'Connection') -> dict:
    """Retrieves the LDAP settings stored in the I-Server metadata.

    The REST API returns every setting as an object with its name, value and
    metadata. Only the values are returned. Settings without a value on
    the I-Server are `None`.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.

    Returns:
        dict: Names of the LDAP settings (in snake case) and their values.
    """

    settings: dict = admin_api.get_ldap_info(connection).json()['settings']

    return camel_to_snake({key: value.get('value') for key, value in settings.items()})


def update_ldap_settings(connection: 'Connection', settings: dict) -> None:
    """Updates the given LDAP settings. Other settings are not changed.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        settings (dict): Names of the LDAP settings (in snake case) and their
            new values.
    """

    admin_api.update_ldap_config(connection, snake_to_camel(settings))
