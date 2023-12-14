import logging
from dataclasses import dataclass
from enum import auto

from stringcase import snakecase

from mstrio import config
from mstrio.connection import Connection
from mstrio.server.language import list_languages
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, delete_none_values
from mstrio.utils.response_processors.projects import (
    get_project_languages,
    update_current_mode,
    update_default_language,
    update_project_languages,
)
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


@dataclass
class SimpleLanguage(Dictable):
    """Object that specify a Simple Language.

    Attributes:
        id (str): ID of the language.
        name (str, optional): Name of the language.
    """

    id: str
    name: str | None = None

    def __eq__(self, other):
        if not isinstance(other, SimpleLanguage):
            return False

        return self.id == other.id


@dataclass
class DataLocalizationLanguage(SimpleLanguage):
    """Object that specify a Data Localization Language.

    Attributes:
        id (str): ID of the language.
        name (str, optional): Name of the language.
        column (str, optional): Column name for the language.
        table (str, optional): Table name for the language.
        connection_id (str, optional): Connection ID for the language.
    """

    column: str | None = None
    table: str | None = None
    connection_id: str | None = None

    def __eq__(self, other):
        if not isinstance(other, DataLocalizationLanguage):
            return False

        return self.id == other.id

    def __repr__(self):
        return f'DataLocalizationLanguage(id={self.id}, name={self.name})'


class CurrentMode(AutoName):
    """Enum that specify a Current Mode for Data Internationalization."""

    SQL = auto()
    NONE = auto()
    CONNECTION = auto()


def _get_valid_language_ids(
    connection: Connection,
    project_id: str,
    operation: str,
    path: str,
) -> list[str]:
    """Gets valid language IDs for the Project.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        operation (str): operation to be performed
            Available values:
                - `add`
                - `remove`
                - `alter`
        path (str): path to target where operation will be performed
            Available values:
                - `data`
                - `metadata`

    Returns:
        A list of valid language IDs for the Project.
    """
    return (
        [language.id for language in list_languages(connection=connection)]
        if operation == 'add'
        else list(get_project_languages(connection, project_id, path))
    )


def _add_language(
    connection: Connection,
    project_id: str,
    languages: list[DataLocalizationLanguage | SimpleLanguage],
    path: str,
) -> list[DataLocalizationLanguage | SimpleLanguage]:
    """Adds languages to the Project.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        languages (list[DataLocalizationLanguage | SimpleLanguage]):
            list of languages to be added to the Project
        path (str): path to target where operation will be performed
            Available values:
                - `data`
                - `metadata`

    Returns:
        A list of languages for the Project.
    """
    operation_list = []
    language_type = DataLocalizationLanguage if path == 'data' else SimpleLanguage
    valid_language_ids = _get_valid_language_ids(
        connection=connection, project_id=project_id, operation='add', path=path
    )

    for language in languages:
        if language.id not in valid_language_ids:
            raise ValueError(f"There is no language with the given ID: {language.id}.")

        operation_list.append(
            {
                'op': 'add',
                'path': f'/{path}/languages',
                'value': language_type.to_dict(language),
            }
        )

    body = {'operationList': operation_list}
    body = delete_none_values(body, recursion=True)

    response = update_project_languages(
        connection=connection, id=project_id, body=body, path=path
    )

    return [
        language_type.from_dict({'id': id, **value}, connection)
        for id, value in response.items()
    ]


def _remove_language(
    connection: Connection,
    project_id: str,
    languages: list[DataLocalizationLanguage | SimpleLanguage],
    path: str,
    default_language_id: str,
) -> list[DataLocalizationLanguage | SimpleLanguage]:
    """Removes languages from the Project.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (str): ID of the project
        languages (list[DataLocalizationLanguage | SimpleLanguage]):
            list of languages to be added to the Project
        path (str): path to target where operation will be performed
            Available values:
                - `data`
                - `metadata`
    """

    operation_list = []
    language_type = DataLocalizationLanguage if path == 'data' else SimpleLanguage
    valid_language_ids = _get_valid_language_ids(
        connection=connection, project_id=project_id, operation='remove', path=path
    )

    for language in languages:
        if language.id not in valid_language_ids:
            raise ValueError(f"There is no language with the given ID: {language.id}.")
        if language.id == default_language_id:
            raise ValueError(f"Cannot remove default language: {language.id}.")

        operation_list.append(
            {'op': 'remove', 'path': f'/{path}/languages/{language.id}'}
        )

    response = update_project_languages(
        connection=connection,
        id=project_id,
        body={'operationList': operation_list},
        path=path,
    )

    return [
        language_type.from_dict({'id': id, **value}, connection)
        for id, value in response.items()
    ]


@dataclass
@class_version_handler(version='11.3.1200')
class DataLanguageSettings(Dictable):
    """Object that specify a Data Language Settings for a Project.

    Attributes:
        default_language (DataLocalizationLanguage):
            Default language for the Project.
        current_mode (CurrentMode):
            Current mode for data internationalization.
        languages (list[DataLocalizationLanguage]):
            List of languages for the Project.
    """

    _FROM_DICT_MAP = {
        'current_mode': CurrentMode,
        'default_language': lambda source, connection: [
            DataLocalizationLanguage.from_dict({'id': id, **value}, connection)
            for id, value in source.items()
        ][0],
        'languages': lambda source, connection: [
            DataLocalizationLanguage.from_dict({'id': id, **value}, connection)
            for id, value in source.items()
        ],
    }

    default_language: DataLocalizationLanguage
    current_mode: CurrentMode
    languages: list[DataLocalizationLanguage]

    def add_language(self, languages: list[DataLocalizationLanguage]) -> None:
        """Adds languages to the Project.

        Args:
            languages (list[DataLocalizationLanguage]):
                list of languages to be added to the Project
        """

        response = _add_language(
            connection=self._connection,
            project_id=self._project_id,
            languages=languages,
            path='data',
        )
        self.languages = response
        if config.verbose:
            logger.info(
                f"Successfully added languages to the project with ID: "
                f"{self._project_id}"
            )

    def alter_language(
        self, languages: list[DataLocalizationLanguage], path: str
    ) -> None:
        """Alters languages for the Project.

        Args:
            languages (list[DataLocalizationLanguage]):
                list of languages to be altered for the Project
            path (str): path to target where operation will be performed
            Available values:
                - `column`
                - `table`
                - `connectionId`
        """
        if path not in ('column', 'table', 'connectionId'):
            raise ValueError(
                f"Invalid path: {path}. "
                f"Path must be one of: 'column', 'table', 'connectionId'."
            )
        operation_list = []
        valid_language_ids = _get_valid_language_ids(
            connection=self._connection,
            project_id=self._project_id,
            operation='alter',
            path='data',
        )

        for language in languages:
            if language.id not in valid_language_ids:
                raise ValueError(
                    f"There is no language with the given ID: {language.id}."
                )

            operation_list.append(
                {
                    'op': 'replace',
                    'path': f'/data/languages/{language.id}/{path}',
                    'value': getattr(language, snakecase(path)),
                }
            )

        response = update_project_languages(
            connection=self._connection,
            id=self._project_id,
            body={'operationList': operation_list},
            path='data',
        )
        self.languages = [
            DataLocalizationLanguage.from_dict({'id': id, **value}, self._connection)
            for id, value in response.items()
        ]
        if config.verbose:
            logger.info(
                f"Successfully altered languages from the project with ID: "
                f"{self._project_id}"
            )

    def remove_language(self, languages: list[DataLocalizationLanguage]) -> None:
        """Removes languages from the Project.

        Args:
            languages (list[DataLocalizationLanguage]):
                list of languages to be removed from the Project
        """

        response = _remove_language(
            connection=self._connection,
            project_id=self._project_id,
            languages=languages,
            path='data',
            default_language_id=self.default_language.id,
        )

        self.languages = response
        if config.verbose:
            logger.info(
                f"Successfully removed languages from the project with ID: "
                f"{self._project_id}"
            )

    def alter_current_mode(self, mode: str | CurrentMode) -> None:
        """Alters the current mode for data internationalization

        Args:
            mode (str | CurrentMode): mode for data internationalization
                Available values:
                    - `none` | `CurrentMode.NONE`
                    - `sql` | `CurrentMode.SQL`
                    - `connection` | `CurrentMode.CONNECTION`
        """
        mode = mode.value if isinstance(mode, CurrentMode) else mode

        if mode not in ('none', 'sql', 'connection'):
            raise ValueError(
                f"Invalid mode: {mode}. "
                f"Mode must be one of: 'none', 'sql', 'connection'."
            )

        response = update_current_mode(
            connection=self._connection,
            id=self._project_id,
            body={
                'operationList': [
                    {
                        'op': 'replace',
                        'path': '/data/currentMode',
                        'value': mode,
                    }
                ]
            },
        )

        self.current_mode = CurrentMode(response)
        if config.verbose:
            logger.info(
                f"Successfully altered current mode for the project with ID: "
                f"{self._project_id}"
            )

    def alter_default_language(self, language: str | DataLocalizationLanguage) -> None:
        """Alters the default language used by data internationalization

        Args:
            language (str | DataLocalizationLanguage):
                Language or it's ID to be set as default.
        """
        language_id = (
            language.id if isinstance(language, DataLocalizationLanguage) else language
        )
        valid_langauge_ids = _get_valid_language_ids(
            connection=self._connection,
            project_id=self._project_id,
            operation='alter',
            path='data',
        )

        if language_id not in valid_langauge_ids:
            raise ValueError(f"There is no language with the given ID: {language_id}.")

        response = update_default_language(
            connection=self._connection,
            id=self._project_id,
            body={
                'operationList': [
                    {
                        'op': 'replace',
                        'path': '/data/default',
                        'value': language_id,
                    }
                ]
            },
        )

        self.default_language = [
            DataLocalizationLanguage.from_dict({'id': id, **value}, self._connection)
            for id, value in response.items()
        ][0]
        if config.verbose:
            logger.info(
                f"Successfully altered default language "
                f"for the project with ID: {self._project_id}"
            )

    def to_dict(self, camel_case: bool = True) -> dict:
        obj_dict = super().to_dict(camel_case=camel_case)
        if hasattr(obj_dict, '_project_id'):
            obj_dict.pop('_projectId')
        return obj_dict


@dataclass
@class_version_handler(version='11.3.1200')
class MetadataLanguageSettings(Dictable):
    """Object that specify a Metadata Language Settings for a Project.

    Attributes:
        default (SimpleLanguage): Default language for the Project.
        languages (list[SimpleLanguage]): List of languages for the Project.
    """

    _FROM_DICT_MAP = {
        'default': lambda source, connection: [
            SimpleLanguage.from_dict({'id': id, **value}, connection)
            for id, value in source.items()
        ][0],
        'languages': lambda source, connection: [
            SimpleLanguage.from_dict({'id': id, **value}, connection)
            for id, value in source.items()
        ],
    }

    default: SimpleLanguage
    languages: list[SimpleLanguage]

    def add_language(self, languages: list[SimpleLanguage]) -> None:
        """Adds languages to the Project.

        Args:
            languages (list[SimpleLanguage]):
                list of languages to be added to the Project
        """

        response = _add_language(
            connection=self._connection,
            project_id=self._project_id,
            languages=languages,
            path='metadata',
        )
        self.languages = response
        if config.verbose:
            logger.info(
                f"Successfully added languages to the project with ID: "
                f"{self._project_id}"
            )

    def remove_language(self, languages: list[SimpleLanguage]) -> None:
        """Removes languages from the Project.

        Args:
            languages (list[SimpleLanguage]):
                list of languages to be removed from the Project
        """
        response = _remove_language(
            connection=self._connection,
            project_id=self._project_id,
            languages=languages,
            path='metadata',
            default_language_id=self.default.id,
        )
        self.languages = response
        if config.verbose:
            logger.info(
                f"Successfully removed languages from the project with ID: "
                f"{self._project_id}"
            )

    def to_dict(self, camel_case: bool = True) -> dict:
        obj_dict = super().to_dict(camel_case=camel_case)
        if hasattr(obj_dict, '_project_id'):
            obj_dict.pop('_projectId')
        return obj_dict
