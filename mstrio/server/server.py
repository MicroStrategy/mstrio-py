from typing import Dict, TYPE_CHECKING

from mstrio.api import administration
import mstrio.config as config
import mstrio.utils.helper as helper
from mstrio.utils.settings import BaseSettings

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ServerSettings(BaseSettings):
    """Object representation of MicroStrategy I-Server Settings.

    Used to fetch, view, modify, update, export to file, import from file and
    validate Server settings.

    The object can be optionally initialized with `connection`, which will
    automatically fetch the current I-Server settings. If not specified,
    settings can be loaded from file using `import_from()` method. Object
    attributes (representing settings) can be modified manually. Lastly, the
    object can be applied to any application using the `update()` method.

    Attributes:
        settings: settings_value
    """

    _TYPE = "allServerSettings"
    _READ_ONLY_SETTINGS = ['historyListRunningStatus']
    _CONVERTION_DICT = {
        'workSetMaxMemoryConsumption': 'KB',
        'pdfMaxMemoryConsumption': 'B',
        'xmlMaxMemoryConsumption': 'B',
        'excelMaxMemoryConsumption': 'B',
        'catalogMaxMemoryConsumption': 'KB',
        'htmlMaxMemoryConsumption': 'B'
    }

    def __init__(self, connection: "Connection"):
        """Initialize `ServerSettings` object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
        """
        super(BaseSettings, self).__setattr__('_connection', connection)
        self._configure_settings()
        self.fetch()

    def fetch(self) -> None:
        """Fetch current I-Server settings and update this `ServerSettings`
        object."""
        super(ServerSettings, self).fetch()

    def update(self) -> None:
        """Update the current I-Server settings using this `ServerSettings`
        object."""
        set_dict = self._prepare_settings_push()
        response = administration.update_iserver_settings(self._connection, set_dict)
        if response.status_code in [200, 204] and config.verbose:
            print("I-Server settings updated.")
        if response.status_code == 207:
            helper.exception_handler("Some settings could not be updated.", Warning)

    def _fetch(self) -> Dict:
        settings = administration.get_iserver_settings(self._connection).json()
        return self._prepare_settings_fetch(settings)

    def _get_config(self):
        if not ServerSettings._CONFIG:
            response = administration.get_iserver_settings_config(self._connection)
            ServerSettings._CONFIG = response.json()
