from dataclasses import dataclass
from enum import auto
import logging
from typing import Optional

from mstrio.modeling import SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, snake_to_camel
from mstrio.utils.wip import module_wip, WipLevels

logger = logging.getLogger(__name__)

module_wip(globals(), level=WipLevels.WARNING)


class PropertyLocation(AutoName):
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
class AttributeJoinType(Dictable):
    _FROM_DICT_MAP = {
        'attribute': SchemaObjectReference.from_dict,
        'resolved_location': PropertyLocation,
    }
    attribute: SchemaObjectReference
    no_participation_in_preserve_row: bool
    resolved_location: PropertyLocation


class JoinType(AutoName):
    INNER = auto()
    OUTER = auto()


@dataclass
class MetricJoinType(Dictable):
    _FROM_DICT_MAP = {
        'metric': SchemaObjectReference.from_dict,
        'join_type': JoinType,
        'resolved_location': PropertyLocation,
    }
    metric: SchemaObjectReference
    join_type: JoinType
    resolved_location: PropertyLocation


class VLDBPropertyType(AutoName):
    """Enumeration constant indicating type of value of a VLDB property value"""

    INT32 = auto()
    INT64 = auto()
    DATE = auto()
    TIME = auto()
    BOOLEAN = auto()
    STRING = auto()
    DOUBLE = auto()


@dataclass
class VLDBProperty(Dictable):
    _FROM_DICT_MAP = {
        'type': VLDBPropertyType,
        'resolved_location': PropertyLocation,
    }
    name: str
    value: str
    type: VLDBPropertyType
    resolved_location: PropertyLocation


@dataclass
class AdvancedProperties(Dictable):
    _KEEP_CAMEL_CASE = [
        'vldbProperties',
        'metricJoinTypes',
        'attributeJoinTypes',
        'vldb_properties',
        'metric_join_types',
        'attribute_join_types',
    ]

    @staticmethod
    def _parse_metric(source, connection):
        return {
            key: MetricJoinType.from_dict(value, connection)
            for key, value in source.items()
        }

    @staticmethod
    def _parse_attribute(source, connection):
        return {
            key: AttributeJoinType.from_dict(value, connection)
            for key, value in source.items()
        }

    @staticmethod
    def _parse_vldb(source, connection):
        return {
            key: VLDBProperty.from_dict(value, connection)
            for key, value in source.items()
        }

    _FROM_DICT_MAP = {
        'vldb_properties': _parse_vldb,
        'metric_join_types': _parse_metric,
        'attribute_join_types': _parse_attribute,
    }
    vldb_properties: Optional[dict] = None
    metric_join_types: Optional[dict] = None
    attribute_join_types: Optional[dict] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        result = {
            'vldb_properties': {
                key: value.to_dict(camel_case)
                for key, value in self.vldb_properties.items()
            } if self.vldb_properties else None,
            'metric_join_types': {
                key: value.to_dict(camel_case)
                for key, value in self.metric_join_types.items()
            } if self.metric_join_types else None,
            'attribute_join_types': {
                key: value.to_dict(camel_case)
                for key, value in self.attribute_join_types.items()
            } if self.attribute_join_types else None,
        }

        return (
            snake_to_camel(result, whitelist=self._KEEP_CAMEL_CASE)
            if camel_case
            else result
        )
