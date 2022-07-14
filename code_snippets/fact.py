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
from workflows.get_all_columns_in_table import list_table_columns

# Following variables are defining basic facts
PROJECT_NAME = '<Project_name>'  # Insert name of project here
FACT_NAME = '<Fact_name>'  # Insert name of existing fact here
FACT_BY_NAME = '<Fact_unique_name>'  # Insert unique name of existing fact here
FACT_ID1 = '<Fact_ID>'  # Insert ID of existing fact here
FACT_ID2 = '<Fact_ID>'  # Insert ID of existing fact here
FACT_NEW_NAME = '<Fact_name>'  # Insert new name of edited Fact here
FACT_NEW_DESC1 = '<Fact_desc>'  # Insert new description of edited fact here
FACT_NEW_DESC2 = '<Fact_desc>'  # Insert new description of edited fact here
FOLDER_ID = '<Folder_ID>'  # Insert folder ID here

conn: Connection = get_connection(workstationData, PROJECT_NAME)

# Example fact data used to create new fact specified as dict
FACT_DATA = {
    'name': 'test_fact',
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
                    'objectId': '<Object_ID>', 'subType': 'logical_table', 'name': 'CITY_MNTH_SLS'
                }, {
                    'objectId': '<Object_ID>', 'subType': 'logical_table', 'name': 'CUSTOMER_SLS'
                }
            ]
        }
    ]
}

# fact expression data with expression specified as tree
FACT_EXP_DATA = FactExpression(
    expression=Expression(tree=ColumnReference(
        column_name='day_date',
        object_id='<Object_ID>',
    )),
    tables=[
        SchemaObjectReference(
            name='LU_DAY',
            sub_type=ObjectSubType.LOGICAL_TABLE,
            object_id='<Object_ID>',
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
list_of_facts_by_name = list_facts(connection=conn, name=FACT_NAME)

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

# Alter fact
test_fact.alter(name=FACT_NEW_NAME, description=FACT_NEW_DESC1)
test_fact.alter(data_type=DATA_TYPE_DATA)

# Delete newly created fact
test_fact.delete(force=True)

# Get specific fact by id with expressions represented as trees
fact = Fact(connection=conn, id=FACT_ID1)

# List all tables for fact
tables_all = fact.get_tables()

# List tables for fact expression
exp_id = fact.expressions[0].id
exp_obj = fact.expressions[0]
tables_exp_id = fact.get_tables(expression=exp_id)
tables_exp_obj = fact.get_tables(expression=exp_obj)

# List fact properties
properties = fact.list_properties()

# Get existing fact by its unique name
fact_by_name = Fact(connection=conn, name=FACT_BY_NAME)

# Get specified fact by id with expressions represented as tokens
fact2 = Fact(connection=conn, id=FACT_ID2, show_expression_as=ExpressionFormat.TOKENS)

# Alter fact description
fact2.alter(description=FACT_NEW_DESC2)
