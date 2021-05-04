import csv
import json
import pickle
from abc import ABCMeta, abstractmethod
from pprint import pprint
from sys import version_info
from typing import List, Dict, Union
from ast import literal_eval
import warnings

import mstrio.config as config
import mstrio.utils.helper as helper
from pandas import DataFrame, Series


class BaseSettings(metaclass=ABCMeta):
    """Base class for fetching and updating Application or Server Settings. The
    settings object can be optionally initialized with `connection` and `id`,
    which will automatically fetch the current settings for the specified
    object. If not specified, settings can be loaded from file using
    `import_from()` method. Settings attributes can be modified manually.
    Lastly, the settings object can be validated and applied to a given object
    (Application, Server) using the `update()` method.

    Attributes:
        settings: settings
    """
    _SUPPORTED_EXTENSIONS = ['.json', '.csv', '.p', '.pkl', '.pickle']
    _CONFIG: Dict = {}
    # !NOTE define in child classes
    _TYPE: Union[str, None] = None
    _READ_ONLY_SETTINGS: List[str] = []
    _CONVERTION_DICT: Dict[str, str] = {}

    def alter(self, **settings):
        """Alter settings in a command manager like way."""
        for setting, value in settings.items():
            setattr(self, setting, value)

    def fetch(self) -> None:
        """Fetch current settings from I-Server and update this Settings
        object."""
        prepared_settings = self._fetch()
        for key, value in prepared_settings.items():
            setting_obj = getattr(self, key)
            setting_obj.value = value['value']
            super(BaseSettings, self).__setattr__(key, setting_obj)

    @abstractmethod
    def _fetch(self):
        pass

    @abstractmethod
    def update(self) -> None:
        """Update the current settings on I-Server using this Settings
        object."""
        pass

    @abstractmethod
    def _get_config(self):
        """Fetch the settings config to be used in this Settings class."""
        pass

    def compare_with_files(self, files: List[str], show_diff_only: bool = False) -> DataFrame:
        """Compare the current application settings to settings in file/files
        Args:
            files (str): List of paths to the settings files. Supported settings
                files are JSON, CSV, Pickle. Ex: "/file.csv"
            show_diff_only(bool, optional): Whether to display all settings or
                only different from first application in list.
        Returns:
            Dataframe with values of current settings and settings from files.
        """
        current = DataFrame.from_dict(self.list_properties(show_names=True), orient='index',
                                      columns=['value']).reset_index()
        base = 'current value'
        current.columns = ['setting', base]
        for app in files:
            self.import_from(app)
            current[app] = self.to_dataframe()['value']
        if show_diff_only:
            index = Series([True] * len(current['setting']))
            for app_name in files:
                compare = current[base].eq(current[app_name])
                index = compare & index
            current = current[~index]
            if current.empty and config.verbose:
                print("There is no difference between current settings and settings from files")
        return current

    def to_csv(self, name: str) -> None:
        """Export the current application settings to the csv file.

        Args:
            name (str): Name of file
        """
        self._save_to_file(name=name, file_type='csv')

    def to_json(self, name: str) -> None:
        """Export the current application settings to the json file
        Args:
            name (str): Name of file
        """
        self._save_to_file(name=name, file_type='json')

    def to_pickle(self, name: str) -> None:
        """Export the current application settings to the pickle file
        Args:
            name (str): Name of file
        """
        self._save_to_file(name=name, file_type='pickle')

    def import_from(self, file: str) -> None:
        """Import application settings from a 'csv', 'json' or 'pickle' file.

        Args:
            file (str): Path to the file with supported extension type name.
                Ex: "<path>/file.csv"
        """
        # Extract settings and check file type
        settings_dict = {}
        file_type = None
        for extension in self._SUPPORTED_EXTENSIONS:
            if extension in file[-7:].lower():
                file_type = extension[1:]
        if file_type is None:
            raise TypeError(
                "This file type is not supported. Supported file types are .json and .csv")
        elif file_type == 'json':
            with open(file, 'r') as f:
                settings_dict = json.load(f)
        elif file_type == 'csv':
            with open(file, 'r') as f:
                reader = csv.reader(f, quoting=csv.QUOTE_ALL)
                settings_dict = self._process_settings(dict(reader))
        elif file_type in ['pkl', 'pickle', 'p']:
            with open(file, 'rb') as f:
                settings_dict = pickle.load(f)

        # Try to validate settings by fetching settings from I-Server
        settings_dict = self._prepare_settings_fetch(settings_dict, from_file=True)
        self._validate_settings(settings_dict)

        # If no Exception was raised, assign the settings to the object
        for (setting, value) in settings_dict.items():
            setattr(self, setting, value)
        if config.verbose:
            print("Settings imported from '{}'".format(file))

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
        df.drop(['name', 'read_only', 'reboot_rule', 'deprecated'], axis='columns', inplace=True,
                errors='ignore')
        return df

    def _process_settings(self, settings: dict) -> dict:
        """Helper function to extract settings from csv settings files."""
        processed_settings = {}
        for setting, value in settings.items():
            setting_obj = getattr(self, setting, None)
            if setting in ['#__page__', '#__version__', 'Name']:  # skip workstation specific lines
                continue
            value_lower = value.lower()
            if value_lower == 'false':
                processed_value = False
            elif value_lower == 'true':
                processed_value = True
            elif value.startswith('['):
                processed_value = literal_eval(value)
            elif not bool(value and value.strip()):
                processed_value = value
            elif setting_obj and not isinstance(setting_obj, DeprecatedSetting):
                try:
                    processed_value = setting_obj.type(value)
                except ValueError:
                    processed_value = value
            else:
                processed_value = value
            processed_settings.update({setting: processed_value})
        return processed_settings

    def _save_to_file(self, name: str, file_type: str = 'csv') -> None:
        file = name
        if file_type == 'json':
            if not name.endswith('.json'):
                msg = ("The file extension is different than '.json', please note that using a "
                       "different extension might disrupt opening the file correctly.")
                helper.exception_handler(msg, exception_type=Warning)
            with open(file, 'w') as f:
                json.dump(self._prepare_settings_push(to_file=True), f, indent=4)
        elif file_type == 'csv':
            if not name.endswith('.csv'):
                msg = ("The file extension is different than '.csv', please note that using a "
                       "different extension might disrupt opening the file correctly")
                helper.exception_handler(msg, exception_type=Warning)
            with open(file, 'w') as f:
                # Add lines for workstation compatibility
                f.write(f"""#__page__,{self._TYPE}\n#__version__,1\nName, Value\n""")
                w = csv.DictWriter(f, fieldnames=['Name', 'Value'], quoting=csv.QUOTE_ALL)
                rows = [{
                    'Name': setting,
                    'Value': value
                } for setting, value in self._prepare_settings_push(to_file=True).items()]
                w.writerows(rows)
        elif file_type in ['pkl', 'pickle', 'p']:
            if name.split('.')[-1] not in ['pkl', 'pickle', 'p']:
                msg = ("The file extension is different than available pickle extensions, "
                       "please note that using a different extension might disrupt opening "
                       "the file correctly.")
                helper.exception_handler(msg, exception_type=Warning)
            with open(file, 'wb') as f:
                pickle.dump(self._prepare_settings_push(to_file=True), f,
                            protocol=pickle.HIGHEST_PROTOCOL)
        else:
            helper.exception_handler(
                "This file type is not supported. Supported file types are .json and .csv",
                exception_type=TypeError)
        if config.verbose:
            print("Settings exported to '{}'".format(file))

    def _validate_settings(self, settings: dict = None, bad_setting=Warning, bad_type=Warning,
                           bulk_error=True) -> None:
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
                msg = "Setting '{}' is not supported.".format(setting)
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
                    [item[0] + ': ' + str(item[1]) for item in bad_settings_keys]),
                exception_type=ValueError)

    def _prepare_settings_push(self, to_file=False) -> dict:
        settings_dict = self.list_properties(show_names=False)
        for setting, value in settings_dict.items():
            unit = self._CONVERTION_DICT.get(setting)
            if unit is not None:
                if unit == 'B':
                    settings_dict[setting] = value * (1024**2)
                elif unit == 'KB':
                    settings_dict[setting] = value * 1024
        if to_file:
            return {k: v for k, v in settings_dict.items() if k not in self._READ_ONLY_SETTINGS}
        else:
            return {
                k: {
                    'value': v
                } for k, v in settings_dict.items() if k not in self._READ_ONLY_SETTINGS
            }

    def _prepare_settings_fetch(self, settings_dict: dict, from_file=False) -> dict:
        for setting, value in settings_dict.items():
            unit = self._CONVERTION_DICT.get(setting)
            if unit is not None:
                if not from_file:
                    value = value['value']
                if unit == 'B':
                    value = value / (1024**2)
                elif unit == 'KB':
                    value = value / 1024
                if from_file:
                    settings_dict.update({setting: int(value)})
                else:
                    settings_dict.update({setting: {'value': int(value)}})
        return settings_dict

    def _configure_settings(self):
        """Sets up the settings object to allow for verification of
        settings."""
        self._get_config()
        setting_value_types = {
            'number': NumberSetting,
            'string': StringSetting,
            'enum': EnumSetting,
            'boolean': BoolSetting,
            'time': TimeSetting,
            'email': EmailSetting,
            None: DeprecatedSetting
        }
        for setting, cfg in self._CONFIG.items():
            setting_type = cfg.get('type')
            if setting_type is None:
                self._READ_ONLY_SETTINGS.append(setting)
            cfg.update({'name': setting})
            value = setting_value_types[setting_type](cfg)
            if value.name in ['hLAutoDeleteMsgCount',
                              'cacheCleanUpFrequency']:  # config not accurate, needs override
                value.options.append({'name': 'No Limit', 'value': -1})
            if value.name == 'catalogMaxMemoryConsumption':
                value.min_value = 0
            super(BaseSettings, self).__setattr__(setting, value)

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
            super(BaseSettings, self).__setattr__(name, value)


class SettingValue(object):
    """Base Settings Value class.

    It represents single setting configuration.
    """

    def __init__(self, config: dict):
        self.value = None
        self.name = config.get('name')
        self.description = config.get('description')
        self.reboot_rule = config.get('reboot_rule')
        self.multi_select = config.get('multi_select')
        self.options = config.get('options', [])
        self.relationship = config.get('relationship')

    def __repr__(self):
        return str(self._get_value())

    def __setattr__(self, name, value):
        """Setattr that allows setting valid name values defined in options."""
        if name == 'value' and getattr(self, 'options', None):
            option_found = helper.filter_list_of_dicts(self.options, name=value)
            if option_found:
                super().__setattr__(name, option_found[0]['value'])
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        return helper.validate_param_value(self.name, value, self.type, special_values=options,
                                           exception=exception)

    def _get_value(self):
        return self.value

    @property
    def info(self):
        return self.__dict__


class EnumSetting(SettingValue):
    """Representation of an Enum setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else type(self.options[0]['value'])

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        if self.type == list:
            options.append('')
        return helper.validate_param_value(self.name, value, self.type, special_values=options,
                                           exception=exception)

    def _get_value(self):
        option_name = [
            option['name']
            for option in helper.filter_list_of_dicts(self.options, value=self.value)
        ]
        if len(option_name) == 1:
            return option_name[0]
        else:
            return option_name


class BoolSetting(SettingValue):
    """Representation of a Boolean setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else bool


class NumberSetting(SettingValue):
    """Representation of a Number setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else int
        self.max_value = config.get('max_value')
        self.min_value = config.get('min_value')
        self.unit = config.get('unit')

    def _validate_value(self, value, exception=True):
        options = helper.extract_all_dict_values(self.options)
        return helper.validate_param_value(self.name, value, self.type, self.max_value,
                                           self.min_value, options, exception=exception)


class StringSetting(SettingValue):
    """Representation of a String setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        return helper.validate_param_value(self.name, value, self.type, exception=exception)


class TimeSetting(SettingValue):
    """Representation of a Time setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        regex = r"^[1-2][0-9](:[0-5][0-9]){1,2}$"
        return helper.validate_param_value(self.name, value, str, regex=regex, exception=exception,
                                           valid_example='23:45')


class EmailSetting(SettingValue):
    """Representation of a Email setting type."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.type = list if self.multi_select else str

    def _validate_value(self, value, exception=True):
        regex = r"[^@]+@[^@]+\.[^@]+"
        return helper.validate_param_value(self.name, value, self.type, special_values=[''],
                                           regex=regex, exception=exception,
                                           valid_example='name@mail.com')


class DeprecatedSetting(object):
    """Representation of a Deprecated setting type."""

    def __init__(self, config: dict):
        self.value = None
        self.name = config.get('name')
        self.description = config.get('description')

    def _validate_value(self, value, exception=False):
        msg = f"Setting '{self.name}' is deprecated and is read-only"
        warnings.warn(msg, DeprecationWarning)
        return True

    def __repr__(self):
        return str(self._get_value())

    def _get_value(self):
        return self.value

    @property
    def info(self):
        return self.__dict__
