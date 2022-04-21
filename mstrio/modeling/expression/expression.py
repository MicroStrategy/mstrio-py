from enum import auto
from typing import List, Optional, Type, TYPE_CHECKING, Union

from mstrio.modeling.schema.helpers import ObjectSubType, SchemaObjectReference
from mstrio.object_management import search_operations
from mstrio.object_management.search_enums import SearchPattern
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import camel_to_snake, delete_none_values, Dictable, snake_to_camel

from .enums import DependenceType, DimtyType, ExpressionType, NodeType

if TYPE_CHECKING:
    from mstrio.connection import Connection

# Add support for keyword-only dataclasses, to enable inheritance of parent
# dataclasses that have attributes with default values
# Keyword-only dataclasses has been added only in python 3.10
# The conditional import below adds support for the same functionality
# for Python 3.9.
# TODO: to be removed when minimal supported version of python is 3.10 or later
import sys

if sys.version_info >= (3, 10):
    from dataclasses import dataclass
else:
    from functools import partial

    from attrs import define

    dataclass = partial(define, slots=False)


@dataclass(kw_only=True)
class ExpressionNode(Dictable):
    """Base class representing a node of an expression tree."""

    _DELETE_NONE_VALUES_RECURSION = False
    _TYPE = None
    _FROM_DICT_MAP = {
        'expression_type': ExpressionType,
        'dimty_type': DimtyType,
        'dependence_type': DependenceType,
    }

    expression_type: Optional[ExpressionType] = None
    dimty_type: Optional[DimtyType] = None
    dependence_type: Optional[DependenceType] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        result['type'] = self._TYPE.value

        return result

    @staticmethod
    def dispatch(source, connection: Optional['Connection'] = None) -> Type['ExpressionNode']:
        """Method dispatching node data to appropriate class that represents
        this type of node.
        """
        data = source.copy()
        node_type = NodeType(data.pop('type'))

        # this import is here due to circular imports issue
        from mstrio.modeling.expression.expression_nodes import NODE_TYPE_TO_CLASS_MAP
        cls = NODE_TYPE_TO_CLASS_MAP[node_type]

        return cls.from_dict(data, connection)


@dataclass
class Token(Dictable):
    """Class representation of a single tokens of an expression.

    Attributes:
        type: Enumeration constant that classifies the text within this token

        value: The raw text represented by a token

        target: If the token represents an object, provide information about
            the object

        level: Describe the amount of processing performed on this parser token

        state: Whether token is in an error or not

        attribute_form: If the token represents an attribute form in the context
           of an object (say City@DESC) then provide attribute form id
    """

    _DELETE_NONE_VALUES_RECURSION = False

    class Type(AutoName):
        """Enumeration constant that classifies the text within a token"""
        END_OF_TEXT = auto()
        ERROR = auto()
        UNKNOWN = auto()
        EMPTY = auto()
        CHARACTER = auto()
        LITERAL = auto()
        IDENTIFIER = auto()
        STRING_LITERAL = auto()
        INTEGER = auto()
        FLOAT = auto()
        BOOLEAN = auto()
        GUID = auto()
        OBJECT_REFERENCE = auto()
        COLUMN_REFERENCE = auto()
        OBJECT_AT_FORM = auto()
        FUNCTION = auto()
        KEYWORD = auto()
        OTHER = auto()
        ELEMENTS = auto()

    class Level(AutoName):
        """Enumeration constant describing the amount of processing performed
        on a parser token
        """
        CLIENT = auto()
        LEXED = auto()
        RESOLVED = auto()
        PARSED = auto()

    class State(AutoName):
        """Enumeration constant describing whether token in an error or not"""
        ERROR = auto()
        INITIAL = auto()
        OKAY = auto()

    _FROM_DICT_MAP = {
        'type': Type,
        'target': SchemaObjectReference,
        'level': Level,
        'state': State,
    }

    value: str
    type: Optional[Type] = None
    target: Optional[SchemaObjectReference] = None
    attribute_form: Optional[str] = None
    level: Optional[Level] = None
    state: Optional[State] = None

    def to_dict(self, camel_case=True) -> dict:
        result = super().to_dict(camel_case=camel_case)
        if self.attribute_form:
            result['attribute_form'] = {
                'object_id': self.attribute_form,
            }

        result = delete_none_values(result, recursion=False)
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(cls, source: dict, connection: Optional['Connection'] = None,
                  to_snake_case: bool = True):
        data = camel_to_snake(source) if to_snake_case else source.copy()

        attribute_form = data.get('attribute_form')
        data['attribute_form'] = attribute_form['object_id'] if attribute_form else None

        return super().from_dict(data, connection, to_snake_case=False)


@dataclass
class Expression(Dictable):
    """Class representation of Expression.

    A generic specification for a calculation stored within a metadata object.
    The expression is represented as a tree over nodes. Most internal nodes
    (called operator nodes) are defined by applying a function to the operator's
    child nodes.

    Usually an expression must be non-empty. But in a few cases, most notably
    a filter expression it is valid for an expression to contain no nodes
    at all. An expression is empty if and only if it does not have a tree
    property.

    Alternatively the client may prefer to handle an expression as a list of
    tokens. Each token represents part of the raw text of the expression,
    in some cases annotated with additional information.

    Attributes:
        text: Read only. Human-readable description of the expression.
            It is generated from the current specification of the expression.

        tokens: Optional list, used if the expression is to be presented as
            a stream of tokens.

        tree: Representation of an expression as a tree of nodes, instance of
            one of classes inheriting from ExpressionNode class
    """

    _DELETE_NONE_VALUES_RECURSION = False

    _FROM_DICT_MAP = {
        'tokens': [Token],
        'tree': ExpressionNode.dispatch,
    }

    text: Optional[str] = None
    tokens: Optional[List[Token]] = None
    tree: Optional[ExpressionNode] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        if self.tree and self.tokens:
            raise ValueError("Expression can have either tree or tokens."
                             "Providing both is not allowed.")

        return super().to_dict(camel_case)

    @classmethod
    def from_dict(cls, source: dict, connection: Optional['Connection'] = None,
                  to_snake_case: bool = True) -> 'Expression':
        result = super().from_dict(source, connection, to_snake_case)
        if not result.tree and not result.tokens:
            raise AttributeError("Attribute: tree or tokens is required for Expressions.")

        return result

    def __repr__(self):
        return f"Expression(text='{self.text}')"


def list_functions(connection: 'Connection', name: Optional[str] = None,
                   to_dictionary: bool = False, limit: Optional[int] = None,
                   **filters) -> Union[List['SchemaObjectReference'], List[dict]]:
    """Get list of SchemaObjectReference objects or dicts representing
    functions. Optionally filter functions by specifying 'name'.

    When attribute is: `function` for Operator node is set to Function.CUSTOM or
    Function.THIRD_PARTY, `custom_function` attribute is required. This function
    give list of SchemaObjectReference object that can be used as values for
    `custom_function`.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): characters that the function name must
            begin with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns SchemaObjectReference objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters:
            id str: Attribute's id
            name str: Attribute's name
            date_created str: format: 2001-01-02T20:48:05.000+0000
            date_modified str: format: 2001-01-02T20:48:05.000+0000
            version str: function's version
            owner dict: e.g. {'id': <user's id>, 'name': <user's name>},
                with one or both of the keys: id, name
            acg str | int: access control group

    Returns:
        list with SchemaObjectReference objects or list of dictionaries
    """
    objects = search_operations.full_search(
        connection,
        object_types=ObjectTypes.FUNCTION,
        project=connection.project_id,
        name=name,
        pattern=SearchPattern.BEGIN_WITH,
        limit=limit,
        **filters,
    )

    if to_dictionary:
        return objects

    objects = [
        {
            **obj,
            'object_id': obj.get('id'),
            'sub_type': ObjectSubType.FUNCTION
                        if obj.get('subtype') == ObjectSubTypes.FUNCTION.value else None,  # noqa
        } for obj in objects
    ]

    return [SchemaObjectReference.from_dict(obj, connection) for obj in objects]
