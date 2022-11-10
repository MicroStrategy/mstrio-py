from enum import auto
import logging
from typing import Optional, Type

import pandas as pd

from mstrio.api import incremental_refresh_reports as refresh_api
from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.modeling import (
    Expression,
    ExpressionFormat,
    ObjectSubType,
    SchemaObjectReference,
)
from mstrio.object_management import Folder, full_search
from mstrio.project_objects import OlapCube
from mstrio.project_objects.incremental_refresh_report import (
    AdvancedProperties,
    Template,
)
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    filter_params_for_func,
    get_objects_id,
    get_valid_project_id,
)
from mstrio.utils.parser import Parser
from mstrio.utils.version_helper import class_version_handler, method_version_handler
from mstrio.utils.wip import module_wip, WipLevels

logger = logging.getLogger(__name__)

module_wip(globals(), level=WipLevels.WARNING)


@method_version_handler('11.3.0600')
def list_incremental_refresh_reports(
    connection: Connection,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    folder_id: Optional[str] = None,
    filters: Optional[dict] = None,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    show_filter_tokens: bool = False,
    show_advanced_properties: bool = False,
) -> list[Type['IncrementalRefreshReport']] | list[dict]:
    return IncrementalRefreshReport.list(
        connection,
        name,
        project_id,
        project_name,
        to_dictionary,
        limit,
        folder_id,
        filters,
        show_expression_as,
        show_filter_tokens,
        show_advanced_properties,
    )


@class_version_handler('11.3.0600')
class IncrementalRefreshReport(Entity, CopyMixin, MoveMixin, DeleteMixin):
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
        ): objects.get_object_info,
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
        ): (objects.update_object, 'partial_put'),
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
    }

    _API_DELETE = staticmethod(objects.delete_object)
    _ALLOW_NONE_ATTRIBUTES = ['filter', 'template']
    _KEEP_CAMEL_CASE = ['vldbProperties', 'metricJoinTypes', 'attributeJoinTypes']

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ):
        connection._validate_project_selected()

        if id is None:
            reports = super()._find_object_with_name(
                connection=connection, name=name, listing_function=self.list
            )
            id = reports['id']

        super().__init__(
            connection=connection,
            object_id=id,
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
        fields: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> None:
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
                f"Execution of Incremental Refresh Report: '{self.name}' has been successfully "
                f"scheduled under job: {response.json()}."
            )

    @classmethod
    def list(
        cls,
        connection: Connection,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        to_dictionary: bool = False,
        limit: Optional[int] = None,
        folder_id: Optional[str] = None,
        filters: Optional[dict] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ) -> list[Type['IncrementalRefreshReport']] | list[dict]:
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True,
        )
        filters = filters or {}

        if folder_id:
            filters = filters | {'root': folder_id}

        objects = full_search(
            connection,
            object_types=ObjectSubTypes.INCREMENTAL_REFRESH_REPORT,
            project=project_id,
            name=name,
            limit=limit,
            **filters,
        )

        if to_dictionary:
            return objects

        return [
            cls.from_dict(
                obj
                | {
                    'show_expression_as': show_expression_as
                    if isinstance(show_expression_as, ExpressionFormat)
                    else ExpressionFormat(show_expression_as),
                    'show_filter_tokens': show_filter_tokens,
                    'show_advanced_properties': show_advanced_properties,
                },
                connection,
            )
            for obj in objects
        ]

    @classmethod
    def create(
        cls,  # NOSONAR
        connection: Connection,
        name: str,
        destination_folder: Folder | str,
        target_cube: OlapCube | SchemaObjectReference | dict,
        increment_type: IncrementType | str,
        refresh_type: RefreshType | str,
        template: Template | dict = None,
        filter: Optional[Expression | dict] = None,
        advanced_properties: Optional[dict] = None,
        description: Optional[str] = None,
        primary_locale: Optional[str] = None,
        is_embedded: bool = False,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ) -> 'IncrementalRefreshReport':
        information = {
            'name': name,
            'description': description,
            'destinationFolderId': get_objects_id(destination_folder, Folder),
            'primaryLocale': primary_locale,
            'isEmbedded': is_embedded,
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
            'template': template.to_dict()
            if isinstance(template, Template)
            else template,
            'filter': filter.to_dict()
            if isinstance(filter, Expression)
            else (filter or {}),
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
        destination_folder: Folder | str,
        target_cube: OlapCube | SchemaObjectReference | dict,
        refresh_type: RefreshType | str,
        filter: Optional[Expression | dict] = None,
        advanced_properties: Optional[dict] = None,
        description: Optional[str] = None,
        primary_locale: Optional[str] = None,
        is_embedded: bool = False,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
        show_advanced_properties: bool = False,
    ) -> 'IncrementalRefreshReport':
        parameters = filter_params_for_func(cls.create_from_cube, locals(), ['cls'])

        return cls.create(**parameters, increment_type=cls.IncrementType.REPORT)

    def alter(
        self,
        name: Optional[str] = None,
        target_cube: Optional[OlapCube | SchemaObjectReference | dict] = None,
        increment_type: Optional[IncrementType | str] = None,
        refresh_type: Optional[RefreshType | str] = None,
        template: Optional[Template | dict] = None,
        filter: Optional[Expression | dict] = None,
        advanced_properties: Optional[dict] = None,
        description: Optional[str] = None,
        primary_locale: Optional[str] = None,
        is_embedded: Optional[bool] = None,
    ):
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
        self.fetch()
        self.template = None
        self.alter(increment_type=IncrementalRefreshReport.IncrementType.FILTER)

    def reset_template_to_default(self) -> None:
        if self.increment_type == IncrementalRefreshReport.IncrementType.REPORT:
            self.change_increment_type_to_filter()
            self.alter(increment_type=IncrementalRefreshReport.IncrementType.REPORT)

    def list_applicable_vldb_properties(self) -> dict:
        response = refresh_api.get_incremental_refresh_report_vldb_properties(
            self.connection, id=self.id, project_id=self.connection.project_id
        )
        return response.json()

    def get_preview_data(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[str] = None,
    ) -> pd.DataFrame:
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
