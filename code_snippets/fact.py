"""This is the sample script to show how to manage schema facts.
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import Connection, get_connection
from mstrio.modeling.expression import (
    ColumnReference, Expression, ExpressionFormat, FactExpression
)
from mstrio.modeling.schema.fact import Fact, list_facts
from mstrio.modeling.schema.helpers import DataType, ObjectSubType
from mstrio.modeling.schema import SchemaManagement, SchemaObjectReference, SchemaUpdateType

# For every object we want to reference using a SchemaObjectReference we need
# to provide an Object ID for. For the script to work correctly all occurences
# of `'<object_id>'` and others with form `<some_name>` need to be replaced with
# data specific to the object used.

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project here

conn: Connection = get_connection(workstationData, PROJECT_NAME)

# Define a variable which can be later used in a script
FOLDER_ID = $folder_id  # Insert folder ID here

# Example of fact data used to create new fact specified as dict
FACT_DATA = {
    'name': '<fact_name>',
    'sub_type': ObjectSubType.FACT,
    'destination_folder': FOLDER_ID,
    'data_type': {
        'type': 'float', 'precision': 8, 'scale': -2147483648
    },
    'expressions': [
        {
            'expression': {
                'tokens': [{
                    'value': 'TOT_DOLLAR_SALES + TOT_COST'
                }]
            },
            'tables': [
                {
                    'objectId': '<object_id>', 'subType': 'logical_table', 'name': '<table_name>'
                },
                {
                    'objectId': '<object_id>', 'subType': 'logical_table', 'name': '<table_name>'
                }
            ]
        }
    ]
}

# fact expression data with expression specified as tree
FACT_EXP_DATA = FactExpression(
    expression=Expression(
        tree=ColumnReference(
            column_name='<column_name>',
            object_id='<object_id>',
        )
    ),
    tables=[
        SchemaObjectReference(
            name='<table_name>',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<object_id>',
        ),
    ],
)

# DataType object used to alter fact's data_type value
DATA_TYPE_DATA = DataType(type='float', precision=6, scale=-2147483648)

# Facts management
# Get list of facts, with examples of different conditions
list_of_all_facts = list_facts(connection=conn)
list_of_limited_facts = list_facts(connection=conn, limit=10)
list_of_limited_facts_to_dict = list_facts(connection=conn, limit=10, to_dictionary=True)

# Define a variable which can be later used in a script
FACT_NAME = $fact_name  # Insert name of existing fact here

list_of_facts_by_name = list_facts(connection=conn, name=FACT_NAME)

# Define a variable which can be later used in a script
FACT_ID = $fact_id  # Insert ID of existing fact here

# Get fact by id with expressions represented as tree (default value)
fact = Fact(connection=conn, id=FACT_ID)

# Get fact by id with expressions represented as tokens
fact = Fact(connection=conn, id=FACT_ID, show_expression_as=ExpressionFormat.TOKENS)

# Get fact by name
fact_by_name = Fact(connection=conn, name=FACT_NAME)

# list of facts with expressions represented as trees
list_of_facts_as_trees = list_facts(connection=conn, show_expression_as=ExpressionFormat.TREE)

# list of facts with expressions respresented as tokens
list_of_facts_as_tokens = list_facts(connection=conn, show_expression_as=ExpressionFormat.TOKENS)

# create new fact
test_fact = Fact.create(
    connection=conn,
    name=FACT_DATA['name'],
    destination_folder=FACT_DATA['destination_folder'],
    expressions=FACT_DATA['expressions'],
    data_type=FACT_DATA['data_type']
)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=conn.project_id)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])

# Add new expression to the fact
test_fact.add_expression(FACT_EXP_DATA)
first_exp_id = test_fact.expressions[0].id

# Remove first expression from the fact
test_fact.remove_expression(first_exp_id)

# Define variables which can be later used in a script
FACT_NEW_NAME = $fact_new_name  # Insert new name of edited Fact here
FACT_NEW_DESCRIPTION = $fact_new_description  # Insert new description of edited fact here

# Alter fact
test_fact.alter(name=FACT_NEW_NAME, description=FACT_NEW_DESCRIPTION)
test_fact.alter(data_type=DATA_TYPE_DATA)

# Delete newly created fact
test_fact.delete(force=True)

# List all tables for fact
tables_all = fact.get_tables()

# List tables for fact expression
exp_id = fact.expressions[0].id
exp_obj = fact.expressions[0]
tables_exp_id = fact.get_tables(expression=exp_id)
tables_exp_obj = fact.get_tables(expression=exp_obj)

# List fact properties
properties = fact.list_properties()
