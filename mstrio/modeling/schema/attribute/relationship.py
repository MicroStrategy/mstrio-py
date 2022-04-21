from enum import auto
from typing import List, Optional

from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable


class Relationship(Dictable):
    """Python representation of MicroStrategy Attributes Relationship object.

    Attributes:
        parent: parent in a relationship
        child: child in a relationship
        joint_child: list of joint children in a relationship
        relationship_table: relationship table in a relationship
        ralationship_type: type of relationship, one of:
            one_to_many, one_to_one, many_to_many
    """

    _DELETE_NONE_VALUES_RECURSION = True

    class RelationshipType(AutoName):
        """Enumeration constants used to specify type of the relationship"""
        ONE_TO_MANY = auto()
        ONE_TO_ONE = auto()
        MANY_TO_MANY = auto()

    _FROM_DICT_MAP = {
        'parent': SchemaObjectReference.from_dict,
        'child': SchemaObjectReference.from_dict,
        'joint_child': [SchemaObjectReference.from_dict],
        'relationship_table': SchemaObjectReference.from_dict,
        'relationship_type': RelationshipType
    }

    def __init__(self, relationship_type: RelationshipType,
                 relationship_table: SchemaObjectReference, parent: SchemaObjectReference,
                 child: Optional[SchemaObjectReference] = None,
                 joint_child: Optional[List[SchemaObjectReference]] = None) -> None:
        self.relationship_type = relationship_type
        self.relationship_table = relationship_table
        self.parent = parent
        if (child and joint_child) or (child is None and joint_child is None):
            raise AttributeError(
                "Please specify either 'child' or 'joint_child' parameter in the constructor.")
        elif child:
            self.child = child
        elif joint_child:
            self.joint_child = joint_child if isinstance(joint_child, list) else [joint_child]

    def __eq__(self, other):
        if not isinstance(other, Relationship):
            # don't attempt to compare against unrelated types
            return False

        if hasattr(self, 'child') and hasattr(other, 'child'):
            return self.relationship_type == other.relationship_type \
                and self.relationship_table == other.relationship_table \
                and self.parent == other.parent and self.child == other.child
        elif hasattr(self, 'joint_child') and hasattr(other, 'joint_child'):
            return self.relationship_type == other.relationship_type \
                and self.relationship_table == other.relationship_table \
                and self.parent == other.parent and bool(
                    set(self.joint_child).intersection(other.joint_child))
        else:
            return False

    def __repr__(self):
        if hasattr(self, 'child'):
            child_name = self.child.name
        else:
            child_name = "[" + ", ".join(child.name for child in self.joint_child) + "]"
        return f'{self.parent.name} -> {self.relationship_type.name} -> {child_name} relationship'
