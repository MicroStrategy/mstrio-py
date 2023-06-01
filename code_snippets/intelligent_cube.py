"""This is the demo script to show how to manage intelligent (OLAP) cubes. 

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to ease
its usage.
"""

from mstrio.project_objects import list_olap_cubes, OlapCube
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project to connect to here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Define a variable which can be later used in a script
CUBE_ID = $cube_id  # ID for OLAP Cube object lookup here

# List OLAP Cubes with different conditions
list_of_all_cubes = list_olap_cubes(connection=conn)
print(list_of_all_cubes)
list_of_all_cubes_as_dicts = list_olap_cubes(connection=conn, to_dictionary=True)
print(list_of_all_cubes_as_dicts)
list_of_one_olap_cube = list_olap_cubes(connection=conn, id=CUBE_ID)
print(list_of_one_olap_cube)

# Get OLAP Cube by its ID
olap_cube = OlapCube(conn, CUBE_ID)

# List available attributes, metrics and attribute forms which can be used for
# creation of a new OLAP Cube
OlapCube.available_metrics(conn)
OlapCube.available_attributes(conn)

# Define variables which can be later used in a script
ATTRIBUTE_ID = $attribute_id            # Insert ID of an attribute here
ATTRIBUTE_NAME = $attribute_name        # Insert name of an attribute here
METRIC_ID = $metric_id                  # Insert ID of a metric here
METRIC_NAME = $metric_name              # Insert name of a metric here
CUBE_NAME = $cube_name                  # Insert name of a cube here
CUBE_DESCRIPTION = $cube_description    # Insert description for a cube here
CUBE_FOLDER_ID = $cube_folder_id        # Insert ID for a cube folder here
ATTRIBUTE = {'id': ATTRIBUTE_ID, 'name': ATTRIBUTE_NAME, 'type': 'attribute'}
METRIC = {'id': METRIC_ID, 'name': METRIC_NAME, 'type': 'metric'}

# Create new OLAP Cube with attributes and metrics
attributes = [ATTRIBUTE]
metrics = [METRIC]
new_olap_cube_from_attributes_and_metrics = OlapCube.create(
    conn,
    name=CUBE_NAME,
    description=CUBE_DESCRIPTION,
    folder_id=CUBE_FOLDER_ID,
    attributes=attributes,
    metrics=metrics
)

# Define variables which can be later used in a script
TEMPLATE = $template                        # Insert template here
FILTER_EXPRESSION = $filter_expression      # Insert filter here
CUBE_OPTIONS = $cube_options                # Insert cube options here
ADVANCED_PROPERTIES = $advanced_properties  # Insert advanced properties here
TIME_BASED_SETTINGS = $time_based_settings  # Insert time based settings here

# Create an OLAP Cube with template
new_olap_cube = OlapCube.create(
    connection=conn,
    name=CUBE_NAME,
    folder_id=CUBE_FOLDER_ID,
    description=CUBE_DESCRIPTION,
    template=TEMPLATE,
    filter=FILTER_EXPRESSION,
    options=CUBE_OPTIONS,
    advanced_properties=ADVANCED_PROPERTIES,
    time_based_settings=TIME_BASED_SETTINGS,
)

# Define variables which can be later used in a script
NEW_CUBE_NAME = $new_cube_name                      # Insert new name of cube here
NEW_CUBE_DESCRIPTION = $new_cube_description        # Insert new description for cube here
NEW_CUBE_ABBREVIATION = $new_cube_abbreviation      # Insert new abbreviation for cube here
NEW_TEMPLATE = $new_template                        # Insert new template here
NEW_FILTER_EXPRESSION = $new_filter_expression      # Insert new filter here
NEW_CUBE_OPTIONS = $new_cube_options                # Insert new cube options here
NEW_TIME_BASED_SETTINGS = $new_time_based_settings  # Insert new time based settings here

# Alter an OLAP Cube
new_olap_cube.alter(
    name=NEW_CUBE_NAME,
    description=NEW_CUBE_DESCRIPTION,
    abbreviation=NEW_CUBE_ABBREVIATION,
    template=NEW_TEMPLATE,
    filter=NEW_FILTER_EXPRESSION,
    options=NEW_CUBE_OPTIONS,
    time_based_settings=NEW_TIME_BASED_SETTINGS,
)

# Define variables which can be later used in a script
NEW_ATTRIBUTE_ID = $new_attribute_id
NEW_ATTRIBUTE_NAME = $new_attribute_name
NEW_METRIC_ID = $new_metric_id
NEW_METRIC_NAME = $new_metric_name
NEW_ATTRIBUTE = {'id': NEW_ATTRIBUTE_ID, 'name': NEW_ATTRIBUTE_NAME, 'type': 'attribute'}
NEW_METRIC = {'id': NEW_METRIC_ID, 'name': NEW_METRIC_NAME, 'type': 'metric'}
# Update attributes and metrics of a newly created OLAP Cube. When cube is not
# published yet, then it is possible to add/remove metrics or attributes.
# When cube is published it is possible to only change order of attributes or
# metrics which have already been added to cube.
attributes = [ATTRIBUTE, NEW_ATTRIBUTE]
metrics = [METRIC, NEW_METRIC]
new_olap_cube_from_attributes_and_metrics.update(attributes=attributes, metrics=metrics)
new_olap_cube.update(attributes=attributes, metrics=metrics)

# Set new partition attribute for OLAP Cube by ID
new_olap_cube.set_partition_attribute(ATTRIBUTE_ID)
# Remove partition attribute for OLAP Cube
new_olap_cube.remove_partition_attribute()
# Listing attribute forms for OLAP Cube
attribute_forms = new_olap_cube.list_attribute_forms()

# Publish newly created and updated OLAP Cube
new_olap_cube_from_attributes_and_metrics.publish()
new_olap_cube.publish()

# Refresh and show status of an OLAP Cube
new_olap_cube_from_attributes_and_metrics.refresh_status()
new_olap_cube.refresh_status()
new_olap_cube_from_attributes_and_metrics.show_status()
new_olap_cube.show_status()

# Export sql view of an OLAP Cube
sql_view = new_olap_cube_from_attributes_and_metrics.export_sql_view()
sql_view = new_olap_cube.export_sql_view()

# Unpublish an OLAP Cube
new_olap_cube_from_attributes_and_metrics.unpublish(force=True)
new_olap_cube.unpublish(force=True)

# Delete an OLAP Cube. When `force` argument is set to `False` (default value)
# then deletion must be approved.
new_olap_cube_from_attributes_and_metrics.delete(force=True)
new_olap_cube.delete(force=True)
