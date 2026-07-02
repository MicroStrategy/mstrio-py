# flake8: noqa
from .attribute_form import AttributeForm
from .relationship import Relationship, RelationshipType
from .smart_attribute import (
    SmartAttribute,
    list_smart_attribute_templates,
    list_smart_attributes,
    update_smart_attributes,
)

# isort: split

# This import has to be at the bottom due to circular import errors
from .attribute import Attribute, list_attributes
