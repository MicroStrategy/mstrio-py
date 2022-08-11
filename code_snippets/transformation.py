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

# Following variables are defining basic transformations
PROJECT_NAME = '<Project_name>'  # Insert name of project here
TRANSFORMATION_NAME = '<Transformation_name>'  # Insert name of edited transformation here
TRANSFORMATION_ID = '<Transformation_ID>'  # Insert ID of transformation here
TRANSFORMATION_NEW_NAME = '<Transformation_name>'  # Insert new name of edited transformation here
TRANSFORMATION_NEW_DESCRIPTION = '<Transformation_desc>'  # Insert new description of edited transformation here
FOLDER_ID = '<Folder_ID>'  # Insert folder ID here

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for, the below placeholder will replace all IDs for
# these code snippets. In actual scripts the OBJECT_ID instances need to be
# replaced with IDs specific to the object used.
OBJECT_ID = '<Object_ID>'

conn = get_connection(workstationData, PROJECT_NAME)

# Example Transformation data
# Parts of this dictionary will be used in the later parts of this demo script
TRANSFORMATION_DATA = {
    'name': 'Demo Transformation',
    'destination_folder': FOLDER_ID,
    'sub_type': ObjectSubType.ROLE_TRANSFORMATION,
    'attributes': [
        TransformationAttribute(
            id="96ED42A511D5B117C000E78A4CC5F24F",
            base_attribute=SchemaObjectReference(
                object_id=OBJECT_ID,
                sub_type=ObjectSubType.ATTRIBUTE,
                name="Day"
            ),
            forms=[
                TransformationAttributeForm(
                    id="45C11FA478E745FEA08D781CEA190FE5",
                    name="ID",
                    lookup_table=SchemaObjectReference(
                        object_id=OBJECT_ID,
                        sub_type=ObjectSubType.LOGICAL_TABLE,
                        name="LU_DAY"
                    ),
                    expression=Expression(
                        tokens=[
                            Token(value='lq_day_date', type='column_reference'),
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
    id='45C11FA478E745FEA08D781CEA190FE5',
    name='ID',
    lookup_table=SchemaObjectReference(
        object_id=OBJECT_ID,
        sub_type=ObjectSubType.LOGICAL_TABLE,
        name='LU_QUARTER'
    ),
    expression=Expression(
        text='ly_quarter_id',
        tokens=[
            Token(value='ly_quarter_id', type='column_reference'),
            Token(value='', type='end_of_text')
        ]
    )
)

# Example TransformationAttribute data
# This object will nbe used in the later parts of this demo script
TRANSFORMATION_ATTRIBUTE = TransformationAttribute(
    id='2437C06311D5BD85C000F98A4CC5F24F',
    base_attribute=SchemaObjectReference(
        object_id=OBJECT_ID,
        sub_type=ObjectSubType.ATTRIBUTE,
        name='Quarter'
    ),
    forms=[
        TransformationAttributeForm(
            id='45C11FA478E745FEA08D781CEA190FE5',
            name='ID',
            lookup_table=SchemaObjectReference(
                object_id=OBJECT_ID,
                sub_type=ObjectSubType.LOGICAL_TABLE,
                name='LU_QUARTER'
            ),
            expression=Expression(
                text='prev_quarter_id',
                tokens=[
                    Token(value='prev_quarter_id', type='column_reference'),
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
list_of_transformations_by_id = list_transformations(connection=conn, id=TRANSFORMATION_ID)
list_of_transformations_as_trees = list_transformations(
    connection=conn, show_expression_as=ExpressionFormat.TREE
)

# List Transformations with expressions as tokens
list_of_transformations_as_tokens = list_transformations(
    connection=conn, show_expression_as=ExpressionFormat.TOKENS
)

# Get specific Transformation by id or name with expression represented as trees
transf = Transformation(connection=conn, id=TRANSFORMATION_ID)
transf = Transformation(connection=conn, name=TRANSFORMATION_NAME)
transf = Transformation(
    connection=conn, name=TRANSFORMATION_NAME, show_expression_as=ExpressionFormat.TREE
)

# Get a Transformation with expression represented as tokens
transf = Transformation(
    connection=conn, name=TRANSFORMATION_NAME, show_expression_as=ExpressionFormat.TOKENS
)

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
