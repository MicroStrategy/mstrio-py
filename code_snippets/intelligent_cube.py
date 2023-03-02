"""This is the demo script to show how to manage intelligent (OLAP) cubes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import list_olap_cubes, OlapCube
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# list all OLAP Cubes
olap_cubes = list_olap_cubes(conn)

# Define a variable which can be later used in a script
CUBE_ID = $cube_id  # id for OlapCube object lookup

# get OLAP Cube by its id
olap_cube = OlapCube(conn, CUBE_ID)

# list available attributes, metrics and attribute forms which can be used for
# creation of a new OLAP Cube
OlapCube.available_metrics(conn)
OlapCube.available_attributes(conn)

# Define variables which can be later used in a script
ATTRIBUTE_ID = $attribute_id
ATTRIBUTE_NAME = $attribute_name
ATTRIBUTE = {'id': ATTRIBUTE_ID, 'name': ATTRIBUTE_NAME, 'type': 'attribute'}
METRIC_ID = $metric_id
METRIC_NAME = $metric_name
METRIC = {'id': METRIC_ID, 'name': METRIC_NAME, 'type': 'metric'}
CUBE_NAME = $cube_name
CUBE_DESCRIPTION = $cube_description
CUBE_FOLDER_ID = $cube_folder_id

# create new OLAP Cube
attributes = [ATTRIBUTE]
metrics = [METRIC]
new_olap_cube = OlapCube.create(
    conn,
    name=CUBE_NAME,
    description=CUBE_DESCRIPTION,
    folder_id=CUBE_FOLDER_ID,
    attributes=attributes,
    metrics=metrics
)

# Update attributes and metrics of a newly created OLAP Cube. When cube is not
# published yet, then it is possible to add/remove metrics or attributes.
# When cube is published it is possible to only change order of attributes or
# metrics which have already been added to cube.
attributes.append(ATTRIBUTE)
metrics.append(METRIC)
new_olap_cube.update(attributes=attributes, metrics=metrics)

# publish newly created and updated OLAP Cube
new_olap_cube.publish()

# refresh and show status of an OLAP Cube
new_olap_cube.refresh_status()
new_olap_cube.show_status()

# export sql view of an OLAP Cube
sql_view = new_olap_cube.export_sql_view()

# unpublish an OLAP Cube
new_olap_cube.unpublish()

# Delete an OLAP Cube. When `force` argument is set to `False` (default value)
# then deletion must be approved.
new_olap_cube.delete(force=True)
