from dataclasses import dataclass, field
from enum import auto
from typing import List, Optional, Type, TYPE_CHECKING

from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import camel_to_snake, delete_none_values, snake_to_camel

from .dynamic_date_time import DynamicDateTimeStructure
from .enums import Function, IsIndependent, NodeType
from .expression import Expression, ExpressionNode
from .parameters import AttributeElement, FunctionProperty, PredicateParameter, Variant

if TYPE_CHECKING:
    from mstrio.connection import Connection


@dataclass(kw_only=True)
class PredicateNode(ExpressionNode):
    """Base class for all predicate nodes.

    Attributes:
        predicate_id: String identifier that uniquely identifies this predicate
            within the context of its larger filter. Any non-empty string of
            printable characters can be used as a predicate.
        predicate_text: Text representation of a predicate
    """
    predicate_id: Optional[str] = None
    predicate_text: Optional[str] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        result = {
            'type': self._TYPE.value,
            'predicate_id': self.predicate_id,
            'predicate_text': self.predicate_text,
            **self._get_node_data(),
        }

        result = delete_none_values(result, recursion=False)
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(
        cls, source: dict, connection: Optional['Connection'] = None, to_snake_case: bool = True
    ) -> Type['PredicateNode']:
        data = camel_to_snake(source) if to_snake_case else source.copy()
        # get a dict under predicate_tree attribute to unpack it
        predicate_tree = data.pop('predicate_tree')
        return super().from_dict({**data, **predicate_tree}, connection, to_snake_case=False)

    def _get_node_data(self):
        """Return dictionary that contains data unique to particular predicate
        node that should be merged with data common to all predicate nodes in
        to_dict.
        """
        pass


@dataclass(kw_only=True)
class CustomExpressionPredicate(PredicateNode):
    """Specialized expression node that contains a custom expression predicate.
    This qualification contains a valid expression, usually created by the user,
    which can't be categorized into other types.

    The expression is represented by a list of tokens. The predicate has the
    predicate details which contains the tokens representing the expression.
    It's controlled by the showPredicates to show or hide.

    Attributes:
        expression: Generic specification for calculation, instance of
            Expression class
        node_property: A property used for persisting back-compatibility
            information for the filter editing. Usually it will not show.
    """

    _TYPE = NodeType.PREDICATE_CUSTOM
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'expression': Expression,
    }

    expression: Expression
    node_property: Optional[int] = None

    def _get_node_data(self):
        return {
            'node_property': self.node_property,
            'predicate_tree': {
                'expression': self.expression.to_dict(),
            },
        }


@dataclass(kw_only=True)
class MetricPredicate(PredicateNode):
    """Specialized expression node that contains a metric qualification
    predicate.

    This qualification selects tuples of elements at a specified level by
    comparing the value of a specified metric evaluated at the tuple with
    a value of an expression. The comparison operator used is also specified.
    However, there are multiple options for specifying the expression with which
    the metric is compared:

        - The client may specify a literal value.
        - The client may specify an object reference.
        - The client may ask to use a prompt to determine the value.
        - The client may supply an arbitrary metric style expression to evaluate
          to obtain the value.

    Attributes:
        function: Specify the comparison function that should be used to compare
            the value computed by the filter with an expression value.
        metric: The metric over whose values this qualification is evaluated.
        parameters: List of objects that correspond to the parameters for the
            comparison function.
            In nearly all cases the comparison function will take one extra
            parameter (in addition to the parameter referenced by the
            predicate's main object).
        level_type: Enumeration value indicating how the predicate's level
             should be determined.
             If there is a level it is usually taken to be the same level as is
             used in the display grid, or which was used to obtain the data.
             There is also an option to specify an absolute level as part of the
             predicate definition.
        level: Within an expression we sometimes need to state at which
            a computation is performed.
            In some cases the level is obtained by examining the execution
            environment. This object is used if the designer wishes to specify
            an explicit level. An explicit level is a list of attributes.
            Alternatively the client may defer selecting an attribute
            (or attributes) at design time by using a prompt instead.
            If a prompt is used it should be a choose-attributes prompt, and it
            may return any number of attributes (including zero).
        metric_function: Optional parameter that describes how the metric is
            used within the predicate. If this parameter is omitted it is
            treated as if it had been set to value.
        null_include: NullInclude is an integer parameter which specifies
            how null values are considered when evaluating the Rank function.
            Use 1 to place null values after the value list, use -1 to place
            null values before the value list or use 0 to apply the Null
            checking setting for Analytical Engine in VLDB properties. If this
            value is not set, 0 will be applied.
        break_by: The break by property of a metric qualification allows you to
            choose the attribute level at which to restart counting rank or
            percent values for a metric. This attribute level must be higher
            than or equal to the level of aggregation for the metric itself.
            break_by is a list of distinct attribute references. The list may
            also contain a choose-attribute prompt instead which can be answered
            with zero, one or more attributes. This value is only used when
            the metric_function property is not set to value.
        is_independent: Flag that indicates whether the metric will be evaluated
           independently of other parts of the larger filter:
           - If set to 1 (the default value, also used if this property is
               omitted) then this metric will be evaluated by itself.
           - If set to 0 then other parts of the larger filter will be applied
               when evaluating the metric.
    """

    class MetricFunction(AutoName):
        """Enumeration constant that describes how the metric is used
        within the predicate.
        """
        VALUE = auto()
        RANK_DESCEND = auto()
        RANK_ASCEND = auto()
        PERCENTILE_DESCEND = auto()
        PERCENTILE_ASCEND = auto()

    _TYPE = NodeType.PREDICATE_METRIC_QUALIFICATION
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'function': Function,
        'parameters': [PredicateParameter.dispatch],
        'level': [SchemaObjectReference],
        'metric': SchemaObjectReference,
        'metric_function': MetricFunction,
        'break_by': [SchemaObjectReference],
        'is_independent': IsIndependent,
    }
    _ALLOW_NONE_ATTRIBUTES = ['parameters']

    function: Function
    metric: SchemaObjectReference
    level_type: str
    parameters: List[PredicateParameter] = field(default_factory=list)
    level: Optional[List[SchemaObjectReference]] = None
    metric_function: Optional[MetricFunction] = None
    null_include: Optional[int] = None
    break_by: Optional[List[SchemaObjectReference]] = None
    is_independent: IsIndependent = IsIndependent.YES

    def _get_node_data(self):
        result = {
            'predicate_tree': {
                'function': self.function.value,
                'parameters': [item.to_dict() for item in self.parameters],
                'level': [item.to_dict() for item in self.level] if self.level else None,
                'level_type': self.level_type,
                'metric': self.metric.to_dict(),
                'metric_function': self.metric_function.value,
                'break_by': [item.to_dict() for item in self.break_by] if self.break_by else None,
                'null_include': self.null_include,
                'is_independent': self.is_independent.value,
            }
        }

        return delete_none_values(
            result, recursion=True, whitelist_attributes=self._ALLOW_NONE_ATTRIBUTES
        )


@dataclass(kw_only=True)
class SetFromRelationshipPredicate(PredicateNode):
    """Specialized expression node that contains a relationship set
    qualification predicate. In words this predicate describes a qualification
    of the form "SET of WHERE".

    This node is used within filter expressions to represent a predicate whose
    value is determined by starting with an arbitrary filter expression at some
    natural level. This filter is then projected to a filter at a level
    specified within this predicate by using a relationship. The relationship
    might be the natural relationship inferred by the engine for the schema, the
    relationship given by an explicit table, or a relationship implied by a fact
    (i.e. the engine selects the best table from the set of tables where the
    given fact is implemented).

    This predicate is the only kind of filter predicate that may have a child
    expression.

    Attributes:
        level: Within an expression we sometimes need to state at which a
            computation is performed. In some cases the level is obtained by
            examining the execution environment. This object is used if the
            designer wishes to specify an explicit level.

            An explicit level is a list of attributes. Alternatively the client
            may defer selecting an attribute (or attributes) at design time by
            using a prompt instead. If a prompt is used it should be a
            choose-attributes prompt, and it may return any number of
            attributes (including zero).

        guide: An optional object that specifies how to relate the child filter
            with the output filter. There are three options, depending on the
            nature of the guide object:

            The object may be a logicalTable, in which case the filter is
            projected through this table. The object may be a fact, in which
            case the filter is projected via one of the tables on which the
            fact is defined. There might not be a guide object at all, in which
            case the filter is projected via the engine's usual join rules
            (using attribute relationships from the system hierarchy).

        is_independent: Flag that indicates whether this child filter will be
            considered independently of other parts of the larger filter:

            - If set to 1 (the default value, used if this property is omitted)
            then this filter will be evaluated by itself.

            - If set to 0 then other parts of the larger filter will be merged
            into this filter. Using this setting could change the value of a
            metric or relationship set qualification that appears within the
            child filter.

        children: List containing the optional root node of the child filter
            expression. We require that a relationship predicate always has a
            child filter is always given, but it is possible that the child
            filter is the empty filter. We model that situation by either
            omitting the children value or by using an empty list.

            This expression is also a filter expression, and it is manipulated
            in the same manner as the rest of the filter. The predicate ids
            that appear within this expression must have disjoint values from
            the predicate ids used in the larger filter. Thus, an individual
            node within this expression can be manipulated by treating it as a
            manipulation of the larger filter in the usual manner.

            We use a list so that this value matches the list value of the
            same name used in an operator node.
    """

    _TYPE = NodeType.PREDICATE_RELATIONSHIP
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'level': [SchemaObjectReference],
        'guide': SchemaObjectReference,
        'is_independent': IsIndependent,
        'children': [ExpressionNode.dispatch],
    }

    level: List[SchemaObjectReference]
    guide: Optional[SchemaObjectReference] = None
    is_independent: IsIndependent = IsIndependent.YES
    children: Optional[List[ExpressionNode]] = None

    def _get_node_data(self):
        result = {
            'predicate_tree': {
                'level': [item.to_dict() for item in self.level],
                'guide': self.guide.to_dict() if self.guide else None,
                'is_independent': self.is_independent.value,
            },
            'children': [item.to_dict() for item in self.children] if self.children else None,
        }

        return delete_none_values(result, recursion=True)


@dataclass(kw_only=True)
class JointElementListPredicate(PredicateNode):
    """Specialized expression node that contains a joint element list predicate.

    This qualification represents a filter at the level of two or more
    attributes.
    The filter is defined by simply listing the tuples of elements that satisfy
    the filter.

    Attributes:
        level: The level of this filter represented as a list of attributes.
            The attributes must be different from each other, and their order
            is significant.

        tuples: List of tuples of elements.

            Each element of this list is a joint element. That is the members
            of this list are themselves lists of elements. The elements in
            the tuples must be listed in the same order as the attributes were
            listed in the level list. There is no need to list the attribute
            on each element.
    """

    _TYPE = NodeType.PREDICATE_JOINT_ELEMENT_LIST
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'level': [SchemaObjectReference],
        'tuples': [[AttributeElement]],
    }

    level: List[SchemaObjectReference]
    tuples: List[List[AttributeElement]]

    def _get_node_data(self):
        return {
            'predicate_tree': {
                'level': [item.to_dict() for item in self.level],
                'tuples': [[item.to_dict() for item in tuple_item] for tuple_item in self.tuples],
            },
        }


@dataclass(kw_only=True)
class ElementListPredicate(PredicateNode):
    """Specialized expression node that contains an element list predicate.

    This qualification selects elements of a specified attribute by either
    listing the elements that should be selected, or alternatively by listing
    the elements that should be excluded from the selection.

    Attributes:
        attribute: The attribute whose elements are selected by this
            qualification. Property is not needed if the predicate uses a
            prompt since in that case the attribute is specified by the prompt.

        elements: List of the elements in the predicate

        elements_prompt: A choose-elements prompt used to obtain the elements
            in the qualification. If this object is used then it will specify
            the attribute and elements for the qualification. The prompt will
            specify an attribute from which the elements should be selected.

        function: Specify the function that should be used in this predicate.

            Although this property is a function identifier, there are only two
            functions that make sense for this predicate:

            - IN (the filter accepts any element in the list, default value)
            - NOT_IN (the filter accepts any element not included in the list)
    """

    class ElementListFunction(AutoName):
        """Enumeration constant that describes what functions can be used
        within ElementListPredicate
        """
        IN = auto()
        NOT_IN = auto()

    _TYPE = NodeType.PREDICATE_ELEMENT_LIST
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'attribute': SchemaObjectReference,
        'elements': [AttributeElement],
        'elements_prompt': SchemaObjectReference,
        'function': ElementListFunction,
    }

    attribute: Optional[SchemaObjectReference] = None
    elements: Optional[List[AttributeElement]] = None
    elements_prompt: Optional[SchemaObjectReference] = None
    function: ElementListFunction = ElementListFunction.IN

    def _get_node_data(self):
        result = {
            'predicate_tree': {
                'attribute': self.attribute.to_dict() if self.attribute else None,
                'elements': [item.to_dict() for item in self.elements] if self.elements else None,
                'elements_prompt': self.elements_prompt.to_dict()
                if self.elements_prompt else None,  # noqa
                'function': self.function.value,
            }
        }

        return delete_none_values(result, recursion=True)


@dataclass(kw_only=True)
class AttributeFormPredicate(PredicateNode):
    """Specialized expression node that contains an attribute form qualification
    predicate.

    This qualification selects elements of a specified attribute by comparing
    the value of
    a specified form of the element with an expression. The comparison operator
    used is also specified. However, there are three options for specifying the
    expression with which it is compared:

    - The client may specify a literal value.
    - The client may ask to use a prompt to determine the value.
    - The client may supply an arbitrary metric style expression to evaluate to
    obtain the value.

    Attributes:
        function: Specify the comparison function that should be used to
            compare the value computed by the filter with an expression value.

        parameters: list of objects that correspond to the parameters for the
            comparison function. In nearly all cases the comparison function
            will take one extra parameter (in addition to the parameter
            referenced by the predicate's main object).

            This value is a list because there are a few functions which take
            a different number of extra parameters. For example isNull does not
            need any additional parameters; notBetween needs two additional
            parameters.

        attribute: The attribute whose elements are selected by this
            qualification

        form: The attribute form whose value is used to specify the
            qualification

        data_locale: Optional data locale used to select values of the form.
            The format should follow the IETF BCP 47 language tag, for example:
            "en-US".

            Some forms of some attributes may be configured to store
            representation in multiple locales. If a predicate qualifies on a
            form that has been translated in this manner it is likely that the
            elements selected by the predicate will be different for different
            locales. But we do not want the meaning of a filter to vary based
            on the locale preferences of the user executing the filter. So this
            property is used to specify the data locale to be used for the
            qualification. When set it will override the user's personal data
            locale preference.

            Retrieving a filter only returns this field if the form is
            multilingual. If the form is multilingual but no particular locale
            is set, an empty string will be returned. When updating or creating
            a filter, again a check will be made to see if the form is capable
            of being multilingual. If not, users inputs are ignored. If the
            form is indeed multilingual and the field is omitted from the
            input, the locale will default to the warehouse data locale of the
            user.
    """

    _TYPE = NodeType.PREDICATE_FORM_QUALIFICATION
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'parameters': [PredicateParameter.dispatch],
        'attribute': SchemaObjectReference,
        'form': SchemaObjectReference,
        'function': Function
    }
    _ALLOW_NONE_ATTRIBUTES = ['parameters']

    function: Function
    attribute: SchemaObjectReference
    form: SchemaObjectReference
    # in swagger is required, but can be empty list
    parameters: List[PredicateParameter] = field(default_factory=list)
    data_locale: Optional[str] = None

    def _get_node_data(self):
        result = {
            'predicate_tree': {
                'function': self.function.value,
                'attribute': self.attribute.to_dict(),
                'form': self.form.to_dict(),
                'parameters': [item.to_dict() for item in self.parameters],
                'data_locale': self.data_locale,
            }
        }

        return delete_none_values(
            result, recursion=True, whitelist_attributes=self._ALLOW_NONE_ATTRIBUTES
        )


@dataclass(kw_only=True)
class FilterQualificationPredicate(PredicateNode):
    """Specialized expression node that contains a filter qualification
    predicate.

    This node is used within filter expressions to represent a predicate whose
    value is determined by using an external filter object. At execution time
    the engine will typically act as if the specified filter had been included
    directly. By using shared filter objects, the client can build complex
    filter expressions to utilise common subexpressions.

    A filter object may not reference itself, or any filter that depends on
    itself. If such a filter is saved to the metadata any calculation that uses
    the filter will fail.

    Attributes:
        filter: Reference to the child filter that should be included in this
            predicate.

        is_independent: Flag that indicates whether this child filter will be
            considered independently of other parts of the larger filter:

            - If set to 1 (the default value, used if this property is omitted)
            then this filter will be evaluated by itself.

            - If set to 0 then other parts of the larger filter will be merged
            into this filter. Using this setting could change the value of a
            metric or relationship set qualification that appears within the
            child filter.
    """

    _TYPE = NodeType.PREDICATE_FILTER_QUALIFICATION
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'filter': SchemaObjectReference,
        'is_independent': IsIndependent,
    }

    filter: SchemaObjectReference
    is_independent: IsIndependent = IsIndependent.YES

    def _get_node_data(self):
        return {
            'predicate_tree': {
                'filter': self.filter.to_dict(),
                'is_independent': self.is_independent.value,
            },
        }


@dataclass(kw_only=True)
class ReportQualificationPredicate(PredicateNode):
    """Specialized expression node that contains a report qualification
    predicate.

    This node is used within filter expressions to represent a predicate
    whose value is determined by using a report as filter. That is the engine
    will evaluate a report, and determine the rows that it covers. These filter
    will consist of these rows.

    Attributes:
        report: Reference to the child report that should be included in this
            predicate.
    """

    _TYPE = NodeType.PREDICATE_REPORT_QUALIFICATION
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'report': SchemaObjectReference,
    }

    report: SchemaObjectReference

    def _get_node_data(self):
        return {
            'predicate_tree': {
                'report': self.report.to_dict(),
            },
        }


@dataclass(kw_only=True)
class PromptPredicate(PredicateNode):
    """Specialized expression node for a predicate whose value is prompted at
    execution time.

    This predicate is used for various kinds of expression prompts. At execution
    time the end user in effect enters an entire predicate (or an even more
    complex expression).
    The answer is then substituted into the filter in place of this node.

    Attributes:
        prompt: reference to a prompt, whose value is prompted at execution
    """

    _TYPE = NodeType.PREDICATE_PROMPT_QUALIFICATION
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'prompt': SchemaObjectReference,
    }

    prompt: SchemaObjectReference

    def _get_node_data(self):
        return {
            'predicate_tree': {
                'prompt': self.prompt.to_dict(),
            },
        }


@dataclass(kw_only=True)
class Operator(ExpressionNode):
    """An expression node whose value is obtained by applying a specified
    function to a list of child expressions. Most internal nodes within
    an expression are operator nodes.

    Attributes:

        children: The list of child expression that combined at this operator.
            If there are multiple child expressions then their order
            is significant. In a few cases (depending on the function) it is
            valid for an operator node to have no children, in which case this
            member property may be omitted.

        function: Enumeration constant that identifies all the built-in
            functions. This value will always be provided when the service
            generates the object. When the client generates the object it may
            use this field by itself to specify the function. This value by
            itself is insufficient to identify the function if it is set to
            CUSTOM or THIRD_PARTY, in which case the custom_function value must
            be provided. This property is required in the predicate model but
            can be replaced by 'function_prompt' in the expression model.

        function_properties: The list of additional properties associated with
            the function. This is most useful when the function is 'RANK', as
            we'll need the "by_value" and "ascending" properties. This field is
            only used in a custom expression tree.

        function_prompt: The prompt used by this function. This field is only
            used in a custom expression tree.

        level_type: Enumeration value indicating how the predicate's level
            should be determined.

            If there is a level it is usually taken to be the same level as is
            used in the display grid, or which was used to obtain the data.
            There is also an option to specify an absolute level as part of the
            predicate definition.

            This field is only used in a custom expression tree.

        level: This field is only used in a custom expression tree.

        node_property: A property used for persisting back-compatibility
            information for the filter editing. Usually it will not show. If
            it's displayed in the response, you should consider include it with
            the same value in the same node in the request body when you're
            performing the PUT/POST/PATCH.

            If you don't put it back in the request, there can be some behavior
            difference in Filter Expression Editors of other MicroStrategy
            apps.
    """

    class LevelType(AutoName):
        """Enumeration value indicating how the predicate's level should be
        determined
        """
        NONE = auto()
        METRIC_LEVEL = auto()
        GRID_LEVEL = auto()
        EXPLICIT_LEVEL = auto()

    _TYPE = NodeType.OPERATOR
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'children': [ExpressionNode.dispatch],
        'function': Function,
        'function_properties': [FunctionProperty],
        'function_prompt': SchemaObjectReference,
        'level_type': LevelType,
        'level': [SchemaObjectReference],
        'node_property': int,
        'custom_function': SchemaObjectReference,
    }

    children: Optional[List[ExpressionNode]] = None
    function: Optional[Function] = None
    function_properties: Optional[List[FunctionProperty]] = None
    function_prompt: Optional[SchemaObjectReference] = None
    level_type: Optional[LevelType] = None
    level: Optional[List[SchemaObjectReference]] = None
    node_property: Optional[int] = None
    custom_function: Optional[SchemaObjectReference] = None


@dataclass(kw_only=True)
class ObjectReference(ExpressionNode):
    """An expression node whose value is a reference to some other object in
    the metadata.

    The meaning of the reference depends on the context. If the referenced
    object is an object that is based on an expression (say a filter or a
    metric) then it usually means we inline the expression from the object.
    But in other cases (say a fact) it means that on execution the object
    reference is replaced with a value of the fact in the context of execution.

    Although unusual, it is possible that an object reference node might not
    refer to an object. If that happens this target property is usually omitted
    (but might be present but use 00000000000000000000000000000000 as its
    object_id).

    The object could be a prompt to select the target object at runtime.
    Typically, it is not acceptable for the prompt to return more than
    one answer.

    Attributes:
        target: object being referenced

        is_independent: Flag that indicates whether this child filter will be
            considered independently of other parts of the larger filter:

            - If set to 1 (the default value, used if this property is omitted)
            then this filter will be evaluated by itself.

            - If set to 0 then other parts of the larger filter will be merged
            into this filter. Using this setting could change the value of a
            metric or relationship set qualification that appears within the
            child filter.

        substitute_function_type: Specify how to merge multiple answers if the
            predicate's value is obtained via a prompt.
            This property is only used when filter's value is a prompt. If the
            end user selects multiple answers to the prompt, the platform will
            replace this node by a Boolean operator, used to combine the
            answers. This property determines which operator it uses. By
            default, it uses the parent Boolean operator (or AND if this
            predicate is the root of the filter). Set this property to override
            the default behavior.
    """

    class SubstituteFunctionType(AutoName):
        """Enumeration constant that specify how to merge multiple answers
        if the predicate's value is obtained via a prompt.
        """
        AND = auto()
        OR = auto()

    _TYPE = NodeType.OBJECT_REFERENCE
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'target': SchemaObjectReference,
        'is_independent': IsIndependent,
        'substitute_function_type': SubstituteFunctionType,
    }

    target: Optional[SchemaObjectReference] = None
    is_independent: IsIndependent = IsIndependent.YES
    substitute_function_type: Optional[SubstituteFunctionType] = None


@dataclass(kw_only=True)
class ColumnReference(ExpressionNode):
    """n expression node whose value is some column from a table implied
    by the expression's context.

    This kind of node is used when we wish to define an expression over
    the columns of a table or potentially over more than one table.
    The reference specifies, the column of interest, by name alone. So the
    reference is to a selected column on the implied table. It is not
    a reference to a specific column on a specific table. Defining a column
    reference in this manner allows the architect to specify an expression
    that can be usefully applied to more than one table.

    Attributes:
        column_name: The name of the column, as it appears within the RDBMS.

        object_id: A globally unique identifier used to distinguish between
            metadata objects within the same project. It is possible for two
            metadata objects in different projects to have the same Object id.
    """

    _TYPE = NodeType.COLUMN_REFERENCE
    column_name: str
    object_id: Optional[str] = None


@dataclass(kw_only=True)
class Constant(ExpressionNode):
    """An expression node that contains a literal value. The value was
    fixed when the expression node was first specified. This kind of node
    is only used for simple values (integers, floating point numbers and text
    strings).

    Alternatively, instead of the variant the node could contain a choose-value
    prompt reference.

    Attributes:
        variant: constant value specified as Variant
        prompt: reference to a prompt
    """

    _TYPE = NodeType.CONSTANT
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'variant': Variant,
        'prompt': SchemaObjectReference,
    }

    variant: Optional[Variant] = None
    prompt: Optional[SchemaObjectReference] = None


@dataclass(kw_only=True)
class DynamicDateTime(ExpressionNode):
    """An expression node that represents Dynamic Date Time.

    Attributes:
        value (DynamicDateTimeStructure): an object that represents
            date and/or time.
    """

    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'value': DynamicDateTimeStructure,
    }
    _TYPE = NodeType.DYNAMIC_DATE_TIME
    value: DynamicDateTimeStructure


@dataclass(kw_only=True)
class ExpressionFormShortcut(ExpressionNode):
    """An expression node that represents shortcut to an expression form.

    Attributes:

        attribute (SchemaObjectReference): Information about an object
            referenced within the specification of another object. An object
            reference typically contains only enough fields to uniquely
            identify the referenced objects.

        form (SchemaObjectReference): Information about an object referenced
            within the specification of another object. An object reference
            typically contains only enough fields to uniquely identify the
            referenced objects.

        data_locale (str): Optional data locale used to select values of the
            form. The format should follow the IETF BCP 47 language tag, for
            example: "en-US".

            Some forms of some attributes may be configured to store
            representation in multiple locales. If a predicate qualifies on a
            form that has been translated in this manner it is likely that the
            elements selected by the predicate will be different for different
            locales. But we do not want the meaning of a filter to vary based
            on the locale preferences of the user executing the filter. So this
            property is used to specify the data locale to be used for the
            qualification. When set it will override the user's personal data
            locale preference.
    """
    _TYPE = NodeType.FORM_SHORTCUT
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'attribute': SchemaObjectReference,
        'form': SchemaObjectReference,
    }

    attribute: SchemaObjectReference
    form: SchemaObjectReference
    data_locale: Optional[str] = None


@dataclass(kw_only=True)
class ExpressionRelationship(ExpressionNode):
    """An expression node that represents expression relationship.

    Attributes:
        level: Within an expression we sometimes need to state at which a
            computation is performed. In some cases the level is obtained by
            examining the execution environment. This object is used if the
            designer wishes to specify an explicit level.

            An explicit level is a list of attributes. Alternatively the client
            may defer selecting an attribute (or attributes) at design time by
            using a prompt instead. If a prompt is used it should be a
            choose-attributes prompt, and it may return any number of
            attributes (including zero).

        guide: An optional object that specifies how to relate the child filter
            with the output filter. There are three options, depending on the
            nature of the guide object:

            - The object may be a logicalTable, in which case the filter is
            projected through this table.

            - The object may be a fact, in which case the filter is projected
            via one of the tables on which the fact is defined.

            - There might not be a guide object at all, in which case the
            filter is projected via the engine's usual join rules (using
            attribute relationships from the system hierarchy).

        is_independent: Flag that indicates whether this child filter will be
            considered independently of other parts of the larger filter:

            - If set to 1 (the default value, used if this property is omitted)
            then this filter will be evaluated by itself.

            - If set to 0 then other parts of the larger filter will be merged
            into this filter. Using this setting could change the value of a
            metric or relationship set qualification that appears within the
            child filter.

        children: List containing the optional root node of the child filter
            expression. We require that a relationship predicate always has a
            child filter is always given, but it is possible that the child
            filter is the empty filter. We model that situation by either
            omitting the children value or by using an empty list.

            This expression is also a filter expression, and it is manipulated
            in the same manner as the rest of the filter. The predicate ids
            that appear within this expression must have disjoint values from
            the predicate ids used in the larger filter. Thus, an individual
            node within this expression can be manipulated by treating it as a
            manipulation of the larger filter in the usual manner.

            We use a list so that this value matches the list value of the
            same name used in an operator node.
    """
    _TYPE = NodeType.RELATIONSHIP
    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'level': [SchemaObjectReference],
        'guide': SchemaObjectReference,
        'is_independent': IsIndependent,
        'children': [ExpressionNode.dispatch],
    }

    level: List[SchemaObjectReference]
    guide: Optional[SchemaObjectReference] = None
    is_independent: IsIndependent = IsIndependent.YES
    children: Optional[List[ExpressionNode]] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        data = super().to_dict()
        result = {'type': data.pop('type'), 'relationship': data}

        return result if camel_case else camel_to_snake(result)

    @classmethod
    def from_dict(
        cls, source: dict, connection: 'Connection' = None, to_snake_case: bool = True
    ) -> 'ExpressionRelationship':
        data = source.get('relationship')
        return super().from_dict(data, connection, to_snake_case)


@dataclass(kw_only=True)
class BandingPredicate(PredicateNode):
    """Base class for banding predicates

    Attributes:
        level: level at which the computation will be performed

        metric: metric for which this banding will be applied

        band_metric_function: function used to slice metric values into bands

        band_names: list of band names, a band name cannot contain "#;" or "#,"
    """

    class BandMetricFunction(AutoName):
        """Enumeration constant used to specify function used to slice
        metric values into bands
        """
        VALUE = auto()
        RANK_DESCEND = auto()
        PERCENTILE_DESCEND = auto()

    _FROM_DICT_MAP = {
        **ExpressionNode._FROM_DICT_MAP,
        'level': [SchemaObjectReference],
        'metric': SchemaObjectReference,
        'band_metric_function': BandMetricFunction,
    }
    level: List[SchemaObjectReference]
    metric: SchemaObjectReference
    band_metric_function: BandMetricFunction

    def _get_banding_common_data(self):
        return {
            'predicate_tree': {
                'level': [item.to_dict() for item in self.level],
                'metric': self.metric.to_dict(),
                'band_metric_function': self.band_metric_function.value,
            },
        }


@dataclass(kw_only=True)
class BandingSizePredicate(BandingPredicate):
    """The Band size type of banding qualification slices a range of metric
    values into a number of bands that appear as rows on a report.

    You define the range by setting the start at and stop at values.
    You also set the step size, which is the size of each band.

    Attributes:
        start: the start of the range
        stop: the end of the range
        size: the size of each band
    """

    _TYPE = NodeType.PREDICATE_BANDING_SIZE
    _FROM_DICT_MAP = {
        **BandingPredicate._FROM_DICT_MAP,
        'start': Variant,
        'stop': Variant,
        'size': Variant,
    }

    start: Variant
    stop: Variant
    size: Variant
    band_names: Optional[List[str]] = None

    def _get_node_data(self):
        result = self._get_banding_common_data()
        result['predicate_tree'].update(
            {
                'start': self.start.to_dict(),
                'stop': self.stop.to_dict(),
                'size': self.size.to_dict(),
                'band_names': self.band_names,
            }
        )

        return result


@dataclass(kw_only=True)
class BandingCountPredicate(BandingPredicate):
    """The Band count type of banding qualification slices a range of metric
    values into a number of equal bands that appear as rows on a report.

    You define the range by setting the start at and stop at values.
    You also set the band count, which is the number of bands to use.

    Attributes:
        start: the start of the range
        stop: the end of the range
        count: number of bands
    """

    _TYPE = NodeType.PREDICATE_BANDING_COUNT
    _FROM_DICT_MAP = {
        **BandingPredicate._FROM_DICT_MAP,
        'start': Variant,
        'stop': Variant,
        'count': Variant,
    }

    start: Variant
    stop: Variant
    count: Variant
    band_names: Optional[List[str]] = None

    def _get_node_data(self):
        result = self._get_banding_common_data()
        result['predicate_tree'].update(
            {
                'start': self.start.to_dict(),
                'stop': self.stop.to_dict(),
                'count': self.count.to_dict(),
                'band_names': self.band_names,
            }
        )

        return result


@dataclass(kw_only=True)
class BandingPointsPredicate(BandingPredicate):
    """The Banding points type of banding qualification slices a range of metric
    values into a number of bands that appear as rows on a report.

    You manually define each band, which allows you to produce bands of varying
    sizes.

    Attributes:
        points: list of number used to slice metric values into bands
    """

    _TYPE = NodeType.PREDICATE_BANDING_POINTS
    points: List[float]
    band_names: Optional[List[str]] = None

    def _get_node_data(self):
        result = self._get_banding_common_data()
        result['predicate_tree'].update({
            'points': self.points,
            'band_names': self.band_names,
        })

        return result


@dataclass(kw_only=True)
class BandingDistinctPredicate(BandingPredicate):
    """The Band for each distinct metric value type of banding qualification
    creates a separate band for each value calculated by the metric. The bands
    appear as rows on a report. This type of banding qualification directly uses
    the results of a metric as bands.

    It is very useful with metrics that already contain the logic needed to
    calculate sequential band numbers. Such metrics use mathematical formulas,
    NTile functions, Band functions, or Case functions.
    """

    _TYPE = NodeType.PREDICATE_BANDING_DISTINCT

    def _get_node_data(self):
        return self._get_banding_common_data()


# Dictionary mapping node types to class representing that node
NODE_TYPE_TO_CLASS_MAP = {
    NodeType.COLUMN_REFERENCE: ColumnReference,
    NodeType.CONSTANT: Constant,
    NodeType.DYNAMIC_DATE_TIME: DynamicDateTime,
    NodeType.FORM_SHORTCUT: ExpressionFormShortcut,
    NodeType.OBJECT_REFERENCE: ObjectReference,
    NodeType.OPERATOR: Operator,
    NodeType.PREDICATE_CUSTOM: CustomExpressionPredicate,
    NodeType.PREDICATE_PROMPT_QUALIFICATION: PromptPredicate,
    NodeType.PREDICATE_METRIC_QUALIFICATION: MetricPredicate,
    NodeType.PREDICATE_RELATIONSHIP: SetFromRelationshipPredicate,
    NodeType.PREDICATE_JOINT_ELEMENT_LIST: JointElementListPredicate,
    NodeType.PREDICATE_ELEMENT_LIST: ElementListPredicate,
    NodeType.PREDICATE_FORM_QUALIFICATION: AttributeFormPredicate,
    NodeType.PREDICATE_FILTER_QUALIFICATION: FilterQualificationPredicate,
    NodeType.PREDICATE_REPORT_QUALIFICATION: ReportQualificationPredicate,
    NodeType.PREDICATE_BANDING_SIZE: BandingSizePredicate,
    NodeType.PREDICATE_BANDING_COUNT: BandingCountPredicate,
    NodeType.PREDICATE_BANDING_POINTS: BandingPointsPredicate,
    NodeType.PREDICATE_BANDING_DISTINCT: BandingDistinctPredicate,
    NodeType.RELATIONSHIP: ExpressionRelationship,
}
