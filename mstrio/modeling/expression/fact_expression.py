from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.helper import Dictable

from .expression import Expression

if TYPE_CHECKING:
    from mstrio.connection import Connection


@dataclass
class FactExpression(Dictable):
    """Object that gives information about an expression that is in use by
    a fact or an attribute.
    Naturally the most important part of a fact expression is the expression.
    This is often just a single column reference, but more complex expressions
    are supported. The object also lists those tables where the expression is
    currently used or where it could be used.

    We say that a table supports a fact if it is possible to compute a value
    for the fact by means of a SELECT expression for each row of the table. The
    expression represents a SELECT expression.

    Args:

        id (str): FactExpression's id, a globally unique identifier used to
        distinguish between metadata objects within the same project.

        expression (Expression): A generic specification for a calculation
        stored within a metadata object. The expression is represented as a
        tree over nodes. Most internal nodes (called operator nodes) are
        defined by applying a function to the operator's child nodes.

        Usually an expression must be non-empty. But in a few cases, most
        notably a filter expression it is valid for an expression to contain no
        nodes at all. An expression is empty if and only if it does not have a
        tree property.

        Alternatively the client may prefer to handle an expression as a list
        of tokens. Each token represents part of the raw text of the
        expression, in some cases annotated with additional information.

        tables (List[SchemaObjectReference]): Array with a member object for
        each logical table that computes a value for this fact by evaluating
        the expression.

        This array should be non-empty for a fact or an attribute that is saved
        into metadata, but may be empty during an edit changeset. The order of
        the tables within the array has no significance.
    """

    _DELETE_NONE_VALUES_RECURSION = False
    _FROM_DICT_MAP = {
        'tables': [SchemaObjectReference],
        'expression': Expression,
    }

    expression: Expression
    tables: List[SchemaObjectReference]
    id: Optional[str] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        result['expressionId'] = result.pop('id', None)

        return result

    @classmethod
    def from_dict(cls, source: dict, connection: Optional['Connection'] = None,
                  to_snake_case: bool = True) -> 'FactExpression':
        data = source.copy()
        data['id'] = data.get('expressionId', None)

        return super().from_dict(data, connection, to_snake_case)

    def local_alter(self, expression: Expression = None,
                    tables: List[SchemaObjectReference] = None):
        if expression:
            self.expression = expression

        if tables:
            self.tables = tables
