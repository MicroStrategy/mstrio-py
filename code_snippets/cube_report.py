"""This is the demo script to show how to import data from OlapCubes and
Reports. It is possible to select attributes, metrics and attribute forms which
is presented.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.project_objects import OlapCube, Report
import pandas as pd
import datetime as dt

# get connection to an environment
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Define variables which can be later used in a script
CUBE_ID = $cube_id
REPORT_ID = $report_id

# get cube based on its id and store it in data frame
my_cube = OlapCube(connection=conn, id=CUBE_ID)
my_cube_df = my_cube.to_dataframe()

# if any of your columns should have type 'Time' please set it manually
# Column name should be set to the name of column that should have type 'Time'.
# Please repeat this line for all of the columns that should have type 'Time'.
COLUMN_NAME = $column_name
my_cube_df[COLUMN_NAME] = pd.to_datetime(my_cube_df[COLUMN_NAME], format='%H:%M:%S').dt.time
# If the values in column name are in HH:MM format and not in HH:MM:SS
# you can format it as below
my_cube_df[COLUMN_NAME] = pd.to_datetime(my_cube_df[COLUMN_NAME], format='%H:%M').dt.time

# get report based on its id and store it in data frame
my_report = Report(connection=conn, id=REPORT_ID, parallel=False)
my_report_df = my_report.to_dataframe()

# get list of ids of metrics, attributes or attribute elements available within
# Cube or Report
my_cube.metrics
my_cube.attributes
my_cube.attr_elements

# Define variables which can be later used in a script
ATTRIBUTES_LIST = $attributes_list  # Insert list of attributes that you want to include in  your functions
METRICS_LIST = $metrics_list  # insert list of metrics to be used in your functions
ATTRIBUTES_ELEMENTS_LIST = $attributes_elements_list  # insert list of attributes to be used in your functions

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
