import logging
from enum import auto

import pandas as pd

from mstrio.api import incremental_refresh_reports as refresh_api
from mstrio.connection import Connection
from mstrio.modeling import (
    Expression,
    ExpressionFormat,
    ObjectSubType,
    SchemaObjectReference,
)
from mstrio.object_management import Folder, SearchPattern, full_search
from mstrio.object_management.folder import get_folder_id_from_path
from mstrio.project_objects import OlapCube
from mstrio.project_objects.datasets.helpers import AdvancedProperties, Template
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    filter_params_for_func,
    find_object_with_name,
    get_objects_id,
    get_valid_project_id,
)
from mstrio.utils.parser import Parser
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import class_version_handler, method_version_handler
from mstrio.utils.vldb_mixin import ModelVldbMixin

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0600')
def list_incremental_refresh_reports(
    connection: Connection,
    name: str | None = None,
    pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    folder_id: str | None = None,
    folder_path: str | None = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = True,
    **filters,
) -> list["IncrementalRefreshReport"] | list[dict]:
    """Get a list of Incremental Refresh Reports.
    Optionally filter reports by specifying 'name'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name = ?onny will return Sonny and Tonny

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): value the search pattern is set to, which
            will be applied to the names of reports being searched
        pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Contains. Possible values are available
            in ENUM mstrio.object_management.SearchPattern.
            Default value is BEGIN WITH (4).
        project_id (string, optional): Project ID
        project_name (string, optional): Project name
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Report objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        folder_id (string, optional): ID of a folder where the search
            will be performed. Defaults to None.
        folder_path (str, optional): Path of the folder in which to look for
            reports. Can be provided as an alternative to the `folder_id`
            parameter. If both are provided, `folder_id` is used.
            The path has to be provided in the following format:
                if it's inside of a project, example:
                    /MicroStrategy Tutorial/Public Objects
                if it's a root folder, example:
                    /CASTOR_SERVER_CONFIGURATION/Users
        show_expression_as (ExpressionFormat or str, optional): specify how
            expressions should be presented
            Available values:
            - None
            (expression is returned in "text" format)
            - `ExpressionFormat.TREE` or `tree`
            (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS` or `tokens`
            (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool, optional): Specify whether "qualification"
            is returned in "tokens" format,
            along with `text` and `tree` formats.
            - If omitted or false, only `text` and `tree`
            formats are returned.
            - If true, all `text`, `tree` and `tokens` formats are returned.
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties. If false, nothing will be
            returned for the advanced properties, default True.
        filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=not project_name,
    )
    filters = filters or {}

    if folder_path and not folder_id:
        folder_id = get_folder_id_from_path(connection=connection, path=folder_path)
    if folder_id:
        filters = filters | {'root': folder_id}

    objects = full_search(
        connection,
        object_types=ObjectSubTypes.INCREMENTAL_REFRESH_REPORT,
        project=project_id,
        name=name,
        pattern=pattern,
        limit=limit,
        **filters,
    )

    if to_dictionary:
        return objects

    return [
        IncrementalRefreshReport.from_dict(
            obj
            | {
                'show_expression_as': (
                    show_expression_as
                    if isinstance(show_expression_as, ExpressionFormat)
                    else ExpressionFormat(show_expression_as)
                ),
                'show_filter_tokens': show_filter_tokens,
                'show_advanced_properties': show_advanced_properties,
            },
            connection,
        )
        for obj in objects
    ]


@class_version_handler('11.3.0600')
class IncrementalRefreshReport(
    Entity, CopyMixin, MoveMixin, DeleteMixin, TranslationMixin, ModelVldbMixin
):
    """Python representation of MicroStrategy Incremental Refresh Report object.

    Attributes:
        name: (str) Name of the Incremental Refresh Report
        id: (str) ID of the Incremental Refresh Report
        description: (str) Description of the Incremental Refresh Report
        destination_folder_id: (str) ID of the folder
        target_cube: (SchemaObjectReference) Reference to an Intelligent Cube
        refresh_type: (str) Mode the report will be refreshed in
        increment_type: (str) Mode the report will be executed in
        template: (Template) Template of information layout across dimensions
        filter: (Expression) Filtering expression for the report
    """

    class IncrementType(AutoName):
        REPORT = auto()
        FILTER = auto()

    class RefreshType(AutoName):
        INSERT = auto()
        UPDATE = auto()
        UPDATE_ONLY = auto()
        REPLACE = auto()
        DELETE = auto()

    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'target_cube': SchemaObjectReference.from_dict,
        'increment_type': IncrementType,
        'refresh_type': RefreshType,
        'template': Template.from_dict,
        'filter': Expression.from_dict,
        'advanced_properties': AdvancedProperties.from_dict,
    }

    _API_GETTERS = {
        (
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'acg',
            'acl',
            'hidden',
        ): objects_processors.get_info,
        (
            'id',
            'name',
            'description',
            'sub_type',
            'date_created',
            'date_modified',
            'path',
            'version_id',
            'is_embedded',
            'primary_locale',
            'destination_folder_id',
            'target_cube',
            'refresh_type',
            'increment_type',
            'template',
            'filter',
            'advanced_properties',
        ): refresh_api.get_incremental_refresh_report,
    }
    _API_PATCH: dict = {
        (
            'target_cube',
            'refresh_type',
            'increment_type',
            'template',
            'filter',
            'advanced_properties',
        ): (refresh_api.update_incremental_refresh_report, "put"),
        (
            'name',
            'description',
            'destination_folder_id',
            'is_embedded',
            'folder_id',
            'hidden',
        ): (objects_processors.update, 'partial_put'),
    }
    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'destination_folder_id': str,
        'is_embedded': bool,
        'target_cube': dict,
        'refresh_type': str,
        'increment_type': str,
        'filter': dict,
        'advanced_properties': dict,
        'hidden': bool,
    }
    _MODEL_VLDB_API = {
        'GET_ADVANCED': refresh_api.get_incremental_refresh_report,
        'PUT_ADVANCED': refresh_api.update_incremental_refresh_report,
        'GET_APPLICABLE': refresh_api.get_incremental_refresh_report_vldb_properties,
    }

    _ALLOW_NONE_ATTRIBUTES = ['filter', 'template']
    _KEEP_CAMEL_CASE = ['vldbProperties', 'metricJoinTypes', 'attributeJoinTypes']

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ):
        """Initialize an Incremental Refresh Report object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            id (str, optional): ID of the Incremental Refresh Report
            name (str, optional): Name of the Incremental Refresh Report
            show_expression_as (ExpressionFormat or str, optional): specify how
                expressions should be presented
                Available values:
                - None
                (expression is returned in "text" format)
                - `ExpressionFormat.TREE` or `tree`
                (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`
                (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): Specify whether "qualification"
                is returned in "tokens" format,
                along with `text` and `tree` formats.
                - If omitted or false, only `text` and `tree`
                formats are returned.
                - If true, all `text`, "tree" and `tokens` formats are returned.
            show_advanced_properties (bool, optional): Specify whether to
                retrieve the values of the advanced properties.
                The advanced properties are presented in the following groups:
                    "vldbProperties": A list of properties as determined by
                        the common infrastructure.
                    "metricJoinTypes": A list of Metric Join Types, one for each
                        metric that appears in the template.
                    "attributeJoinTypes": A list of Attribute Join Types, one
                        for each attribute that appears in the template.
                If omitted or false, nothing will be returned for the advanced
                    properties.
                If true, all applicable advanced properties are returned.
        """
        connection._validate_project_selected()

        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            reports = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_incremental_refresh_reports,
            )
            object_id = reports['id']
        else:
            object_id = id

        super().__init__(
            connection=connection,
            object_id=object_id,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
            show_advanced_properties=show_advanced_properties,
        )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self.primary_locale = kwargs.get('primary_locale')
        self.is_embedded = kwargs.get('is_embedded')
        self.destination_folder_id = kwargs.get('destination_folder_id')

        self._sub_type = (
            ObjectSubType(kwargs.get('sub_type')) if kwargs.get('sub_type') else None
        )
        self._path = kwargs.get('path')

        self.target_cube = (
            SchemaObjectReference.from_dict(kwargs.get('target_cube'))
            if kwargs.get('target_cube')
            else None
        )
        self.refresh_type = (
            self.RefreshType(kwargs.get('refresh_type'))
            if kwargs.get('refresh_type')
            else None
        )
        self.increment_type = (
            self.IncrementType(kwargs.get('increment_type'))
            if kwargs.get('increment_type')
            else None
        )
        self.template = (
            Template.from_dict(kwargs.get('template'), self.connection)
            if kwargs.get('template')
            else None
        )
        self.filter = (
            Expression.from_dict(kwargs.get('filter'), self.connection)
            if kwargs.get('filter')
            else None
        )
        self.advanced_properties = (
            AdvancedProperties.from_dict(
                kwargs.get('advanced_properties'), self.connection
            )
            if kwargs.get('advanced_properties')
            else None
        )

        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self._show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        self._show_filter_tokens = kwargs.get('show_filter_tokens', False)
        self._show_advanced_properties = kwargs.get('show_advanced_properties', False)

    def execute(
        self,
        fields: str | None = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Execute (run) the report.

        Args:
            fields (str, optional): A comma-separated list of fields to include
                in the response. By default, all fields are returned.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        project_id = get_valid_project_id(
            self.connection, project_id, project_name, with_fallback=True
        )

        response = refresh_api.execute_incremental_refresh_report(
            self.connection,
            id=self.id,
            project_id=project_id,
            fields=fields,
        )

        if response.ok:
            logger.info(
                f"Execution of Incremental Refresh Report: '{self.name}' has been "
                f"successfully scheduled under job: {response.json()}."
            )

    @classmethod
    def create(
        cls,  # NOSONAR
        connection: Connection,
        name: str,
        destination_folder: Folder | str | None = None,
        destination_folder_path: str | None = None,
        target_cube: OlapCube | SchemaObjectReference | dict | None = None,
        increment_type: IncrementType | str | None = None,
        refresh_type: RefreshType | str | None = None,
        template: Template | dict | None = None,
        filter: Expression | dict | None = None,
        advanced_properties: dict | None = None,
        description: str | None = None,
        primary_locale: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ) -> 'IncrementalRefreshReport':
        """Create a new Incremental Refresh Report.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name (str, optional): Name of the Incremental Refresh Report
            destination_folder (Folder, str): Folder object or folder ID where
                the new object will be saved
            destination_folder_path (str, optional): Path of the folder in which
                to create the report. If both folder and path parameters are
                provided, `destination_folder` is used.
                The path has to be provided in the following format:
                    if it's inside of a project, example:
                        /MicroStrategy Tutorial/Public Objects
                    if it's a root folder, example:
                        /CASTOR_SERVER_CONFIGURATION/Users
            target_cube (OlapCube, SchemaObjectReference, dict, optional):
                Reference to an Intelligent Cube
            increment_type (IncrementType, str, optional): Mode the report will
                be executed in. Accepted values: 'report', 'filter'
            refresh_type (RefreshType, str, optional): Mode the report will be
                refreshed in. Accepted values: 'update', 'insert', 'delete',
                'update_only', 'replace'
            template (Template, dict, optional): Template of information layout
                across dimensions
            filter (Expression, dict, optional): Filtering expression for the
                report. Accepted values: 'tree', 'tokens'
            advanced_properties (dict, optional): Advanced properties of the
                report
            description (str, optional): Description of the MSTR object
            primary_locale (str, optional): The primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
            show_expression_as (ExpressionFormat or str, optional): specify how
                expressions should be presented
                Available values:
                - None
                (expression is returned in "text" format)
                - `ExpressionFormat.TREE` or `tree`
                (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`
                (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): Specify whether "qualification"
                is returned in "tokens" format,
                along with `text` and `tree` formats.
                - If omitted or false, only `text` and `tree`
                formats are returned.
                - If true, all `text`, "tree" and `tokens` formats are returned.
        """

        if destination_folder_path and not destination_folder:
            destination_folder = get_folder_id_from_path(
                connection=connection, path=destination_folder_path
            )
        information = {
            'name': name,
            'description': description,
            'destinationFolderId': get_objects_id(destination_folder, Folder),
            'primaryLocale': primary_locale,
        }

        if isinstance(target_cube, SchemaObjectReference):
            target_cube = target_cube.to_dict()
        elif isinstance(target_cube, OlapCube):
            target_cube = SchemaObjectReference(
                object_id=target_cube.id,
                name=target_cube.name,
                sub_type=ObjectSubType.REPORT_CUBE,
            ).to_dict()

        body = {
            'information': delete_none_values(information, recursion=True),
            'targetCube': target_cube,
            'incrementType': get_enum_val(increment_type, cls.IncrementType),
            'refreshType': get_enum_val(refresh_type, cls.RefreshType),
            'template': (
                template.to_dict() if isinstance(template, Template) else template
            ),
            'filter': (
                filter.to_dict() if isinstance(filter, Expression) else (filter or {})
            ),
            'advanced_properties': advanced_properties,
        }

        response = refresh_api.create_incremental_refresh_report(
            connection=connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
            show_filter_tokens=show_filter_tokens,
            show_advanced_properties=show_advanced_properties,
        ).json()

        logger.info(
            f"Successfully created Incremental Refresh Report named: "
            f"'{name}' with ID: '{response['id']}'"
        )

        return cls.from_dict(
            source={
                **response,
                'show_expression_as': show_expression_as,
                'show_filter_tokens': show_filter_tokens,
                'show_advanced_properties': show_advanced_properties,
            },
            connection=connection,
        )

    @classmethod
    def create_from_cube(
        cls,
        connection: Connection,
        name: str,
        destination_folder: Folder | str | None = None,
        destination_folder_path: str | None = None,
        target_cube: OlapCube | SchemaObjectReference | dict | None = None,
        refresh_type: RefreshType | str | None = None,
        filter: Expression | dict | None = None,
        advanced_properties: dict | None = None,
        description: str | None = None,
        primary_locale: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ) -> 'IncrementalRefreshReport':
        """Create a new Incremental Refresh Report, using a data layout template
        from an existing Intelligent Cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name (str, optional): Name of the Incremental Refresh Report
            destination_folder (Folder, str): Folder object or folder ID where
                the new object will be saved
            destination_folder_path (str, optional): Path of the folder in which
                to create the report. If both folder and path parameters are
                provided, `destination_folder` is used.
                The path has to be provided in the following format:
                    if it's inside of a project, example:
                        /MicroStrategy Tutorial/Public Objects
                    if it's a root folder, example:
                        /CASTOR_SERVER_CONFIGURATION/Users
            target_cube (OlapCube, SchemaObjectReference, dict, optional):
                Reference to an Intelligent Cube
            refresh_type (RefreshType, str, optional): Mode the report will be
                refreshed in. Accepted values: 'update', 'insert', 'delete',
                'update_only', 'replace'
            filter (Expression, dict, optional): Filtering expression for the
                report. Accepted values: 'tree', 'tokens'
            advanced_properties (dict, optional): Advanced properties of the
                report
            description (str, optional): Description of the MSTR object
            primary_locale (str, optional): The primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
            show_expression_as (ExpressionFormat or str, optional): specify how
                expressions should be presented
                Available values:
                - None
                (expression is returned in "text" format)
                - `ExpressionFormat.TREE` or `tree`
                (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`
                (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): Specify whether "qualification"
                is returned in "tokens" format,
                along with `text` and `tree` formats.
                - If omitted or false, only `text` and `tree`
                formats are returned.
                - If true, all `text`, "tree" and `tokens` formats are returned.
        """
        parameters = filter_params_for_func(cls.create_from_cube, locals(), ['cls'])

        return cls.create(**parameters, increment_type=cls.IncrementType.REPORT)

    def alter(
        self,
        name: str | None = None,
        target_cube: OlapCube | SchemaObjectReference | dict | None = None,
        increment_type: IncrementType | str | None = None,
        refresh_type: RefreshType | str | None = None,
        template: Template | dict | None = None,
        filter: Expression | dict | None = None,
        advanced_properties: dict | None = None,
        description: str | None = None,
        primary_locale: str | None = None,
    ):
        """Alter the Incremental Refresh Report object's properties.

        Args:
            name (str, optional): Name of the Incremental Refresh Report.
            target_cube (OlapCube, SchemaObjectReference, dict, optional):
                Reference to an Intelligent Cube
            increment_type (IncrementType, str, optional): Mode the report will
                be executed in. Accepted values: 'report', 'filter'
            refresh_type (RefreshType, str, optional): Mode the report will be
                refreshed in. Accepted values: 'update', 'insert', 'delete',
                'update_only', 'replace'
            template (Template, dict, optional): Template of information layout
                across dimensions
            filter (Expression, dict, optional): Filtering expression for the
                report. Accepted values: 'tree', 'tokens'
            advanced_properties (dict, optional): Advanced properties of the
                report
            description (str, optional): Description of the MSTR object
            primary_locale (str, optional): The primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
        """
        if isinstance(target_cube, OlapCube):
            target_cube = SchemaObjectReference(
                object_id=target_cube.id,
                name=target_cube.name,
                sub_type=ObjectSubType.REPORT_CUBE,
            )
        filter = {} if self.filter is None and filter is None else filter  # NOSONAR
        arguments = filter_params_for_func(self.alter, locals(), exclude=['self'])

        self._alter_properties(**arguments)

    def change_increment_type_to_filter(self) -> None:
        """Change the Incremental Refresh Report's type to 'Filter'.
        This will reset the template to default.
        """
        self.fetch()
        self.template = None
        self.alter(increment_type=IncrementalRefreshReport.IncrementType.FILTER)

    def reset_template_to_default(self) -> None:
        """Reset the Incremental Refresh Report's template to default."""
        if self.increment_type == IncrementalRefreshReport.IncrementType.REPORT:
            self.change_increment_type_to_filter()
            self.alter(increment_type=IncrementalRefreshReport.IncrementType.REPORT)

    def get_preview_data(
        self,
        offset: int | None = None,
        limit: int | None = None,
        fields: str | None = None,
    ) -> pd.DataFrame:
        """Get preview data for the Incremental Refresh Report.

        Args:
            offset (int): Starting point within the collection of returned
                results. Used to control paging behavior. Default is 0.
            limit (int): limit the number of elements returned.
                If `None` (default), all objects are returned.
            fields (str, optional): A whitelist of top-level fields separated by
                commas.
        """
        response = refresh_api.create_incremental_refresh_report_instance(
            self.connection, self.id
        )
        instance_id = response.headers['X-MSTR-MS-Instance']
        refresh_api.request_incremental_refresh_report_preview_data(
            connection=self.connection,
            id=self.id,
            instance_id=instance_id,
            project_id=self.connection.project_id,
            fields=fields,
        )
        json = refresh_api.get_incremental_refresh_report_preview_data(
            connection=self.connection,
            id=self.id,
            instance_id=instance_id,
            project_id=self.connection.project_id,
            offset=offset,
            limit=limit,
            fields=fields,
        ).json()

        refresh_api.delete_incremental_refresh_report_instance(
            connection=self.connection,
            id=self.id,
            instance_id=instance_id,
        )

        parser = Parser(response=json, parse_cube=False)
        parser.parse(response=json)

        return parser.dataframe
