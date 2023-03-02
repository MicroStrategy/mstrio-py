"""This is the demo script to show how to manage tables.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
from mstrio.connection import get_connection
from mstrio.datasources.datasource_instance import list_connected_datasource_instances
from mstrio.modeling import DataType, SchemaManagement, SchemaUpdateType
from mstrio.modeling.schema.helpers import (
    ObjectSubType, PhysicalTableType, SchemaObjectReference, TableColumn, TableColumnMergeOption
)
from mstrio.modeling.schema.table import (
    list_logical_tables,
    list_physical_tables,
    list_tables_prefixes,
    list_warehouse_tables,
    LogicalTable,
    PhysicalTable,
)

# Define variables which can be later used in a script
PROJECT_ID = $project_id  # Project ID to connect to
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Get a list of table prefixes
table_prefixes = list_tables_prefixes(connection=conn)
print(table_prefixes)

# Define a variable which can be later used in a script
PHYSICAL_TABLE_PREFIX = $physical_table_prefix  # Insert prefix of the Table here

# Get a list of physical tables
physical_tables = list_physical_tables(connection=conn, project_id=PROJECT_ID)
print(physical_tables)

# Get a list of logical tables
logical_tables = list_logical_tables(connection=conn)
print(logical_tables)

# List connected datasource instances
connected_datasource_instances = list_connected_datasource_instances(connection=conn)
print(connected_datasource_instances)

# Define variables which can be later used in a script
DATASOURCE_ID = $datasource_id
DATASOURCE_NAME = $datasource_name

# List of all available Warehouse Tables
all_warehouse_tables = list_warehouse_tables(connection=conn)
print(all_warehouse_tables)

# Define a variable which can be later used in a script
WAREHOUSE_TABLE_NAME = $warehouse_table_name  # Insert name of the Table here

# List all Warehouse tables with the name WAREHOUSE_TABLE_NAME
lu_item_tables = list_warehouse_tables(connection=conn, name=WAREHOUSE_TABLE_NAME)
print(lu_item_tables)

# List all Warehouse tables from the DATASOURCE_ID datasource
datasource_tables = list_warehouse_tables(connection=conn, datasource_id=DATASOURCE_ID)
print(datasource_tables)

# Get a Warehouse tables with the name WAREHOUSE_TABLE_NAME
# from the specified DATASOURCE_ID
lu_item_table = list_warehouse_tables(
    connection=conn, name=WAREHOUSE_TABLE_NAME, datasource_id=DATASOURCE_ID
)[0]

print(lu_item_table)

# List Warehouse table columns
print(lu_item_table.list_columns())

# List dependent logical tables of a Warehouse Table.
print(lu_item_table.list_dependent_logical_tables())

# Add a Warehouse Table to a project. This will automatically create both a
# logical table object and physical table object on the server

# Define a variable which can be later used in a script
NEW_LOGICAL_TABLE_NAME = $new_logical_table_name  # Insert name of the logical table

logical_table = lu_item_table.add_to_project(logical_table_name=NEW_LOGICAL_TABLE_NAME)
print(logical_table)
print(logical_table.physical_table)  # List a physical table for a logical table defined above

# List logical tables
logical_tables = list_logical_tables(conn)
print(logical_tables)

# Define variables which can be later used in a script
LOGICAL_TABLE_ID = $logical_table_id  # Insert ID of the logical table
LOGICAL_TABLE_NAME = $logical_table_name  # Insert name of the logical table

# These tables can then be retrieved from the server on demand.
# Get logical table by id
logical_table = LogicalTable(connection=conn, id=LOGICAL_TABLE_ID)
print(logical_table)

# Get logical table by name
logical_table = LogicalTable(connection=conn, name=LOGICAL_TABLE_NAME)
print(logical_table)

# List columns of logical table
print(logical_table.list_columns())

# List physical tables in a project
list_physical_tables(conn, project_id=PROJECT_ID)

# Define a variable which can be later used in a script
PHYSICAL_TABLE_ID = $physical_table_id

# Physical table can be retrieved by its id
physical_table = PhysicalTable(connection=conn, id=PHYSICAL_TABLE_ID)
print(physical_table)

# List dependent logical tables of a physical table
print(physical_table.list_dependent_logical_tables())

# Create logical table alias for physical table
LogicalTable.create_alias(connection=conn, id=PHYSICAL_TABLE_ID)

# Define a variable which can be later used in a script
# The variable below is needed when altering or creating a logical table
LOGICAL_TABLE_DESCRIPTION = $logical_table_description  # Insert description of the logical table

# Create logical table of type normal for a physical table
logical_table = LogicalTable.create(
    connection=conn,
    physical_table=PhysicalTable(connection=conn, id=PHYSICAL_TABLE_ID),
    primary_data_source=SchemaObjectReference(
        object_id=DATASOURCE_ID, sub_type=ObjectSubType.DB_ROLE
    ),
    table_name=LOGICAL_TABLE_NAME,
    table_description=LOGICAL_TABLE_DESCRIPTION,
    sub_type=ObjectSubType.LOGICAL_TABLE,
)
print(logical_table)

# Create logical table of type SQL
logical_table = LogicalTable.create(
    connection=conn,
    physical_table_type=PhysicalTableType.SQL,
    columns=[
        TableColumn(
            data_type=DataType(type=DataType.Type.INTEGER, scale="-2147483648", precision="2"),
            column_name="item_id",
        )
    ],
    sql_statement="SELECT item_id FROM inventory_orders",
    primary_data_source=SchemaObjectReference(
        object_id=DATASOURCE_ID, sub_type=ObjectSubType.DB_ROLE
    ),
    table_name=LOGICAL_TABLE_NAME,
    table_description=LOGICAL_TABLE_DESCRIPTION,
)

# Remove all logical tables added for a specific Warehouse Table from a project.
# All dependent tables will be listed before deletion.
lu_item_table.delete_from_project(force=True)

# List all logical tables based on physical tables of type normal
normal_tables = list_logical_tables(connection=conn, table_type=PhysicalTableType.NORMAL)
print(normal_tables)

# Define a variable which can be later used in a script
NORMAL_TABLE_NAME = $normal_table_name

# Get a table by the name
normal_table = LogicalTable(conn, name=NORMAL_TABLE_NAME)
print(normal_table)

# List all logical tables based on physical tables of type SQL
sql_tables = list_logical_tables(connection=conn, table_type=PhysicalTableType.SQL)
print(sql_tables)

# Define a variable which can be later used in a script
SQL_TABLE_NAME = $sql_table_name

# Get a table by the name
sql_table = LogicalTable(conn, name=SQL_TABLE_NAME)
print(sql_table)

# List all logical tables based on physical tables of type warehouse_partition
warehouse_partition_tables = list_logical_tables(
    connection=conn, table_type=PhysicalTableType.WAREHOUSE_PARTITION
)
print(warehouse_partition_tables)

# List properties for the first logical table in a list
print(logical_tables[0].list_properties())

# List properties for the third logical table in a list
print(logical_tables[2].list_properties())

# Remove logical table
logical_tables[0].delete(force=True)

# Alter table

# Define variables which can be later used in a script
# The variable below is needed when altering a logical table
LOGICAL_TABLE_NAME_ALTERED = $logical_table_name_altered  # Insert altered Table name
# Physical Table
PHYSICAL_TABLE_NAME_ALTERED = $physical_table_name_altered  # Insert altered Table name

# Alter logical table based on physical table of type normal
normal_table.alter(name=LOGICAL_TABLE_NAME_ALTERED)  # logical table name
normal_table.alter(is_true_key=True)
normal_table.alter(logical_size=10)
normal_table.alter(is_logical_size_locked=True)
normal_table.alter(physical_table_object_name=PHYSICAL_TABLE_NAME_ALTERED)
normal_table.alter(physical_table_prefix=PHYSICAL_TABLE_PREFIX)

# Alter logical table based on physical table of type SQL
sql_table.alter(name=LOGICAL_TABLE_NAME_ALTERED)  # logical table name
sql_table.alter(is_true_key=True)
sql_table.alter(logical_size=10)
sql_table.alter(is_logical_size_locked=True)
sql_table.alter(enclose_sql_in_parentheses=True)
sql_table.alter(physical_table_object_name=PHYSICAL_TABLE_NAME_ALTERED)

# You cannot alter logical tables based on physical tables of  type warehouse_partition!

# Update structure of physical table of type normal
normal_table.update_physical_table_structure(TableColumnMergeOption.REUSE_ANY)
normal_table.update_physical_table_structure(TableColumnMergeOption.REUSE_COMPATIBLE_DATA_TYPE)
normal_table.update_physical_table_structure(TableColumnMergeOption.REUSE_MATCHED_DATA_TYPE)

# Update structure of physical table of type SQL
sql_table.update_physical_table_structure(TableColumnMergeOption.REUSE_ANY)
sql_table.update_physical_table_structure(TableColumnMergeOption.REUSE_COMPATIBLE_DATA_TYPE)
sql_table.update_physical_table_structure(TableColumnMergeOption.REUSE_MATCHED_DATA_TYPE)

# Delete a physical table.
physical_table.delete(force=True)

# Any changes to a schema objects must be followed by schema_reload
# in order to use them in reports, dossiers and so on
schema_manager = SchemaManagement(connection=conn, project_id=PROJECT_ID)
task = schema_manager.reload(update_types=[SchemaUpdateType.LOGICAL_SIZE])
