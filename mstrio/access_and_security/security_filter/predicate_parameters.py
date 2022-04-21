from enum import auto
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

from mstrio.access_and_security.security_filter import ObjectReference
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ParameterType(AutoName):
    CONSTANT = auto()
    OBJECT_REFERENCE = auto()
    EXPRESSION = auto()
    PROMPT = auto()
    ARRAY = auto()
    DYNAMIC_DATE_TIME = auto()


class ParameterBase(Dictable):

    TYPE = None
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self):
        self.parameter_type = self.TYPE


class ConstantType(AutoName):
    INT_32 = "int32"
    INT_64 = "int64"
    DOUBLE = auto()
    DATE = auto()
    TIME = auto()
    STRING = auto()


class ConstantParameter(ParameterBase):

    TYPE = ParameterType.CONSTANT
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, type: Union["ConstantType", str], value: str):
        """Constant parameter for predicate.

        Args:
            type (enum): type of constant. Possible values are defined in enum
                `ConstantType`.
            value (str): value of constant.
        """
        super().__init__()
        self.constant = {"type": get_enum_val(type, ConstantType), "value": value}

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source["type"] = source.get('constant', {}).get('type')
        source["value"] = source.get('constant', {}).get('value')
        return super().from_dict(source, connection)


class ObjectReferenceParameter(ParameterBase):

    TYPE = ParameterType.OBJECT_REFERENCE
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, target: "ObjectReference"):
        super().__init__()
        self.target = target

    _FROM_DICT_MAP = {"target": ObjectReference.from_dict}


class ExpressionParameter(ParameterBase):

    TYPE = ParameterType.OBJECT_REFERENCE
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, expression: dict):
        super().__init__()
        self.expression = expression


class PromptParameter(ParameterBase):

    TYPE = ParameterType.PROMPT
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, prompt: "ObjectReference"):
        super().__init__()
        self.prompt = prompt

    _FROM_DICT_MAP = {"prompt": ObjectReference.from_dict}


class DynamicDateTimeParameter(ParameterBase):

    TYPE = ParameterType.DYNAMIC_DATE_TIME
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, dynamic_date_time: dict):
        super().__init__()
        # TODO think about some object for dynamic_date_structure
        self.dynamic_date_time = dynamic_date_time


class ConstantArrayParameter(ParameterBase):

    TYPE = ParameterType.ARRAY
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, type: Union["ConstantType", str], values: List[str]):
        super().__init__()
        self.constants_type = type if isinstance(type, ConstantType) else ConstantType(type)
        self.constants = values

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None,
                  to_snake_case: bool = True):
        source["type"] = source.get('constantsType' if to_snake_case else 'constants_type')
        source["values"] = source.get('constants')
        return super().from_dict(source, connection)
