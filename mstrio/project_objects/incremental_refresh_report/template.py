import logging
from dataclasses import dataclass, field
from enum import auto
from typing import Optional, Type

from mstrio.connection import Connection
from mstrio.modeling import ObjectSubType
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.exceptions import NotSupportedError
from mstrio.utils.helper import Dictable
from mstrio.utils.wip import module_wip, WipLevels

logger = logging.getLogger(__name__)

module_wip(globals(), level=WipLevels.WARNING)


class TemplateUnitType(AutoName):
    ATTRIBUTE = auto()
    DIMENSION = auto()
    METRICS = auto()
    CUSTOM_GROUP = auto()
    CONSOLIDATION = auto()
    PROMPT = auto()
    RAW_UNIT = auto()


@dataclass
class TemplateUnit(Dictable):

    _TYPE = None

    @staticmethod
    def dispatch(
        source, connection: Optional[Connection] = None
    ) -> Type['TemplateUnit']:
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
    id: str
    name: str


@dataclass
class AttributeTemplateUnit(TemplateUnit):
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
    _TYPE = TemplateUnitType.METRICS
    _FROM_DICT_MAP = {
        'elements': [MetricElement.from_dict],
    }
    elements: list[MetricElement]


@dataclass
class Template(Dictable):
    _FROM_DICT_MAP = {
        'rows': [TemplateUnit.dispatch],
        'columns': [TemplateUnit.dispatch],
        'page_by': [TemplateUnit.dispatch],
    }
    rows: list[TemplateUnit] = field(default_factory=list)
    columns: list[TemplateUnit] = field(default_factory=list)
    page_by: list[TemplateUnit] = field(default_factory=list)
