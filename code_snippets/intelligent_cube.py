"""This is the demo script to show how to manage intelligent (OLAP) cubes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import list_olap_cubes, OlapCube
from mstrio.connection import get_connection

PROJECT_NAME = '<Project_name>'  # Project to connect to
CUBE_ID = '<Cube_id>'  # id for OlapCube object lookup

# properties for defining a new OlapCube object
ATTRIBUTE = {'id': '<Attribute_ID>', 'name': '<Attribute_name>', 'type': 'attribute'}
METRIC = {'id': '<Metric_ID>', 'name': '<Metric_name>', 'type': 'metric'}
CUBE_NAME = '<Name_of_OLAP_cube>'
CUBE_DESCRIPTION = '<Description_of_OLAP_cube>'
CUBE_FOLDER_ID = '<Folder_id>'

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# list all OLAP Cubes
olap_cubes_ = list_olap_cubes(conn)

# get OLAP Cube by its identifier
olap_cube_ = OlapCube(conn, CUBE_ID)

# list available attributes, metrics and attribute forms which can be used for
# creation of a new OLAP Cube
OlapCube.available_metrics(conn)
OlapCube.available_attributes(conn)

# create new OLAP Cube
attributes = [ATTRIBUTE]
metrics = [METRIC]
new_olap_cube = OlapCube.create(conn, name=CUBE_NAME, description=CUBE_DESCRIPTION,
                                folder_id=CUBE_FOLDER_ID, attributes=attributes, metrics=metrics)

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
