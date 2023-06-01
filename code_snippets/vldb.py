"""This is the demo script to show how administrator can manage VLDB settings.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.server import Project
from mstrio.project_objects.datasets import OlapCube
from mstrio.datasources import DatasourceInstance
from mstrio.connection import get_connection

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project to interact with

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Project VLDB settings management
# Get project with a given name
project = Project(connection=conn, name=PROJECT_NAME)

# Define variables which can be later used in a script
PROPERTY_SET = $property_set    # Insert name of property set
GROUP_NAME = $group_name        # Insert name of group
GROUP_ID = $group_id            # Insert ID of group
SETTING_NAME1 = $setting_name1  # Insert name of first VLDB setting
SETTING_NAME2 = $setting_name2  # Insert name of second VLDB setting
SETTING_NAME3 = $setting_name3  # Insert name of third VLDB setting

# Listing VLDB setting properties
vldb_setting_properties = project.vldb_settings[SETTING_NAME1].list_properties()
print(vldb_setting_properties)

# Listing VLDB settings with different conditions
project_settings = project.list_vldb_settings()
print(project_settings)
project_settings_as_dicts = project.list_vldb_settings(to_dictionary=True)
print(project_settings_as_dicts)
project_settings_as_dataframe = project.list_vldb_settings(to_dataframe=True)
print(project_settings_as_dataframe)
project_settings_from_set = project.list_vldb_settings(set_names=[PROPERTY_SET])
print(project_settings_from_set)
project_settings_from_group_by_name = project.list_vldb_settings(groups=[GROUP_NAME])
print(project_settings_from_group_by_name)
project_settings_from_group_by_id = project.list_vldb_settings(groups=[GROUP_ID])
print(project_settings_from_group_by_id)
project_settings_from_names = project.list_vldb_settings(
    names=[SETTING_NAME1, SETTING_NAME2, SETTING_NAME3])
print(project_settings_from_names)

# Define variables which can be later used in a script
SETTING_VALUE1 = $setting_value1  # Insert new value for first VLDB setting
SETTING_VALUE2 = $setting_value2  # Insert new value for second VLDB setting
SETTING_VALUE3 = $setting_value3  # Insert new value for third VLDB setting

# Altering different VLDB settings
project.reset_vldb_settings(force=True)
print(project.vldb_settings[SETTING_NAME1].value)
print(project.vldb_settings[SETTING_NAME2].value)
print(project.vldb_settings[SETTING_NAME3].value)
project.alter_vldb_settings(names_to_values={
    SETTING_NAME1: SETTING_VALUE1,
    SETTING_NAME2: SETTING_VALUE2,
    SETTING_NAME3: SETTING_VALUE3
})
print(project.vldb_settings[SETTING_NAME1].value)
print(project.vldb_settings[SETTING_NAME2].value)
print(project.vldb_settings[SETTING_NAME3].value)

# Reseting VLDB settings with different conditions
# Set values to default for all settings in set
project.reset_vldb_settings(set_names=[PROPERTY_SET])
project_settings_from_set = project.list_vldb_settings(set_names=[PROPERTY_SET])
# Set values to default for all settings in group specified by name
project.reset_vldb_settings(groups=[GROUP_NAME])
project_settings_from_group_by_name = project.list_vldb_settings(groups=[GROUP_NAME])
# Set values to default for all settings in group specified by ID
project_settings_from_group_by_id = project.list_vldb_settings(groups=[GROUP_ID])
# Set values to default for all settings specified by names
project.reset_vldb_settings(names=[SETTING_NAME1, SETTING_NAME2, SETTING_NAME3])
project_settings_from_names = project.list_vldb_settings(
    names=[SETTING_NAME1, SETTING_NAME2, SETTING_NAME3])
print(project.vldb_settings[SETTING_NAME1].value)
print(project.vldb_settings[SETTING_NAME2].value)
print(project.vldb_settings[SETTING_NAME3].value)

# Datasource VLDB settings management

# Define a variable which can be later used in a script
DATASOURCE_NAME = $datasource_name  # Insert name of datasource to interact with

# Get datasource with a given name
datasource = DatasourceInstance(conn, name=DATASOURCE_NAME)

# Listing VLDB settings with different conditions
datasource_settings_as_dicts_from_set = datasource.list_vldb_settings(
    to_dictionary=True, set_names=[PROPERTY_SET])
print(datasource_settings_as_dicts_from_set)
datasource_settings_as_dataframe_from_group = datasource.list_vldb_settings(
    to_dataframe=True, groups=[GROUP_NAME])
print(datasource_settings_as_dataframe_from_group)
datasource_settings_from_names = datasource.list_vldb_settings(
    names=[SETTING_NAME1, SETTING_NAME2])
print(datasource_settings_from_names)

# Altering different VLDB settings
datasource.reset_vldb_settings(force=True)
print(datasource.vldb_settings[SETTING_NAME1].value)
print(datasource.vldb_settings[SETTING_NAME2].value)
datasource.alter_vldb_settings(names_to_values={
    SETTING_NAME1: SETTING_VALUE1,
    SETTING_NAME2: SETTING_VALUE2
})
print(datasource.vldb_settings[SETTING_NAME1].value)
print(datasource.vldb_settings[SETTING_NAME2].value)

# Reseting VLDB settings with different conditions
# Set values to default for all settings in set
datasource.reset_vldb_settings(set_names=[PROPERTY_SET])
# Set values to default for all settings specified by names
datasource.reset_vldb_settings(names=[SETTING_NAME2, SETTING_NAME3])
datasource_settings_from_names = datasource.list_vldb_settings(
    names=[SETTING_NAME1, SETTING_NAME2, SETTING_NAME3])
print(datasource_settings_from_names[SETTING_NAME1].value)
print(datasource_settings_from_names[SETTING_NAME2].value)
print(datasource_settings_from_names[SETTING_NAME3].value)

# OLAP Cube VLDB settings management

# Define a variable which can be later used in a script
CUBE_ID = $cube_id

# Get OLAP Cube based on its ID
olap_cube = OlapCube(connection=conn, id=CUBE_ID)

# Listing VLDB settings with different conditions
cube_settings_from_set = olap_cube.list_vldb_settings(set_names=[PROPERTY_SET])
print(cube_settings_from_set)
cube_settings_as_dicts = olap_cube.list_vldb_settings(to_dictionary=True)
print(cube_settings_as_dicts)
cube_settings_as_dataframe_from_group = olap_cube.list_vldb_settings(
    to_dataframe=True, groups=[GROUP_NAME]
)
print(cube_settings_as_dataframe_from_group)

# Altering different VLDB settings
olap_cube.reset_vldb_settings(force=True)
print(olap_cube.vldb_settings[SETTING_NAME3].value)
olap_cube.alter_vldb_settings(names_to_values={SETTING_NAME3: SETTING_VALUE3})
print(olap_cube.vldb_settings[SETTING_NAME3].value)

# Reseting VLDB settings
# Set values to default for all settings specified by names
olap_cube.reset_vldb_settings(names=[SETTING_NAME3])
cube_settings_from_names = olap_cube.list_vldb_settings(names=[SETTING_NAME3])
print(cube_settings_from_names[SETTING_NAME3].value)
