from abc import ABCMeta, abstractmethod
import json
import logging
from pprint import pprint
from sys import version_info
from typing import Any, Dict, List, Optional, Union
import warnings

from pandas import DataFrame, Series

from mstrio import config
import mstrio.utils.helper as helper

from .setting_types import DeprecatedSetting, SettingValue, SettingValueFactory
from .settings_helper import convert_settings_to_byte, convert_settings_to_mega_byte
from .settings_io import CSVSettingsIO, JSONSettingsIO, PickleSettingsIO, SettingsSerializerFactory

logger = logging.getLogger(__name__)


class BaseSettings(metaclass=ABCMeta):
    """Base class for fetching and updating Project or Server Settings. The
    settings object can be optionally initialized with `connection` and `id`,
    which will automatically fetch the current settings for the specified
    object. If not specified, settings can be loaded from file using
    `import_from()` method. Settings attributes can be modified manually.
    Lastly, the settings object can be validated and applied to a given object
    (Project, Server) using the `update()` method.

    Attributes:
        settings: settings
    """
    _CONFIG: Dict = {}
    # !NOTE define in child classes
    _TYPE: Union[str, None] = None
    _READ_ONLY: List[str] = []
    _CONVERSION_MAP: Dict[str, str] = {}

    def alter(self, **settings):
        """Alter settings in a command manager like way."""
        for setting, value in settings.items():
            setattr(self, setting, value)

    def fetch(self) -> None:
        """Fetch current settings from I-Server and update this Settings
        object."""
        prepared_settings = self._fetch()
        for key, value in prepared_settings.items():
            if hasattr(self, key):
                setting_obj = getattr(self, key)
                setting_obj.value = value
                super().__setattr__(key, setting_obj)

    @abstractmethod
    def _fetch(self):
        pass

    @abstractmethod
    def update(self) -> None:
        """Update the current settings on I-Server using this Settings
        object."""
        pass

    def _get_config(self):
        """Fetch the settings config to be used in this Settings class."""
        for setting, cfg in self._CONFIG.items():
            setting_type = cfg.get('type')
            if setting_type is None:
                self._READ_ONLY.append(setting)
            cfg.update({'name': setting})

    def compare_with_files(self, files: List[str], show_diff_only: bool = False) -> DataFrame:
        """Compare the current project settings to settings in file/files
        Args:
            files (str): List of paths to the settings files. Supported settings
                files are JSON, CSV, Pickle. Ex: "/file.csv"
            show_diff_only(bool, optional): Whether to display all settings or
                only different from first project in list.
        Returns:
            Dataframe with values of current settings and settings from files.
        """
        current = DataFrame.from_dict(
            self.list_properties(show_names=True), orient='index', columns=['value']
        ).reset_index()
        base = 'current value'
        current.columns = ['setting', base]
        for proj in files:
            self.import_from(proj)
            current[proj] = self.to_dataframe()['value']
        if show_diff_only:
            index = Series([True] * len(current['setting']))
            for proj_name in files:
                compare = current[base].eq(current[proj_name])
                index = compare & index
            current = current[~index]
            if current.empty and config.verbose:
                logger.info(
                    'There is no difference between current settings and settings from files.'
                )
        return current

    def to_csv(self, name: str) -> None:
        """Export the current project settings to the csv file.

        Args:
            name (str): Name of file
        """
        CSVSettingsIO.to_file(file=name, settings_obj=self)

    def to_json(self, name: str) -> None:
        """Export the current project settings to the json file
        Args:
            name (str): Name of file
        """
        JSONSettingsIO.to_file(file=name, settings_obj=self)

    def to_pickle(self, name: str) -> None:
        """Export the current project settings to the pickle file
        Args:
            name (str): Name of file
        """
        PickleSettingsIO.to_file(file=name, settings_obj=self)

    def import_from(self, file: str) -> None:
        """Import project settings from a 'csv', 'json' or 'pickle' file.

        Args:
            file (str): Path to the file with supported extension type name.
                Ex: "<path>/file.csv"
        """
        # Extract settings from supported file
        serializer = SettingsSerializerFactory().get_serializer(file)
        settings_dict = serializer.from_file(file, self)

        # Try to validate settings by fetching settings from I-Server
        self._validate_settings(settings_dict)

        # If no Exception was raised, assign the settings to the object
        for (setting, value) in settings_dict.items():
            setattr(self, setting, value)
        if config.verbose:
            logger.info(f"Settings imported from '{file}'")

    def list_properties(self, show_names: bool = True) -> dict:
        """Return settings and their values as dictionary.

        Args:
            show_names: if True, return meaningful setting values, else, return
                exact setting values
        """
        if show_names:
            return {
                key: self.__dict__[key]._get_value()
                for key in sorted(self.__dict__)
                if not key.startswith('_')
            }
        else:
            return {
                key: self.__dict__[key].value
                for key in sorted(self.__dict__)
                if not key.startswith('_')
            }

    def to_dataframe(self) -> DataFrame:
        """Return a `DataFrame` object containing settings and their values."""

        df = DataFrame.from_dict(self.list_properties(), orient='index', columns=['value'])
        df.reset_index(inplace=True)
        df.rename({'index': 'setting'}, axis=1, inplace=True)
        return df

    @property
    def info(self) -> None:
        if version_info.major >= 3 and version_info.minor >= 7:
            pprint(self.list_properties(), sort_dicts=False)
        else:
            pprint(self.list_properties())

    @property
    def setting_types(self) -> DataFrame:
        df = DataFrame.from_dict(self._CONFIG, orient='index')
        df.drop(
            ['name', 'read_only', 'reboot_rule', 'deprecated'],
            axis='columns',
            inplace=True,
            errors='ignore'
        )
        return df

    def _validate_settings(
        self,
        settings: Optional[dict] = None,
        bad_setting=Warning,
        bulk_error=True
    ) -> None:
        """Validate setting-value pairs and raise AttributeError or TypeError
        if invalid. If `bad_setting` or `bad_type` is of type Exception, then
        Exception is raised as soon as the first invalid pair is found. If they
        are of type Warning the validation will continue and not raise error.

        Raises:
            ValueError if `bulk_error` True, tries to evaluate all settings.
        """
        settings = settings if settings else self.list_properties(show_names=False)
        bad_settings_keys = []

        for setting, value in settings.items():
            if setting not in self._CONFIG.keys():
                msg = f"Setting '{setting}' is not supported."
                helper.exception_handler(msg, bad_setting)
                bad_settings_keys.append((setting, value))
            else:
                setting_obj = getattr(self, setting)
                if isinstance(setting_obj, DeprecatedSetting):
                    continue
                else:
                    valid = setting_obj._validate_value(value, exception=not bulk_error)
                    if not valid:
                        bad_settings_keys.append((setting, value))
        if bulk_error and bad_settings_keys:
            helper.exception_handler(
                "Invalid settings: {}".format(
                    [item[0] + ': ' + str(item[1]) for item in bad_settings_keys]
                ),
                exception_type=ValueError
            )

    def _prepare_settings_push(self) -> dict:

        def to_rest_format(settings: dict) -> dict:
            return {k: {'value': v} for k, v in settings.items() if k not in self._READ_ONLY}

        settings = self.list_properties(show_names=False)
        settings = convert_settings_to_byte(settings, self._CONVERSION_MAP)
        settings = to_rest_format(settings)
        return settings

    def _prepare_settings_fetch(self, settings: dict) -> dict:

        def from_rest_format(settings: dict) -> dict:
            return {k: v['value'] for k, v in settings.items()}

        settings = from_rest_format(settings)
        settings = convert_settings_to_mega_byte(settings, self._CONVERSION_MAP)
        return settings

    def _cast_type_from_obj(self, setting: str, value: Any) -> Any:
        setting_obj = getattr(self, setting, None)
        processed_value = None

        if setting_obj and not isinstance(setting_obj, DeprecatedSetting):
            try:
                processed_value = setting_obj.type(value)
            except ValueError:
                processed_value = value
        else:
            processed_value = value
        return processed_value

    def _configure_settings(self):
        """Sets up the settings object to allow for verification of
        settings."""

        self._get_config()
        for setting, cfg in self._CONFIG.items():
            factory = SettingValueFactory()
            value = factory.get_setting(cfg)
            self.__override_settings_config(value)
            super().__setattr__(setting, value)

    def __override_settings_config(self, value: SettingValue) -> None:
        # placeholder to be overwriten
        pass

    def __str__(self):
        """String interpretation of the Setting object."""
        return json.dumps((self.list_properties()), indent=4)

    def __setattr__(self, name, value):
        name = super().__getattribute__(name)
        if isinstance(name, (SettingValue, DeprecatedSetting)):
            if name.value != value or not isinstance(name.value, type(value)):
                name._validate_value(value)
                if getattr(name, 'reboot_rule', None) is not None:
                    msg = f"{name.name}: {name.reboot_rule.get('description')}"
                    warnings.warn(msg, Warning)
                name.value = value
        else:
            super().__setattr__(name, value)
