from abc import ABCMeta, abstractclassmethod
from ast import literal_eval
import csv
import json
import logging
import pickle
from typing import Optional, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api.exceptions import VersionException
import mstrio.utils.helper as helper

from .settings_helper import convert_settings_to_mega_byte

if TYPE_CHECKING:
    from mstrio.utils.settings.base_settings import BaseSettings

logger = logging.getLogger(__name__)

EXPORTED_MSG = "Settings exported to"


class SettingsSerializerFactory():

    def get_serializer(self, file):
        file_type = None
        for extension in ['.json', '.csv', '.p', '.pkl', '.pickle']:
            if extension in file[-7:].lower():
                file_type = extension[1:]

        if file_type is None:
            raise ValueError(
                "This file type is not supported. Supported file types are .json, .csv, .pickle")
        elif file_type == 'json':
            return JSONSettingsIO()
        elif file_type == 'csv':
            return CSVSettingsIO()
        elif file_type in ['pkl', 'pickle', 'p']:
            return PickleSettingsIO()


class SettingsIO(metaclass=ABCMeta):
    FILE_NAME: Union[str, tuple, None] = None
    PROJECT_VERSION: Optional[int] = None
    SERVER_VERSION: Optional[int] = None

    @abstractclassmethod
    def to_file(cls, file: str, settings_obj: "BaseSettings") -> None:
        pass

    @abstractclassmethod
    def from_file(cls, file: str, settings_obj: "BaseSettings") -> dict:
        pass

    @classmethod
    def validate_file_name(cls, file):
        if not isinstance(cls.FILE_NAME, (str, tuple)):
            raise NotImplementedError("FILE_NAME not defined")
        elif not file.endswith(cls.FILE_NAME):
            msg = (f'The file extension is different than {cls.FILE_NAME}, please note that using'
                   ' a different extension might disrupt opening the file correctly.')
            helper.exception_handler(msg, exception_type=Warning)

    @classmethod
    def check_type(cls, settings_type: Union[str, None], settings_obj: "BaseSettings") -> None:
        if settings_type is None:
            return None
        elif settings_type != settings_obj._TYPE:
            raise TypeError('Unsupported settings.')

    @classmethod
    def check_version(cls, version: Union[str, int, None], settings_type: Union[str,
                                                                                None]) -> None:
        if isinstance(version, str):
            version = int(version)
        if version is None or settings_type is None:
            return None
        else:
            server_settings_not_supported = (settings_type == "allServerSettings"
                                             and version > cls.SERVER_VERSION)
            project_settings_not_supported = (settings_type == "allProjectSettings"
                                              and version > cls.PROJECT_VERSION)
            if server_settings_not_supported or project_settings_not_supported:
                raise VersionException("Unsupported settings version")

    @classmethod
    def get_version(cls, settings_obj: "BaseSettings") -> int:
        if settings_obj._TYPE == "allServerSettings":
            return cls.SERVER_VERSION
        elif settings_obj._TYPE == "allProjectSettings":
            return cls.PROJECT_VERSION


class PickleSettingsIO(SettingsIO):
    FILE_NAME = ('.pkl', '.pickle', '.p')
    PROJECT_VERSION = 2
    SERVER_VERSION = 2

    @classmethod
    def to_file(cls, file: str, settings_obj: "BaseSettings") -> None:
        cls.validate_file_name(file)
        settings_dict = settings_obj.list_properties(show_names=False)

        with open(file, 'wb') as f:
            # save version and type
            settings_dict.update(__version__=cls.get_version(settings_obj),
                                 __page__=settings_obj._TYPE)
            pickle.dump(settings_dict, f, protocol=4)  # pickle protocol added in python 3.4
        if config.verbose:
            logger.info(f"{EXPORTED_MSG} '{file}'")

    @classmethod
    def from_file(cls, file: str, settings_obj: "BaseSettings") -> dict:

        with open(file, 'rb') as f:
            settings_dict = pickle.load(f)

            # check versioning and type
            version = settings_dict.pop("__version__", None)
            settings_type = settings_dict.pop('__page__', None)
            cls.check_type(settings_type, settings_obj)
            cls.check_version(version, settings_type)
            # convert memory units for v1 (no version) settings
            if version is None:
                settings_dict = convert_settings_to_mega_byte(settings_dict,
                                                              settings_obj._CONVERSION_MAP)

        return settings_dict


class JSONSettingsIO(SettingsIO):
    FILE_NAME = '.json'
    PROJECT_VERSION = 2
    SERVER_VERSION = 2

    @classmethod
    def to_file(cls, file: str, settings_obj: "BaseSettings") -> None:
        cls.validate_file_name(file)
        settings_dict = settings_obj.list_properties(show_names=False)

        with open(file, 'w') as f:
            # save version and type
            settings_dict.update(__version__=cls.get_version(settings_obj),
                                 __page__=settings_obj._TYPE)
            json.dump(settings_dict, f, indent=4)
        if config.verbose:
            logger.info(f"{EXPORTED_MSG} '{file}'")

    @classmethod
    def from_file(cls, file: str, settings_obj: "BaseSettings") -> dict:

        with open(file) as f:
            settings_dict = json.load(f)

            # check versioning and type
            version = settings_dict.pop("__version__", None)
            settings_type = settings_dict.pop('__page__', None)
            cls.check_type(settings_type, settings_obj)
            cls.check_version(version, settings_type)
            # convert memory units for v1 (no version) settings
            if version is None:
                settings_dict = convert_settings_to_mega_byte(settings_dict,
                                                              settings_obj._CONVERSION_MAP)

        return settings_dict


class CSVSettingsIO(SettingsIO):
    FILE_NAME = '.csv'
    PROJECT_VERSION = 1
    SERVER_VERSION = 2

    @classmethod
    def to_file(cls, file: str, settings_obj: "BaseSettings") -> None:
        cls.validate_file_name(file)
        with open(file, 'w') as f:
            # Add lines for workstation compatibility
            version = cls.get_version(settings_obj)
            f.write(f"#__page__,{settings_obj._TYPE}\n#__version__,{version}\nName, Value\n")
            w = csv.DictWriter(f, fieldnames=['Name', 'Value'], quoting=csv.QUOTE_ALL)

            settings_dict = settings_obj.list_properties(show_names=False)
            rows = [{'Name': setting, 'Value': value} for setting, value in settings_dict.items()]
            w.writerows(rows)
            if config.verbose:
                logger.info(f"{EXPORTED_MSG} '{file}'")

    @classmethod
    def from_file(cls, file: str, settings_obj: "BaseSettings") -> dict:

        with open(file) as f:
            settings_dict = dict(csv.reader(f, quoting=csv.QUOTE_ALL))
            return cls.process_csv_settings(settings_dict, settings_obj)

    @classmethod
    def process_csv_settings(cls, settings: dict, settings_obj: "BaseSettings") -> dict:
        """Helper function to extract settings from csv settings files."""
        version = settings.pop("#__version__", None)
        settings_type = settings.pop('#__page__', None)
        cls.check_type(settings_type, settings_obj)
        cls.check_version(version, settings_type)

        processed_settings = {}
        for setting, value in settings.items():
            if setting == 'Name':  # skip header line
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
            else:
                processed_value = settings_obj._cast_type_from_obj(setting, value)

            processed_settings.update({setting: processed_value})

        # convert memory units for v1 Server settings
        if version == "1" and settings_type == "allServerSettings":
            processed_settings = convert_settings_to_mega_byte(processed_settings,
                                                               settings_obj._CONVERSION_MAP)

        return processed_settings

    @classmethod
    def check_type(cls, settings_type: Union[str, None], settings_obj: "BaseSettings") -> None:
        if settings_type is None:
            raise ValueError('CSV settings are missing `#__page__` header')
        elif settings_type != settings_obj._TYPE:
            raise TypeError('Unsupported settings.')

    @classmethod
    def check_version(cls, version: Union[int, None], settings_type: str) -> None:
        if version is None:
            raise ValueError('CSV settings are missing `#__version__` header')
        elif isinstance(version, str):
            version = int(version)

        server_settings_not_supported = (settings_type == "allServerSettings"
                                         and version > cls.SERVER_VERSION)
        project_settings_not_supported = (settings_type == "allProjectSettings"
                                          and version > cls.PROJECT_VERSION)
        if server_settings_not_supported or project_settings_not_supported:
            raise VersionException('Unsupported CSV settings version.')
