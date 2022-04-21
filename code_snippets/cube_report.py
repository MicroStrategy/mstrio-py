"""This is the demo script to show how to import data from OlapCubes and
Reports. It is possible to select attributes, metrics and attribute forms which
is presented.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import OlapCube, Report


# get connection to an environment
from mstrio.connection import get_connection

PROJECT_NAME='<Project_name>' # Insert project name here
CUBE_ID = "<Cube_ID>"
REPORT_ID = "<Report_ID>"
ATTRIBUTES_LIST = ["<Attribute_ID>", "<Attribute_ID>"] #Insert list of attributes that you want to include in  your functions
METRICS_LIST = ["<Metric_ID>"] # insert list of metrics to be used in your functions
ATTRIBUTES_ELEMENTS_LIST=["<Attribute_ID:Element_Name>", "<Attribute_ID:Element_Name>"]

conn = get_connection(workstationData, project_name= PROJECT_NAME)


# get cube based on its id and store it in data frame
my_cube = OlapCube(connection=conn, id=CUBE_ID)
my_cube_df = my_cube.to_dataframe()

# get report based on its id and store it in data frame
my_report = Report(connection=conn, id=REPORT_ID, parallel=False)
my_report_df = my_report.to_dataframe()

# get list of ids of metrics, attributes or attribute elements available within
# Cube or Report
my_cube.metrics
my_cube.attributes
my_cube.attr_elements

# by default all elements are shown in the data frame. To choose elements you
# have to pass proper IDs to function 'apply_filters()' which is available for
# Cube and Report
my_cube.apply_filters(
    attributes=ATTRIBUTES_LIST,
    metrics=METRICS_LIST,
    attr_elements=ATTRIBUTES_ELEMENTS_LIST,
)
# check selected elements which will be placed into a dataframe
my_cube.selected_attributes
my_cube.selected_metrics
my_cube.selected_attr_elements

my_cube_applied_filters_df = my_cube.to_dataframe()

# to exclude specific attribute elements, pass the `operator="NotIn"` to
# `apply_filters()` method
my_cube.apply_filters(
    attributes=ATTRIBUTES_LIST,
    metrics=METRICS_LIST,
    attr_elements=ATTRIBUTES_ELEMENTS_LIST,
    operator="NotIn",
)

my_cube_excluded_elements_df = my_cube.to_dataframe()
