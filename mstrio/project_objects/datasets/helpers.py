import logging
from dataclasses import dataclass, field
from enum import auto
from typing import Any, Optional, TypeVar

from mstrio.connection import Connection
from mstrio.modeling import ObjectSubType, SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.exceptions import NotSupportedError
from mstrio.utils.helper import Dictable, camel_to_snake, snake_to_camel
from mstrio.utils.vldb_mixin import ResolvedLocation

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class AttributeJoinType(Dictable):
    """Class representation of single joining operation for attribute.

    Attributes:
        attribute (SchemaObjectReference): Reference to the attribute used
            for joining.
        no_participation_in_preserve_row (bool): Value corresponding to the
            targeted VLDB setting of given attribute.
        resolved_location (ResolvedLocation, optional): Type of location where
            value of related VLDB setting was last time resolved.
        is_inherited (bool, optional): Whether the related VLDB setting value
            is inherited from other objects or not. If False value is set on
            the object. If True, value is inherited from other objects.
        next_no_participation_in_preserve_row (bool, optional): Previously set
            value of attribute targeted VLDB setting.
        next_resolved_location (ResolvedLocation, optional): Previously set
            resolved_location.
    """

    _FROM_DICT_MAP = {
        'attribute': SchemaObjectReference.from_dict,
        'resolved_location': ResolvedLocation,
        'next_resolved_location': ResolvedLocation,
    }

    attribute: SchemaObjectReference
    no_participation_in_preserve_row: bool
    resolved_location: ResolvedLocation = ResolvedLocation.DEFAULT
    is_inherited: bool = True
    next_no_participation_in_preserve_row: Optional[bool] = None
    next_resolved_location: Optional[ResolvedLocation] = None


class JoinType(AutoName):
    """Enumeration constant indicating type of metric joining operation."""

    INNER = auto()
    OUTER = auto()


@dataclass
class MetricJoinType(Dictable):
    """Class representation of single joining operation for metric.

    Attributes:
        metric (SchemaObjectReference): Reference to the metric used for
            joining.
        join_type (JoinType): Value corresponding to the targeted VLDB setting
            of given metric.
        resolved_location (ResolvedLocation, optional): Type of location where
            value of related VLDB setting was last time resolved.
        is_inherited (bool, optional): Whether the related VLDB setting value
            is inherited from other objects or not. If False value is set on
            the object. If True, value is inherited from other objects.
        next_join_type (JoinType, optional): Previously set value of metric
            targeted VLDB setting.
        next_resolved_location (ResolvedLocation, optional): Previously set
            resolved_location.
    """

    _FROM_DICT_MAP = {
        'metric': SchemaObjectReference.from_dict,
        'join_type': JoinType,
        'resolved_location': ResolvedLocation,
        'next_join_type': JoinType,
        'next_resolved_location': ResolvedLocation,
    }

    metric: SchemaObjectReference
    join_type: JoinType
    resolved_location: ResolvedLocation = ResolvedLocation.DEFAULT
    is_inherited: bool = True
    next_join_type: Optional[JoinType] = None
    next_resolved_location: Optional[ResolvedLocation] = None


@dataclass
class AdvancedProperties(Dictable):
    """Class representation of advanced properties containing joining
    information.

    Attributes:
        metric_join_types (list[MetricJoinType], optional): List containing
            joining information for each metric that appears in the template.
        attribute_join_types (list[AttributeJoinType], optional): List
            containing joining information for each attribute that appears in
            the template.
    """

    _KEEP_CAMEL_CASE = [
        'metricJoinTypes',
        'attributeJoinTypes',
        'metric_join_types',
        'attribute_join_types',
    ]

    @staticmethod
    def _parse_metric(source, connection):
        return [
            MetricJoinType.from_dict(value, connection) for value in source.values()
        ]

    @staticmethod
    def _parse_attribute(source, connection):
        return [
            AttributeJoinType.from_dict(value, connection) for value in source.values()
        ]

    _FROM_DICT_MAP = {
        'metric_join_types': _parse_metric,
        'attribute_join_types': _parse_attribute,
    }

    metric_join_types: list[MetricJoinType] = field(default_factory=list)
    attribute_join_types: list[AttributeJoinType] = field(default_factory=list)

    def to_dict(self, camel_case: bool = True) -> dict:
        result = {
            'metric_join_types': {
                value.metric.object_id: value.to_dict(camel_case)
                for value in self.metric_join_types
            }
            if self.metric_join_types
            else None,
            'attribute_join_types': {
                value.attribute.object_id: value.to_dict(camel_case)
                for value in self.attribute_join_types
            }
            if self.attribute_join_types
            else None,
        }
        return (
            snake_to_camel(result, whitelist=self._KEEP_CAMEL_CASE)
            if camel_case
            else result
        )


class TemplateUnitType(AutoName):
    """Enumeration constant indicating type of single template unit."""

    ATTRIBUTE = auto()
    DIMENSION = auto()
    METRICS = auto()
    CUSTOM_GROUP = auto()
    CONSOLIDATION = auto()
    PROMPT = auto()
    RAW_UNIT = auto()


@dataclass
class TemplateUnit(Dictable):
    """Class representation of single template unit."""

    _TYPE = None

    @staticmethod
    def dispatch(
        source, connection: Optional[Connection] = None
    ) -> type['TemplateUnit']:
        data = source.copy()
        unit_type = TemplateUnitType(data.pop('type'))

        if unit_type == TemplateUnitType.ATTRIBUTE:
            cls = AttributeTemplateUnit
        elif unit_type == TemplateUnitType.METRICS:
            cls = MetricTemplateUnit
        else:
            raise NotSupportedError(
                f"Unit type: '{unit_type}' is not supported for Template class."
            )

        return cls.from_dict(data, connection)

    def to_dict(self, camel_case: bool = True) -> dict:
        return {
            **super().to_dict(camel_case),
            'type': self._TYPE.value,
        }


@dataclass
class AttributeFormReference(Dictable):
    """Class representation of single attribute form.

    Attributes:
        id (str): ID of the referenced attribute.
        name (str, optional): Name of attribute.
    """

    id: str
    name: Optional[str] = None


@dataclass
class AttributeTemplateUnit(TemplateUnit):
    """Class representation of single attribute template unit.

    Attributes:
        id (str): ID of the referenced attribute.
        name (str, optional): Name of attribute.
        alias (str, optional): Alias for attribute.
        forms (list[AttributeFormReference], optional): Referenced
            attribute forms.
    """

    _TYPE = TemplateUnitType.ATTRIBUTE
    _FROM_DICT_MAP = {
        'forms': [AttributeFormReference.from_dict],
    }

    id: str
    name: Optional[str] = None
    alias: Optional[str] = None
    forms: Optional[list[AttributeFormReference]] = None


@dataclass
class MetricElement(Dictable):
    """Class representation of single metric element.

    Attributes:
        id (str): ID of the referenced metric.
        name (str, optional): Name of metric.
        alias (str, optional): Alias for metric.
    """

    _TYPE = ObjectSubType.METRIC

    id: str
    name: Optional[str] = None
    alias: Optional[str] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        return {
            **super().to_dict(camel_case),
            'subType': self._TYPE.value,
        }


@dataclass
class MetricTemplateUnit(TemplateUnit):
    """Class representation of single metric element.

    Attributes:
        elements (list[MetricElement]): List containing
            metric elements used in template.
    """

    _TYPE = TemplateUnitType.METRICS
    _FROM_DICT_MAP = {
        'elements': [MetricElement.from_dict],
    }

    elements: list[MetricElement]


@dataclass
class Template(Dictable):
    """Class representation of single template.

    Attributes:
        rows (list[TemplateUnit], optional): List containing
            attribute and metric elements used in template rows.
        columns (list[TemplateUnit], optional): List containing
            attribute and metric elements used in template columns.
        page_by (list[TemplateUnit], optional): List containing
            attribute elements used in template for paging.
    """

    _FROM_DICT_MAP = {
        'rows': [TemplateUnit.dispatch],
        'columns': [TemplateUnit.dispatch],
        'page_by': [TemplateUnit.dispatch],
    }

    rows: list[TemplateUnit] = field(default_factory=list)
    columns: list[TemplateUnit] = field(default_factory=list)
    page_by: list[TemplateUnit] = field(default_factory=list)


class DataLanguageType(AutoName):
    """Enumeration constant indicating type of data language
    configuration type."""

    PROJECT_DEFAULT = auto()
    ALL_PROJECT_DATA_LANGUAGE = auto()
    SPECIFIC_LANGUAGES = auto()


class DataRefreshType(AutoName):
    """Enumeration constant indicating type of data refresh
    operation."""

    REPLACE = auto()
    ADD = auto()
    DYNAMIC_REFRESH = auto()
    UPSERT = auto()


@dataclass
class DataLanguages(Dictable):
    """Class representation of data language configuration.

    Attributes:
        data_language_type (DataLanguageType): Type of used
            data language configuration.
        selected_languages (list[str], optional): List with
            selected languages passed as abbreviations.
    """

    _FROM_DICT_MAP = {
        'data_language_type': DataLanguageType,
    }

    data_language_type: DataLanguageType = DataLanguageType.PROJECT_DEFAULT
    selected_languages: Optional[list[str]] = field(default_factory=list)


@dataclass
class DataPartition(Dictable):
    """Class representation of data partition.

    Attributes:
        partition_attribute (SchemaObjectReference, optional): Reference
            to attribute used in partition.
        number_of_partitions (int, optional): Number of data partitions.
        fetch_data_slices_in_parallel (bool, optional): Bool indicating
            whether to fetch data in parallel, default False.
    """

    partition_attribute: Optional[SchemaObjectReference] = None
    number_of_partitions: Optional[int] = None
    fetch_data_slices_in_parallel: bool = False

    @classmethod
    def from_dict(
        cls: T,
        source: dict[str, Any],
        connection: Optional['Connection'] = None,
        to_snake_case: bool = True,
    ) -> T:
        """Initialize DataPartition object from dictionary."""
        source = camel_to_snake(source)
        obj = super().from_dict(
            source=source, connection=connection, to_snake_case=to_snake_case
        )
        obj.partition_attribute = (
            SchemaObjectReference.from_dict(partition_attribute)
            if (partition_attribute := source.get('partition_attribute'))
            else None
        )
        return obj

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict()
        if self.partition_attribute:
            result['partitionAttribute']['subType'] = str.lower(
                self.partition_attribute.sub_type.name
            )
        else:
            result['partitionAttribute'] = {}
        return snake_to_camel(result) if camel_case else result


@dataclass
class CubeOptions(Dictable):
    """Class representation of cube options for cube.

    Attributes:
        data_languages (DataLanguages, optional): Information related
            to data languages configuration.
        data_refresh (DataRefreshType, optional): Type of data refresh
            operation, default 'DataRefreshType.REPLACE'.
        data_partition (DataPartition, optional): Object which
            represents information about data partition.
    """

    _FROM_DICT_MAP = {
        'data_languages': DataLanguages.from_dict,
        'data_refresh': DataRefreshType,
        'data_partition': DataPartition.from_dict,
    }

    data_languages: DataLanguages = field(default_factory=DataLanguages)
    data_refresh: DataRefreshType = DataRefreshType.REPLACE
    data_partition: DataPartition = field(default_factory=DataPartition)


@dataclass
class TimeBasedSettings(Dictable):
    """Class representation of time based settings.

    Attributes:
        timezone (SchemaObjectReference, optional): Reference to timezone
            object or None.
        calendar (SchemaObjectReference, optional): Reference to calendar
            object or None.
        enable_timezone_and_calendar_reporting (bool, optional): Bool
            indicating whether to enable timezone and calendar reporting,
            default True.
    """

    timezone: Optional[SchemaObjectReference] = None
    calendar: Optional[SchemaObjectReference] = None
    enable_timezone_and_calendar_reporting: bool = True

    @classmethod
    def from_dict(
        cls: T,
        source: dict[str, Any],
        connection: Optional['Connection'] = None,
        to_snake_case: bool = True,
    ) -> T:
        """Initialize TimeBasedSettings object from dictionary."""
        source = camel_to_snake(source)
        obj = super().from_dict(
            source=source, connection=connection, to_snake_case=to_snake_case
        )
        obj.timezone = (
            SchemaObjectReference.from_dict(timezone)
            if (timezone := source.get('timezone'))
            else None
        )
        obj.calendar = (
            SchemaObjectReference.from_dict(calendar)
            if (calendar := source.get('calendar'))
            else None
        )
        return obj
