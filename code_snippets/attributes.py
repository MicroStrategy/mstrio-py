"""This is the demo script to show how to manage attributes, attribute forms
and expressions. This script will not work without replacing parameters
with real values. Its basic goal is to present what can be done with
this module and to ease its usage.
"""
from mstrio.connection import get_connection
from mstrio.modeling.schema import (
    Attribute,
    AttributeDisplays,
    AttributeForm,
    AttributeSort,
    AttributeSorts,
    DataType,
    FormReference,
    list_attributes,
    ObjectSubType,
    Relationship,
    SchemaManagement,
    SchemaObjectReference,
    SchemaUpdateType
)
from mstrio.modeling.expression import (
    Expression,
    ExpressionFormat,
    Token,
    ColumnReference,
    Constant,
    Operator,
    FactExpression,
    Variant,
    VariantType,
    Function
)
from mstrio.modeling.schema.table import list_logical_tables, LogicalTable

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for. For the script to work correctly all occurences
# of `'<object_id>'` and others with form `<some_name>` need to be replaced with
# data specific to the object used.

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

conn = get_connection(workstationData, PROJECT_NAME)

# Function list_logical_tables() might be useful to get table information
# needed to create/alter an Attribute.
# Table name and ID will be used in tables[] in ATTRIBUTE_DATA
logical_tables = list_logical_tables(conn)

# Function LogicalTable.list_columns() might be useful to get table columns information
# needed to create/alter an Attribute.
# Column name and ID will be used in expressions[] in ATTRIBUTE_DATA
logical_table = LogicalTable(conn, id='<logical_table_id>')
table_columns = logical_table.list_columns()

# Define a variable which can be later used in a script
FOLDER_ID = $folder_id  # Insert folder ID here

# Example attribute data.
# Parts of this dictionary will be used in the later parts of this demo script
# Many values in this dictionary should be changed to real ones
ATTRIBUTE_DATA = {
    'name': '<attribute_name>',
    'sub_type': ObjectSubType.ATTRIBUTE,
    'destination_folder': FOLDER_ID,
    'forms': [
        AttributeForm.local_create(
            conn,
            name='<attribute_form_name>',
            alias='<alias>',
            category='<category>',
            display_format=AttributeForm.DisplayFormat.DATE,
            data_type=DataType(
                type=DataType.Type.TIME_STAMP,
                precision=8,
                scale=-2147483648,
            ),
            expressions=[
                FactExpression(
                    expression=Expression(
                        tree=ColumnReference(
                            column_name='<column_name>',
                            object_id='<object_id>',
                        ),
                    ),
                    tables=[
                        SchemaObjectReference(
                            name='<table_name>',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<object_id>',
                        ),
                        SchemaObjectReference(
                            name='<table_name>',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<object_id>',
                        ),
                    ],
                ),
            ],
            lookup_table=SchemaObjectReference(
                name='<lookup_table_name>',
                sub_type=ObjectSubType.LOGICAL_TABLE,
                object_id='<object_id>',
            ),
        ),
        AttributeForm.local_create(
            conn,
            name='<attribute_form_name>',
            alias='<alias>',
            category='<cost>',
            display_format=AttributeForm.DisplayFormat.NUMBER,
            data_type=DataType(
                type=DataType.Type.FLOAT,
                precision=8,
                scale=-2147483648,
            ),
            expressions=[
                FactExpression(
                    expression=Expression(
                        tree=ColumnReference(
                            column_name='<column_name>',
                            object_id='<object_id>',
                        ),
                    ),
                    tables=[
                        SchemaObjectReference(
                            name='<table_name>',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<object_id>',
                        )
                    ],
                ),
            ],
            lookup_table=SchemaObjectReference(
                name='<lookup_table_name>',
                sub_type=ObjectSubType.LOGICAL_TABLE,
                object_id='<object_id>',
            ),
        ),
    ],
    'key_form': FormReference(name='<form_name>'),
    'displays': AttributeDisplays(
        report_displays=[FormReference(name='<form_name>')],
        browse_displays=[FormReference(name='<form_name>')],
    ),
    'attribute_lookup_table': SchemaObjectReference(
        name='<attribute_lookup_table_name>',
        sub_type=ObjectSubType.LOGICAL_TABLE,
        object_id='<object_id>',
    ),
}

# Define a variable which can be later used in a script
ATTRIBUTE_NAME = $attribute_name # Insert name of edited attribute here

# Attributes management
# Get list of attributes, with examples of different conditions
# with expressions represented as trees
list_of_all_atrs = list_attributes(connection=conn)
list_of_limited_atrs = list_attributes(connection=conn, limit=10)
list_of_atrs_by_name = list_attributes(connection=conn, name=ATTRIBUTE_NAME)
list_of_atrs_as_trees = list_attributes(conn, show_expression_as=ExpressionFormat.TREE)

# list attributes with expressions represented as tokens
list_of_atrs_as_tokens = list_attributes(conn, show_expression_as=ExpressionFormat.TOKENS)

# Define a variable which can be later used in a script
ATTRIBUTE_ID = $attribute_id  # Insert ID of edited attribute here

# Get specific attribute by id
attr = Attribute(connection=conn, id=ATTRIBUTE_ID)

# Get specific attribute by name
attr = Attribute(connection=conn, name=ATTRIBUTE_NAME)

# Get specific attribute with expression represented as tree (default argument)
attr = Attribute(conn, name=ATTRIBUTE_NAME, show_expression_as=ExpressionFormat.TREE)

# Get an attribute with expression represented as tokens
attr = Attribute(conn, id=ATTRIBUTE_ID, show_expression_as=ExpressionFormat.TOKENS)

# Listing properties
properies = attr.list_properties()

# Create attribute and get it with expression represented as tree.
# Data from constant `ATTRIBUTE_DATA` defined above in the file is used here
attr = Attribute.create(connection=conn, **ATTRIBUTE_DATA)
attr = Attribute.create(
    connection=conn,
    name=ATTRIBUTE_DATA['name'],
    sub_type=ATTRIBUTE_DATA['sub_type'],
    destination_folder=ATTRIBUTE_DATA['destination_folder'],
    forms=ATTRIBUTE_DATA['forms'],
    key_form=ATTRIBUTE_DATA['key_form'],
    displays=ATTRIBUTE_DATA['displays'],
    attribute_lookup_table=ATTRIBUTE_DATA['attribute_lookup_table'],
)
attr = Attribute.create(
    connection=conn, **ATTRIBUTE_DATA, show_expression_as=ExpressionFormat.TREE
)

# Create an attribute and get it with expression represented as tokens
attr = Attribute.create(conn, **ATTRIBUTE_DATA, show_expression_as=ExpressionFormat.TOKENS)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])

# Define variables which can be later used in a script
ATTRIBUTE_NEW_NAME = $attribute_new_name  # Insert new name of edited attribute here
ATTRIBUTE_DESCRIPTION = $attribute_description  # Insert new description of edited attribute here

# Alter attributes
attr.alter(name=ATTRIBUTE_NEW_NAME, description=ATTRIBUTE_DESCRIPTION)

# Get displays and sorts
displays = attr.displays
sorts = attr.sorts

# Alter displays and sorts
attr.alter(
    displays=AttributeDisplays(
        report_displays=[FormReference(name='<form_name>'), FormReference(name='<form_name>')],
        browse_displays=[FormReference(name='<form_name>')],
    )
)
attr.alter(
    sorts=AttributeSorts(
        report_sorts=[
            AttributeSort(FormReference(name='form_name'), ascending=True),
            AttributeSort(FormReference(name='form_name'))
        ],
        browse_sorts=[AttributeSort(FormReference(name='<form_name>'))],
    )
)

# *Relationship management
# Listing relationship candidates
attr_item = Attribute(conn, name=ATTRIBUTE_NAME)
candidates = attr_item.list_relationship_candidates(already_used=False, to_dictionary=True)

# Listing tables
tables = attr_item.list_tables()

TABLE_NAME = $table_name  # Insert table name here


# Select table with given TABLE_NAME from tables
[choosen_table] = [tab for tab in tables if tab.name == TABLE_NAME]

# Get candidates from choosen table
candidate_attrs = candidates[choosen_table.name]

# Add child and parent
relationship_child: SchemaObjectReference = candidate_attrs[0]
relationship_child_1: SchemaObjectReference = candidate_attrs[1]
relationship_parent: SchemaObjectReference = candidate_attrs[2]
relationship_child_table: SchemaObjectReference = choosen_table

attr_item.add_child(
    relationship_child,
    relationship_type=Relationship.RelationshipType.ONE_TO_MANY,
    table=relationship_child_table
)
attr_item.add_child(
    joint_child=[relationship_child, relationship_child_1],
    relationship_type=Relationship.RelationshipType.MANY_TO_MANY,
    table=relationship_child_table
)
attr_item.add_parent(relationship_parent, table=choosen_table)

# Remove child and parent
attr_item.remove_child(relationship_child)
attr_item.remove_child(joint_child=[relationship_child, relationship_child_1])
attr_item.remove_parent(relationship_parent)

# *Attribute forms management
# Add a form to the attribute
attribute_form = AttributeForm.local_create(
    conn,
    name='<attribute_form_name>',
    alias='<alias>',
    category='<category>',
    display_format=AttributeForm.DisplayFormat.NUMBER,
    data_type=DataType(
        type=DataType.Type.FLOAT,
        precision=8,
        scale=-2147483648,
    ),
    expressions=[
        FactExpression(
            expression=Expression(
                tree=ColumnReference(
                    column_name='<column_name>',
                    object_id='<object_id>',
                ),
            ),
            tables=[
                SchemaObjectReference(
                    name='<table_name>',
                    sub_type=ObjectSubType.LOGICAL_TABLE,
                    object_id='<object_id>',
                )
            ],
        ),
    ],
    lookup_table=SchemaObjectReference(
        name='<lookup_table_name>',
        sub_type=ObjectSubType.LOGICAL_TABLE,
        object_id='<object_id>',
    ),
)

attr.add_form(form=attribute_form)

ATTRIBUTE_FORM_NAME = $attribute_form_name  # Insert attribute form name here


# Get form with specified id. This retrieves the form from the local
# Attribute object, not from the server
attr_form = attr.get_form(name=ATTRIBUTE_FORM_NAME)

ATTRIBUTE_FORM_ALTERED_NAME = $attribute_form_altered_name  # Insert altered attribute form name here
ATTRIBUTE_FORM_DESCRIPTION = $attribute_form_description  # Insert altered attribute form description here

# Alter form
attr.alter_form(
    form_id=attr_form.id, name=ATTRIBUTE_FORM_ALTERED_NAME, description=ATTRIBUTE_FORM_DESCRIPTION
)
attr.alter_form(form_id=attr_form.id, name=ATTRIBUTE_FORM_ALTERED_NAME)

# Removing form with specified id
attr.remove_form(form_id=attr_form.id)

# *AttributeForm's expression management
# Add a fact expression to the attribute form

# create a fact expression with expression specified as tokens
fact_expression = FactExpression(
    expression=Expression(
        tokens=[
            Token(
                type=Token.Type.COLUMN_REFERENCE,
                value='<value>',
                target=SchemaObjectReference(
                    object_id='<object_id>',
                    name='<target_name>',
                    sub_type=ObjectSubType.COLUMN,
                ),
                level=Token.Level.RESOLVED,
                state=Token.State.INITIAL,
            ),
            Token(
                type=Token.Type.END_OF_TEXT,
                value='',
                level=Token.Level.RESOLVED,
                state=Token.State.INITIAL,
            ),
        ],
    ),
    tables=[
        SchemaObjectReference(
            name='<table_name>',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<object_id>',
        ),
        SchemaObjectReference(
            name='<table_name>',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<object_id>',
        ),
    ],
)

# create a fact expression with expression specified as tree
fact_expression = FactExpression(
    expression=Expression(
        tree=ColumnReference(
            column_name='<column_name>',
            object_id='<object_id>',
        ),
    ),
    tables=[
        SchemaObjectReference(
            name='<table_name>',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<object_id>',
        ),
    ],
)

# Add new fact expression to a form
form = attr.get_form(name=ATTRIBUTE_FORM_ALTERED_NAME)
attr.add_fact_expression(form_id=form.id, expression=fact_expression)

# Create a new expression locally using tree format
new_expression = Expression(
    tree=Operator(
        function=Function.ADD,
        children=[
            ColumnReference(
                column_name='<column_name>',
                object_id='<object_id>',
            ),
            Constant(variant=Variant(VariantType.INT32, '1')),
        ],
    ),
)

attr_form = attr.get_form(name=ATTRIBUTE_FORM_ALTERED_NAME)

# Get a fact expression from form by using form name
fact_expression, *_ = [f for f in attr_form.expressions if f.expression.text == 'DAY_DATE']

# Alter the fact expression
attr.alter_fact_expression(
    form_id=attr_form.id, fact_expression_id=fact_expression.id, expression=new_expression
)

# Remove the fact expression from the the attribute form
attr_form = attr.get_form(name=ATTRIBUTE_FORM_ALTERED_NAME)
fact_expression, *_ = attr_form.expressions
attr.remove_fact_expression(form_id=form.id, fact_expression_id=fact_expression.id)

# Deleting attributes
attr.delete(force=True)
