"""This is the demo script to show how to manage user hierachies.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.modeling.schema import (
    ElementDisplayOption,
    HierarchyAttribute,
    HierarchyRelationship,
    SchemaManagement,
    SchemaObjectReference,
    SchemaUpdateType,
    ObjectSubType,
    UserHierarchy,
    UserHierarchySubType,
    list_user_hierarchies
)

from mstrio.connection import get_connection

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for. For the script to work correctly all occurences
# of `'<object_id>'` and others with form `<some_name>` need to be replaced with
# data specific to the object used.

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# get a list of user hierarchies
user_hierarchies = list_user_hierarchies(conn)

# Define variables which can be later used in a script
ATTRIBUTE_NAME_1 = $attribute_name_1
ATTRIBUTE_NAME_2 = $attribute_name_2
ATTRIBUTE_NAME_3 = $attribute_name_3
ATTRIBUTE_NAME_4 = $attribute_name_4

# create attributes to be added to a user hierarchy
# an attribute can be either an object (HierarchyAttribute) or a dict
attribute1 = HierarchyAttribute(
    object_id='<object_id>',
    entry_point=True,
    name=ATTRIBUTE_NAME_1,
    # see modeling/schema/user_hierarchy/user_hierarchy.py for available options
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
)

# Define a variable which can be later used in a script
# see modeling/schema/user_hierarchy/user_hierarchy.py -
# - ElementDisplayOption class for available options
ELEMENT_DISPLAY_OPTION = $element_display_option

attribute2 = {
    "objectId": '<object_id>',
    "entryPoint": True,
    "name": ATTRIBUTE_NAME_2,
    "elementDisplayOption": ELEMENT_DISPLAY_OPTION
}

# create SchemaObjectReference objects to be used
# for relationship creation
sor1 = SchemaObjectReference(
    object_id='<object_id>',
    sub_type=ObjectSubType.ATTRIBUTE  # see modeling/schema/helpers.py - ObjectSubType class
    # for available options
)

sor2 = SchemaObjectReference(
    object_id='<object_id>',
    sub_type=ObjectSubType.ATTRIBUTE  # see modeling/schema/helpers.py - ObjectSubType class
    # for available options
)

# create a hierarhcy relationship between two attributes
relationship = HierarchyRelationship(parent=sor1, child=sor2)

# Define variables which can be later used in a script
USER_HIERARCHY_NAME = $user_hierarchy_name
FOLDER_ID = $folder_id

# create a user hierarchy with subtype `DIMENSION_USER_HIERARCHY`
# and previously created atributes and relationship
new_user_hierarchy = UserHierarchy.create(
    connection=conn,
    name=USER_HIERARCHY_NAME,
    # see modeling/schema/user_hierarchy/user_hierarchy.py for available options
    sub_type=UserHierarchySubType.DIMENSION_USER_HIERARCHY,
    attributes=[attribute1, attribute2],
    relationships=[relationship],
    destination_folder_id=FOLDER_ID,
)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])

# Define a variable which can be later used in a script
USER_HIERARCHY_DESCRIPTION = $user_hierarchy_description

# alter a user hierarchy, change it's name, description
# and subtype
new_user_hierarchy.alter(
    name=USER_HIERARCHY_NAME,
    description=USER_HIERARCHY_DESCRIPTION,
    # see modeling/schema/user_hierarchy/user_hierarchy.py for available options
    sub_type=UserHierarchySubType.DIMENSION_USER,
    use_as_drill_hierarchy=False
)

# define additional attributes
attribute3 = HierarchyAttribute(
    object_id='<object_id>',
    entry_point=True,
    name=ATTRIBUTE_NAME_3,
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
)

attribute4 = HierarchyAttribute(
    object_id='<object_id>',
    entry_point=False,
    name=ATTRIBUTE_NAME_4,
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
    limit=50
)

# add new attributes to a hierarchy
new_user_hierarchy.add_attribute(attribute3)
new_user_hierarchy.add_attribute(attribute4)

# define another relationship (it may be a dict)
relationship = {
    'parent': {
        'objectId': '<object_id>',
        'subType': ObjectSubType.ATTRIBUTE  # see modeling/schema/helpers.py for available values
    },
    'child': {
        'objectId': '<object_id>',
        'subType': ObjectSubType.ATTRIBUTE  # see modeling/schema/helpers.py for available values
    }
}

# add new relationship to a hierarchy
new_user_hierarchy.add_relationship(relationship)

# remove a relationship from a hierarchy
new_user_hierarchy.remove_relationship(relationship)

# remove an attribute from a hierarchy
new_user_hierarchy.remove_attribute(attribute3)

# get a user hierarchy by ID. User hierarchy can be also found by its name.
user_hierarchy = UserHierarchy(conn, id=new_user_hierarchy.id)
user_hierarchy_by_name = UserHierarchy(conn, name=USER_HIERARCHY_NAME)

# list properties for user hierarchy
user_hierarchy.list_properties()

# Delete a user_hierarchy.
# When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
user_hierarchy.delete(force=True)
