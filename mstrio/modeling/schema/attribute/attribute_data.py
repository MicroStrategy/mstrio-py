from dataclasses import dataclass
from mstrio.modeling.expression.enums import ExpressionFormat
from mstrio.modeling.schema.attribute.attribute_form import AttributeForm
from mstrio.modeling.schema.helpers import AttributeDisplays, AttributeSorts, FormReference, ObjectSubType, SchemaObjectReference
from mstrio.object_management.folder import Folder


@dataclass
class AttributeData:
    """Create data object for creating an attribute

    Args:
        name: attribute's name
        sub_type: attribute's sub_type
        destination_folder: A globally unique identifier used to
            distinguish between metadata objects within the same project.
            It is possible for two metadata objects in different projects
            to have the same Object ID.
        forms: attribute's forms list
        key_form: a key form of an attribute
        displays: The collections of attribute displays and browse displays
            of the attribute.
        description: attribute's description
        is_embedded: If true indicates that the target object of this
            reference is embedded within this object. Alternatively if
            this object is itself embedded, then it means that the target
            object is embedded in the same container as this object.
        attribute_lookup_table: Information about an object referenced
            within the  specification of another object. An object reference
            typically contains only enough fields to uniquely identify
            the referenced objects.
        sorts: The collections of attribute sorts and browse sorts
            of the attribute.
        show_expression_as (ExpressionFormat, str): specify how expressions
            should be presented
            Available values:
            - `ExpressionFormat.TREE` or `tree` (default)
            - `ExpressionFormat.TOKENS or `tokens`
        hidden (bool, optional): Specifies whether the object is hidden.
            Default value: False.

    Return:
        HTTP response object. Expected status: 201
    """
    name: str
    sub_type: ObjectSubType | str
    destination_folder: Folder | str
    forms: list[AttributeForm]
    key_form: FormReference
    displays: AttributeDisplays
    description: str | None = None
    is_embedded: bool = False
    attribute_lookup_table: SchemaObjectReference | None = None
    sorts: AttributeSorts | None = None
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE.value
    hidden: bool | None = None
