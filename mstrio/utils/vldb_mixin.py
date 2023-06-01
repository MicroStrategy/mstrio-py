import logging
from dataclasses import dataclass
from enum import auto
from typing import Callable, Optional

from pandas import DataFrame

from mstrio import config
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


class VldbPropertyType(AutoName):
    """Enumeration constant indicating type of VLDB property value."""

    INT32 = auto()
    INT64 = auto()
    DOUBLE = auto()
    BOOLEAN = auto()
    STRING = auto()
    DATE = auto()
    TIME = auto()


@dataclass
class PreviewOption(Dictable):
    """Class representation of single SQL Preview Option related to VldbSetting.

    Attributes:
        value (str): Value of SQL preview option.
        sql_preview (str): Description of SQL preview option
    """

    value: str
    sql_preview: str


class ResolvedLocation(AutoName):
    """Enumeration constant indicating type of VLDB property resolved
    and next resolved locations."""

    REPORT_TARGET = auto()
    REPORT = auto()
    TEMPLATE_TARGET = auto()
    TEMPLATE = auto()
    OBJECT = auto()
    PROJECT = auto()
    DB_ROLE = auto()
    DBMS = auto()
    DEFAULT = auto()


@dataclass
class VldbSetting(Dictable):
    """Class representation of single MicroStrategy VLDB setting.

    Attributes:
        type (VldbPropertyType): Type of VLDB setting value.
        name (str): VLDB setting name.
        property_set (str): Name of corresponding VLDB setting set.
        group_id (int): ID of VLDB setting group, settings are sorted by that
            parameter while listing.
        group_name (str): Name of VLDB setting group.
        value (str | int | float | bool): Current value set for VLDB setting.
        default_value (str | int | float | bool): Default value.
        display_type (str): Determines way of displaying settings on frontend.
        display_name (str): Name that will be displayed on frontend for
            particular settings.
        sql_preview (bool): Determines if SQL preview should be displayed.
        options (list[PreviewOption]): List of allowed sql options.
        resolved_location (ResolvedLocation): Type of location where value of
            related VLDB setting was last time resolved.
        is_inherited (bool): Whether the related VLDB setting value is inherited
            from other objects or not. If False value is set on the object.
            If True, value is inherited from other objects.
        max_value (int, optional): Shows maximum number of options that can be
            provided for the property, if applicable.
        next_value (str, optional): Previously set value.
        next_resolved_location (ResolvedLocation, optional): Previously set
            resolved_location.
        value_separator (str, optional): Values will be joined using that symbol
            when displaying on frontend.
    """

    _FROM_DICT_MAP = {
        'type': VldbPropertyType,
        'options': [PreviewOption.from_dict],
        'resolved_location': ResolvedLocation,
        'next_resolved_location': ResolvedLocation,
    }

    type: VldbPropertyType
    property_set: str
    name: str
    group_id: int
    group_name: str
    value: str | int | float | bool
    default_value: str | int | float | bool
    display_type: str
    display_name: str
    sql_preview: bool
    options: list[PreviewOption]
    resolved_location: ResolvedLocation
    is_inherited: bool
    max_value: Optional[int] = None
    next_value: Optional[str] = None
    next_resolved_location: Optional[ResolvedLocation] = None
    value_separator: Optional[str] = None

    type_map = {
        VldbPropertyType.INT32: int,
        VldbPropertyType.INT64: int,
        VldbPropertyType.DOUBLE: float,
        VldbPropertyType.BOOLEAN: lambda x: x == 'true',
        VldbPropertyType.STRING: str,
        VldbPropertyType.DATE: str,
        VldbPropertyType.TIME: str,
    }

    def __repr__(self) -> str:
        value_repr, default_value_repr = str(self.value), str(self.default_value)
        if type(self.value) == str:
            value_repr, default_value_repr = (
                f"'{value_repr}'",
                f"'{default_value_repr}'",
            )
        setting_repr = (
            f"VldbSetting(type={self.type}, property_set='{self.property_set}', "
            f"name='{self.name}', group_id={self.group_id}, "
            f"group_name='{self.group_name}', value={value_repr}, "
            f"default_value={default_value_repr}, "
        )
        if self.max_value:
            setting_repr += f"max_value={self.max_value}, "
        setting_repr += (
            f"display_type='{self.display_type}', "
            f"display_name='{self.display_name}', "
            f"sql_preview={self.sql_preview}, options={self.options}, "
            f"resolved_location={self.resolved_location}, "
            f"is_inherited={self.is_inherited})"
        )
        return setting_repr

    @classmethod
    def from_dict(cls, source: dict) -> 'VldbSetting':
        source['value'] = cls.type_map[VldbPropertyType(source['type'])](
            source['value']
        )
        return super().from_dict(source=source)

    def list_properties(self) -> dict:
        """List properties for the VLDB setting."""
        return self.to_dict()


@class_version_handler('11.3.0800')
class ModelVldbMixin:
    """ModelVldbMixin class adds VLDB management for supported objects through
    modeling service endpoints.

    Class attributes:
        _MODEL_VLDB_API (dict[str, Callable]): Dict containing references to API
            wrappers.

    Attributes:
        vldb_settings (dict[str, VldbSetting]): Dict with settings names as keys
            and VldbSetting objects as values.

    Objects currently supporting ModelVldbMixin settings are Project,
    DatasourceInstance and OlapCube. Must be mixedin with Entity or its
    subclasses.
    """

    _MODEL_VLDB_API: dict[str, Callable]
    _vldb_settings: dict[str, VldbSetting] = {}

    def _fetch(self):
        applicable_properties = self._MODEL_VLDB_API['GET_APPLICABLE'](
            self.connection, self.id
        ).json()['applicableProperties']
        advanced_properties = self._MODEL_VLDB_API['GET_ADVANCED'](
            self.connection, self.id
        ).json()['advancedProperties']['vldbProperties']
        self._vldb_settings = {}

        for key, applicable in applicable_properties.items():
            vldb_setting = VldbSetting.from_dict(
                {
                    'propertySet': ''.join(key.split('.')[0][1:-1]),
                    'sqlPreview': applicable['showSqlPreview'],
                    **advanced_properties[key],
                    **applicable,
                }
            )
            self._vldb_settings[vldb_setting.name] = vldb_setting

    def __filter_settings(
        self,
        vldb_settings: dict[str, VldbSetting],
        str_arg: str,
        args: list[str],
    ) -> dict[str, VldbSetting]:
        all_args = {
            getattr(setting, str_arg) for setting in self.vldb_settings.values()
        }

        for arg in args:
            if arg not in all_args:
                msg = f"There is no VldbSetting with '{str_arg}' equals to '{arg}'."
                raise ValueError(msg)

        return {
            name: setting
            for name, setting in vldb_settings.items()
            if getattr(setting, str_arg) in args
        }

    def list_vldb_settings(
        self,
        set_names: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
        groups: Optional[list[int] | list[str]] = None,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
    ) -> dict[str, VldbSetting]:
        """List VLDB settings according to given parameters.

        Args:
            set_names (list[str], optional): List of names of VLDB settings
                sets.
            names (list[str], optional): List of names of VLDB settings.
            groups (list[int], list[str], optional): List of group names or ids.
            to_dictionary(bool, optional): If True, return VldbSetting
                objects as list of dicts, default False.
            to_dataframe (bool, optional): If True, return VldbSetting
                objects as pandas DataFrame, default False.

        Raises:
            ValueError: If there are no VldbSetting objects with given
                parameters or some of the parameters are incorrectly
                specified.
            TypeError: If groups list parameter consists of objects of
                different types.

        Returns:
            Dict with settings names as keys and VldbSetting objects as values.
        """

        if to_dictionary and to_dataframe:
            msg = (
                "Please select either `to_dictionary=True` or `to_dataframe=True`, "
                "but not both.",
            )
            raise ValueError(msg)

        self._fetch()
        vldb_settings = self.vldb_settings.copy()

        if set_names:
            vldb_settings = self.__filter_settings(
                vldb_settings, 'property_set', set_names
            )

        if groups:
            if all(isinstance(group, int) for group in groups):
                vldb_settings = self.__filter_settings(
                    vldb_settings, 'group_id', groups
                )
            elif all(isinstance(group, str) for group in groups):
                vldb_settings = self.__filter_settings(
                    vldb_settings, 'group_name', groups
                )
            else:
                msg = "Elements in the groups list must be of the same type."
                raise TypeError(msg)

        if names:
            vldb_settings = self.__filter_settings(vldb_settings, 'name', names)

        if not vldb_settings:
            msg = "There is no VldbSetting objects found with given parameters."
            raise ValueError(msg)

        if to_dictionary or to_dataframe:
            vldb_settings = {
                key: setting.to_dict() for key, setting in vldb_settings.items()
            }

        if to_dataframe:
            return DataFrame(vldb_settings)
        else:
            return vldb_settings

    def alter_vldb_settings(
        self, names_to_values: dict[str, str | int | float | bool]
    ) -> None:
        """Alter VLDB settings according to given name to value pairs.

        Note:
            Only common value type conversion will be done by default,
            such as int->float, bool->int, int->bool and only if that is
            possible according to interval of allowed values, error will be
            thrown in other cases.

        Args:
            names_to_values (dict[str, str | int | float | bool]): Dict with
                VlDB settings names as keys and newly requested to set values
                as dictionary values.

        Raises:
            ValueError: If there are no VldbSetting objects for some
                provided names or names and values are not provided or some
                of provided values will not be possible to set.
            TypeError: If some of provided values to set have wrong type,
                different from type of default VLDB setting value.

        Returns:
            None
        """

        if not names_to_values:
            msg = "Please provide not empty dict with names to values pairs."
            raise ValueError(msg)

        body = {'advancedProperties': {'vldbProperties': {}}}

        for name, value in names_to_values.items():
            if name not in self.vldb_settings:
                msg = f"There is no VldbSetting with name '{name}'."
                raise ValueError(msg)

            setting = self.vldb_settings[name]

            if isinstance(value, int):
                value = self.__convert_int(value, setting)

            if not isinstance(value, type(setting.value)):
                value_type = type(setting.value)
                msg = f"Wrong type of VldbSetting value, it should be {value_type}."
                raise TypeError(msg)

            key = f'[{setting.property_set}].[{setting.name}]'
            body['advancedProperties']['vldbProperties'][key] = {'value': value}

        self._MODEL_VLDB_API['PUT_ADVANCED'](self.connection, self.id, body)

        self._fetch()
        if config.verbose:
            logger.info(f"VLDB settings for object with ID '{self.id}' were altered.")

    def __convert_int(self, value, setting):
        setting_value_type = type(setting.value)
        max_value = setting.max_value if setting.max_value else float('inf')
        min_value = 0 if setting.max_value else float('-inf')

        if (value < min_value or value > max_value) or (
            not setting.max_value and isinstance(value, bool)
        ):
            msg = "Incorrect value of VldbSetting, it should be"
            if setting.max_value:
                msg += f" positive and less or equal to {setting.max_value}"
            msg += f" of {setting_value_type}."
            raise ValueError(msg)

        return setting_value_type(value)

    def reset_vldb_settings(
        self,
        set_names: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
        groups: Optional[list[int] | list[str]] = None,
        force: bool = False,
    ) -> None:
        """Reset VLDB settings specified by parameters to its default values.
        If call was without parameters then additional prompt will be shown.

        Args:
            set_names (list[str], optional): List of names of VLDB setting
                sets.
            names (list[str], optional): List of names of VLDB settings.
            groups (list[int], list[str], optional): List of groups names
                or ids.
            force: (bool, optional): If True, no additional prompt will
                be shown before resetting in case when all other
                arguments are not provided, default False.

        Raises:
            ValueError: If there are no VldbSetting objects with given
                parameters or some of the parameters are incorrectly
                specified.
            TypeError: If groups list parameter consists of objects of
                different types.

        Returns:
            None
        """

        if not (set_names or names or groups or force):
            user_input = input(
                f"Are you sure you want to reset all VLDB settings for object with "
                f"ID '{self.id}'? [Y/N]: "
            )
            if user_input != 'Y':
                return

        body = {'advancedProperties': {'vldbProperties': {}}}
        names = self.list_vldb_settings(set_names, names, groups)

        for name in names:
            setting = self.vldb_settings[name]
            if setting.value != setting.default_value:
                key = f'[{setting.property_set}].[{setting.name}]'
                body['advancedProperties']['vldbProperties'][key] = {
                    'value': setting.default_value
                }

        self._MODEL_VLDB_API['PUT_ADVANCED'](self.connection, self.id, body)

        self._fetch()
        if config.verbose:
            logger.info(f"VLDB settings for object with ID '{self.id}' were reset.")

    @property
    def vldb_settings(self) -> dict[str, VldbSetting]:
        if not self._vldb_settings:
            self._fetch()
        return self._vldb_settings
