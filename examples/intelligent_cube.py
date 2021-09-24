"""This is the demo script to show how to manage intelligent (OLAP) cubes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.project_objects import OlapCube, list_olap_cubes

# get connection to an environment
base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
connection = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                        login_mode=1)

# list all OLAP Cubes
olap_cubes_ = list_olap_cubes(connection)

# get OLAP Cube by its identifier
olap_cube_ = OlapCube(connection, "<cube_id>")

# list available attributes, metrics and attribute forms which can be used for
# creation of a new OLAP Cube
OlapCube.available_metrics(connection)
OlapCube.available_attributes(connection)

# create new OLAP Cube
attributes = [{
    'id': '8D679D3C11D3E4981000E787EC6DE8A4',
    'name': 'Customer',
    'type': 'attribute',
    'forms': [{
        'id': '8D67A35B11D3E4981000E787EC6DE8A4',
        'name': 'Customer DESC 1',
        'type': 'form'
    }, {
        'id': '8D67A35F11D3E4981000E787EC6DE8A4',
        'name': 'Customer DESC 2',
        'type': 'form'
    }]
}]
metrics = [{'id': '5E2B495C11D66F4BC0006CBEB630224F', 'name': 'Average Sales', 'type': 'metric'}]
new_olap_cube = OlapCube.create(connection, name="New OLAP Cube", description="Some description",
                                folder_id="<folder_id>", attributes=attributes, metrics=metrics)

# Update attributes and metrics of a newly created OLAP Cube. When cube is not
# published yet, then it is possible to add/remove metrics or attributes.
# When cube is published it is possible to only change order of attributes or
# metrics which have already been added to cube.
attributes.append({
    'id': '8D679D3511D3E4981000E787EC6DE8A4',
    'name': 'Call Center',
    'type': 'attribute'
})
metrics.append({
    'id': '785636E5442BBFE1959BE3A708284498',
    'name': 'Count of Samples',
    'type': 'metric'
})
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
