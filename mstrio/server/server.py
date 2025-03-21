import logging

from mstrio import config
from mstrio.api import administration
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.settings.base_settings import BaseSettings
from mstrio.utils.settings.setting_types import SettingValue
from mstrio.utils.version_helper import (
    is_server_min_version,
    meets_minimal_version,
    method_version_handler,
)

logger = logging.getLogger(__name__)


class ServerSettings(BaseSettings):
    """Object representation of Strategy One I-Server Settings.

    Used to fetch, view, modify, update, export to file, import from file and
    validate Server settings.

    The object can be optionally initialized with `connection`, which will
    automatically fetch the current I-Server settings. If not specified,
    settings can be loaded from file using `import_from()` method. Object
    attributes (representing settings) can be modified manually. Lastly, the
    object can be applied to any project using the `update()` method.

    Attributes:
        settings: settings_value
    """

    _TYPE = "allServerSettings"
    _READ_ONLY = ['historyListRunningStatus']
    _CONVERSION_MAP = {
        'pdfMaxMemoryConsumption': 'B',
        'xmlMaxMemoryConsumption': 'B',
        'excelMaxMemoryConsumption': 'B',
        'htmlMaxMemoryConsumption': 'B',
        'workSetMaxMemoryConsumption': 'KB',
        'catalogMaxMemoryConsumption': 'KB',
    }

    def __init__(self, connection: Connection):
        """Initialize `ServerSettings` object.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`
        """
        # fix conversion map due to changes in REST Layer
        if meets_minimal_version(connection.iserver_version, "11.3.0000"):
            self._CONVERSION_MAP.update(
                {
                    'workSetMaxMemoryConsumption': 'B',
                    'catalogMaxMemoryConsumption': 'B',
                }
            )
        if meets_minimal_version(connection.iserver_version, "11.4.0300"):
            self._READ_ONLY.append('enableHtmlContentInDossier')
        super(BaseSettings, self).__setattr__('_connection', connection)
        self._configure_settings()
        self.fetch()

    @method_version_handler('11.3.0000')
    def fetch(self) -> None:
        """Fetch current I-Server settings and update this `ServerSettings`
        object."""
        super().fetch()

    @method_version_handler('11.3.0000')
    def update(self) -> None:
        """Update the current I-Server settings using this `ServerSettings`
        object."""
        set_dict = self._prepare_settings_push()
        if hl_property := set_dict.get('hLRepositoryType', {}):
            if (
                is_server_min_version(self._connection, '11.4.0600')
                and hl_property.get('value') != 3
            ):
                set_dict.pop('hLRepositoryType')
        if not set_dict and config.verbose:
            logger.info('No settings to update.')
            return

        response = administration.update_iserver_settings(self._connection, set_dict)
        if response.status_code in [200, 204] and config.verbose:
            logger.info('I-Server settings updated.')
        if response.status_code == 207:
            helper.exception_handler("Some settings could not be updated.", Warning)
        super().update()

    def _fetch(self) -> dict:
        settings = administration.get_iserver_settings(self._connection).json()
        return self._prepare_settings_fetch(settings)

    @method_version_handler('11.3.0000')
    def _get_config(self):
        if not ServerSettings._CONFIG:
            response = administration.get_iserver_settings_config(self._connection)
            ServerSettings._CONFIG = response.json()
            super()._get_config()

    def __override_settings_config(self, value: SettingValue) -> None:  # NOSONAR
        # config not accurate, needs override DE179361
        if not meets_minimal_version(self._connection.iserver_version, "11.3.0000"):
            if value.name in ['maxJobsPerServer', 'maxInteractiveJobsPerServer']:
                value.max_value = 100000
            elif value.name == 'maxUserConnectionPerServer':
                value.max_value = 1000000
            elif value.name == 'cacheCleanUpFrequency':
                value.min_value = 0
                value.options.append({'name': 'No Limit', 'value': -1})
            elif value.name == 'backupPeriodicity':
                value.min_value = 0
                value.max_value = 99999
            elif value.name == 'xmlMaxMemoryConsumption':
                value.options.clear()
            elif value.name == 'hLAutoDeleteMsgCount':
                value.options.append({'name': 'No Limit', 'value': -1})
            elif value.name == 'catalogMaxMemoryConsumption':
                value.min_value = 1
                value.options.append({"name": "Disabled", "value": -1})
