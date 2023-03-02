"""This is the demo script to show how to manage transformations, transformation
attributes and transformation attribute forms. Its basic goal is to present what
can be done with this module and to ease its usage.
"""
from mstrio.connection import get_connection
from mstrio.modeling.expression.enums import ExpressionFormat
from mstrio.modeling.expression.expression import Expression, Token
from mstrio.modeling.schema.helpers import ObjectSubType, SchemaObjectReference
from mstrio.modeling.schema.schema_management import SchemaManagement, SchemaUpdateType
from mstrio.modeling.schema.transformation.transformation import (
    list_transformations, Transformation, TransformationAttribute, TransformationAttributeForm
)

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for. For the script to work correctly all occurences
# of `'<object_id>'` and others with form `<some_name>` need to be replaced with
# data specific to the object used.

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn = get_connection(workstationData, PROJECT_NAME)

# Define variables which can be later used in a script
FOLDER_ID = $folder_id  # Insert folder ID here
TRANSFORMATION_NAME = $transformation_name  # Insert name of edited transformation here

# Example of Transformation data
# Parts of this dictionary will be used in the later parts of this demo script
TRANSFORMATION_DATA = {
    'name': TRANSFORMATION_NAME,
    'destination_folder': FOLDER_ID,
    'sub_type': ObjectSubType.ROLE_TRANSFORMATION,
    'attributes': [
        TransformationAttribute(
            id='<object_id>',
            base_attribute=SchemaObjectReference(
                object_id='<object_id>',
                sub_type=ObjectSubType.ATTRIBUTE,
                name="<attribute_name>"
            ),
            forms=[
                TransformationAttributeForm(
                    id='<object_id>',
                    name='<transformation_attribute_form_name>',
                    lookup_table=SchemaObjectReference(
                        object_id='<object_id>',
                        sub_type=ObjectSubType.LOGICAL_TABLE,
                        name='<logical_table_name>'
                    ),
                    expression=Expression(
                        tokens=[
                            Token(value='<token_value>', type='column_reference'),
                            Token(value='', type='end_of_text')
                        ]
                    )
                )
            ]
        )
    ],
    'mapping_type': 'one_to_one'
}

# Example TransformationAttributeForm data
# This object will be used in the later parts of this demo script
TRANSFORMATION_ATTRIBUTE_FORM = TransformationAttributeForm(
    id='<object_id>',
    name='<transformation_attribute_form_name>',
    lookup_table=SchemaObjectReference(
        object_id='<object_id>',
        sub_type=ObjectSubType.LOGICAL_TABLE,
        name='<logical_table_name>'
    ),
    expression=Expression(
        text='<text>',
        tokens=[
            Token(value='<token_value>', type='column_reference'),
            Token(value='', type='end_of_text')
        ]
    )
)

# Example TransformationAttribute data
# This object will nbe used in the later parts of this demo script
TRANSFORMATION_ATTRIBUTE = TransformationAttribute(
    id='<object_id>',
    base_attribute=SchemaObjectReference(
        object_id='<object_id>',
        sub_type=ObjectSubType.ATTRIBUTE,
        name='<attribute_name>'
    ),
    forms=[
        TransformationAttributeForm(
            id='<object_id>',
            name='<transformation_attribute_form_name>',
            lookup_table=SchemaObjectReference(
                object_id='<object_id>',
                sub_type=ObjectSubType.LOGICAL_TABLE,
                name='<logical_table_name>'
            ),
            expression=Expression(
                text='<expression_text>',
                tokens=[
                    Token(value='<token_value>', type='column_reference'),
                    Token(value='', type='end_of_text')
                ]
            )
        )
    ]
)

# Transformation management
# Get list of transformations, with examples of different conditions
# with expressions represented as tree
list_of_all_transformations = list_transformations(connection=conn)
list_of_limited_transformations = list_transformations(connection=conn, limit=5)
list_of_transformations_by_name = list_transformations(connection=conn, name=TRANSFORMATION_NAME)

# Define a variable which can be later used in a script
TRANSFORMATION_ID = $transformation_id  # Insert ID of transformation here

list_of_transformations_by_id = list_transformations(connection=conn, id=TRANSFORMATION_ID)
list_of_transformations_as_trees = list_transformations(
    connection=conn, show_expression_as=ExpressionFormat.TREE
)

# List Transformations with expressions as tokens
list_of_transformations_as_tokens = list_transformations(
    connection=conn, show_expression_as=ExpressionFormat.TOKENS
)

# Get specific Transformation by id with expression represented as trees (default)
transf = Transformation(connection=conn, id=TRANSFORMATION_ID, show_expression_as=ExpressionFormat.TREE)
# Get specific Transformation by id with expression represented as tokens
transf = Transformation(connection=conn, id=TRANSFORMATION_ID, show_expression_as=ExpressionFormat.TOKENS)
# Get specific Transformation by name with expression represented as trees (default)
transf = Transformation(connection=conn, name=TRANSFORMATION_NAME, show_expression_as=ExpressionFormat.TREE)
# Get specific Transformation by name with expression represented as tokens
transf = Transformation(connection=conn, name=TRANSFORMATION_NAME, show_expression_as=ExpressionFormat.TOKENS)

# Listing properties
properties = transf.list_properties()

# Create transformation and get it with expression represented as tree
transf = Transformation.create(connection=conn, **TRANSFORMATION_DATA)
transf = Transformation.create(
    connection=conn,
    sub_type=TRANSFORMATION_DATA['sub_type'],
    name=TRANSFORMATION_DATA['name'],
    destination_folder=TRANSFORMATION_DATA['destination_folder'],
    attributes=TRANSFORMATION_DATA['attributes'],
    mapping_type=TRANSFORMATION_DATA['mapping_type']
)
transf = Transformation.create(
    connection=conn, **TRANSFORMATION_DATA, show_expression_as=ExpressionFormat.TREE
)

# Create transformation and get it with expression represented as tokens
transf = Transformation.create(
    connection=conn, **TRANSFORMATION_DATA, show_expression_as=ExpressionFormat.TOKENS
)

# Define variables which can be later used in a script
TRANSFORMATION_NEW_NAME = $transformation_new_name  # Insert new name of edited transformation here
TRANSFORMATION_NEW_DESCRIPTION = $transformation_new_description  # Insert new description of edited transformation here

# Alter transformations
transf.alter(name=TRANSFORMATION_NEW_NAME)
transf.alter(description=TRANSFORMATION_NEW_DESCRIPTION)

# Alter TransformationAttribute
transf.alter(attributes=[TRANSFORMATION_ATTRIBUTE])

# Alter TransformationAttributeForm
# Each TransformationAttribute can store only one TransformationAttributeForm
attr = transf.attributes[0]
attr.forms = [TRANSFORMATION_ATTRIBUTE_FORM]
transf.alter(attributes=[attr])

# Deleting Transformation
transf.delete(force=True)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])
