"""This is the demo script to show how to manage user hierachies.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.modeling.schema import (
    ElementDisplayOption, HierarchyAttribute, HierarchyRelationship, SchemaObjectReference,
    SubType, UserHierarchy, UserHierarchySubType, list_user_hierarchies
)

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(
    base_url=base_url,
    username=username,
    password=password,
    project_name="MicroStrategy Tutorial",
    login_mode=1
)

# get a list of user hierarchies
user_hierarchies = list_user_hierarchies(conn)

# create attributes to be added to a user hierarchy
# an attribute can be either an object (HierarchyAttribute) or a dict
attribute1 = HierarchyAttribute(
    object_id='8D679D3511D3E4981000E787EC6DE8A4',
    entry_point=True,
    name='Call Center',
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
)

attribute2 = {
    "objectId": "8D679D3F11D3E4981000E787EC6DE8A4",
    "entryPoint": True,
    "name": "Country",
    "elementDisplayOption": "all_elements"
}

# create SchemaObjectReference objects to be used
# for relationship creation
sor1 = SchemaObjectReference(
    object_id='8D679D3511D3E4981000E787EC6DE8A4',
    sub_type=SubType.ATTRIBUTE
)

sor2 = SchemaObjectReference(
    object_id='8D679D3F11D3E4981000E787EC6DE8A4',
    sub_type=SubType.ATTRIBUTE
)

# create a hierarhcy relationship between two attributes
relationship = HierarchyRelationship(
    parent=sor1,
    child=sor2
)

# create a user hierarchy with subtype `DIMENSION_USER_HIERARCHY`
# and previously created atributes and relationship
new_user_hierarchy = UserHierarchy.create(
    connection=conn,
    name='User Hiararchy name',
    sub_type=UserHierarchySubType.DIMENSION_USER_HIERARCHY,
    attributes=[attribute1, attribute2],
    relationships=[relationship],
    destination_folder_id='98FE182C2A10427EACE0CD30B6768258',
)

# alter a user hierarchy, change it's name, description
# and subtype
new_user_hierarchy.alter(
    name='New name of a user hierarchy',
    description='New description of a user hierarchy',
    sub_type=UserHierarchySubType.DIMENSION_USER,
    use_as_drill_hierarchy=False
)

# define additional attributes
attribute3 = HierarchyAttribute(
    object_id='8D679D3711D3E4981000E787EC6DE8A4',
    entry_point=True,
    name='Category',
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
)

attribute4 = HierarchyAttribute(
    object_id='8D679D4211D3E4981000E787EC6DE8A4',
    entry_point=False,
    name='Item',
    element_display_option=ElementDisplayOption.ALL_ELEMENTS,
    limit=50
)

# add new attributes to a hierarchy
new_user_hierarchy.add_attribute(attribute3)
new_user_hierarchy.add_attribute(attribute4)

# define another relationship (it may be a dict)
relationship = {
    'parent': {
        'objectId': '8D679D3711D3E4981000E787EC6DE8A4',
        'subType': 'attribute'
    },
    'child': {
        'objectId': '8D679D4211D3E4981000E787EC6DE8A4',
        'subType': 'attribute'
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
user_hierarchy_by_name = UserHierarchy(conn, name='New name of a user hierarchy')

# list properties for user hierarchy
user_hierarchy.list_properties()

# Delete a user_hierarchy. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
user_hierarchy.delete(force=True)
