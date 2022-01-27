"""This is the demo script to show how to import data from OlapCubes and
Reports. It is possible to select attributes, metrics and attribute forms which
is presented.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.project_objects import Report
from mstrio.project_objects.datasets import OlapCube

# get connection to an environment
base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
connection = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                        login_mode=1)

cube_id = "some_cube_id"
report_id = "some_report_id"

# get cube based on its id and store it in data frame
my_cube = OlapCube(connection=connection, id=cube_id)
my_cube_df = my_cube.to_dataframe

# get report based on its id and store it in data frame
my_report = Report(connection=connection, id=report_id, parallel=False)
my_report_df = my_report.to_dataframe

# get list of ids of metrics, attributes or attribue elements available within
# Cube or Report
my_cube.metrics
my_cube.attributes
my_cube.attr_elements

# by default all elements are shown in the data frame. To choose elements you
# have to pass proper IDs to function 'apply_filters()' which is available for
# Cube and Report
my_cube.apply_filters(
    attributes=["A598372E11E9910D1CBF0080EFD54D63", "A59855D811E9910D1CC50080EFD54D63"],
    metrics=["B4054F5411E9910D672E0080EFC5AE5B"],
    attr_elements=[
        "A598372E11E9910D1CBF0080EFD54D63:Los Angeles", "A598372E11E9910D1CBF0080EFD54D63:Seattle"
    ],
)
# check selected elements which will be placed into a dataframe
my_cube.selected_attributes
my_cube.selected_metrics
my_cube.selected_attr_elements

my_cube_applied_filters_df = my_cube.to_dataframe

# to exclude specific attribue elements, pass the `operator="NotIn"` to
# `apply_filters()` method
my_cube.apply_filters(
    attributes=["A598372E11E9910D1CBF0080EFD54D63", "A59855D811E9910D1CC50080EFD54D63"],
    metrics=["B4054F5411E9910D672E0080EFC5AE5B"],
    attr_elements=[
        "A598372E11E9910D1CBF0080EFD54D63:Los Angeles", "A598372E11E9910D1CBF0080EFD54D63:Seattle"
    ],
    operator="NotIn",
)

my_cube_exceluded_elements_df = my_cube.to_dataframe
