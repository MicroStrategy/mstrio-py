import logging

from mstrio.connection import Connection
from mstrio.utils.helper import camel_to_snake, snake_to_camel
from mstrio.utils.response_processors import test_center as tc_processors
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


@class_version_handler("11.5.0600")
class TestCenterSettings:
    """Object representation of Test Center Settings.

    The object will fetch the current Test Center settings. Object attributes
    (representing settings) can be modified manually.
    """

    __test__ = False  # marks this as not a pytest test class

    def __init__(self, connection: Connection):
        self._connection = connection

        # signifies keys that are settings as opposed to
        # any potentially added attributes
        self._setting_keys = set()

        self._updated_settings = set()

        # invariant: all keys are keys of self and elements of _setting_keys
        self._old_settings = {}

        self.fetch()

    def fetch(self):
        """Fetch Test Center settings and sets them as object attributes."""
        settings: dict = tc_processors.get_test_center_settings(self._connection).json()
        settings = camel_to_snake(settings)
        for key, value in settings.items():
            setattr(self, key, value)
            self._setting_keys.add(key)
        self._updated_settings.clear()
        self._old_settings.clear()

    def __setattr__(self, key, value):
        if (
            hasattr(self, "_setting_keys")
            and key in self._setting_keys
            and getattr(self, key) != value
        ):
            self._old_settings[key] = getattr(self, key)
            self._updated_settings.add(key)
        super().__setattr__(key, value)

    def update(self):
        """Update Test Center settings with the currently set values.
        On failure, reverts to last, good values.
        """
        if not self._updated_settings:
            logger.info("No settings to update.")
            return
        body = {key: getattr(self, key) for key in self._updated_settings}
        body = snake_to_camel(body)
        try:
            tc_processors.update_test_center_settings(self._connection, body)
        except Exception:
            logger.warning(
                "Failed to update Test Center settings. Reverting to old values."
            )
            for key in self._updated_settings:
                super().__setattr__(key, self._old_settings[key])
            self._updated_settings.clear()
            self._old_settings.clear()
            raise
        else:
            logger.info("Updated Test Center settings.")
            self._updated_settings.clear()
            self._old_settings.clear()
