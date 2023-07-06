import logging
from dataclasses import dataclass
from enum import auto
from typing import TYPE_CHECKING, Optional

from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mstrio.connection import Connection


@dataclass
class DimensionalityUnit(Dictable):
    """
    Object that specifies the dimensionality unit.

    Attributes:
        dimtyUnitType: Type of unit in dimensionality
        target: target of dimensionality
        aggregation: type of aggregation in dimensionality
        filtering: Type of filtering applied in this dimensionality
        relativePosition: number showing relative position of dimensionality
        in metric reports
        target: Object reference to attribute or report, on which the
        dimensionality will be grouped at
        axisCollection: dict of numbers showing, at which axis
        metric will be shown
    """

    class DimensionalityUnitType(AutoName):
        DEFAULT = auto()
        ATTRIBUTE = auto()
        DIMENSION = auto()
        REPORT_LEVEL = auto()
        REPORT_BASE_LEVEL = auto()
        ROLE = auto()

    class Aggregation(AutoName):
        NORMAL = auto()
        FIRST_IN_FACT = auto()
        LAST_IN_FACT = auto()
        FIRST_IN_RELATIONSHIP = auto()
        LAST_IN_RELATIONSHIP = auto()

    class Filtering(AutoName):
        APPLY = auto()
        ABSOLUTE = auto()
        IGNORE = auto()
        NONE = auto()

    _FROM_DICT_MAP = {
        'dimensionality_unit_type': DimensionalityUnitType,
        'filtering': Filtering,
        'aggregation': Aggregation,
        'target': SchemaObjectReference.from_dict,
    }

    dimensionality_unit_type: DimensionalityUnitType
    aggregation: Aggregation | None = None
    filtering: Filtering | None = None
    group_by: bool | None = None
    relative_position: int | None = None
    target: SchemaObjectReference | None = None
    axis_collection: dict | None = None

    @classmethod
    def from_dict(cls, source: dict):
        new_source = source.copy()
        new_source['dimensionality_unit_type'] = source.get('dimtyUnitType', [])
        return super().from_dict(new_source)

    def to_dict(cls, camel_case: bool = True) -> dict:
        obj_dict = super().to_dict(camel_case=camel_case)
        if obj_dict.get('dimensionalityUnitType'):
            obj_dict['dimtyUnitType'] = obj_dict.pop('dimensionalityUnitType')
        return obj_dict


@dataclass
class Dimensionality(Dictable):
    """
    Object that specifies the dimensionality.

    This class can only be used for simple metrics.
    For creation and altering of compound metrics, dimensionality needs to be
    defined through the use of the Expression class.

    Attributes:
        dimtyUnits: The list of dimty unit
        excludeAttribute: boolean whether to exclude attribute
            absent in report or level(dimensionality)
        allowAddingUnit: boolean whether to allow other users
            to add extra units
        prompt: reference to a prompt
    """

    _FROM_DICT_MAP = {
        'dimensionality_units': [DimensionalityUnit],
        'prompt': SchemaObjectReference,
    }

    dimensionality_units: list[DimensionalityUnit] | None = None
    exclude_attribute: bool | None = None
    allow_adding_unit: bool | None = None
    prompt: SchemaObjectReference | None = None

    @classmethod
    def from_dict(
        cls,
        source: dict,
        connection: Optional['Connection'] = None,
        to_snake_case: bool = True,
    ):
        data = source.copy()
        data['dimensionality_units'] = data.get('dimty_units', [])
        return super().from_dict(data, connection, to_snake_case)

    def to_dict(cls, camel_case: bool = True) -> dict:
        obj_dict = super().to_dict(camel_case=camel_case)
        if obj_dict.get('dimensionalityUnits'):
            obj_dict['dimtyUnits'] = obj_dict.pop('dimensionalityUnits')
        return obj_dict
