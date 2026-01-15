"""This is the demo script to show how to manage Custom Groups. Its basic goal
is to present what can be done with the CustomGroup class, its related methods
and to ease its usage.

This script will not work without replacing parameters with real values.
"""

from mstrio.connection import get_connection
from mstrio.modeling.expression.enums import Function
from mstrio.modeling.expression.expression import Expression
from mstrio.modeling.expression.expression_nodes import AttributeFormPredicate
from mstrio.modeling.expression.parameters import (
    ConstantParameter,
    Variant,
    VariantType,
)
from mstrio.modeling.custom_group import (
    CustomGroup,
    CustomGroupElement,
    ElementDisplayOption,
    list_custom_groups,
)
from mstrio.modeling.schema.helpers import SchemaObjectReference

# Define variables which can be later used in a script
FOLDER_ID = $folder_id  # ID of the folder where the Custom Group will be created
SOURCE_CUSTOM_GROUP_ID = $source_custom_group_id  # ID of the Custom Group to copy elements from
CUSTOM_GROUP_NAME = $custom_group_name  # Name of the new Custom Group
CUSTOM_GROUP_NAME_UPDATED = $custom_group_name_updated  # Updated name of the Custom Group
QUALIFICATION_EXPRESSION_STRING = $qualification_expr_string  # Qualification expression string for the new element
ELEMENT_NAME_TO_DELETE = $element_name_to_delete  # Name of the element to delete from the Custom Group

# Connect to the Strategy One environment
conn = get_connection(workstationData, project_name="MicroStrategy Tutorial")

# List Custom Groups
listed = list_custom_groups(connection=conn)

source_cg = CustomGroup(conn, id=SOURCE_CUSTOM_GROUP_ID)

# Create Custom Group
new_cg = CustomGroup.create(
    connection=conn,
    name=CUSTOM_GROUP_NAME,
    destination_folder=FOLDER_ID,
    elements=source_cg.elements,
    drill_map_name="Empty Drill Map",
)

# List properties of Custom Group
properties = new_cg.list_properties()
print(properties)

# Alter Custom Group
print("Updating the new Custom Group...")
new_cg.alter(
    name=CUSTOM_GROUP_NAME_UPDATED,
)

# List elements of Custom Group
for element in new_cg.elements:
    print(f" - {element.name} (ID: {element.id})")

# Add element to Custom Group
print("Adding a new element to the Custom Group...")
new_element = new_cg.create_element(
    name="Element 4",
    display=ElementDisplayOption.ELEMENT,
    qualification=QUALIFICATION_EXPRESSION_STRING,
)

# Delete element from Custom Group
element_to_delete = new_cg.get_element(name=ELEMENT_NAME_TO_DELETE)
print(f"Deleting element '{element_to_delete.name}' from the Custom Group...")
new_cg.delete_element(id=element_to_delete.id)

# Delete Custom Group
new_cg.delete(force=True)
