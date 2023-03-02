from dataclasses import dataclass
from enum import auto, Enum
import logging
from typing import Optional, TYPE_CHECKING

from mstrio import config
from mstrio.api import metrics, objects
from mstrio.connection import Connection
from mstrio.modeling.expression import Expression, ExpressionFormat
from mstrio.modeling.metric import Dimensionality, FormatProperty, MetricFormat
from mstrio.modeling.schema.helpers import DataType, ObjectSubType, SchemaObjectReference
from mstrio.object_management import Folder, search_operations, SearchPattern
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    delete_none_values, Dictable, filter_params_for_func, get_valid_project_id
)
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.metric import Metric

logger = logging.getLogger(__name__)


@method_version_handler(version='11.3.0500')
def list_metrics(
    connection: Connection,
    name: Optional[str] = None,
    metric_type: ObjectTypes = ObjectTypes.METRIC,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TOKENS,
    **filters
) -> list["Metric"] | list[dict]:
    """Get list of Metric objects or dicts with them.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (str, optional): characters that the metric name must
            begin with
        metric_type (ObjectTypes): one of metric subtypes: Metric or AggMetric
        project_id (str, optional): ID of the project to list the metrics from
        project_name (str, optional): Project name
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Metric objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        show_expression_as (ExpressionFormat, str): specify how expressions
            should be presented
            Available values:
                - `ExpressionFormat.TREE` or `tree`
                - `ExpressionFormat.TOKENS or `tokens` (default)
        **filters: Available filter parameters:
            id (str): Metric's ID
            name (str): Metric's name
            date_created (str): format: 2001-01-02T20:48:05.000+0000
            date_modified (str): format: 2001-01-02T20:48:05.000+0000
            version (str): Metric's version
            owner dict: e.g. {'id': <user's id>, 'name': <user's name>},
                with one or both of the keys: id, name
            acg (str | int): access control group
            root (str): Folder ID of the root folder where the search
                will be performed.

    Returns:
        list with Metric objects or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects_ = search_operations.full_search(
        connection,
        object_types=metric_type,
        project=project_id,
        name=name,
        pattern=search_pattern,
        limit=limit,
        **filters
    )
    if to_dictionary:
        return objects_
    else:
        show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat
        ) else ExpressionFormat(show_expression_as)
        return [
            Metric.from_dict({
                **obj_, 'show_expression_as': show_expression_as
            }, connection) for obj_ in objects_
        ]


class DefaultSubtotals(Enum):
    AGGREGATION = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='F225147A4CA0BB97368A5689D9675E73'
    )
    AVERAGE = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='B328C60462634223B2387D4ADABEEB53'
    )
    COUNT = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='078C50834B484EE29948FA9DD5300ADF'
    )
    GEOMETRIC_MEAN = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='E1853D5A36C74F59A9F8DEFB3F9527A1'
    )
    MAXIMUM = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='B1F4AA7DE683441BA559AA6453C5113E'
    )
    MEDIAN = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='83A663067F7E43B2ABF67FD38ECDC7FE'
    )
    MINIMUM = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='00B7BFFF967F42C4B71A4B53D90FB095'
    )
    MODE = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='36226A4048A546139BE0AF5F24737BA8'
    )
    PRODUCT = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='54E7BFD129514717A92BC44CF1FE5A32'
    )
    RESERVED = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='F341109B11D5D528C00084916B98494F'
    )
    STANDARD_DEVIATION = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='7FBA414995194BBAB2CF1BB599209824'
    )
    SUM_OF_WYA = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='F7AE84A511D78008B00092BE4E571AD0'
    )
    TOTAL = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='96C487AF4D12472A910C1ACACFB56EFB'
    )
    VARIANCE = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='1769DBFCCF2D4392938E40418C6E065E'
    )
    WEIGHTED_YEARLY_AVERAGE = SchemaObjectReference(
        sub_type=ObjectSubType.SYSTEM_SUBTOTAL, object_id='F7AE852A11D78008B00092BE4E571AD0'
    )


@dataclass
class Threshold(Dictable):
    """Object that specifies a threshold

    Attributes:
        format (list[FormatProperty]): list of format properties for the
            threshold
        condition (Expression, optional): expression that specifies the
            condition on which the threshold is going to be applied
        name (string, optional): name of the threshold
        replace_text (string, optional): text that will replace the metric's
            value if the threshold is met
        semantics (Semantics, optional): value of an enumerator that specifies
            the type of replacement in the replace_text string
        scope (Scope, optional): value of an enumerator that specifies what the
            threshold applies to, the metric values, the subtotal value or both
        enable (bool): whether the threshold is enabled or not, True by default
    """

    class Scope(AutoName):
        METRIC_ONLY = auto()
        SUBTOTAL_ONLY = auto()
        METRIC_AND_SUBTOTAL = auto()

    class Semantics(AutoName):
        NUMBER = auto()
        TEXT = auto()
        PICTURE = auto()
        SYMBOL = auto()

    _FROM_DICT_MAP = {
        'format': [FormatProperty],
        'condition': Expression.from_dict,
        'semantics': Semantics,
        'scope': Scope,
    }

    format: list[FormatProperty]
    condition: Optional[Expression] = None
    name: Optional[str] = None
    replace_text: Optional[str] = None
    semantics: Optional[Semantics] = None
    scope: Optional[Scope] = None
    enable: bool = True


class Metric(Entity, CopyMixin, MoveMixin, DeleteMixin):  # noqa: F811
    """Python representation of MicroStrategy Metric object.

    Attributes:
        id: metric's ID
        name: metric's name
        sub_type: string literal used to identify the type of a metadata object
        description: metric's description
        type: object type, ObjectTypes enum
        subtype: object subtype, ObjectSubTypes enum
        ext_type: object extended type, ExtendedType enum
        ancestors: list of ancestor folders
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        is_embedded: If true indicates that the target object of this
            reference is embedded within this object. Alternatively if
            this object is itself embedded, then it means that the target
            object is embedded in the same container as this object.
        owner: User object that is the owner
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
        version: the version number this object is currently carrying
        expression: the Expression representing the metric's formula
        dimensionality: the object that specifies the dimensionality
        conditionality: the object that specifies the conditionality
        metric_subtotals: a list of the enabled subtotals for the metric
        aggregate_from_base: bool used to specify whether the metric aggregates
            from base
        formula_join_type: join type of the metric's formula, FormulaJoinType
            enumerator
        smart_total: whether the metric is decomposable or not, SmartTotal
            enumerator
        data_type: DataType object for metric values
        format: MetricFormat object that stores the formatting of the metric
        subtotal_from_base: bool used to specify whether the metric is
            a subtotal from base type
        column_name_alias: name for the column representing the metric in SQL
        metric_format_type: specifies whether the metric has HTML content,
            MetricFormatType enumerator
        thresholds: list of Threshold for the metric
        """

    @dataclass
    class Conditionality(Dictable):
        """Object that specifies the conditionality

        This class can only be used for simple metrics.
        For creation and altering of compound metrics, conditionality needs to
        be defined through the use of the Expression class.

        Attributes:
            filter (SchemaObjectReference, optional): reference to the filter
                to be used for the connditionality
            embed_method (EmbedMethod, optional): value of the enumerator that
                specifies the type of filter interaction between the metric and
                report filters
            prompt (SchemaObjectReference, optional): reference to the prompt
                to be used for the conditionality, only prompts of the type
                Prompt Object may be used
            remove_elements (bool): whether to remove related filter elements
        """

        class EmbedMethod(AutoName):
            BOTH_FILTERS_TOGETHER = auto()
            REPORT_INTO_METRIC_FILTER = auto()
            METRIC_INTO_REPORT_FILTER = auto()

        _FROM_DICT_MAP = {
            'filter': SchemaObjectReference.from_dict,
            'embedMethod': EmbedMethod,
            'prompt': SchemaObjectReference.from_dict,
        }

        filter: Optional[SchemaObjectReference] = None
        embed_method: Optional[EmbedMethod] = None
        prompt: Optional[SchemaObjectReference] = None
        remove_elements: bool = False

    @dataclass
    class MetricSubtotal(Dictable):
        """Object that specifies the subtotal. User can use predefined subtotals
            using `DefaultSubtotals` enum, or specify custom made subtotals
            using SchemaObjectReference.

        Attributes:
            definition(SchemaObjectReference or DefaultSubtotals): Reference to
                the definition object
            implementation(SchemaObjectReference or DefaultSubtotals):
                Reference to the implementation object. Only used when the
                definition Subtotal is 'Total' to specify what the default
                subtotal type for the Total should be
        """

        _FROM_DICT_MAP = {
            'definition': SchemaObjectReference.from_dict,
            'implementation': SchemaObjectReference.from_dict,
        }

        def __init__(
            self,
            definition: SchemaObjectReference | DefaultSubtotals | None = None,
            implementation: SchemaObjectReference | DefaultSubtotals | None = None,
        ) -> None:
            self.definition = definition.value if isinstance(
                definition, DefaultSubtotals
            ) else definition
            self.implementation = implementation.value if isinstance(
                implementation, DefaultSubtotals
            ) else implementation

    class MetricFormatType(AutoName):
        RESERVED = auto()
        HTML_TAG = auto()
        LAST_ONE = auto()

    class SmartTotal(AutoName):
        DECOMPOSABLE_FALSE = auto()
        DECOMPOSABLE_TRUE = auto()

    class FormulaJoinType(AutoName):
        DEFAULT = auto()
        INNER = auto()
        OUTER = auto()

    _OBJECT_TYPE = ObjectTypes.METRIC
    _API_GETTERS = {
        (
            'id',
            'sub_type',
            'name',
            'is_embedded',
            'description',
            'destination_folder_id',
            'expression',
            'dimty',
            'conditionality',
            'metric_subtotals',
            'aggregate_from_base',
            'formula_join_type',
            'smart_total',
            'data_type',
            'format',
            'subtotal_from_base',
            'column_name_alias',
            'metric_format_type',
            'thresholds'
        ): metrics.get_metric,
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
            'target_info'
        ): objects.get_object_info
    }
    _API_PATCH = {
        (
            'id',
            'sub_type',
            'name',
            'is_embedded',
            'description',
            'destination_folder_id',
            'expression',
            'dimty',
            'conditionality',
            'metric_subtotals',
            'aggregate_from_base',
            'formula_join_type',
            'smart_total',
            'data_type',
            'format',
            'subtotal_from_base',
            'column_name_alias',
            'metric_format_type',
            'thresholds'
        ): (metrics.update_metric, 'partial_put'),  # noqa: E131
        ('folder_id'): (objects.update_object, 'partial_put')
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'sub_type': ObjectSubType,
        'expression': Expression.from_dict,
        'dimensionality': Dimensionality.from_dict,
        'conditionality': Conditionality.from_dict,
        'metric_subtotals': (
            lambda source,
            connection:
            [Metric.MetricSubtotal.from_dict(content, connection) for content in source]
        ),
        'formula_join_type': FormulaJoinType,
        'data_type': DataType.from_dict,
        'smart_total': SmartTotal,
        'format': MetricFormat.from_dict,
        'metric_format_type': MetricFormatType,
        'thresholds': (
            lambda source,
            connection: [Threshold.from_dict(content, connection) for content in source]
        ),
    }
    _REST_ATTR_MAP = {
        'dimty': 'dimensionality',
    }

    @classmethod
    @method_version_handler('11.3.0500')
    def from_dict(cls, source: dict, connection: Optional['Connection'] = None):
        new_source = source.copy()
        new_source['dimensionality'] = source.get('dimty', None)
        return super().from_dict(new_source, connection)

    @method_version_handler('11.3.0500')
    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TOKENS
    ) -> None:
        """Initializes a new instance of Metric class

        Args:
            connection (Connection): MicroStrategy connection object returned
                by `connection.Connection()`
            id (str, optional): Metric's ID. Defaults to None.
            name (str, optional): Metric's name. Defaults to None.
            show_expression_as (ExpressionFormat or str, optional):
                specify how expressions should be presented.
                Defaults to ExpressionFormat.TOKENS.

                Available values:
                - `ExpressionFormat.TREE` or `tree`
                - `ExpressionFormat.TOKENS or `tokens` (default)
        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Raises:
            ValueError: if both `id` and `name` are not provided
                or if Metric with the given `name` doesn't exist.
        """
        if id is None:
            metric = super()._find_object_with_name(
                connection=connection, name=name, listing_function=list_metrics
            )
            id = metric['id']
        super().__init__(
            connection=connection, object_id=id, name=name, show_expression_as=show_expression_as
        )

    @method_version_handler('11.3.0500')
    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._id = kwargs.get('id')
        self._sub_type = ObjectSubType(kwargs.get('sub_type')) if kwargs.get('sub_type') else None
        self.name = kwargs.get('name')
        self._is_embedded = kwargs.get('is_embedded')
        self.description = kwargs.get('description')
        self.destination_folder_id = kwargs.get('destination_folder_id')

        self.expression = Expression.from_dict(exp) if (exp := kwargs.get('expression')) else None
        self.dimensionality = Dimensionality.from_dict(dimty) if (
            dimty := kwargs.get('dimensionality')
        ) else None
        self.conditionality = Metric.Conditionality.from_dict(cond) if (
            cond := kwargs.get('conditionality')
        ) else None
        self.metric_subtotals = [
            Metric.MetricSubtotal.from_dict(subtotal) for subtotal in subtotals
        ] if (subtotals := kwargs.get('metric_subtotals')) else None
        self.aggregate_from_base = kwargs.get('aggregate_from_base')
        self.formula_join_type = Metric.FormulaJoinType(join_type) if (
            join_type := kwargs.get('formula_join_type')
        ) else None
        self.smart_total = Metric.SmartTotal(tot) if (tot := kwargs.get('smart_total')) else None
        self.data_type = DataType.from_dict(dtype) if (dtype := kwargs.get('data_type')) else None
        self.format = MetricFormat.from_dict(form) if (form := kwargs.get('format')) else None
        self.subtotal_from_base = kwargs.get('subtotal_from_base')
        self.column_name_alias = kwargs.get('column_name_alias')
        self.metric_format_type = Metric.MetricFormatType(fromat_type) if (
            fromat_type := kwargs.get('metric_format_type')
        ) else None
        self.thresholds = [Threshold.from_dict(threshold) for threshold in thresholds
                           ] if (thresholds := kwargs.get('thresholds')) else None  # noqa: E124

        show_expression_as = kwargs.get('show_expression_as', 'tree')
        self.show_expression_as = show_expression_as if isinstance(
            show_expression_as, ExpressionFormat
        ) else ExpressionFormat(show_expression_as)

    @classmethod
    @method_version_handler('11.3.0500')
    def create(
        cls,
        connection: 'Connection',
        name: str,
        sub_type: ObjectSubType | str,
        destination_folder: Folder | str,
        expression: Expression,
        description: str | None = None,
        is_embedded: bool = False,
        dimensionality: Optional[Dimensionality] = None,
        conditionality: Optional[Conditionality] = None,
        metric_subtotals: Optional[list[MetricSubtotal]] = None,
        aggregate_from_base: bool = False,
        formula_join_type: Optional[FormulaJoinType] = FormulaJoinType.DEFAULT,
        smart_total: Optional[SmartTotal] = None,
        data_type: Optional[DataType] = None,
        format: Optional[MetricFormat] = None,
        subtotal_from_base: bool = False,
        column_name_alias: Optional[str] = None,
        metric_format_type: Optional[MetricFormatType] = None,
        thresholds: Optional[list[Threshold]] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TOKENS,
    ) -> "Metric":
        """Create a new metric with specified properties.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: metric's name
            sub_type: metric's sub_type
            destination_folder_id: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id
            description: metric's description
            is_embedded: If true indicates that the target object of this
                reference is embedded within this object. Alternatively if
                this object is itself embedded, then it means that the target
                object is embedded in the same container as this object.
            expression: the Expression representing the metric's formula
            dimensionality: the object that specifies the dimensionality
            conditionality: the object that specifies the conditionality
            metric_subtotals: a list of the enabled subtotals for the metric
            aggregate_from_base: bool used to specify whether the metric
                aggregates from base
            formula_join_type: join type of the metric's formula,
                FormulaJoinType enumerator
            smart_total: whether the metric is decomposable or not, SmartTotal
                enumerator
            data_type: DataType object for metric values
            format: MetricFormat object that stores the formatting of the metric
            subtotal_from_base: bool used to specify whether the metric is
                a subtotal from base type
            column_name_alias: name of the column representing the metric in SQL
            metric_format_type: specifies whether the metric has HTML content,
                MetricFormatType enumerator
            thresholds: list of Threshold for the metric
            show_expression_as (ExpressionFormat, str): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree`
                - `ExpressionFormat.TOKENS or `tokens` (default)

        Returns:
            Metric class object.
        """
        body = {
            'information': {
                'name': name,
                'subType': get_enum_val(sub_type, ObjectSubType),
                'isEmbedded': is_embedded,
                'description': description,
                'destinationFolderId': destination_folder.id
                if isinstance(destination_folder, Folder) else destination_folder,
            },
            'expression': expression.to_dict() if expression else None,
            'dimty': dimensionality.to_dict() if dimensionality else None,
            'conditionality': conditionality.to_dict() if conditionality else None,
            'metricSubtotals': [sub.to_dict() for sub in metric_subtotals]
            if metric_subtotals else None,  # noqa: E131
            'aggregateFromBase': aggregate_from_base,
            'formulaJoinType': formula_join_type.value if formula_join_type else None,
            'smartTotal': smart_total.value if smart_total else None,
            'dataType': data_type.to_dict() if data_type else None,
            'format': format.to_dict() if format else None,
            'subtotalFromBase': subtotal_from_base,
            'columnNameAlias': column_name_alias,
            'metricFormatType': metric_format_type.value if metric_format_type else None,
            'thresholds': [x.to_dict() for x in thresholds] if thresholds else None,
        }
        body = delete_none_values(body, recursion=True)
        response = metrics.create_metric(
            connection,
            body=body,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat)
        ).json()

        if config.verbose:
            logger.info(f"Successfully created metric named: '{name}' with ID: '{response['id']}'")

        return cls.from_dict(
            source={
                **response, 'show_expression_as': show_expression_as
            }, connection=connection
        )

    @method_version_handler('11.3.0500')
    def alter(
        self,
        name: str = None,
        destination_folder_id: str = None,
        expression: Expression = None,
        description: Optional[str] = None,
        dimensionality: Optional[Dimensionality] = None,
        conditionality: Optional[Conditionality] = None,
        metric_subtotals: Optional[list[MetricSubtotal]] = None,
        aggregate_from_base: bool = False,
        formula_join_type: Optional[FormulaJoinType] = FormulaJoinType.DEFAULT,
        smart_total: Optional[SmartTotal] = None,
        data_type: Optional[DataType] = None,
        format: Optional[MetricFormat] = None,
        subtotal_from_base: bool = False,
        column_name_alias: Optional[str] = None,
        metric_format_type: Optional[MetricFormatType] = None,
        thresholds: Optional[list[Threshold]] = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TOKENS,
    ):
        """Alter a metric's specified properties

        Args:
            name: metric's name
            destination_folder_id: A globally unique identifier used to
                distinguish between metadata objects within the same project.
                It is possible for two metadata objects in different projects
                to have the same Object Id.
            expression: the Expression representing the metric's formula
            description: metric's description
            dimensionality: the object that specifies the dimensionality
            conditionality: the object that specifies the conditionality
            metric_subtotals: a list of the enabled subtotals for the metric
            aggregate_from_base: bool used to specify whether the metric
                aggregates from base
            formula_join_type: join type of the metric's formula,
                FormulaJoinType enumerator
            smart_total: whether the metric is decomposable or not, SmartTotal
                enumerator
            data_type: DataType object for metric values
            format: MetricFormat object that stores the formatting of the metric
            subtotal_from_base: bool used to specify whether the metric is
                a subtotal from base type
            column_name_alias: name of the column representing the metric in SQL
            metric_format_type: specifies whether the metric has HTML content,
                MetricFormatType enumerator
            thresholds: list of Threshold for the metric
            show_expression_as (ExpressionFormat, str): specify how expressions
                should be presented
                Available values:
                - `ExpressionFormat.TREE` or `tree`
                - `ExpressionFormat.TOKENS or `tokens` (default)
        """

        name = name or self.name
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @method_version_handler('11.3.0500')
    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        result.pop('_showExpressionAs', None)
        if result.get('dimensionality'):
            result['dimty'] = result.pop('dimensionality')
        return result

    @property
    def sub_type(self):
        return self._sub_type

    @property
    def is_embedded(self):
        return self._is_embedded
