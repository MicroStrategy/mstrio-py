"""
Create a dataframe from a Cube.
List available cubes, retrieve their attributes and metrics. Operate with given
cube.

1. Connect to the environment using data from workstation
2. List available cubes (with limit of 10)
3. Get cube with given id and check its available attributes and metrics
4. Choose attributes and metrics for filtering
5. Publish cube before applying filters
6. Apply filters to the cube specifying attributes and metrics
7. Create a dataframe from the filtered cube
8. Print first few rows of newly created dataframe
"""

from time import sleep
from mstrio.connection import get_connection
from mstrio.project_objects.datasets import list_all_cubes, OlapCube

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
connection = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# List available Cubes (limited to 10)
cubes = list_all_cubes(connection, limit=10)
for cube in cubes:
    print(cube)

# Check available attributes and metrics of a Cube
sample_cube_id = '42FF415D4E162846C87D4FAD8B26BF4E'
sample_cube = OlapCube(connection, id=sample_cube_id)
attributes = sample_cube.attributes
metrics = sample_cube.metrics
print(f"Attributes: {attributes}\nMetrics: {metrics}")

# Choose attributes and metrics
call_center_attribute = attributes[0].get('id')
category_attribute = attributes[1].get('id')

profit_metric = metrics[0].get('id')
profit_margin_metric = metrics[1].get('id')

# Cube needs to be published before we can apply filters
sample_cube.publish()
sleep(5)

# Filter which attributes and metrics to use in a dataframe
sample_cube.apply_filters(
    attributes=[call_center_attribute, category_attribute],
    metrics=[profit_metric, profit_margin_metric],
)

# Create a dataframe from a Cube
dataframe = sample_cube.to_dataframe()
print(dataframe.head())
