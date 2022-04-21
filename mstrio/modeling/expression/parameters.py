from dataclasses import dataclass
from enum import auto
from typing import List, Optional, Type, TYPE_CHECKING

from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import camel_to_snake, Dictable

from .dynamic_date_time import DynamicDateTimeStructure
from .expression import Expression

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ParameterType(AutoName):
    """Enumeration constant indicating type of parameter"""
    CONSTANT = auto()
    OBJECT_REFERENCE = auto()
    EXPRESSION = auto()
    PROMPT = auto()
    ARRAY = auto()
    DYNAMIC_DATE_TIME = auto()


class VariantType(AutoName):
    """Enumeration constant indicating type of value of a variant object"""
    INT32 = auto()
    INT64 = auto()
    DATE = auto()
    TIME = auto()
    BOOLEAN = auto()
    STRING = auto()
    DOUBLE = auto()


@dataclass
class PredicateParameter(Dictable):
    """Base class for parameters"""

    _TYPE = None
    _DELETE_NONE_VALUES_RECURSION = False

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        result[camel_case and 'parameterType' or 'parameter_type'] = self._TYPE.value

        return result

    @staticmethod
    def dispatch(source, connection: Optional['Connection'] = None) -> Type['PredicateParameter']:
        data = camel_to_snake(source)
        parameter_type = ParameterType(data.pop('parameter_type'))
        cls = PREDICATE_PARAMETER_MAP[parameter_type]

        return cls.from_dict(data, connection, to_snake_case=False)


@dataclass
class AttributeElement(Dictable):
    """This object represents a concrete element.
    A concrete element is a metadata representation of an element
    that exists in some data source.

    Since an external data source can be modified without using
    the MicroStrategy Platform, the existence of a concrete element in
    the metadata does not mean that the element described currently exists.
    It means that it existed at some point.

    Attributes:
        display: Human readable string to display to describe the element to
            a reader
        element_id: Opaque string value that identifies the element to
            the service.

            The client should make no assumption about the format of this
            string, and should not attempt to parse it (even though forms of
            the element are likely to be visibly concatenated into it). This
            string will remain valid even if the current client is using a
            different locale to the locale of the client that created the
            element.

            When creating an element, the client should copy this string from
            other fields of the element browse result. If a "terse" element id
            is used, the service will need to know the attribute in order to
            decode the element id.
        attribute: Optionally the element may specify the attribute that it uses

            Note that in most cases elements are used in a context in which the
            attribute value is implied (for example the element is part of an
            IN-list of elements for some attribute). if the attribute is
            implied there is no need to redundantly repeat it on each element
            in the collection.

    """

    _DELETE_NONE_VALUES_RECURSION = False
    _FROM_DICT_MAP = {
        'attribute': SchemaObjectReference,
    }
    display: str
    element_id: str
    attribute: Optional[SchemaObjectReference] = None


@dataclass
class Variant(Dictable):
    """The typed value used in the predicates

    Attributes:
        type: Identifies the type of `value` attribute
        value: The value, encoded as a string in a standard,
            locale-neutral, format.
    """

    _DELETE_NONE_VALUES_RECURSION = False
    _FROM_DICT_MAP = {
        'type': VariantType,
    }

    type: VariantType
    value: str


@dataclass
class FunctionProperty(Dictable):
    """Additional properties associated with a function.

    Attributes:
        name: function's property name
        value: function's property value
    """

    _DELETE_NONE_VALUES_RECURSION = False

    name: str
    value: Variant


@dataclass
class ConstantParameter(PredicateParameter):
    """Object used to describe a parameter that appears in a filter predicate
    and whose value is constant.

    Attributes:
        constant: representation of constant as Variant object
    """

    _TYPE = ParameterType.CONSTANT
    _FROM_DICT_MAP = {
        'constant': Variant,
    }
    constant: Variant


@dataclass
class ObjectReferenceParameter(PredicateParameter):
    """Object that describe a parameter that appears in a filter predicate and
    whose value is an object reference.

    For example, a parameter of this type would be used by a filter predicate
    that compares the value of two metrics. This would be modelled by using a
    metric predicate (containing one of the two metrics); this parameter would
    then be used to record the other metric.

    Attributes:
        target: reference to object
    """

    _TYPE = ParameterType.OBJECT_REFERENCE
    _FROM_DICT_MAP = {
        'target': SchemaObjectReference,
    }
    target: SchemaObjectReference


@dataclass
class ExpressionParameter(PredicateParameter):
    """Object used to describe a parameter that appears in a filter predicate
    and whose value is given as a custom expression.

    This predicate parameter option is used for when the end user wants to
    provide a custom expression for the predicate. We would expect the parser
    to be used to modify the expression.

    Attributes:
        expression: custom expression, instance of Expression class
    """

    _TYPE = ParameterType.EXPRESSION
    _FROM_DICT_MAP = {
        'expression': Expression,
    }
    expression: Expression


@dataclass
class PromptParameter(PredicateParameter):
    """Object used to describe a parameter that appears in a filter predicate
    and whose value will be obtained on execution by resolving a prompt object.

    The prompt could be any type of prompt that returns a simple value: integer
    prompt, double prompt, big-decimal prompt, string prompt or date prompt.
    The prompt should be consistent with the data type of the value to be
    compared with the prompt.

    Attributes:
        prompt: reference to prompt object
    """

    _TYPE = ParameterType.PROMPT
    _FROM_DICT_MAP = {
        'prompt': SchemaObjectReference,
    }
    prompt: SchemaObjectReference


@dataclass
class ConstantArrayParameter(PredicateParameter):
    """Object used to describe a parameter that appears in a filter predicate
    and whose value is a list of constants.

    This kind of parameter is very specific. It is used for the IN and NOT_IN
    comparison functions. These functions compare one value with an array of
    constant values. Note that all the values in the array must have the
    same type.

    Attributes:
        constants_type: Identifies the type of values in `constants` attribute
        constants: list of constant values, each of which is encoded as a string
            in a standard, locale-neutral representation.
            Their common datatype is given by constants_type.

    """

    _TYPE = ParameterType.ARRAY
    _FROM_DICT_MAP = {
        'constants_type': VariantType,
    }
    constants_type: VariantType
    constants: List[str]


@dataclass
class DynamicDateTimeParameter(PredicateParameter):
    """Object used to describe a parameter that appears in a filter predicate
    and whose value is a dynamic date/time.

    Attributes:
        dynamic_date_time: Object that represents a date/time.
    """

    _TYPE = ParameterType.DYNAMIC_DATE_TIME
    _FROM_DICT_MAP = {
        'dynamic_date_time': DynamicDateTimeStructure,
    }
    dynamic_date_time: DynamicDateTimeStructure


PREDICATE_PARAMETER_MAP = {
    ParameterType.ARRAY: ConstantArrayParameter,
    ParameterType.CONSTANT: ConstantParameter,
    ParameterType.DYNAMIC_DATE_TIME: DynamicDateTimeParameter,
    ParameterType.EXPRESSION: ExpressionParameter,
    ParameterType.OBJECT_REFERENCE: ObjectReferenceParameter,
    ParameterType.PROMPT: PromptParameter,
}
