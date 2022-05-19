"""This is the demo script to show how to manage attributes, attribute forms
and expressions. This script will not work without replacing parameters
with real values. Its basic goal is to present what can be done with
this module and to ease its usage.
"""
from mstrio.connection import Connection, get_connection
from mstrio.modeling.schema import (Attribute, AttributeDisplays, AttributeForm, AttributeSort,
                                    AttributeSorts, DataType, ExpressionFormat, FormReference,
                                    list_attributes, ObjectSubType, Relationship,
                                    SchemaObjectReference)
from mstrio.modeling.expression import (Expression, Token, ColumnReference, Constant, Operator,
                                        FactExpression, Variant, VariantType, Function)
from workflows.get_all_columns_in_table import list_table_columns

# Following variables are defining basic attributes
PROJECT_NAME = '<Project_name>'  # Insert name of project here
ATTRIBUTE_NAME = '<Attribute_name>'  # Insert name of edited attribute here
ATTRIBUTE_ID = '<Attribute_ID>'  # Insert ID of edited attribute here
ATTRIBUTE_NEW_NAME = '<Attribute_name>'  # Insert new name of edited attribute here
ATTRIBUTE_DESCRIPTION = '<Attribute_desc>'  # Insert new description of edited attribute here
TABLE_NAME = '<Table_name>'  # Insert table name here
ATTRIBUTE_FORM_NAME = '<Attribute_name>'  # Insert attribute form name here
ATTRIBUTE_FORM_ALTERED_NAME = '<Attribute_name>'  # Insert altered attribute form name here
ATTRIBUTE_FORM_DESCRIPTION = '<Attribute_desc>'  # Insert altered attribute form description here
FOLDER_ID = '<Folder_ID>'  # Insert folder ID here

conn = get_connection(workstationData, PROJECT_NAME)

# Function list_table_columns() might be useful to get table columns information
# needed to create/alter an Attribute
table_columns = list_table_columns(conn)

# Example attribute data.
# Parts of this dictionary will be used in the later parts of this demo script
ATTRIBUTE_DATA = {
    'name': 'Demo Attribute',
    'sub_type': ObjectSubType.ATTRIBUTE,
    'destination_folder': FOLDER_ID,
    'forms': [
        AttributeForm.local_create(
            conn,
            name='ID',
            alias='day_date',
            category='ID',
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
                            column_name='day_date',
                            object_id='<Object_ID>',
                        ),),
                    tables=[
                        SchemaObjectReference(
                            name='DAY_CTR_SLS',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<Object_ID>',
                        ),
                        SchemaObjectReference(
                            name='LU_DAY',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<Object_ID>',
                        ),
                    ],
                ),
            ],
            lookup_table=SchemaObjectReference(
                name='LU_DAY',
                sub_type=ObjectSubType.LOGICAL_TABLE,
                object_id='<Object_ID>',
            ),
        ),
        AttributeForm.local_create(
            conn,
            name='COST',
            alias='total_cost',
            category='COST',
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
                            column_name='tot_cost',
                            object_id='<Object_ID>',
                        ),),
                    tables=[
                        SchemaObjectReference(
                            name='DAY_CTR_SLS',
                            sub_type=ObjectSubType.LOGICAL_TABLE,
                            object_id='<Object_ID>',
                        )
                    ],
                ),
            ],
            lookup_table=SchemaObjectReference(
                name='DAY_CTR_SLS',
                sub_type=ObjectSubType.LOGICAL_TABLE,
                object_id='<Object_ID>',
            ),
        ),
    ],
    'key_form': FormReference(name='ID'),
    'displays': AttributeDisplays(
        report_displays=[FormReference(name='ID')],
        browse_displays=[FormReference(name='ID')],
    ),
    'attribute_lookup_table': SchemaObjectReference(
        name='LU_DAY',
        sub_type=ObjectSubType.LOGICAL_TABLE,
        object_id='<Object_ID>',
    ),
}

# Attributes management
# Get list of attributes, with examples of different conditions
# with expressions represented as trees
list_of_all_atrs = list_attributes(connection=conn)
list_of_limited_atrs = list_attributes(connection=conn, limit=10)
list_of_atrs_by_name = list_attributes(connection=conn, name=ATTRIBUTE_NAME)
list_of_atrs_by_id = list_attributes(connection=conn, id=ATTRIBUTE_ID)
list_of_atrs_as_trees = list_attributes(conn, show_expression_as=ExpressionFormat.TREE)

# list attributes with expressions represented as tokens
list_of_atrs_as_tokens = list_attributes(conn, show_expression_as=ExpressionFormat.TOKENS)

# Get specific attribute by id or name with expression represented as trees
attr = Attribute(connection=conn, id=ATTRIBUTE_ID)
attr = Attribute(connection=conn, name=ATTRIBUTE_NAME)
attr = Attribute(conn, name=ATTRIBUTE_NAME, show_expression_as=ExpressionFormat.TREE)

# Get an attribute with expression represented as tokens
attr = Attribute(conn, id=ATTRIBUTE_ID, show_expression_as=ExpressionFormat.TOKENS)

# Listing properties
properies = attr.list_properties()

# Create attribute and get it with expression represented as tree
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
attr = Attribute.create(connection=conn, **ATTRIBUTE_DATA,
                        show_expression_as=ExpressionFormat.TREE)

# Create an attribute and get it with expression represented as tokens
attr = Attribute.create(conn, **ATTRIBUTE_DATA, show_expression_as=ExpressionFormat.TOKENS)

# Alter attributes
attr.alter(name=ATTRIBUTE_NEW_NAME, description=ATTRIBUTE_DESCRIPTION)

# Get displays and sorts
displays = attr.displays
sorts = attr.sorts

# Alter displays and sorts
attr.alter(displays=AttributeDisplays(
    report_displays=[FormReference(
        name='ID'), FormReference(name='COST')],
    browse_displays=[FormReference(name='ID')],
))
attr.alter(sorts=AttributeSorts(
    report_sorts=[
        AttributeSort(FormReference(name='ID'), ascending=True),
        AttributeSort(FormReference(name='COST'))
    ],
    browse_sorts=[AttributeSort(FormReference(name='COST'))],
))

# *Relationship management
# Listing relationship candidates
attr_item = Attribute(conn, name=ATTRIBUTE_NAME)
candidates = attr_item.list_relationship_candidates(already_used=False, to_dictionary=True)

# Listing tables
tables = attr_item.list_tables()

# Select table with given TABLE_NAME from tables
[choosen_table] = [tab for tab in tables if tab.name == TABLE_NAME]

# Get candidates from choosen table
candidate_attrs = candidates[choosen_table.name]

# Add child and parent
relationship_child: SchemaObjectReference = candidate_attrs[0]
relationship_child_1: SchemaObjectReference = candidate_attrs[1]
relationship_parent: SchemaObjectReference = candidate_attrs[2]
relationship_child_table: SchemaObjectReference = choosen_table

attr_item.add_child(relationship_child,
                    relationship_type=Relationship.RelationshipType.ONE_TO_MANY,
                    table=relationship_child_table)
attr_item.add_child(joint_child=[relationship_child, relationship_child_1],
                    relationship_type=Relationship.RelationshipType.MANY_TO_MANY,
                    table=relationship_child_table)
attr_item.add_parent(relationship_parent, table=choosen_table)

# Remove child and parent
attr_item.remove_child(relationship_child)
attr_item.remove_child(joint_child=[relationship_child, relationship_child_1])
attr_item.remove_parent(relationship_parent)

# *Attribute forms management
# Add a form to the attribute
attribute_form = AttributeForm.local_create(
    conn,
    name='SALES',
    alias='tot_unit_sales',
    category='SALES',
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
                    column_name='tot_unit_sales',
                    object_id='<Object_ID>',
                ),),
            tables=[
                SchemaObjectReference(
                    name='DAY_CTR_SLS',
                    sub_type=ObjectSubType.LOGICAL_TABLE,
                    object_id='<Object_ID>',
                )
            ],
        ),
    ],
    lookup_table=SchemaObjectReference(
        name='DAY_CTR_SLS',
        sub_type=ObjectSubType.LOGICAL_TABLE,
        object_id='<Object_ID>',
    ),
)

attr.add_form(form=attribute_form)

# Get form with specified id. This retrieves the form from the local
# Attribute object, not from the server
attr_form = attr.get_form(name=ATTRIBUTE_FORM_NAME)
# Alter form
attr.alter_form(form_id=attr_form.id, name=ATTRIBUTE_FORM_ALTERED_NAME,
                description=ATTRIBUTE_FORM_DESCRIPTION)
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
                value='order_date',
                target=SchemaObjectReference(
                    object_id='<Object_ID>',
                    name='order_date',
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
        ],),
    tables=[
        SchemaObjectReference(
            name='table 1 name',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='table 1 id',
        ),
        SchemaObjectReference(
            name='table 2 name',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='table 2 id',
        ),
    ],
)

# create a fact expression with expression specified as tree
fact_expression = FactExpression(
    expression=Expression(tree=ColumnReference(
        column_name='DAY_DATE',
        object_id='<Object_ID>',
    ),),
    tables=[
        SchemaObjectReference(
            name='LU_DAY',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<Object_ID>',
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
                column_name='ly_date_day',
                object_id='<Object_ID>',
            ),
            Constant(variant=Variant(VariantType.INT32, '1')),
        ],
    ),)

attr_form = attr.get_form(name=ATTRIBUTE_FORM_ALTERED_NAME)

# Get a fact expression from form by using form name
fact_expression, *_ = [f for f in attr_form.expressions if f.expression.text == 'DAY_DATE']

# Alter the fact expression
attr.alter_fact_expression(form_id=attr_form.id, fact_expression_id=fact_expression.id,
                           expression=new_expression)

# Remove the fact expression from the the attribute form
attr_form = attr.get_form(name=ATTRIBUTE_FORM_ALTERED_NAME)
fact_expression, *_ = attr_form.expressions
attr.remove_fact_expression(form_id=form.id, fact_expression_id=fact_expression.id)

# Deleting attributes
attr.delete(force=True)
