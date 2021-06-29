from enum import Enum
from mstrio.utils.helper import Dictable, Any, camel_to_snake
from typing import List, Optional, Dict, TYPE_CHECKING

from mstrio.access_and_security.security_filter import ObjectReference

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ParameterType(Enum):
    CONSTANT = "constant"
    OBJECT_REFERENCE = "object_reference"
    EXPRESSION = "expression"
    PROMPT = "prompt"
    ARRAY = "array"
    DYNAMIC_DATE_TIME = "dynamic_date_time"


class ParameterBase(Dictable):

    TYPE = None

    def __init__(self):
        self.parameter_type = self.TYPE


class ConstantType:
    INT_32 = "int32"
    INT_64 = "int64"
    DOUBLE = "double"
    DATE = "date",
    TIME = "time",
    STRING = "string"


class ConstantParameter(ParameterBase):

    TYPE = ParameterType.CONSTANT

    def __init__(self, type: "ConstantType", value: str):
        """Constant parameter for predicate.

        Args:
            type (enum): type of constant. Possible values are defined in enum
                `ConstantType`.
            value (str): value of constant.
        """
        super().__init__()
        self.constant = {"type": type, "value": value}

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None,
                  to_snake_case=True):
        source = camel_to_snake(source) if to_snake_case else source
        type = source.get('constant', {}).get('type')
        value = source.get('constant', {}).get('value')
        return ConstantParameter(type, value)


class ObjectReferenceParameter(ParameterBase):

    TYPE = ParameterType.OBJECT_REFERENCE

    def __init__(self, target: "ObjectReference"):
        super().__init__()
        self.target = target

    _FROM_DICT_MAP = {"target": ObjectReference.from_dict}


class ExpressionParameter(ParameterBase):

    TYPE = ParameterType.OBJECT_REFERENCE

    def __init__(self, expression: dict):
        super().__init__()
        self.expression = expression


class PromptParameter(ParameterBase):

    TYPE = ParameterType.PROMPT

    def __init__(self, prompt: "ObjectReference"):
        super().__init__()
        self.prompt = prompt

    _FROM_DICT_MAP = {"prompt": ObjectReference.from_dict}


class DynamicDateTimeParameter(ParameterBase):

    TYPE = ParameterType.DYNAMIC_DATE_TIME

    def __init__(self, dynamic_date_time: dict):
        super().__init__()
        # TODO think about some object for dynamic_date_stucture
        self.dynamic_date_time = dynamic_date_time


class ConstantArrayParameter(ParameterBase):

    TYPE = ParameterType.ARRAY

    def __init__(self, type: "ConstantType", values: List[str]):
        super().__init__()
        self.constants_type = type
        self.constants = values

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None,
                  to_snake_case=True):
        source = camel_to_snake(source) if to_snake_case else source
        type = source.get('constants_type')
        values = source.get('constants')
        return ConstantArrayParameter(type, values)
