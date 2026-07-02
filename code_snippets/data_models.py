"""This is the demo script to show how to manage Mosaic data models.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.connection import get_connection
from mstrio.modeling.data_model import (
    DataModel,
    DataModelAttribute,
    DataModelMetric,
    DataModelSecurityFilter,
    DataModelTable,
    DataServeMode,
    RefreshPolicy,
    list_data_model_attributes,
    list_data_model_metrics,
    list_data_model_security_filters,
    list_data_model_tables,
    list_data_models,
)

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert ID of project here

conn = get_connection(connectionData, project_id=PROJECT_ID)

# List data models with different conditions
# Note: data models share the metadata subtype with classic super cubes,
# so classic super cubes may appear in the results as well
list_of_all_dms = list_data_models(connection=conn)
print(list_of_all_dms)
list_of_all_dms_as_dicts = list_data_models(connection=conn, to_dictionary=True)
print(list_of_all_dms_as_dicts)

# Define variables which can be later used in a script
DM_NAME = $dm_name  # Insert name of data model here
FOLDER_ID = $folder_id  # Insert ID of destination folder here

# Create a data model. Servers enforce a minimum committable model: at
# least one table (error 8004e46f), each table with at least one attribute
# or metric (8004e42f), and each attribute with `displays` (8004cf06) —
# so provide `tables` and `attributes` together. In attribute bodies,
# logical tables created in the same call may be referenced by name.
ID_FORM = '45C11FA478E745FEA08D781CEA190FE5'  # universal system ID form
dm = DataModel.create(
    connection=conn,
    name=DM_NAME,
    destination_folder=FOLDER_ID,
    data_serve_mode=DataServeMode.CONNECT_LIVE,
    description='Data model created via mstrio-py',
    tables=[
        {
            'name': $table_name,  # Insert name of logical table here
            'physicalTable': {
                # 'warehouse_partition_table', 'pipeline' or 'freeform_sql'
                'type': $physical_table_type,
                # provide the fields matching the chosen type, e.g. for
                # 'warehouse_partition_table': 'namespace', 'tableName' and
                # 'databaseInstance': {'objectId': $datasource_id}
                'columns': [
                    {
                        'columnName': $column_name,
                        'dataType': {
                            'type': $data_type,  # e.g. 'utf8_char'
                            'precision': $precision,
                            'scale': $scale,
                        },
                    },
                ],
                'information': {'name': $physical_table_name},
            },
        },
    ],
    attributes=[
        {
            'information': {'name': $attribute_name},
            'forms': [
                {
                    'id': ID_FORM,
                    'category': 'ID',
                    'type': 'system',
                    'displayFormat': 'text',
                    'expressions': [
                        {
                            'expression': {
                                'tokens': [
                                    {
                                        'type': 'column_reference',
                                        'value': $column_name,
                                    },
                                ],
                            },
                            'tables': [$table_name],  # by-name reference
                        },
                    ],
                    'lookupTable': $table_name,  # by-name reference
                },
            ],
            'keyForm': {'id': ID_FORM},
            'displays': {
                'reportDisplays': [{'id': ID_FORM}],
                'browseDisplays': [{'id': ID_FORM}],
            },
            'attributeLookupTable': $table_name,  # by-name reference
        },
    ],
)

# Define a variable which can be later used in a script
DM_ID = $dm_id  # Insert ID of data model here

# Get a data model by its id or name
dm = DataModel(connection=conn, id=DM_ID)
dm = DataModel(connection=conn, name=DM_NAME)

# Define variables which can be later used in a script
DM_NAME_ALTERED = $dm_name_altered
DM_DESCRIPTION_ALTERED = $dm_description_altered

# Alter a data model
dm.alter(
    name=DM_NAME_ALTERED,
    description=DM_DESCRIPTION_ALTERED,
    data_serve_mode=DataServeMode.IN_MEMORY,
)

# Define variables which can be later used in a script
TABLE_NAME = $table_name
NAMESPACE = $namespace  # Insert warehouse namespace (schema) here
PHYSICAL_TABLE_NAME = $physical_table_name
DATABASE_INSTANCE_ID = $database_instance_id

# Add a table to a data model based on a warehouse table
# Note: replace warehouse-catalog sentinel dataTypes (precision -1 /
# scale -MIN_INT) in the columns before publishing, otherwise publish
# will silently no-op
table = DataModelTable.create(
    connection=conn,
    data_model=dm,
    name=TABLE_NAME,
    physical_table={
        'type': 'warehouse_partition_table',
        'namespace': NAMESPACE,
        'tableName': PHYSICAL_TABLE_NAME,
        'databaseInstance': {'objectId': DATABASE_INSTANCE_ID},
    },
)

# List tables of a data model
tables = list_data_model_tables(connection=conn, data_model=dm)
tables = dm.list_tables()
print(tables)

# Define variables which can be later used in a script
ATTRIBUTE_NAME = $attribute_name
ATTRIBUTE_FORM = $attribute_form  # Insert form definition dict here

# Create an attribute in a data model
attribute = DataModelAttribute.create(
    connection=conn,
    data_model=dm,
    name=ATTRIBUTE_NAME,
    forms=[ATTRIBUTE_FORM],
)

# List attributes of a data model
attributes = list_data_model_attributes(connection=conn, data_model=dm)
attributes = dm.list_attributes()
print(attributes)

# Manage attribute relationships
# Note: the update is a PUT replacing the ENTIRE relationship list -
# read, modify and send the full list back
relationships = attribute.list_relationships()
attribute.update_relationships(relationships)

# List elements of an attribute (runtime endpoint)
elements = attribute.list_elements(limit=10)
print(elements)

# Smart attributes of a data model attribute
smart_attributes = attribute.list_smart_attributes()
smart_attribute_templates = attribute.list_smart_attribute_templates()
# Passing None regenerates the service-managed smart attributes
attribute.update_smart_attributes()

# Define variables which can be later used in a script
METRIC_NAME = $metric_name
METRIC_EXPRESSION = $metric_expression  # Insert expression dict here

# Create a metric in a data model
metric = DataModelMetric.create(
    connection=conn,
    data_model=dm,
    name=METRIC_NAME,
    expression=METRIC_EXPRESSION,
)

# List metrics and fact metrics of a data model
metrics = list_data_model_metrics(connection=conn, data_model=dm)
fact_metrics = dm.list_fact_metrics()
print(metrics)
print(fact_metrics)

# Publish a data model and wait for completion
# Note: publish is a 3-step flow (instance -> publish -> status poll);
# success is reported only when every table reaches the 'loaded' status
status = dm.publish(refresh_policy=RefreshPolicy.REPLACE)
print(status)

# Publish without waiting and poll manually
instance_id = dm.publish(await_completion=False)
status = dm.get_publish_status(instance_id)
print(status)

# Define variables which can be later used in a script
SF_NAME = $sf_name
SF_QUALIFICATION = $sf_qualification  # Insert qualification tree dict here
USER_ID = $user_id

# Create a security filter in a data model and assign members
security_filter = DataModelSecurityFilter.create(
    connection=conn,
    data_model=dm,
    name=SF_NAME,
    qualification=SF_QUALIFICATION,
)
security_filters = list_data_model_security_filters(connection=conn, data_model=dm)
security_filter.add_members([USER_ID])
members = security_filter.list_members()
print(members)
security_filter.remove_members([USER_ID])

# Manage folders inside a data model
folder = dm.create_folder(name='Folder created via mstrio-py')
folders = dm.list_folders()
dm.delete_folder(folder_id=folder.id)

# Manage object ACLs and translations inside a data model
# Note: the ACL update is a wholesale replacement; 255 is the magic
# "Full Control" rights mask
acl = dm.get_object_acl(object_id=table.id, sub_type='logical_table')
dm.update_object_acl(
    object_id=table.id,
    sub_type='logical_table',
    acl={
        USER_ID: {
            'granted': 255,
            'denied': 0,
            'subType': 'user',
            'inheritable': True,
        }
    },
)

# Export a data model to YAML and restore it
yaml_definition = dm.to_yaml()
dm.to_yaml(path='data_model.yaml')
dm.restore_from_yaml('data_model.yaml')

# Save a data model under a new name
dm_copy = dm.save_as(name='Copy of ' + DM_NAME, destination_folder=FOLDER_ID)

# Delete components and the data model itself without prompt
metric.delete(force=True)
attribute.delete(force=True)
security_filter.delete(force=True)
table.delete(force=True)
dm_copy.delete(force=True)
dm.delete(force=True)
