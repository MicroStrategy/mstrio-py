import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd
import pypika as sql

from mstrio import config
from mstrio.connection import Connection
from mstrio.datasources import DatasourceInstance
from mstrio.server.project import Project
from mstrio.types import ObjectTypes
from mstrio.utils.entity import Entity
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    Dictable,
    IServerError,
    VersionException,
)
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import objects, projects
from mstrio.utils.version_helper import is_server_min_version, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.language import Language

logger = logging.getLogger(__name__)


@method_version_handler(version='11.3.7')
def list_translations(
    connection: Connection,
    id: str,
    object_type: int | ObjectTypes,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    languages: 'list[Language | str] | None' = None,
    to_dictionary: bool = False,
) -> list['Translation'] | list[dict]:
    """Lists translations of the given Object.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the Object the translations will be listed for
        object_type (int | ObjectTypes): type of the Object the translations
            will be listed for
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
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
        list of Translation Objects.
    """
    object_type = get_enum_val(object_type, ObjectTypes)

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
        assert_id_exists=False,
    )

    output = objects.get_translations(
        connection=connection,
        project_id=proj_id,
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

    _db_types = {
        'MySQL': sql.MySQLQuery,
        'MSSQL': sql.MSSQLQuery,
        'PostgreSQL': sql.PostgreSQLQuery,
        'Oracle': sql.OracleQuery,
        'Vertica': sql.VerticaQuery,
    }

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
    translation_values: list[TranslationValue]

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translation(
        connection: Connection,
        id: str,
        object_type: int | ObjectTypes,
        translations: list[OperationData],
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> list['Translation']:
        """Adds translations to the Object.

        Args:
            connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            A list of translations for the Object.
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        object_type = get_enum_val(object_type, ObjectTypes)
        operations_list = []
        translations = Translation._get_valid_target_ids(
            connection=connection,
            translations=translations,
            id=id,
            object_type=object_type,
            project_id=proj_id,
            operation_type='adding',
        )

        for translation in translations:
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
            project_id=proj_id,
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
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Alters translations for the Object.

        Args:
            connection(Connection): Strategy One connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        object_type = get_enum_val(object_type, ObjectTypes)
        operations_list = []
        obj_translations = list_translations(
            connection=connection,
            id=id,
            object_type=object_type,
            project_id=proj_id,
        )
        translations = Translation._get_valid_target_ids(
            connection=connection,
            translations=translations,
            id=id,
            object_type=object_type,
            project_id=proj_id,
            operation_type='altering',
        )

        for translation in translations:
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
            project_id=proj_id,
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
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Removes translations from the Object.

        Args:
            connection(Connection): Strategy One connection object returned by
            `connection.Connection()`
            id (str): ID of the Object the translation will be added to
            object_type (int | ObjectTypes): type of the Object
            translations (list[OperationData]): list of translations to be added
                to the Object
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        object_type = get_enum_val(object_type, ObjectTypes)
        operations_list = []
        translations = Translation._get_valid_target_ids(
            connection=connection,
            translations=translations,
            id=id,
            object_type=object_type,
            project_id=proj_id,
            operation_type='deleting',
        )

        for translation in translations:
            base_lcid = Translation._get_lang_lcid(
                connection=connection, language=translation.target_language
            )
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
            project_id=proj_id,
            body=body,
            object_type=object_type,
        )

        if config.verbose:
            logger.info(f"Successfully deleted Translations for Object with ID: {id}")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def to_csv_from_list(
        connection: Connection,
        object_list: list[Entity],
        separator: str = ';',
        languages: list | None = None,
        file_path: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        denormalized_form: bool = False,
        add_object_path: bool = False,
        add_object_description: bool = False,
        add_object_version: bool = False,
        add_object_last_modified_date: bool = False,
        add_object_creation_date: bool = False,
    ) -> str | None:
        """Export translations of the given objects to a CSV file.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            separator (str, optional): specify the separator for the csv file.
                Defaults to a semicolon ;
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            file_path (str, optional): a path specifying where to save the csv
                file
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            denormalized_form (bool, optional): if True exports the data in a
                denormalized form, if False exports the data in a normalized
                form. False by default.
                Normalised form means that each row contains a single target_id
                with translation values for all required languages
                Denormalised form means each row represents a translation value
                for one target_id and one language at a time
            add_object_path (bool, optional): if True adds a column with the
                path of the Object
            add_object_description (bool, optional): if True adds a column with
                the description of the Object
            add_object_version (bool, optional): if True adds a column with the
                version of the Object
            add_object_last_modified_date (bool, optional): if True adds a
                column with the last modified date of the Object
            add_object_creation_date (bool, optional): if True adds a column
                with the creation date of the Object

        Returns:
            String representation of the CSV file if no path was given or
            `None` if path was provided.
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        _prepare_dataframe = (
            Translation._prepare_denormalized_dataframe
            if denormalized_form
            else Translation._prepare_normalized_dataframe
        )
        dataframe = _prepare_dataframe(
            connection=connection,
            project_id=proj_id,
            object_list=object_list,
            languages=languages,
            path=add_object_path,
            description=add_object_description,
            version=add_object_version,
            last_modified=add_object_last_modified_date,
            creation_date=add_object_creation_date,
        )
        return dataframe.to_csv(index=False, path_or_buf=file_path, sep=separator)

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translations_from_csv(
        connection: Connection,
        file_path: str,
        separator: str = ';',
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        delete: bool = False,
        automatch_target_ids: bool = False,
    ) -> None:
        """Add translations from a specified CSV file.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            file_path (str): a path specifying the CSV file
            separator (str, optional): specify the separator of the csv file.
                Defaults to a semicolon ;
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            delete (bool, optional): if True deletes translations for languages
                that are empty in the CSV file. False by default.
            automatch_target_ids (bool, optional): if True tries to match the
                target IDs from the file that are not found in the Objects on
                the server by the content of the translation for the project's
                default language. False by default.

        To ensure correct import, the columns from the original file cannot be
        renamed. Columns can be deleted (with the exception of object ID, object
        type and target ID) but new columns cannot be added. The column order
        does not matter.
        """

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )
        df = pd.read_csv(file_path, na_filter=False, sep=separator)

        Translation._implement_changes_from_dataframe(
            connection=connection,
            df=df,
            project_id=proj_id,
            delete=delete,
            automatch_target_ids=automatch_target_ids,
        )
        if config.verbose:
            logger.info("Successfully implemented changes from the CSV file.")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def to_database_from_list(
        connection: Connection,
        object_list: list[Entity],
        table_name: str,
        datasource: DatasourceInstance | str,
        database_type: str | None = None,
        languages: list | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        denormalized_form: bool = False,
        add_object_path: bool = False,
        add_object_description: bool = False,
        add_object_version: bool = False,
        add_object_last_modified_date: bool = False,
        add_object_creation_date: bool = False,
        force: bool = False,
    ) -> None:
        """Export translations of the given objects to an SQL database table.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            table_name (str): name of the table to export the data to
                If the table with the given name already exists, the existing
                table will be dropped first, then a new one will be created.
            datasource (DatasourceInstance | str): DatasourceInstance object or
                ID of the DatasourceInstance containing the connection to the
                database to export the data to
            database_type (str, optional): type of the database, if not provided
                standard SQL will be used.
                Supported database types include:
                    - MySQL
                    - MSSQL
                    - PostgreSQL
                    - Oracle
                    - Vertica
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            denormalized_form (bool, optional): if True exports the data in a
                denormalized form, if False exports the data in a normalized
                form. False by default.
                Normalised form means that each row contains a single target_id
                with translation values for all required languages
                Denormalised form means each row represents a translation value
                for one target_id and one language at a time
            add_object_path (bool, optional): if True adds a column with the
                path of the Object
            add_object_description (bool, optional): if True adds a column with
                the description of the Object
            add_object_version (bool, optional): if True adds a column with the
                version of the Object
            add_object_last_modified_date (bool, optional): if True adds a
                column with the last modified date of the Object
            add_object_creation_date (bool, optional): if True adds a column
                with the creation date of the Object
            force (bool, optional): if True skips the prompt asking for
                confirmation before dropping the table. False by default.
        """
        if not force:
            user_input = input(
                "Warning: This method will drop the specified table if "
                "it exists before exporting the translations, proceed? [Y/N]: "
            )
            if user_input != "Y":
                return None

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        if isinstance(datasource, DatasourceInstance):
            datasource = datasource.id
        _prepare_dataframe = (
            Translation._prepare_denormalized_dataframe
            if denormalized_form
            else Translation._prepare_normalized_dataframe
        )
        dataframe = _prepare_dataframe(
            connection=connection,
            project_id=proj_id,
            object_list=object_list,
            languages=languages,
            path=add_object_path,
            description=add_object_description,
            version=add_object_version,
            last_modified=add_object_last_modified_date,
            creation_date=add_object_creation_date,
        )
        if config.verbose:
            logger.info("Getting query status on dropping table.")
        DatasourceInstance._execute_query(
            connection=connection,
            query=sql.Query.drop_table(table_name).if_exists(),
            datasource_id=datasource,
            project_id=proj_id,
        )

        if config.verbose:
            logger.info("Getting query status on creating table.")
        DatasourceInstance._execute_query(
            connection=connection,
            query=Translation._create_table_query(
                dataframe=dataframe,
                table_name=table_name,
                database_type=database_type,
            ),
            datasource_id=datasource,
            project_id=proj_id,
        )

        if config.verbose:
            logger.info("Getting query status on populating table.")
        DatasourceInstance._execute_query(
            connection=connection,
            query=Translation._create_data_query(
                dataframe=dataframe,
                table_name=table_name,
                database_type=database_type,
            ),
            datasource_id=datasource,
            project_id=proj_id,
        )

        if config.verbose:
            logger.info("Successfully exported translations to the database.")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translations_from_database(
        connection: Connection,
        table_name: str,
        datasource: DatasourceInstance | str,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        delete: bool = False,
        automatch_target_ids: bool = False,
    ) -> None:
        """Add translations from a specified database table.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            table_name (str): name of the table to import the data from
            datasource (DatasourceInstance | str): DatasourceInstance object or
                ID of the DatasourceInstance containing the connection to the
                database to export the data to
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            delete (bool, optional): if True deletes translations for languages
                that are empty in the database table. False by default.
            automatch_target_ids (bool, optional): if True tries to match the
                target IDs from the file that are not found in the Objects on
                the server by the content of the translation for the project's
                default language. False by default.

        To ensure correct import, the columns originally exported to database
        cannot be renamed. Columns can be deleted (with the exception of object
        ID, object type and target ID) but new columns cannot be added.
        """

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        if isinstance(datasource, DatasourceInstance):
            datasource = datasource.id
        if config.verbose:
            logger.info("Fetching translation data from the table.")
        execution_data = DatasourceInstance._execute_query(
            connection=connection,
            query=sql.Query.from_(table_name).select('*'),
            datasource_id=datasource,
            project_id=proj_id,
        )
        df = pd.DataFrame.from_dict(
            data=execution_data.get('results').get('data'), orient='columns'
        )
        Translation._implement_changes_from_dataframe(
            connection=connection,
            df=df,
            project_id=proj_id,
            delete=delete,
            automatch_target_ids=automatch_target_ids,
        )
        if config.verbose:
            logger.info("Successfully implemented changes from the database.")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def to_json_from_list(
        connection: Connection,
        object_list: list[Entity],
        languages: list | None = None,
        file_path: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        denormalized_form: bool = False,
        add_object_path: bool = False,
        add_object_description: bool = False,
        add_object_version: bool = False,
        add_object_last_modified_date: bool = False,
        add_object_creation_date: bool = False,
    ) -> str | None:
        """Export translations of the given objects to a JSON file.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            file_path (str, optional): a path specifying where to save the
                json file
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            denormalized_form (bool, optional): if True exports the data in a
                denormalized form, if False exports the data in a normalized
                form. False by default.
                Normalised form means that each row contains a single target_id
                with translation values for all required languages
                Denormalised form means each row represents a translation value
                for one target_id and one language at a time
            add_object_path (bool, optional): if True adds a column with the
                path of the Object
            add_object_description (bool, optional): if True adds a column with
                the description of the Object
            add_object_version (bool, optional): if True adds a column with the
                version of the Object
            add_object_last_modified_date (bool, optional): if True adds a
                column with the last modified date of the Object
            add_object_creation_date (bool, optional): if True adds a column
                with the creation date of the Object

        Returns:
            String representation of the JSON file if no path was given or
            `None` if path was provided.
        """

        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        _prepare_dataframe = (
            Translation._prepare_denormalized_dataframe
            if denormalized_form
            else Translation._prepare_normalized_dataframe
        )
        dataframe = _prepare_dataframe(
            connection=connection,
            project_id=proj_id,
            object_list=object_list,
            languages=languages,
            path=add_object_path,
            description=add_object_description,
            version=add_object_version,
            last_modified=add_object_last_modified_date,
            creation_date=add_object_creation_date,
        )
        if file_path:
            with open(file=file_path, mode='w', encoding='utf-8') as file:
                return dataframe.to_json(
                    path_or_buf=file,
                    orient='records',
                    force_ascii=False,
                    date_format='iso',
                )
        else:
            return dataframe.to_json(orient='records', date_format='iso')

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translations_from_json(
        connection: Connection,
        file_path: str,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        delete: bool = False,
        automatch_target_ids: bool = False,
    ) -> None:
        """Add translations from a specified JSON file.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            file_path (str): a path specifying the JSON file
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            delete (bool, optional): if True deletes translations for languages
                that are empty in the JSON file. False by default.
            automatch_target_ids (bool, optional): if True tries to match the
                target IDs from the file that are not found in the Objects on
                the server by the content of the translation for the project's
                default language. False by default.

        To ensure correct import, the columns from the original file cannot be
        renamed. Columns can be deleted (with the exception of object ID, object
        type and target ID) but new columns cannot be added. The column order
        does not matter.
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )
        df = pd.read_json(file_path, orient='records')

        Translation._implement_changes_from_dataframe(
            connection=connection,
            df=df,
            project_id=proj_id,
            delete=delete,
            automatch_target_ids=automatch_target_ids,
        )

        if config.verbose:
            logger.info("Successfully implemented changes from the JSON file.")

    @staticmethod
    @method_version_handler(version='11.3.7')
    def to_dataframe_from_list(
        connection: Connection,
        object_list: list[Entity],
        languages: list | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        denormalized_form: bool = False,
        add_object_path: bool = False,
        add_object_description: bool = False,
        add_object_version: bool = False,
        add_object_last_modified_date: bool = False,
        add_object_creation_date: bool = False,
    ) -> pd.DataFrame:
        """Export translations of the given objects to a dataframe.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            denormalized_form (bool, optional): if True exports the data in a
                denormalized form, if False exports the data in a normalized
                form. False by default.
                Normalised form means that each row contains a single target_id
                with translation values for all required languages
                Denormalised form means each row represents a translation value
                for one target_id and one language at a time
            add_object_path (bool, optional): if True adds a column with the
                path of the Object
            add_object_description (bool, optional): if True adds a column with
                the description of the Object
            add_object_version (bool, optional): if True adds a column with the
                version of the Object
            add_object_last_modified_date (bool, optional): if True adds a
                column with the last modified date of the Object
            add_object_creation_date (bool, optional): if True adds a column
                with the creation date of the Object

        Returns:
            A pandas Dataframe containing the translation data.
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )
        _prepare_dataframe = (
            Translation._prepare_denormalized_dataframe
            if denormalized_form
            else Translation._prepare_normalized_dataframe
        )
        dataframe = _prepare_dataframe(
            connection=connection,
            project_id=proj_id,
            object_list=object_list,
            languages=languages,
            path=add_object_path,
            description=add_object_description,
            version=add_object_version,
            last_modified=add_object_last_modified_date,
            creation_date=add_object_creation_date,
        )
        return dataframe

    @staticmethod
    @method_version_handler(version='11.3.7')
    def add_translations_from_dataframe(
        connection: Connection,
        dataframe: pd.DataFrame,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        delete: bool = False,
        automatch_target_ids: bool = False,
    ) -> None:
        """Add translations from a given dataframe.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            dataframe (pd.DataFrame): dataframe containing the data to be
                imported
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
            delete (bool, optional): if True deletes translations for languages
                that are empty in the dataframe. False by default.
            automatch_target_ids (bool, optional): if True tries to match the
                target IDs from the file that are not found in the Objects on
                the server by the content of the translation for the project's
                default language. False by default.

        To ensure correct import, the columns from the original dataframe cannot
        be renamed. Columns can be deleted (with the exception of object ID,
        object type and target ID) but new columns cannot be added. The column
        order does not matter.
        """
        proj_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
            assert_id_exists=False,
        )

        Translation._implement_changes_from_dataframe(
            connection=connection,
            df=dataframe,
            project_id=proj_id,
            delete=delete,
            automatch_target_ids=automatch_target_ids,
        )

        if config.verbose:
            logger.info("Successfully implemented changes from the dataframe.")

    @staticmethod
    def _get_lang_lcid(connection: Connection, language) -> int:
        """Returns the lcid of the language.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            language (str | int | Language): language to get the lcid for, can
                be one of the following:
                    - lcid attribute of the language (will be returned back)
                    - ID of the language
                    - Language class object

        Returns:
            lcid of the language.
        """
        from mstrio.server.language import Language

        if isinstance(language, int):
            return language
        elif isinstance(language, str):
            return Language(connection=connection, id=language).lcid
        elif isinstance(language, Language):
            return language.lcid
        else:
            raise ValueError("Please provide a valid base language.")

    @staticmethod
    def _create_table_query(
        dataframe: pd.DataFrame,
        table_name: str,
        database_type: str | None = None,
    ) -> sql.Query:
        """Creates a query for creating a table in the database.

        Args:
            dataframe (pd.DataFrame): dataframe containing the data on the
                columns necessary for the table
            table_name (str): name of the table to be created
            database_type (str, optional): type of the database, if not provided
                standard SQL will be used.

        Returns:
            Prepared pypika query.
        """
        columns = []
        for column in dataframe.columns.values:
            columns.append(sql.Column(column, 'VARCHAR'))
        if database_type is None:
            return sql.Query.create_table(table_name).columns(*columns)
        else:
            return (
                Translation._db_types.get(database_type)
                .create_table(table_name)
                .columns(*columns)
            )

    @staticmethod
    def _create_data_query(
        dataframe: pd.DataFrame,
        table_name: str,
        database_type: str | None = None,
    ) -> sql.Query:
        """Creates a query for inserting data into the database.

        Args:
            dataframe (pd.DataFrame): dataframe containing the data to be
                inserted into the table
            table_name (str): name of the table to insert the data into
            database_type (str, optional): type of the database, if not provided
                standard SQL will be used.

        Returns:
            Prepared pypika Query.
        """
        tuples = list(dataframe.itertuples(index=False, name=None))
        if database_type is None:
            return sql.Query.into(table_name).insert(*tuples)
        else:
            return (
                Translation._db_types.get(database_type)
                .into(table_name)
                .insert(*tuples)
            )

    @staticmethod
    def _prepare_normalized_dataframe(
        connection: Connection,
        project_id: str,
        object_list: list[Entity],
        languages: list | None = None,
        path: bool = False,
        description: bool = False,
        version: bool = False,
        last_modified: bool = False,
        creation_date: bool = False,
    ) -> pd.DataFrame:
        """Prepares a normalized dataframe for exporting translations.
        Normalised form means that each row contains a single target_id with
        translation values for all required languages.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            project_id (str): ID of the project the Objects are a part of
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            path (bool, optional): if True adds a column with the path of the
                Object
            description (bool, optional): if True adds a column with the
                description of the Object
            version (bool, optional): if True adds a column with the version of
                the Object
            last_modified (bool, optional): if True adds a column with the last
                modified date of the Object
            creation_date (bool, optional): if True adds a column with the
                creation date of the Object

        Returns:
            Dataframe containing the data to be exported.
        """
        from mstrio.server.language import Language

        if not object_list:
            raise ValueError(
                'List of objects to export translations for is empty. '
                'Please make sure to provide at least one object in object_list.'
            )

        languages_list = []
        languages_list_lcid = []
        dataframes = []
        project_name = Project(connection, id=project_id).name

        if languages:
            for lang in languages:
                if isinstance(lang, str):
                    temp_lang = Language(connection=connection, id=lang)
                    languages_list.append(temp_lang.name)
                    languages_list_lcid.append(temp_lang.lcid)
                elif isinstance(lang, Language):
                    languages_list.append(lang.name)
                    languages_list_lcid.append(lang.lcid)
        else:
            proj_languages = projects.get_project_languages(
                connection=connection, id=project_id, path='metadata'
            )
            for lang in proj_languages:
                languages_list.append(proj_languages.get(lang).get('name'))
                languages_list_lcid.append(
                    Translation._get_lang_lcid(connection=connection, language=lang)
                )
        for curr_object in object_list:
            object_type = get_enum_val(curr_object.type, ObjectTypes)

            translations = list_translations(
                connection=connection,
                id=curr_object.id,
                object_type=object_type,
                project_id=project_id,
                languages=languages_list_lcid,
            )
            columns_list = [
                'project ID',
                'project name',
                'object ID',
                'object name',
                'object type',
            ]
            if path:
                columns_list.append('object path')
            if description:
                columns_list.append('object description')
            if version:
                columns_list.append('object version')
            if last_modified:
                columns_list.append('last modified date')
            if creation_date:
                columns_list.append('creation date')
            columns_list += ['target name', 'target ID']
            for translation in translations:
                row_to_add = [
                    project_id,
                    project_name,
                    curr_object.id,
                    curr_object.name,
                    object_type,
                ]
                if path:
                    row_to_add.append(curr_object.location)
                if description:
                    row_to_add.append(curr_object.description)
                if version:
                    row_to_add.append(curr_object.version)
                if last_modified:
                    row_to_add.append(curr_object.date_modified)
                if creation_date:
                    row_to_add.append(curr_object.date_created)
                row_to_add += [
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
                        columns=columns_list + languages_list,
                    ),
                )
        dataframe = pd.concat(dataframes, ignore_index=True)
        return dataframe

    @staticmethod
    def _prepare_denormalized_dataframe(
        connection: Connection,
        project_id: str,
        object_list: list[Entity],
        languages: list | None = None,
        path: bool = False,
        description: bool = False,
        version: bool = False,
        last_modified: bool = False,
        creation_date: bool = False,
    ) -> pd.DataFrame:
        """Prepares a denormalized dataframe for exporting translations.
        Denormalised form means each row represents a translation value for one
        target_id and one language at a time.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            project_id (str): ID of the project the Objects are a part of
            object_list (list[Entity]): list of Objects to export translations
                for. Objects have to be provided as class objects such as a
                Metric or a Document.
            languages (list, optional): list of languages to list translations
                for, only translations from these languages will be listed.
                If not specified languages will be taken from the project.
                Languages in the list should be one of the following:
                    - ID of the language
                    - Language class object
            path (bool, optional): if True adds a column with the path of the
                Object
            description (bool, optional): if True adds a column with the
                description of the Object
            version (bool, optional): if True adds a column with the version of
                the Object
            last_modified (bool, optional): if True adds a column with the last
                modified date of the Object
            creation_date (bool, optional): if True adds a column with the
                creation date of the Object

        Returns:
            Dataframe containing the data to be exported.
        """
        from mstrio.server.language import Language

        if not object_list:
            raise ValueError(
                'List of objects to export translations for is empty. '
                'Please make sure to provide at least one object in object_list.'
            )

        languages_list = []
        languages_list_lcid = []
        dataframes = []
        project_name = Project(connection, id=project_id).name

        if languages:
            for lang in languages:
                if isinstance(lang, str):
                    temp_lang = Language(connection=connection, id=lang)
                    languages_list.append(temp_lang.name)
                    languages_list_lcid.append(temp_lang.lcid)
                elif isinstance(lang, Language):
                    languages_list.append(lang.name)
                    languages_list_lcid.append(lang.lcid)
        else:
            proj_languages = projects.get_project_languages(
                connection=connection, id=project_id, path='metadata'
            )
            for lang in proj_languages:
                languages_list.append(proj_languages.get(lang).get('name'))
                languages_list_lcid.append(
                    Translation._get_lang_lcid(connection=connection, language=lang)
                )

        for curr_object in object_list:
            object_type = get_enum_val(curr_object.type, ObjectTypes)

            translations = list_translations(
                connection=connection,
                id=curr_object.id,
                object_type=object_type,
                project_id=project_id,
                languages=languages_list_lcid,
            )
            columns_list = [
                'project ID',
                'project name',
                'object ID',
                'object name',
                'object type',
            ]
            if path:
                columns_list.append('object path')
            if description:
                columns_list.append('object description')
            if version:
                columns_list.append('object version')
            if last_modified:
                columns_list.append('last modified date')
            if creation_date:
                columns_list.append('creation date')
            columns_list += [
                'target name',
                'target ID',
                'language name',
                'translation value',
            ]
            for translation in translations:
                for trans_value in translation.translation_values:
                    if int(trans_value.language_lcid) in languages_list_lcid:
                        row_to_add = [
                            project_id,
                            project_name,
                            curr_object.id,
                            curr_object.name,
                            object_type,
                        ]
                        if path:
                            row_to_add.append(curr_object.location)
                        if description:
                            row_to_add.append(curr_object.description)
                        if version:
                            row_to_add.append(curr_object.version)
                        if last_modified:
                            row_to_add.append(curr_object.date_modified)
                        if creation_date:
                            row_to_add.append(curr_object.date_created)
                        row_to_add += [
                            translation.translation_target_name,
                            translation.translation_target_id,
                            languages_list[
                                languages_list_lcid.index(
                                    int(trans_value.language_lcid)
                                )
                            ],
                            trans_value.value,
                        ]
                        dataframes.append(
                            pd.DataFrame(
                                data=[row_to_add],
                                columns=columns_list,
                            ),
                        )
        dataframe = pd.concat(dataframes, ignore_index=True)
        return dataframe

    @staticmethod
    def _implement_changes_from_dataframe(
        connection: Connection,
        df: pd.DataFrame,
        project_id: str,
        delete: bool = False,
        automatch_target_ids: bool = False,
    ) -> None:
        """Implements changes to translations from a dataframe.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            df (pd.DataFrame): dataframe containing the changes to be applied
                to the translations on the server
            project_id (str): ID of the project the Objects are a part of
            delete (bool, optional): if True deletes translations for languages
                that are empty in the dataframe. False by default.
            automatch_target_ids (bool, optional): if True tries to match the
                target IDs from the file that are not found in the Objects on
                the server by the content of the translation for the project's
                default language. False by default.
        """
        from mstrio.server.language import Language

        if delete:
            if not is_server_min_version(
                connection=connection, version_str='11.4.0300'
            ):
                raise VersionException(
                    'Support for deletion requires version 11.4.03 or later'
                )
            operations_delete = []

        if 'language name' in df.columns.tolist():
            raise KeyError('Denormalized form of the dataframe is not supported.')

        if automatch_target_ids:
            project_language = Language(
                connection=connection,
                id=list(
                    projects.get_default_language(
                        connection=connection, id=project_id, path='metadata'
                    ).keys()
                )[0],
            ).lcid

        objects = []
        object_types = []
        operations = []

        intended_columns = [
            'project ID',
            'project name',
            'object ID',
            'object name',
            'object type',
            'object path',
            'object description',
            'object version',
            'last modified date',
            'creation date',
            'target name',
            'target ID',
        ]
        # Code below ensures that the columns are in the correct order specified
        # in the intended_columns list, followed by the languages columns
        columns = [
            column for column in intended_columns if column in df.columns.tolist()
        ]
        df = df[columns + df.columns.drop(columns).tolist()]

        columns = df.columns.tolist()
        languages = [
            Language(connection=connection, name=lang).lcid
            for lang in columns[columns.index('target ID') + 1 :]
        ]
        rows = df.values.tolist()
        for row in rows:
            if row[columns.index('object ID')] not in objects:
                objects.append(row[columns.index('object ID')])
                object_types.append(int(row[columns.index('object type')]))
                operations.append([])
                if delete:
                    operations_delete.append([])
            for index, value in enumerate(row[columns.index('target ID') + 1 :]):
                if value != '':
                    operations[objects.index(row[columns.index('object ID')])].append(
                        Translation.OperationData(
                            target_language=languages[index],
                            target_id=row[columns.index('target ID')],
                            value=value,
                        )
                    )
                elif delete:
                    operations_delete[
                        objects.index(row[columns.index('object ID')])
                    ].append(
                        Translation.OperationData(
                            target_language=languages[index],
                            target_id=row[columns.index('target ID')],
                        )
                    )

        for index, object in enumerate(objects):
            if automatch_target_ids:
                ids_to_replace = Translation._automatch_target_ids(
                    connection=connection,
                    translations=operations[index],
                    id=object,
                    object_type=object_types[index],
                    project_language=project_language,
                    project_id=project_id,
                )
                if ids_to_replace:
                    if config.verbose:
                        logger.info(
                            f"Automatched target IDs: {list(ids_to_replace.keys())} "
                            f"for object: {object} with the "
                            f"following replacements: {list(ids_to_replace.values())}"
                        )
                    for operation in operations[index]:
                        if operation.target_id in ids_to_replace:
                            operation.target_id = ids_to_replace[operation.target_id]
                    if delete and operations_delete[index]:
                        for operation in operations_delete[index]:
                            if operation.target_id in ids_to_replace:
                                operation.target_id = ids_to_replace[
                                    operation.target_id
                                ]
            if operations[index]:
                try:
                    Translation.add_translation(
                        connection=connection,
                        id=object,
                        object_type=int(object_types[index]),
                        translations=operations[index],
                        project_id=project_id,
                    )
                except (IServerError, ValueError) as error:
                    if config.verbose:
                        logger.warning(
                            f"Failed on adding translations for object: {object}"
                            f" with the following error: {error}"
                        )
            if delete and operations_delete[index]:
                try:
                    Translation.remove_translation(
                        connection=connection,
                        id=object,
                        object_type=int(object_types[index]),
                        translations=operations_delete[index],
                        project_id=project_id,
                    )
                except (IServerError, ValueError) as error:
                    if config.verbose:
                        logger.warning(
                            f"Failed on deleting translations for object: {object}"
                            f" with the following error: {error}"
                        )

    @staticmethod
    def _automatch_target_ids(
        connection: Connection,
        translations: list[OperationData],
        id: str,
        object_type: str,
        project_language: int,
        project_id: str,
    ) -> dict:
        """Checks whether all target_ids in the operations are present on
            the server and automatches absent ones if possible.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            translations (list[OperationData]): list of operations to check
            id (str): ID of the object
            object_type (str): type of the object
            project_language (int): lcid of the project's default language
            project_id (str): ID of the project

        Returns:
            A dictionary mapping old target_ids to new ones.
        """
        old_to_new = {}
        object_translations = list_translations(
            connection=connection,
            id=id,
            object_type=object_type,
            languages=[project_language],
            project_id=project_id,
        )
        valid_target_ids = [
            transl.translation_target_id for transl in object_translations
        ]
        for translation in translations:
            if (translation.target_language == project_language) and (
                translation.target_id not in valid_target_ids + list(old_to_new.keys())
            ):
                for existing_translation in object_translations:
                    if (
                        existing_translation.translation_values[0].value
                        == translation.value
                    ):
                        old_to_new[translation.target_id] = (
                            existing_translation.translation_target_id
                        )
                        break
        return old_to_new

    @staticmethod
    def _get_valid_target_ids(
        connection: Connection,
        translations: list[OperationData],
        id: str,
        object_type: str,
        project_id: str,
        operation_type: str,
    ) -> list[OperationData]:
        """Returns a list of target IDs that are valid for the given object.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            translations (list[OperationData]): list of operations to check
            id (str): ID of the object
            object_type (str): type of the object
            project_id (str): ID of the project
            operation_type (str): type of the operation

        Returns:
            List of operations on valid target IDs only.
        """
        new_translations = []
        valid_target_ids = [
            transl.translation_target_id
            for transl in list_translations(
                connection=connection,
                id=id,
                object_type=object_type,
                project_id=project_id,
            )
        ]
        invalid_target_ids = []

        for translation in translations:
            if translation.target_id not in valid_target_ids:
                if translation.target_id not in invalid_target_ids:
                    invalid_target_ids.append(translation.target_id)
                    if config.verbose:
                        logger.warning(
                            f"Target ID: {translation.target_id} is not valid for "
                            f"object: {id}. Skipping {operation_type} translations "
                            "for this target_id."
                        )
            else:
                new_translations.append(translation)
        return new_translations
