from dataclasses import dataclass
from mstrio.modeling.expression.enums import ExpressionFormat
from mstrio.modeling.schema.attribute.attribute_form import AttributeForm
from mstrio.modeling.schema.helpers import AttributeDisplays, AttributeSorts, FormReference, ObjectSubType, SchemaObjectReference
from mstrio.object_management.folder import Folder


@dataclass
class AttributeData:
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
