from enum import auto, Enum
from typing import Dict, List, Optional, TYPE_CHECKING, Union

from mstrio.access_and_security.security_filter import (
    AttributeElement, AttributeFormNormalRef, AttributeFormSystemRef, AttributeRef,
    ConstantArrayParameter, ConstantParameter, DynamicDateTimeParameter, ElementPromptRef,
    ExpressionParameter, FilterRef, ObjectReferenceParameter, ParameterType, PromptParameter
)
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Any, camel_to_snake, delete_none_values, Dictable, snake_to_camel

if TYPE_CHECKING:
    from mstrio.access_and_security.security_filter import ParameterBase
    from mstrio.connection import Connection


class PredicateBase(Dictable):

    TYPE = None
    _DELETE_NONE_VALUES_RECURSION = True

    def _create_predicate_tree(self, **kwargs):
        return None

    def _predicate_tree_to_dict(self, camel_case=True):
        return {}

    def to_dict(self, camel_case=True):
        result = delete_none_values({
            "type": self.type,
            "predicate_id": self.predicate_id,
            "predicate_tree": self._predicate_tree_to_dict(camel_case)
        }, recursion=True)
        return snake_to_camel(result) if camel_case else result

    def __init__(self, predicate_id: Optional[str] = None, **kwargs):
        self.type = self.TYPE
        self.predicate_id = predicate_id
        self.predicate_tree = self._create_predicate_tree(**kwargs)


class PredicateFormFunction(AutoName):
    EQUALS = auto()
    NOT_EQUAL = "not_equals"
    GREATER = auto()
    GREATER_EQUALS = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    IS_NULL = auto()
    IS_NOT_NULL = auto()
    BEGINS_WITH = auto()
    NOT_BEGINS_WITH = auto()
    CONTAINS = auto()
    NOT_CONTAINS = auto()
    LIKE = auto()
    NOT_LIKE = auto()
    IN = auto()
    NOT_IN = auto()
    BETWEEN = auto()
    NOT_BETWEEN = auto()


class PredicateForm(PredicateBase):
    # Attribute Form Predicate
    TYPE = 'predicate_form_qualification'
    _DELETE_NONE_VALUES_RECURSION = True

    def _create_predicate_tree(self, **kwargs):
        self.function = kwargs.get("function")
        self.parameters = kwargs.get("parameters")
        self.attribute = kwargs.get("attribute")
        self.form = kwargs.get("form")
        self.data_locale = kwargs.get("data_locale")

    def _predicate_tree_to_dict(self, camel_case=True):
        result = {
            "function": self.function.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "attribute": self.attribute.to_dict(),
            "form": self.form.to_dict(),
            "dataLocale": self.data_locale
        }
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source = camel_to_snake(source)
        predicate_id = source.get("predicate_id")

        source = source.get('predicate_tree')
        function = PredicateFormFunction(source.get("function"))

        parameters = []
        for parameter in source.get("parameters", []):
            parameter_type = parameter.get("parameterType")
            if parameter_type == ParameterType.CONSTANT.value:
                parameters.append(ConstantParameter.from_dict(parameter, connection))
            elif parameter_type == ParameterType.OBJECT_REFERENCE.value:
                parameters.append(
                    ObjectReferenceParameter.from_dict(parameter, connection))
            elif parameter_type == ParameterType.EXPRESSION.value:
                parameters.append(
                    ExpressionParameter.from_dict(parameter, connection))
            elif parameter_type == ParameterType.PROMPT.value:
                parameters.append(PromptParameter.from_dict(parameter, connection))
            elif parameter_type == ParameterType.DYNAMIC_DATE_TIME.value:
                parameters.append(
                    DynamicDateTimeParameter.from_dict(parameter, connection))
            elif parameter_type == ParameterType.ARRAY.value:
                parameters.append(
                    ConstantArrayParameter.from_dict(parameter, connection))

        attribute = AttributeRef.from_dict(source.get("attribute"), connection)
        form = source.get("form", {})
        form_sub_type = form.get("sub_type")
        if form_sub_type == "attribute_form_system":
            form = AttributeFormSystemRef.from_dict(source.get("form"), connection)
        elif form_sub_type == "attribute_form_normal":
            form = AttributeFormNormalRef.from_dict(source.get("form"), connection)
        else:
            form = None
        data_locale = source.get("data_locale")

        return PredicateForm(function, parameters, attribute, form, data_locale, predicate_id)

    def __init__(self, function: "PredicateFormFunction", parameters: List["ParameterBase"],
                 attribute: "AttributeRef", form: Union["AttributeFormSystemRef",
                                                        "AttributeFormNormalRef"],
                 data_locale: Optional[str] = None, predicate_id: Optional[str] = None):
        """Specialized expression node that contains an attribute form
        qualification predicate.

        This qualification selects elements of a specific attribute by
        comparing the value of a specified form of the element with an
        expression. The comparison operator used is also specified. However
        there are three options for specifying the expression with which it is
        compared:
            - the client may specify a literal value
            - the client may ask to use a prompt to determine the value
            - the client may supply an arbitrary metric style expression to
              evaluate to obtain the value

        Args:
            function (enum): the comparison function that should be used to
                compare the value computed by the filter with an expression
                value. Available values are defined in enum
                `PredicateFormFunction`.
            parameters (list of objects): array of objects that correspond to
                the parameters for the comparison function. In nearly all cases
                the comparison function will take one extra parameter (in
                addition to the parameter referenced by the predicate's main
                object). This value is an array because there are a few
                functions which take a different number of extra parameters. For
                example `isNull` does not need any additional parameters,
                `notBetween` needs two additional parameters.
            attribute (object): object with basic information about attribute
                such as its `object_id` and `name`.
            form (object): object with basic information about attribute form
                such as its `object_id` and `name`.
            data_locale (str): optional data locale used to select value of the
                form.
            predicate_id (str): identifier of this predicate. When creating
                predicate it is not necessary to provide it.

        Example:
            >>> PredicateForm(
            >>>     function=PredicateFormFunction.GREATER,
            >>>     parameters=[
            >>>         ConstantParameter(ConstantType.DOUBLE, "2015.0")
            >>>     ],
            >>>     attribute=AttributeRef("8D679D5111D3E4981000E787EC6DE8A4",
            >>>                            "Year"),
            >>>     form=AttributeFormSystemRef(
            >>>         "45C11FA478E745FEA08D781CEA190FE5", "ID"
            >>>     )
            >>> )
        """
        super().__init__(predicate_id, function=function, parameters=parameters,
                         attribute=attribute, form=form, data_locale=data_locale)


class PredicateElementListFunction(Enum):
    NOT_IN = "notIn"
    IN = "in"


class PredicateElementList(PredicateBase):
    # Element List Predicate
    TYPE = 'predicate_element_list'
    _DELETE_NONE_VALUES_RECURSION = True

    def _create_predicate_tree(self, **kwargs):
        self.function = kwargs.get("function")
        self.attribute = kwargs.get("attribute")
        self.elements = kwargs.get("elements")
        self.elements_prompt = kwargs.get("elements_prompt")

    def _predicate_tree_to_dict(self, camel_case=True):
        elements_prompt = None if self.elements_prompt is None else [
            elem.to_dict(camel_case) for elem in self.elements_prompt
        ]
        result = {
            "function": self.function.value,
            "attribute": self.attribute.to_dict(camel_case),
            "elements": [elem.to_dict(camel_case) for elem in self.elements],
            "elements_prompt": elements_prompt
        }
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source = camel_to_snake(source)
        predicate_id = source.get("predicate_id")

        source = source.get('predicate_tree')
        function = PredicateElementListFunction(source.get("function"))
        attribute = AttributeRef.from_dict(source.get("attribute"), connection)
        elements = [
            AttributeElement.from_dict(elem, connection)
            for elem in source.get("elements")
        ]
        elements_prompt = None if source.get("elements_prompt") is None else [
            ElementPromptRef.from_dict(elem, connection)
            for elem in source.get("elements_prompt")
        ]
        return PredicateElementList(function, attribute, elements, elements_prompt, predicate_id)

    def __init__(self, function: "PredicateElementListFunction", attribute: "AttributeRef",
                 elements: List["AttributeElement"],
                 elements_prompt: Optional[List["ElementPromptRef"]] = None,
                 predicate_id: Optional[str] = None):
        """Specialized expression node that contains an element list predicate.

        This qualification selects elements of a specified attribute by either
        listing the elements that should be selected, or alternatively by
        listing the elements that should be excluded from the selection.

        Args:
            function (enum): function that should be used in this predicate.
                Available values are defined in enum
                `PredicateElementsListFunction`.
            attribute (object): object with basic information about attribute
                such as its `object_id` and `name`.
            elements (list of objects): list of objects with basic information
                about element such its `element_id` and `display`.
            elements_prompt (list of objects): list of objects with basic
                information about a prompt element such its `object_id` and
                `name`
            predicate_id (str): identifier of this predicate. When creating
                predicate it is not necessary to provide it.

        Example:
            >>> PredicateElementList(
            >>>     function=PredicateElementListFunction.IN,
            >>>     attribute=AttributeRef("8D679D3711D3E4981000E787EC6DE8A4",
            >>>                            "Catetgory"),
            >>>     elements=[
            >>>         AttributeElement("h2", "Electronics"),
            >>>         AttributeElement("h1", "Books")
            >>>     ]
            >>> )
        """
        super().__init__(predicate_id, function=function, attribute=attribute, elements=elements,
                         elements_prompt=elements_prompt)


class PredicateFilter(PredicateBase):
    # Filter Qualification Predicate
    TYPE = 'predicate_filter_qualification'
    _DELETE_NONE_VALUES_RECURSION = True

    def _create_predicate_tree(self, **kwargs):
        self.filter = kwargs.get("filter")
        self.is_independent = kwargs.get("is_independent")

    def _predicate_tree_to_dict(self, camel_case=True):
        result = {
            "filter": self.filter.to_dict(camel_case),
            "is_independent": 1 if self.is_independent else 0,
        }
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source = camel_to_snake(source)
        predicate_id = source.get("predicate_id")

        source = source.get('predicate_tree')
        filter = FilterRef.from_dict(source.get("filter"), connection)
        is_independent = bool(source.get("is_independent"))

        return PredicateFilter(filter, is_independent, predicate_id)

    def __init__(self, filter: "FilterRef", is_independent: Optional[bool] = True,
                 predicate_id: Optional[str] = None):
        """Specialized expression node that contains a filter qualification
        predicate.

        This node is used within filter expressions to represent
        a predicate whose value is determined by using an external filter
        object. At execution time the engine will typically act as if the
        specified filter had been included directly. By using filter objects,
        the client can build complex filter expressions that utilise common
        subexpressions.

        Args:
            filter (object): object with basic information about child filter
                such as its `id` and `name`
            is_independent (bool): flag that indicates whethere this child will
                be considered independently of other parts of the larger filter.
                Default value is `True` which means that this filter will be
                evaluated by itself.
            predicate_id (str): identifier of this predicate. When creating
                predicate it is not necessary to provide it.

        Example:
            >>> PredicateFilter (
            >>>     filter=FilterRef("320081BF47ECD3DEB07529B1BEF4271B",
            >>>                      "Filter Object"),
            >>>     is_independent=True
            >>> )
        """
        super().__init__(predicate_id, filter=filter, is_independent=is_independent)


class PredicateJointElementList(PredicateBase):
    # Joint Element List Predicate
    TYPE = 'predicate_joint_element_list'
    _DELETE_NONE_VALUES_RECURSION = True

    def _create_predicate_tree(self, **kwargs):
        self.level = kwargs.get("level")
        self.tuples = kwargs.get("tuples")

    def _predicate_tree_to_dict(self, camel_case=True):
        result = {
            "level": [obj.to_dict(camel_case) for obj in self.level],
            "tuples": [[elem.to_dict(camel_case) for elem in obj] for obj in self.tuples],
            "predicate_id": self.predicate_id
        }
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source = camel_to_snake(source)
        predicate_id = source.get("predicate_id")

        source = source.get('predicate_tree')
        level = [
            AttributeRef.from_dict(obj, connection) for obj in source.get("level")
        ]
        tuples = [[AttributeElement.from_dict(elem, connection)
                   for elem in obj]
                  for obj in source.get("tuples", [])]

        return PredicateJointElementList(predicate_id, level, tuples)

    def __init__(self, level: List["AttributeRef"], tuples: List[List["AttributeElement"]],
                 predicate_id: Optional[str] = None):
        """Specialized expression node that contains a joint element list
        predicate.

        This qualification represents a filter at the level of two or more
        attributes. The filter is defined by simply listing the tuples of
        elements that satisfy the filter.

        Args:
            level (list of objects): the level of this filter is represented as
                an array of attributes. The attributes must be different from
                each other, and their order is significant.
            tuples (list of lists of objects): an array of tuples of elements.
                Each element of this array is a joint element. That is the
                members of this array are themselves arrays of elements. The
                elements in the tuples must be listed in the same order as the
                attributtes were listed in the `level` array. There is no need
                to list the attribute on each element.
            predicate_id (str): identifier of this predicate. When creating
                predicate it is not necessary to provide it.

        Example:
            >>> PredicateJointElementList(
            >>>     level=[
            >>>         AttributeRef("8D679D3711D3E4981000E787EC6DE8A4",
            >>>                      "Category"),
            >>>         AttributeRef("8D679D4B11D3E4981000E787EC6DE8A4",
            >>>                      "Region")
            >>>     ],
            >>>     tuples=[
            >>>         [AttributeElement("h1", "Books"),
            >>>          AttributeElement("h1", "Northeast")],
            >>>         [AttributeElement("h2", "Electronics"),
            >>>          AttributeElement("h7", "Southwest")]
            >>>     ])
        """
        super().__init__(predicate_id, level=level, tuples=tuples)


class LogicFunction(AutoName):
    OR = auto()
    AND = auto()


class LogicOperator(Dictable):

    TYPE = "operator"
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, function: "LogicFunction", children: Union["LogicOperator",
                                                                  "PredicateBase"]):
        self.type = "operator"
        self.function = function
        self.children = children

    def to_dict(self, camel_case=True):
        result = delete_none_values({
            "type": self.type,
            "function": self.function.value,
            "children": [child.to_dict(camel_case) for child in self.children]
        }, recursion=True)
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        source = camel_to_snake(source)
        function = LogicFunction(source.get("function"))
        children = []
        for child in source.get("children"):
            child_type = child.get("type")
            if child_type == "predicate_form_qualification":
                children.append(PredicateForm.from_dict(child, connection))
            elif child_type == "predicate_joint_element_list":
                children.append(
                    PredicateJointElementList.from_dict(child, connection))
            elif child_type == "predicate_filter_qualification":
                children.append(PredicateFilter.from_dict(child, connection))
            elif child_type == "predicate_element_list":
                children.append(PredicateElementList.from_dict(child, connection))
            elif child_type == "operator":
                children.append(LogicOperator.from_dict(child, connection))

        return LogicOperator(function, children)
