import logging
from copy import deepcopy
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.utils.response_processors import ldap_settings as ldap_processors
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@class_version_handler('11.3.0000')
class LDAPSettings:
    """Object representation of the Strategy I-Server LDAP settings.

    The object fetches the current LDAP settings, such as the LDAP server
    connection, the search filters and the options of the LDAP batch import.
    Object attributes (representing settings) can be modified manually and
    applied using the `update()` method, which sends only the modified
    settings.

    Note:
        The I-Server stops a running LDAP batch import when the LDAP settings
        are updated.

    Note:
        To clear a text setting, set it to an empty string. `None` is ignored
        by the I-Server.
    """

    def __init__(self, connection: 'Connection'):
        """Initialize `LDAPSettings` object.

        Args:
            connection: Strategy connection object returned by
                `connection.Connection()`
        """
        self._connection = connection
        self._fetched_settings: dict = {}
        self.fetch()

    def fetch(self) -> None:
        """Fetch the LDAP settings and set them as object attributes.
        Modifications which were not applied using `update()` are discarded."""
        self._fetched_settings = ldap_processors.get_ldap_settings(self._connection)
        # copy, so that in-place modifications (e.g. of lists) are detected
        for key, value in deepcopy(self._fetched_settings).items():
            setattr(self, key, value)

    def update(self) -> None:
        """Update the LDAP settings on I-Server with the modified values."""
        body = {
            key: getattr(self, key)
            for key, value in self._fetched_settings.items()
            if getattr(self, key) != value
        }
        if not body:
            if config.verbose:
                logger.info("No LDAP settings to update.")
            return

        ldap_processors.update_ldap_settings(self._connection, body)
        if config.verbose:
            logger.info("Updated LDAP settings.")
        # the I-Server can change other settings as well
        self.fetch()

    def list_properties(self) -> dict:
        """Return the LDAP settings and their values as a dictionary."""
        return {key: getattr(self, key) for key in self._fetched_settings}
