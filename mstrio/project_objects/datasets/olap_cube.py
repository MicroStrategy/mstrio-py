import logging
from typing import Optional

import pandas as pd

from mstrio.api import cubes
from mstrio.connection import Connection
from mstrio.modeling import (
    Attribute,
    Expression,
    ExpressionFormat,
    SchemaObjectReference,
)
from mstrio.object_management import SearchPattern, full_search
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    deprecation_warning,
    exception_handler,
    filter_params_for_func,
    get_valid_project_id,
)
from mstrio.utils.response_processors import cubes as cube_processors
from mstrio.utils.version_helper import (
    class_version_handler,
    is_server_min_version,
    method_version_handler,
)
from mstrio.utils.vldb_mixin import ModelVldbMixin

from .cube import _Cube, load_cube
from .helpers import (
    AdvancedProperties,
    AttributeTemplateUnit,
    CubeOptions,
    DataPartition,
    Template,
    TimeBasedSettings,
)

logger = logging.getLogger(__name__)


def list_olap_cubes(
    connection: Connection,
    name: Optional[str] = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters,
) -> list['OlapCube'] | list[dict]:
    """Get list of OlapCube objects or dicts with them. Optionally filter cubes
    by specifying 'name'.
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
            will be applied to the names of olap cubes being searched
        search_pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Contains. Possible values are available
            in ENUM mstrio.object_management.SearchPattern.
            Default value is BEGIN WITH (4).
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns OlapCube objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']
    Returns:
        list with OlapCubes or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects_ = full_search(
        connection,
        object_types=ObjectSubTypes.OLAP_CUBE,
        project=project_id,
        name=name,
        pattern=search_pattern,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects_
    return [OlapCube.from_dict(obj_, connection) for obj_ in objects_]


@class_version_handler('11.3.0000')
class OlapCube(ModelVldbMixin, _Cube):
    """Manage single table cube - according to EnumDSSXMLObjectSubTypes its
    subtype is  776 (DssXmlSubTypeReportCube). It inherits all properties from
    Cube.

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (str): Identifier of a pre-existing cube.
        instance_id (str): Identifier of a cube instance if already initialized,
            None by default.
        name (str): Name of the OlapCube.
        size (int): Size of cube.
        status (int): Status of cube.
        path (str): Full path of the cube on environment.
        owner_id (str): ID of cube's owner.
        attributes (list): All attributes of cube.
        metrics (list): All metrics of cube.
        attr_elements (list): All attributes elements of cube.
        selected_attributes (list): IDs of filtered attributes.
        selected_metrics (list): IDs of filtered metrics.
        selected_attr_elements (list): IDs of filtered attribute elements.
        dataframe (DataFrame): Content of a cube extracted into a
            Pandas `DataFrame`.
        template (Template): Template defining OLAP Cube structure with
            references to attributes in rows and to metrics in columns.
        filter (Expression): Filtering element for OLAP Cube, needs to
            be in either 'tree' or 'tokens' format. If both are provided,
            only 'tree' is used.
        options (CubeOptions): Options specifying the behavior of cube.
            Includes possibilities for setting languages, refresh of data
            and partitioning by attribute.
        advanced_properties (AdvancedProperties): Properties containing
            metric join type for every metric and attribute join type for
            every attribute provided in the template.
        time_based_settings (TimeBasedSettings): Settings of timezone and
            calendar objects specified with references by ID.
        show_expression_as (ExpressionFormat): Specify how expressions
            should be presented, default 'ExpressionFormat.TREE'.
            Available values:
            - `ExpressionFormat.TREE`.
                (expression is returned in `text` and `tree` formats)
            - `ExpressionFormat.TOKENS`.
                (expression is returned in `text` and `tokens` formats)
        show_filter_tokens (bool): Specify whether 'filter' is returned in
            'tokens' format, along with `text` and `tree` formats,
            default False.
            - If omitted or False, only `text` and `tree` formats are
                returned.
            - If True, all `text`, 'tree' and `tokens` formats are returned.
    """

    _OBJECT_SUBTYPE = ObjectSubTypes.OLAP_CUBE.value
    _API_GETTERS = {
        **_Cube._API_GETTERS,
        (
            'template',
            'filter',
            'options',
            'advanced_properties',
            'time_based_settings',
        ): None,
    }
    _API_PATCH = {
        **_Cube._API_PATCH,
        (
            'template',
            'filter',
            'options',
            'time_based_settings',
        ): (cube_processors.update, 'partial_put'),
    }
    _PATCH_PATH_TYPES = {
        **_Cube._API_PATCH,
        'template': dict,
        'filter': dict,
        'options': dict,
        'time_based_settings': dict,
    }
    _FROM_DICT_MAP = {
        **_Cube._FROM_DICT_MAP,
        'template': Template.from_dict,
        'filter': Expression.from_dict,
        'options': CubeOptions.from_dict,
        'advanced_properties': AdvancedProperties.from_dict,
        'time_based_settings': TimeBasedSettings.from_dict,
    }
    _MODEL_VLDB_API = {
        'GET_ADVANCED': cubes.get_cube,
        'PUT_ADVANCED': cubes.update_cube,
        'GET_APPLICABLE': cubes.get_applicable_vldb_settings,
    }

    def __init__(
        self,
        connection: Connection,
        id: str,
        name: Optional[str] = None,
        instance_id: Optional[str] = None,
        parallel: bool = True,
        progress_bar: bool = True,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ):
        """Initialize an OlapCube instance.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing cube.
            name (str): Name of a cube.
            instance_id (str): Identifier of an instance if cube instance has
                already been initialized, None by default.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download
                progress bar.
            show_expression_as (ExpressionFormat, str, optional): Specify how
                expressions should be presented,
                default 'ExpressionFormat.TREE'.
                Available values:
                - None.
                    (expression is returned in 'text' format)
                - `ExpressionFormat.TREE` or `tree`.
                    (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`.
                    (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): Specify whether 'filter'
                is returned in 'tokens' format, along with `text` and `tree`
                formats, default False.
                - If omitted or False, only `text` and `tree` formats are
                    returned.
                - If True, all `text`, 'tree' and `tokens` formats are returned.
        """
        # NOTE use the super.init from _Cube once cube_id is deprecated

        super().__init__(
            connection,
            id=id,
            name=name,
            instance_id=instance_id,
            parallel=parallel,
            progress_bar=progress_bar,
        )

        if is_server_min_version(connection, '11.3.0800'):
            self._set_object_attributes(
                show_expression_as=(
                    show_expression_as
                    if isinstance(show_expression_as, ExpressionFormat)
                    else ExpressionFormat(show_expression_as)
                ),
                show_filter_tokens=show_filter_tokens,
            )

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        if is_server_min_version(self.connection, '11.3.0800'):
            self._API_GETTERS[
                (
                    'template',
                    'filter',
                    'options',
                    'advanced_properties',
                    'time_based_settings',
                )
            ] = cube_processors.get
        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self.show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        self.show_filter_tokens = kwargs.get('show_filter_tokens', False)
        self.template = (
            Template.from_dict(template)
            if (template := kwargs.get('template'))
            else None
        )
        self.filter = (
            Expression.from_dict(filter) if (filter := kwargs.get('filter')) else None
        )
        self.options = (
            CubeOptions.from_dict(options)
            if (options := kwargs.get('options'))
            else None
        )
        self.advanced_properties = (
            AdvancedProperties.from_dict(advanced_properties)
            if (advanced_properties := kwargs.get('advanced_properties'))
            else None
        )
        self.time_based_settings = (
            TimeBasedSettings.from_dict(time_based_settings)
            if (time_based_settings := kwargs.get('time_based_settings'))
            else None
        )
        if template:
            self.__set_definition()

    @classmethod
    def available_metrics(
        cls,
        connection: Connection,
        basic_info_only: bool = True,
        to_dataframe: bool = False,
    ) -> list[dict] | list[pd.DataFrame]:
        """Get all metrics available on I-Server.
        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                metric. When False, then all properties of each metric will be
                returned.
            to_dataframe: When False (default value) then metrics are returned
                as a list of dictionaries. When True then metrics are returned
                as Pandas 'DataFrame'.
        Returns:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(
            connection, ObjectTypes.METRIC, basic_info_only, to_dataframe
        )

    @classmethod
    def available_attributes(
        cls,
        connection: Connection,
        basic_info_only: bool = True,
        to_dataframe: bool = False,
    ) -> list[dict] | list[pd.DataFrame]:
        """Get all attributes available on I-Server.
        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                attribute. When False, then all properties of each attribute
                will be returned.
            to_dataframe: When False (default value) then attributes are
                returned as a list of dictionaries. When True then attributes
                are returned as Pandas 'DataFrame'.
        Returns:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(
            connection, ObjectTypes.ATTRIBUTE, basic_info_only, to_dataframe
        )

    @classmethod
    def available_attribute_forms(
        cls,
        connection: Connection,
        basic_info_only: bool = True,
        to_dataframe: bool = False,
    ) -> list[dict] | list[pd.DataFrame]:
        """Get all attribute forms available on I-Server.
        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                attribute form. When False, then all properties of each
                attribute form will be returned.
            to_dataframe: When False (default value) then attribute forms are
                returned as a list of dictionaries. When True then attribute
                forms are returned as Pandas 'DataFrame'.
        Returns:
            List of attribute forms or attribute forms as Pandas `DataFrame`.
        """
        return cls.__available_objects(
            connection, ObjectTypes.ATTRIBUTE_FORM, basic_info_only, to_dataframe
        )

    @classmethod
    def __available_objects(
        cls,
        connection: Connection,
        object_type: ObjectTypes | ObjectSubTypes,
        basic_info_only: bool = True,
        to_dataframe: bool = False,
    ) -> list[dict] | list[pd.DataFrame]:
        """Helper function to get available objects based on their type. It
        should be used to get only available attribute, metrics or attribute
        forms."""
        connection._validate_project_selected()
        avl_objects = full_search(
            connection=connection,
            object_types=object_type,
            project=connection.project_id,
        )
        for a in avl_objects:
            new_type = None
            if a['type'] == ObjectTypes.METRIC.value:
                new_type = 'metric'
            elif a['type'] == ObjectTypes.ATTRIBUTE.value:
                new_type = 'attribute'
            elif a['type'] == ObjectTypes.ATTRIBUTE_FORM.value:
                new_type = 'form'
            if new_type:
                a['type'] = new_type

        if basic_info_only:
            avl_objects = [
                {'id': a['id'], 'name': a['name'], 'type': a['type']}
                for a in avl_objects
            ]
        if to_dataframe:
            avl_objects = pd.DataFrame.from_dict(avl_objects)

        return avl_objects

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        name: str,
        folder_id: str,
        description: Optional[str] = None,
        overwrite: Optional[bool] = None,
        attributes: Optional[list[dict]] = None,
        metrics: Optional[list[dict]] = None,
        template: Optional[Template | dict] = None,
        filter: Optional[Expression | dict] = None,
        options: Optional[CubeOptions | dict] = None,
        advanced_properties: Optional[AdvancedProperties | dict] = None,
        time_based_settings: Optional[TimeBasedSettings | dict] = None,
        template_cube: Optional['OlapCube | str'] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
        show_filter_tokens: bool = False,
    ) -> 'OlapCube | None':
        """Create an OLAP Cube by defining its name, destination folder ID,
        description, attributes and metrics or template from 'Template' class to
        specify structure of cube additionally providing filter, options,
        advanced properties and time based settings.

        Note:
            All types of expressions can be represented in the form of tokens,
            but some expressions with type predicate are yet not supported to be
            used for creation or modification in tokens form. For example:
            'expression_nodes.ElementListPredicate' or
            'expression_nodes.FilterQualificationPredicate' and some cases other
            involving embedded objects. Expected errors while be thrown in such
            cases.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name (str): OLAP Cube name.
            folder_id (str): ID of the folder where OLAP Cube should be saved.
            description (str, optional): OLAP Cube description.
            overwrite (bool, optional): Default value (False) not allow to
                overwrite the object with the same name.
            attributes (list[dict], optional): List with dicts of attributes
                dicts to be in the working set of OLAP Cube. Each attribute dict
                should have keys: `id`, `name` and `type`. Attributes can be
                found with method `OlapCube.available_attributes`.
            metrics (list[dict], optional): List with dicts of metrics to be
                in the working set of OLAP Cube. Each metric dict should have
                keys: `id`, `name` and `type`. Metrics can be found with
                method `OlapCube.available_metrics`.
            template (Template, dict, optional): Template defining
                OLAP Cube structure with references to attributes in
                rows and to metrics in columns.
            filter (Expression, dict, optional): Filtering element for
                OLAP Cube, needs to be in either 'tree' or 'tokens' format.
                If both are provided, only 'tree' is used.
            options (CubeOptions, dict, optional): Options specifying the
                behavior of cube. Includes possibilities for setting languages,
                refresh of data and partitioning by attribute.
            advanced_properties (AdvancedProperties, dict, optional): Properties
                containing metric join type for every metric and attribute join
                type for every attribute provided in the template.
            time_based_settings (TimeBasedSettings, dict, optional): Settings of
                timezone and calendar objects specified with references by ID.
            template_cube (OlapCube, str, optional): If specified, a newly
                created OLAP Cube will inherit its template from a provided
                OlapCube object. A filter of the referenced cube will be used in
                the case when a 'filter' parameter was not specified.
            show_expression_as (ExpressionFormat, str, optional): Specify how
                expressions should be presented,
                default 'ExpressionFormat.TREE'.
                Available values:
                - None.
                    (expression is returned in 'text' format)
                - `ExpressionFormat.TREE` or `tree`.
                    (expression is returned in `text` and `tree` formats)
                - `ExpressionFormat.TOKENS` or `tokens`.
                    (expression is returned in `text` and `tokens` formats)
            show_filter_tokens (bool, optional): Specify whether 'filter'
                is returned in 'tokens' format, along with `text` and `tree`
                formats, default False.
                - If omitted or False, only `text` and `tree` formats are
                    returned.
                - If True, all `text`, 'tree' and `tokens` formats are returned.

        Raises:
            ValueError: When provided template is empty.

        Returns:
            Newly created OLAP Cube or None in case of incorrectly provided
                arguments.
        """

        if attributes or metrics or overwrite:
            attributes = attributes or []
            metrics = metrics or []

            OlapCube.__check_objects(attributes, 'attribute')
            OlapCube.__check_objects(metrics, 'metric')

            definition = {
                'availableObjects': {'attributes': attributes, 'metrics': metrics}
            }
            cube_id = cubes.create(
                connection, name, folder_id, overwrite, description, definition
            ).json()['id']

            deprecation_warning(
                deprecated=(
                    "possibility of providing 'attributes', 'metrics' and 'overwrite' "
                    "parameters during cube creation process"
                ),
                new=(
                    "new 'template', 'filter', 'options', 'advanced_properties' and "
                    "'time_based_settings' parameters"
                ),
                version='11.3.11.101',  # NOSONAR
                module=False,
            )

            logger.info(
                f"Successfully created OLAP Cube named: '{name}' "
                f"with ID: '{cube_id}'."
            )

            return load_cube(connection, cube_id)

        return cls.__create(
            connection=connection,
            name=name,
            folder_id=folder_id,
            description=description,
            template=template,
            filter=filter,
            options=options,
            advanced_properties=advanced_properties,
            time_based_settings=time_based_settings,
            template_cube=template_cube,
            show_expression_as=show_expression_as,
            show_filter_tokens=show_filter_tokens,
        )

    @staticmethod
    def __check_objects(objects_: list[dict], obj_name: str) -> bool:
        """Check objects (attribute or metrics) before creation or update of an
        OLAP Cube."""
        for obj in objects_:
            if not OlapCube.__check_object(obj, obj_name):
                return False
        return True

    @staticmethod
    def __check_object(object_: dict, obj_name: str) -> bool:
        """Check a single object (attribute or metric) represented as dictionary
        before creation or update of OLAP Cube. Each dictionary must have keys:
        `id` and `name`. When it has key `type` then it must be the same as
        value of parameter `obj_name`. When this key is missing its value will
        be set to value of parameter `obj_name`."""

        if 'id' not in object_:
            msg = f"{obj_name.capitalize()} '{object_['name']}' is missing key 'id'."
            raise ValueError(msg)

        if 'type' not in object_:
            object_['type'] = obj_name
        elif object_['type'] != obj_name:
            msg = (
                f"Each element in dictionary with {obj_name}s must be of a type "
                f"'{obj_name}'."
            )
            raise ValueError(msg)
        return True

    def update(self, attributes: list[dict] = [], metrics: list[dict] = []) -> bool:
        """Update an OLAP Cube. When Cube is unpublished, then it is possible to
         add or remove attributes and metrics to/from its definition and
         rearrange existing one. When cube is published it is possible only to
         rearrange attributes and metrics existing in its definition. After this
         operation cube will have only attributes and metrics provided in
         parameters.
         Args:
            attributes(list of dicts, optional): list with dicts of attributes
                dicts to be in the working set of OLAP Cube. Each attribute dict
                should have keys: `id`, `name` and `type`. Attributes can be
                found with method `OlapCube.available_attributes`.
            metrics(list of dicts, optional): list with dicts of metrics to be
                in the working set of OLAP Cube. Each metric dict should have
                keys: `id`, `name` and `type`. Metrics can be found with
                method `OlapCube.available_metrics`.
        Returns:
            True when update was successful. False otherwise.
        Raises:
            `requests.exceptions.HTTPError` when response returned from request
            to I-Server to update new OLAP Cube was not ok.
        """

        deprecation_warning(
            deprecated="'update' method",
            new="'alter' method",
            version='11.3.11.101',  # NOSONAR
            module=False,
        )

        if not OlapCube.__check_attributes_update(
            attributes, self.attributes, self.status
        ):
            return False
        if not OlapCube.__check_metrics_update(metrics, self.metrics, self.status):
            return False

        definition = {
            'availableObjects': {'attributes': attributes, 'metrics': metrics},
        }

        res = cubes.update(self._connection, self._id, definition)
        # refresh definition of cube
        self._get_definition()
        return res.ok

    @staticmethod
    def __check_attributes_update(
        attributes: list[dict], existing_attributes: list[dict], status: int
    ) -> bool:
        """Check dictionaries with attributes before update of an OLAP Cube."""
        return OlapCube.__check_objects_update(
            attributes, existing_attributes, 'attribute', status
        )

    @staticmethod
    def __check_metrics_update(
        metrics: list[dict], existing_metrics: list[dict], status: int
    ) -> bool:
        """Check dictionaries with metrics before update of an OLAP Cube."""
        return OlapCube.__check_objects_update(
            metrics, existing_metrics, 'metric', status
        )

    @staticmethod
    def __check_objects_update(
        objects_: list[dict],
        existing_objects: list[dict],
        object_name: str,
        status: int,
    ) -> bool:
        """Check objects (attributes or metrics) represented as dictionaries
        before update of an OLAP Cube. When status of cube is 0, then it is not
        published and it is possible to freely add or delete objects. Otherwise
        it is possible to only rearrange existing objects. For each object it is
        done also the same check as before creation of an OLAP Cube.
        """
        existing_ids = [o['id'] for o in existing_objects]
        reorganised_objects_count = 0  # to check if all existing objects were provided
        msg = (
            f"It is not possible to add new {object_name}s when editing published cube."
        )
        for object_ in objects_:
            # check if structure of dictionary with an object is correct
            if not OlapCube.__check_object(object_, object_name):
                return False
            # check if status of cube is correct in case of new objects
            if object_['id'] not in existing_ids:
                if status != 0:
                    exception_handler(msg, Warning)
                    return False
            else:
                reorganised_objects_count += 1

        # check if status of cube is correct in case of removing objects
        if reorganised_objects_count != len(existing_ids) and status != 0:
            msg = (
                f"It is not possible delete existing {object_name}s when editing "
                f"published cube."
            )
            exception_handler(msg, Warning)
            return False

        return True

    def publish(self) -> None:
        """Publish an OLAP Cube. Request to publish an OLAP Cube is an
        asynchronous operation, so the result of it can be seen after calling
        method `refresh_status()` inherited from Cube class.
        Returns:
            A dictionary with two keys identifying task IDs.
        """
        response = cubes.publish(self._connection, self._id)
        logger.info(f"Request for publishing cube '{self.name}' was sent.")
        return response.json()

    def export_sql_view(self):
        """Export SQL View of an OLAP Cube.
        Returns:
            SQL View of an OLAP Cube.
        """
        res = cubes.get_sql_view(self._connection, self._id)
        sql_statement = res.json()['sqlStatement']
        return sql_statement

    @classmethod
    @method_version_handler('11.3.0800')
    def __create(
        cls,
        connection: 'Connection',
        name: str,
        folder_id: str,
        template: Template | dict,
        description: str | None,
        filter: Expression | dict | None,
        options: CubeOptions | dict | None,
        advanced_properties: AdvancedProperties | dict | None,
        time_based_settings: TimeBasedSettings | dict | None,
        template_cube: 'OlapCube | str | None',
        show_expression_as: ExpressionFormat | str,
        show_filter_tokens: bool,
    ) -> 'OlapCube | None':
        if not template_cube:
            template = cls.__convert_template_to_dict(template)
        else:
            template_cube = (
                template_cube.id
                if isinstance(template_cube, OlapCube)
                else template_cube
            )

        information = {
            'name': name,
            'description': description,
            'destinationFolderId': folder_id,
        }
        if options:
            options = (
                options.to_dict()
                if isinstance(options, CubeOptions)
                else CubeOptions.from_dict(options).to_dict()
            )
        else:
            options = CubeOptions().to_dict()

        body = {
            'information': information,
            'template': template if not template_cube else None,
            'filter': filter.to_dict() if isinstance(filter, Expression) else filter,
            'options': options,
            'advancedProperties': advanced_properties.to_dict()
            if isinstance(advanced_properties, AdvancedProperties)
            else advanced_properties,
            'timeBased': time_based_settings.to_dict()
            if isinstance(time_based_settings, TimeBasedSettings)
            else time_based_settings,
        }

        data = cube_processors.create(
            connection=connection,
            body=body,
            cube_template_id=template_cube if template_cube else None,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
            show_filter_tokens=show_filter_tokens,
        )
        data.update(
            show_expression_as=show_expression_as, show_filter_tokens=show_filter_tokens
        )

        logger.info(
            f"Successfully created OLAP Cube named: '{name}' "
            f"with ID: '{data['information']['objectId']}'."
        )

        return cls.from_dict(source=data, connection=connection)

    @method_version_handler('11.3.0800')
    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        abbreviation: Optional[str] = None,
        template: Optional[Template | dict] = None,
        filter: Optional[Expression | dict] = None,
        options: Optional[CubeOptions | dict] = None,
        time_based_settings: Optional[TimeBasedSettings | dict] = None,
    ) -> None:
        """Alter OLAP Cube properties by providing new name, description,
        abbreviation, template, filter, options or time_based_settings
        parameters.

        Note:
            All types of expressions can be represented in the form of tokens,
            but some expressions with type predicate are yet not supported to be
            used for creation or modification in tokens form. For example:
            'expression_nodes.ElementListPredicate' or
            'expression_nodes.FilterQualificationPredicate' and some cases other
            involving embedded objects. Expected errors while be thrown in such
            cases.

        Args:
            name (str, optional): New name for the OLAP Cube.
            description (str, optional): New description for the OLAP Cube.
            abbreviation (str, optional): New abbreviation for the OLAP Cube.
            template (Template, dict, str, optional): Template defining
                OLAP Cube structure with references to attributes in
                rows and to metrics in columns.
            filter (Expression, dict, optional): Filtering element for
                OLAP Cube, needs to be in either 'tree' or 'tokens' format.
                If both are provided, only 'tree' is used.
            options (CubeOptions, dict, optional): Options specifying the
                behavior of cube. Includes possibilities for setting languages,
                refresh of data and partitioning by attribute.
            time_based_settings (TimeBasedSettings, dict, optional): Settings of
                timezone and calendar objects specified with references by ID.

        Raises:
            ValueError: When arguments for altering were not provided or given
                template is empty.
            helper.IServerError: When there was an error on IServer side when
                trying to alter an OLAP Cube.

        Returns:
            None
        """

        if template:
            template = self.__convert_template_to_dict(template)

        arguments = filter_params_for_func(self.alter, locals(), exclude=['self'])

        if not arguments:
            msg = (
                "Please provide at least one of the following parameters to alter: "
                "name, description, abbreviation, template, filter, options or "
                "time_based_settings."
            )
            raise ValueError(msg)

        self._alter_properties(**arguments)

        if template:
            self.__set_definition()

    @method_version_handler('11.3.0800')
    def set_partition_attribute(self, attribute: Attribute | str) -> None:
        """Assign new partition attribute to OLAP Cube.

        Args:
            attribute (Attribute, str): Partition attribute that will
                be set, could be provided by ID or with 'Attribute' object.

        Returns:
            None
        """

        attribute_reference = (
            SchemaObjectReference.create_from(attribute)
            if isinstance(attribute, Attribute)
            else SchemaObjectReference(
                sub_type=ObjectSubTypes.ATTRIBUTE, object_id=attribute
            )
        )

        self.alter(
            options=CubeOptions(
                data_partition=DataPartition(partition_attribute=attribute_reference)
            )
        )

        logger.info(
            "Successfully assigned new partition attribute to "
            f"OLAP Cube named: '{self.name}'."
        )

    @method_version_handler('11.3.0800')
    def remove_partition_attribute(self) -> None:
        """Remove assigned to OLAP Cube partition attribute.

        Returns:
            None
        """

        self.alter(
            options=CubeOptions(data_partition=DataPartition(partition_attribute=None))
        )

        logger.info(
            "Successfully removed assigned partition attribute from "
            f"OLAP Cube named: '{self.name}'."
        )

    @method_version_handler('11.3.0800')
    def list_attribute_forms(self) -> list[dict[list[tuple], str]]:
        """Listing forms for every attribute specified in template. If
        default forms for attribute were used, string indicating that
        will be returned instead of forms.

        Returns:
            List with dicts containing attribute name as key and forms
            as values or string indicating that they are default.
        """

        attributes = [
            elem
            for elem in [
                *self.template.rows,
                *self.template.columns,
                *self.template.page_by,
            ]
            if isinstance(elem, AttributeTemplateUnit)
        ]

        return [
            {
                attribute.name: 'Default forms are used.'
                if not attribute.forms
                else [(form.id, form.name) for form in attribute.forms]
            }
            for attribute in attributes
        ]

    @classmethod
    def __convert_template_to_dict(cls, template: Template | dict) -> dict:
        template = template.to_dict() if isinstance(template, Template) else template

        if not (
            template.get('rows') or template.get('columns') or template.get('pageBy')
        ):
            msg = (
                "Please provide not empty template with filled elements in one of "
                "'rows', 'columns' or 'page_by' parameters."
            )
            raise ValueError(msg)

        return template

    def __set_definition(self) -> None:
        definition = self.template.to_dict()
        all_elements = (
            definition.get('rows', [])
            + definition.get('columns', [])
            + definition.get('pageBy', [])
        )
        self._attributes = [
            elem for elem in all_elements if elem['type'] == 'attribute'
        ]
        metrics = [
            elem['elements'] for elem in all_elements if elem['type'] == 'metrics'
        ]
        self._metrics = [] if not metrics else metrics[0]
        self._attr_elements = None
        self.__filter = None
