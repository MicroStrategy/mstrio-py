from typing import Dict, List, Optional, TYPE_CHECKING, Union

from mstrio.access_and_security.security_filter import (
    LogicOperator, PredicateElementList, PredicateFilter, PredicateForm, PredicateJointElementList
)
from mstrio.utils.helper import Any, Dictable

if TYPE_CHECKING:
    from mstrio.access_and_security.security_filter import PredicateBase
    from mstrio.connection import Connection


class Qualification(Dictable):
    """The security filter definition written as an expression tree over
    predicate nodes.

    We do not attempt to represent the entire filter using expression nodes.
    Instead we use predicate nodes as leaves of the main tree expression.

    Most predicate nodes use a simple data structure. Security filter support
    five types of predicates, including: `PredicateCustomExpression`,
    `PredicateJointElementList`, `PredicateElementList`, `PredicateForm`,
    `PredicateFilter`. These simple predicates correspond to the most common
    qualifications that are used in security filters. It is possible to combine
    predicates using class `LogicOperator`.

    It is invalid for a security filter expression to contain no nodes.

    Attributes:
        tree (dict): security filter definition written as an expression tree
            over predicate nodes
        text (string): human readable description of the expression. It is
            generated from the current specification of the expression. This
            string will appear similar to a parsable description of the
            expression in the current user's locale. It is intended to be used
            to allow a user to easily distinguish between expressions. But this
            string cannot actually be used as input to a parser session because
            it does not contain hidden information about ambiguities in the
            parse text. Since this representation is not able to fully describe
            an expression, there is no point in the client ever sending it to
            the service.
        tokens (array of dicts):  optional array, used if the expression is to
            be presented as a stream of tokens. When this representation is
            used by the service we would expect that the tokens would either
            completely parse the expression, or would describe an error in the
            parsing. When this representation is used by the client the tokens
            would either correspond to fresh text from the user (a `client`
            token) or to parts of the text that the user has not edited
            (a `parsed` token).
    """
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, tree: Union["LogicOperator", "PredicateBase"], text: Optional[str] = None,
                 tokens: Optional[List[dict]] = None):
        self.tree = tree
        self.text = text
        self.tokens = tokens

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
        tree = source.get("tree")
        tree_type = tree.get("type")
        if tree_type == "predicate_form_qualification":
            tree = PredicateForm.from_dict(tree, connection)
        elif tree_type == "predicate_joint_element_list":
            tree = PredicateJointElementList.from_dict(tree, connection)
        elif tree_type == "predicate_filter_qualification":
            tree = PredicateFilter.from_dict(tree, connection)
        elif tree_type == "predicate_element_list":
            tree = PredicateElementList.from_dict(tree, connection)
        elif tree_type == "operator":
            tree = LogicOperator.from_dict(tree, connection)
        else:
            tree = None
        new_source = source.copy()
        new_source["tree"] = tree
        return super().from_dict(new_source, connection)
