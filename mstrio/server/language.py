from __future__ import annotations

import logging
from dataclasses import dataclass

from mstrio import config
from mstrio.connection import Connection
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.helper import Dictable, delete_none_values
from mstrio.utils.response_processors import languages, objects
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler(version='11.3.1060')
def list_languages(
    connection: Connection,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list[Language] | list[dict]:
    """Get all languages as a list of Language objects or dictionaries.
    Optionally filter the languages by specifying filters.

    Args:
        connection: MicroStrategy connection object
        to_dictionary: if True returns a list of Language dicts,
            otherwise returns a list of Language objects
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters:
            ['name', 'base_language_lcid', 'lcid', 'interface_language',
            'last_modified', 'hidden', 'is_language_supported']
    """
    return Language._list_languages(
        connection=connection, to_dictionary=to_dictionary, limit=limit, **filters
    )


@method_version_handler(version='11.3.1060')
def list_interface_languages(
    connection: Connection, to_dictionary: bool = False
) -> list[Language.InterfaceLanguage] | list[dict]:
    """List all available interface languages.

    Args:
        connection (Connection): MicroStrategy connection object returned
            by `connection.Connection()`
        to_dictionary: if True returns a list of InterfaceLanguage dicts,
            otherwise returns a list of InterfaceLanguage objects

    Returns:
    A list of interface languages as dictionaries."""
    interface_languages = languages.get_interface_languages(connection=connection)
    if to_dictionary:
        return interface_languages
    else:
        return [
            Language.InterfaceLanguage.from_dict(source=obj)
            for obj in interface_languages
        ]


@class_version_handler(version='11.3.1060')
class Language(Entity, DeleteMixin, TranslationMixin):
    """Python representation of a Microstrategy Language object.

    Attributes:
        id (str): language's ID
        name (str): language's name
        base_language_lcid (int): LC ID of the language serving as a base for
            the language
        lcid (int): LC ID of the language
        owner (User): owner of the language
        last_modified (datetime): date of when language was last modified
        formatting_settings (TimeInterval): formatting settings of the language
        interface_language (InterfaceLanguage): details of the language's
            interface language
        hidden (bool): whether the language is hidden
        is_language_supported (bool): whether the language is supported
    """

    @dataclass
    class TimeInterval(Dictable):
        """Object that stores formatting settings of the Language.

        Attributes:
            minutes15 (str): formatting settings for 15 minutes
            minutes30 (str): formatting settings for 30 minutes
            hour (str): formatting settings for an hour
            day (str): formatting settings for a day
            week (str): formatting settings for a week
            hour_of_day (str): formatting settings for the hour of the day
            month (str): formatting settings for a month
            quarter (str): formatting settings for a quarter
            year (str): formatting settings for a year

        Formatting settings instructions:
            To specify formatting for:
                hours: use the letter h
                minutes: use the letter m
                days: use the letter d
                months: use the capital letter M
                quarters: use the letter q
                years: use the letter y
            To specify 12 hour clock use AM/PM afterwards, example: h:mm AM/PM

         Default formatting settings examples:
            minutes15: h:mm AM/PM -> 9:44 AM
            minutes30: h:mm AM/PM -> 9:44 AM
            hour: h:mm AM/PM -> 9:44 AM
            day: M/d -> 7/26
            week: M/d -> 7/26
            hour_of_day: h:mm AM/PM -> 9:44 AM
            month: MMM -> Jul
            quarter: qqq -> Q3
            year: yyyy -> 2023"""

        minutes15: str
        minutes30: str
        hour: str
        day: str
        week: str
        hour_of_day: str
        month: str
        quarter: str
        year: str

    @dataclass
    class InterfaceLanguage(Dictable):
        """Object that stores the interface language of the Language.

        Attributes:
            name (str): name of the interface language
            id (str): id of the interface language
            sub_type (ObjectSubTypes): subtype of the interface language,
                defaults to None
        """

        name: str
        id: str
        sub_type: ObjectSubTypes | None = None

    _OBJECT_TYPE = ObjectTypes.LOCALE
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'base_language_lcid',
            'lcid',
            'interface_language',
            'last_modified',
            'hidden',
            'is_language_supported',
        ): languages.get,
        (
            'abbreviation',
            'type',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl',
            'target_info',
        ): objects.get_info,
    }

    @staticmethod
    def _parse_owner(source, connection, to_snake_case: bool = True):
        """Parses owner from the API response."""
        from mstrio.users_and_groups import User

        return User.from_dict(source, connection, to_snake_case)

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': _parse_owner,
        'formatting_settings': TimeInterval.from_dict,
        'interface_language': InterfaceLanguage.from_dict,
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initializes a new instance of a Language class

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, Optional): Language's ID, defaults to None
            name (str, Optional): Language's name, defaults to None

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Raises:
            ValueError: if both `id` and `name` are not provided
                or if Language with the given `name` doesn't exist.
        """
        if not id:
            if name:
                language = self.__find_language_by_name(
                    connection=connection, name=name
                )
                id = language['id']
            else:
                raise ValueError("Please provide either 'id' or 'name' argument.")
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.name = kwargs.get('name')
        self.base_language_lcid = kwargs.get('base_laguage_lcid')
        self.lcid = kwargs.get('lcid')
        self.interface_language = (
            Language.InterfaceLanguage.from_dict(inl)
            if (inl := kwargs.get('interface_language'))
            else None
        )
        self.last_modified = kwargs.get('last_modified')
        self._hidden = kwargs.get('hidden')
        self._formatting_settings = None
        self.is_language_supported = kwargs.get('is_language_supported')

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        base_language: Language | str | int,
        interface_language_id: str | None = None,
        formatting_settings: TimeInterval | None = None,
    ) -> Language:
        """Create a new language with specified properties.

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            name (str): the name for the new Language
            base_language (Language | str | int): one of the following:
                - lcid attribute of the language that will be used as a base
                    language for the new Language
                - ID of the language that will be used as a base language for
                    the new Language
                - Language class object that will be used as a base language for
                    the new Language
            interface_language_id (str, Optional): id of the new Language's
                interface language
            formatting_settings (TimeInterval, Optional): formatting settings
                for the new Language

        Returns:
            Language class object.
        """
        if isinstance(base_language, int):
            base_lcid = base_language
        elif isinstance(base_language, str):
            base_lcid = Language(connection=connection, id=base_language).lcid
        elif isinstance(base_language, Language):
            base_lcid = base_language.lcid
        else:
            raise ValueError("Please provide a valid base language.")
        body = {
            'name': name,
            'baseLanguageLcid': base_lcid,
            'interfaceLanguageId': interface_language_id,
        }
        body = delete_none_values(source=body, recursion=True)
        language = cls.from_dict(
            source=languages.create(connection=connection, body=body),
            connection=connection,
        )
        if config.verbose:
            logger.info(
                f"Successfully created Language named: '{name}' with ID:"
                f" '{language.id}'"
            )
        if formatting_settings:
            language._formatting_settings = language._update_formatting_settings(
                formatting_settings=formatting_settings
            )
        else:
            language._formatting_settings = Language.TimeInterval.from_dict(
                source=languages.get_formatting_settings(
                    connection=connection, id=language.id
                )
            )
        return language

    def alter(
        self,
        name: str | None = None,
        formatting_settings: TimeInterval | None = None,
    ) -> None:
        """Alter the language's specified properties.

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            name (str, Optional): new name for the Language
            formatting_settings (TimeInverval, Optional): new formatting
                settings for the Language"""
        if name:
            self._alter_properties(name=name)
        if formatting_settings:
            self._formatting_settings = self._update_formatting_settings(
                formatting_settings=formatting_settings
            )

    def _update_formatting_settings(
        self, formatting_settings: TimeInterval
    ) -> TimeInterval:
        """Updates the formatting settings of the Language.

        Args:
            formatting_settings (TimeInterval): new formatting settings

        Returns:
            New formatting settings as TimeInterval class object."""
        formatting_body = {
            'operationList': [
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/minutes15',
                    'value': formatting_settings.minutes15,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/minutes30',
                    'value': formatting_settings.minutes30,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/hour',
                    'value': formatting_settings.hour,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/day',
                    'value': formatting_settings.day,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/week',
                    'value': formatting_settings.week,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/hourOfDay',
                    'value': formatting_settings.hour_of_day,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/month',
                    'value': formatting_settings.month,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/quarter',
                    'value': formatting_settings.quarter,
                },
                {
                    'op': 'replace',
                    'path': '/formattingSettings/timeInterval/year',
                    'value': formatting_settings.year,
                },
            ]
        }
        return Language.TimeInterval.from_dict(
            languages.update_formatting_settings(
                connection=self.connection, id=self.id, body=formatting_body
            )
        )

    def _remove_interface_language(self) -> None:
        """Removes the interface language from the Language if one exists."""
        if self.interface_language:
            op_list = [
                {
                    'op': 'remove',
                    'path': '/interfaceLanguage',
                    'value': self.interface_language.id,
                }
            ]
            languages.update(
                connection=self.connection, id=self.id, body={'operationList': op_list}
            )
            self.interface_language = None

    @classmethod
    def _list_languages(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        limit: int | None = None,
        **filters,
    ) -> list[Language] | list[dict]:
        objects = languages.get_all(connection=connection, limit=limit, filters=filters)
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @staticmethod
    def __find_language_by_name(connection: Connection, name: str):
        languages = list_languages(connection=connection, name=name)

        if languages:
            number_of_languages = len(languages)
            if number_of_languages > 1:
                raise ValueError(
                    f"There are {number_of_languages} Languages"
                    " with this name. Please initialize with id."
                )
            else:
                return languages[0].to_dict()
        else:
            raise ValueError(f"There is no Language with the given name: '{name}'")

    @property
    def hidden(self):
        return self._hidden

    @property
    def formatting_settings(self):
        if self._formatting_settings:
            return self._formatting_settings
        else:
            self._formatting_settings = Language.TimeInterval.from_dict(
                source=languages.get_formatting_settings(
                    connection=self.connection, id=self.id
                )
            )
