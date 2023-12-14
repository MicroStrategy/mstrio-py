import logging
from dataclasses import dataclass

import pandas as pd

from mstrio import config
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.utils.entity import Entity
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import Dictable, get_valid_project_id
from mstrio.utils.response_processors import objects, projects
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler(version='11.3.7')
def list_translations(
    connection: Connection,
    id: str,
    object_type: int | ObjectTypes,
    project_id: str | None = None,
    languages: list | None = None,
    to_dictionary: bool = False,
) -> list['Translation'] | list[dict]:
    """Lists translations of the given Object.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): ID of the Object the translations will be listed for
        object_type (int | ObjectTypes): type of the Object the translations
            will be listed for
        project_id (str, optional): project ID of the project the Object is on,
            if not provided will be taken from connection
        languages (list, optional): list of languages to list the translations
            for, only translations from these languages will be listed.
            Languages in the list should be one of the following:
                - lcid attribute of the language
                - ID of the language
                - Language class object
        to_dictionary (bool, optional): If True returns a list of dictionaries,
            by default (False) returns a list of Translation objects

    Returns:
        A list of dictionaries representing translations for the Object or a
        list of Translation Objects."""
    object_type = get_enum_val(object_type, ObjectTypes)

    project_id = get_valid_project_id(
        connection=connection, project_id=project_id, with_fallback=True
    )

    output = objects.get_translations(
        connection=connection,
        project_id=project_id,
        target_id=id,
        object_type=object_type,
    )

    if languages:
        proper_language_list = [
            Translation._get_lang_lcid(connection=connection, language=lang)
            for lang in languages
        ]
        new_output = []

        for target_id in output:
            values = target_id.get('translation_values')
            new_values = [
                value
                for value in values
                if int(value.get('language_lcid')) in proper_language_list
            ]

            new_output.append(
                {
                    'translation_target_id': target_id.get('translation_target_id'),
                    'translation_target_name': target_id.get('translation_target_name'),
                    'translation_values': new_values,
                }
            )

        output = new_output

    if to_dictionary:
        return output
    return [
        Translation.from_dict(source=translation_data, to_snake_case=False)
        for translation_data in output
    ]


@dataclass
class Translation(Dictable):
    """Translation class represents a translation for an Object. It also
    contains methods to create, alter and delete translations for all Object
    types including ones not yet supported by mstrio-py

    Attributes:
            translation_target_id (str): ID of the part of the Object the
                translations are for
            translation_target_name (str): name of the part of the Object the
                translations are for
            translation_values (list[Translation.TranslationValues]): list of
                translation values for the part of the Object"""

    @dataclass
    class TranslationValue(Dictable):
        """Object that specifies a Translation for a single Language

        Attributes:
            value (str): value of the translation
            language_lcid (str): LCID of the language
        """

        value: str
        language_lcid: str

    @dataclass
    class OperationData:
        """Object that specifies data for a single Operation on a Translation.

        Attributes:
            target_language (Language | str | int): one of the following:
                - lcid attribute of the language
                - ID of the language
                - Language class object
            target_id (str): ID of the specific part of the Object to be
                translated
            value (str, optional): value of the change, not necessary when
                deleting a translation
        """

        from mstrio.server.language import Language

        target_language: Language | str | int
        target_id: str
        value: str | None = None

    _FROM_DICT_MAP = {
        'translation_values': lambda source, connection: [
            Translation.TranslationValue.from_dict(content, connection)
            for content in source
        ],
    }

    translation_target_id: str
    translation_target_name: str
    translation_values: [TranslationValue]

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translation(
        connection: Connection,
        id: str,
        object_type: int | ObjectTypes,
        translations: list[OperationData],
        project_id: str | None = None,
    ) -> list['Translation']:
        """Adds translations to the Object.

        Args:
            connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project_id (str, optional): project ID of the project the Object is
                located in, if not specified will be taken from the Connection

        Returns:
            A list of translations for the Object.
        """
        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, with_fallback=True
        )

        object_type = get_enum_val(object_type, ObjectTypes)

        operations_list = []
        valid_target_ids = [
            transl.translation_target_id
            for transl in list_translations(
                connection=connection,
                id=id,
                object_type=object_type,
                project_id=project_id,
            )
        ]

        for translation in translations:
            if translation.target_id not in valid_target_ids:
                raise ValueError(
                    f"Object with ID: {id} has no target_id: {translation.target_id}."
                )

            base_lcid = Translation._get_lang_lcid(
                connection=connection, language=translation.target_language
            )
            path = f"/localesAndTranslations/{translation.target_id}/translationValues"
            operation = {
                'op': 'add',
                'path': path,
                'value': {base_lcid: {'translation': translation.value}},
            }
            operations_list.append(operation)

        body = {'operationList': operations_list}

        output = objects.update_translations(
            connection=connection,
            target_id=id,
            project_id=project_id,
            body=body,
            object_type=object_type,
        )
        if config.verbose:
            logger.info(f"Successfully added Translations to Object with ID: {id}")
        return [
            Translation.from_dict(source=translation_data, to_snake_case=False)
            for translation_data in output
        ]

    @staticmethod
    @method_version_handler(version='11.3.7')
    def alter_translation(
        connection: Connection,
        id: str,
        object_type: int | ObjectTypes,
        translations: list[OperationData],
        project_id: str | None = None,
    ) -> None:
        """Alters translations for the Object.

        Args:
            connection(Connection): MicroStrategy connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project_id (str, optional): project ID of the project the Object is
                located in, if not specified will be taken from the Connection
        """
        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, with_fallback=True
        )

        object_type = get_enum_val(object_type, ObjectTypes)

        operations_list = []
        obj_translations = list_translations(
            connection=connection,
            id=id,
            object_type=object_type,
            project_id=project_id,
        )
        valid_target_ids = [transl.translation_target_id for transl in obj_translations]

        for translation in translations:
            if translation.target_id not in valid_target_ids:
                raise ValueError(
                    f"Object with ID: {id} has no target_id: {translation.target_id}."
                )

            base_lcid = Translation._get_lang_lcid(
                connection=connection, language=translation.target_language
            )

            for translation_check in obj_translations:
                if translation_check.translation_target_id == translation.target_id:
                    existing_translation_languages = [
                        value.language_lcid
                        for value in translation_check.translation_values
                    ]
                    if str(base_lcid) not in existing_translation_languages:
                        error_msg = (
                            "Cannot alter translation for Language with LCID: "
                            f"{base_lcid} as there is no translation present in "
                            f"the target_id: {translation.target_id} for the language."
                        )
                        raise ValueError(error_msg)
                    else:
                        break

            path = (
                f"/localesAndTranslations/{translation.target_id}"
                f"/translationValues/{base_lcid}/translation"
            )
            operation = {
                'op': 'replace',
                'path': path,
                'value': translation.value,
            }
            operations_list.append(operation)

        body = {'operationList': operations_list}

        objects.update_translations(
            connection=connection,
            target_id=id,
            project_id=project_id,
            body=body,
            object_type=object_type,
        )
        if config.verbose:
            logger.info(f"Successfully altered Translations of Object with ID: {id}")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def remove_translation(
        connection: Connection,
        id: str,
        object_type: int | ObjectTypes,
        translations: list[OperationData],
        project_id: str | None = None,
    ) -> None:
        """Removes translations from the Object.

        Args:
            connection(Connection): MicroStrategy connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project_id (str, optional): project ID of the project the Object is
                located in, if not specified will be taken from the Connection
        """
        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, with_fallback=True
        )

        object_type = get_enum_val(object_type, ObjectTypes)

        operations_list = []
        obj_translations = list_translations(
            connection=connection,
            id=id,
            object_type=object_type,
            project_id=project_id,
        )
        valid_target_ids = [transl.translation_target_id for transl in obj_translations]

        for translation in translations:
            if translation.target_id not in valid_target_ids:
                raise ValueError(
                    f"Object with ID: {id} has no target_id: {translation.target_id}."
                )

            base_lcid = Translation._get_lang_lcid(
                connection=connection, language=translation.target_language
            )

            for translation_check in obj_translations:
                if translation_check.translation_target_id == translation.target_id:
                    existing_translation_languages = [
                        value.language_lcid
                        for value in translation_check.translation_values
                    ]
                    if str(base_lcid) not in existing_translation_languages:
                        error_msg = (
                            "Cannot delete translation for Language with LCID: "
                            f"{base_lcid} as there is no translation present in "
                            f"the target_id: {translation.target_id} for the language."
                        )
                        raise ValueError(error_msg)
                    else:
                        break

            path = (
                f"/localesAndTranslations/{translation.target_id}"
                f"/translationValues/{base_lcid}"
            )

            operation = {
                'op': 'remove',
                'path': path,
            }
            operations_list.append(operation)

        body = {'operationList': operations_list}

        objects.update_translations(
            connection=connection,
            target_id=id,
            project_id=project_id,
            body=body,
            object_type=object_type,
        )
        if config.verbose:
            logger.info(f"Successfully deleted Translations for Object with ID: {id}")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def to_csv_from_list(
        connection: Connection,
        object_list: list[dict | Entity],
        separator: str = ';',
        path: str | None = None,
        project_id: str | None = None,
    ) -> str | None:
        """Export translations of the given objects to a CSV file.

        Args:
            connection(Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            object_list (list[dict]): list of Objects to export translations for
                Objects can be provided as class objects such as a Metric or a
                Document or in form of a dictionary.
                Every dictionary should consist of:
                    id (str): ID of the object
                    type (int | ObjectType): type of the object
            separator (str, optional): specify the separator for the csv file.
                Defaults to a semicolon ;
            path (str, optional): a path specifying where to save the csv file
            project_id (str, optional): ID of the project the Objects are a part
                of, if not provided will be taken from connection

        Returns:
            String representation of the CSV file if no path was given or
            None if path was provided.
        The columns A-D in the exported file should not be edited for the import
            function to work properly.
        """
        languages_list = []
        languages_list_lcid = []
        dataframes = []
        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, with_fallback=True
        )
        project_languages = projects.get_project_languages(
            connection=connection, id=project_id, path='metadata'
        )
        for lang in project_languages:
            languages_list.append(project_languages.get(lang).get('name'))
            languages_list_lcid.append(
                Translation._get_lang_lcid(connection=connection, language=lang)
            )
        for object in object_list:
            if isinstance(object, dict):
                object_id = object.get('id')
                object_type = get_enum_val(object.get('type'), ObjectTypes)
            elif isinstance(object, Entity):
                object_id = object.id
                object_type = get_enum_val(object.type, ObjectTypes)
            translations = list_translations(
                connection=connection,
                id=object_id,
                object_type=object_type,
                project_id=project_id,
                languages=languages_list_lcid,
            )
            for translation in translations:
                row_to_add = [
                    object_id,
                    object_type,
                    translation.translation_target_name,
                    translation.translation_target_id,
                ]
                for lang in languages_list_lcid:
                    value_to_put = ''
                    for trans_value in translation.translation_values:
                        if int(trans_value.language_lcid) == lang:
                            value_to_put = trans_value.value
                            break
                    row_to_add.append(value_to_put)
                dataframes.append(
                    pd.DataFrame(
                        data=[row_to_add],
                        columns=['object id', 'object type', 'target name', 'target id']
                        + languages_list,
                    ),
                )
        dataframe = pd.concat(dataframes, ignore_index=True)
        return dataframe.to_csv(index=False, path_or_buf=path, sep=separator)

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translations_from_csv(
        connection: Connection,
        csv_file: str,
        separator: str = ';',
        project_id: str | None = None,
    ) -> None:
        """Add translations from a specified CSV file.

        Args:
            connection(Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            csv_file (str): a path specifying the CSV file
            separator (str, optional): specify the separator of the csv file.
                Defaults to a semicolon ;
            project_id (str, optional): ID of the project the Objects are a part
                of, if not provided will be taken from connection
        """
        from mstrio.server.language import Language

        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, with_fallback=True
        )
        df = pd.read_csv(csv_file, na_filter=False, sep=separator)
        objects = []
        object_types = []
        operations = []
        languages = [
            Language(connection=connection, name=lang).lcid
            for lang in df.columns.tolist()[4:]
        ]
        rows = df.values.tolist()
        for row in rows:
            if row[0] not in objects:
                objects.append(row[0])
                object_types.append(row[1])
                operations.append([])
            for index, value in enumerate(row[4:]):
                if value != '':
                    operations[objects.index(row[0])].append(
                        Translation.OperationData(
                            target_language=languages[index],
                            target_id=row[3],
                            value=value,
                        )
                    )
        for index, object in enumerate(objects):
            Translation.add_translation(
                connection=connection,
                id=object,
                object_type=object_types[index],
                translations=operations[index],
                project_id=project_id,
            )
        if config.verbose:
            logger.info("Successfully implemented changes from the CSV file.")

    @staticmethod
    def _get_lang_lcid(connection, language):
        from mstrio.server.language import Language

        if isinstance(language, int):
            return language
        elif isinstance(language, str):
            return Language(connection=connection, id=language).lcid
        elif isinstance(language, Language):
            return language.lcid
        else:
            raise ValueError("Please provide a valid base language.")
