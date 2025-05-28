"""Compare VLDB settings of two objects. These objects can be a Dashboard,
DatasourceInstance, Document, IncrementalRefreshReport,Metric, OlapCube,
SuperCube, Project, Report or dictionary of object VLDB settings.
In this script settings were compared for Project, DatasourceInstance, OlapCube
and SuperCube. The function `compare_obj_vldbs` compares the VLDB settings of
two objects and returns keys were difference was spotted. If the `export_file`
parameter is provided, the differences will be exported to a csv file.

1. Connect to the environment.
2. List projects in the environment.
3. Select two projects for comparison.
4. List VLDB settings of the selected projects.
5. Compare VLDB settings of two projects.
6. List datasource instances.
7. Select two datasource instances for comparison.
8. Compare VLDB settings of two datasource instances.
9. List OLAP cubes.
10. Select two OLAP cubes for comparison.
11. Compare VLDB settings of two OLAP cubes.
12. List SuperCubes.
13. Select two SuperCubes for comparison.
14. Compare VLDB settings of two SuperCubes.
"""

import csv
from pprint import pprint

from mstrio.connection import get_connection
from mstrio.datasources import DatasourceInstance, list_datasource_instances
from mstrio.modeling import Metric
from mstrio.project_objects import (
    Dashboard,
    Document,
    IncrementalRefreshReport,
    Report,
)
from mstrio.project_objects.datasets import (
    OlapCube,
    SuperCube,
    list_olap_cubes,
    list_super_cubes,
)
from mstrio.server import Environment, Project


def get_vldb_settings_dict(obj) -> dict:
    """Get VLDB settings dictionary from the object."""
    if isinstance(obj, (Dashboard, Document, SuperCube, Report)):
        return obj.vldb_settings
    elif isinstance(
        obj,
        (DatasourceInstance, IncrementalRefreshReport, Metric, OlapCube, Project),
    ):
        return obj.list_vldb_settings(to_dictionary=True)
    else:
        return obj


def get_differing_part(dict1: dict, dict2: dict) -> dict:
    """Get differing part of two dictionaries."""
    return {k: dict1[k] for k in dict1 if dict1[k] != dict2.get(k)}


def compare_obj_vldbs(
    obj_1: (
        Dashboard
        | DatasourceInstance
        | Document
        | IncrementalRefreshReport
        | Metric
        | OlapCube
        | SuperCube
        | Project
        | Report
        | dict
    ),
    obj_2: (
        Dashboard
        | DatasourceInstance
        | Document
        | IncrementalRefreshReport
        | Metric
        | OlapCube
        | SuperCube
        | Project
        | Report
        | dict
    ),
    verbose: bool = False,
    comparison_level: int = 0,
    export_file: str = None,
) -> list[str]:
    """
    Compare VLDB settings of two objects.
    Args:
        obj_1(Dashboard, DatasourceInstance, Document, IncrementalRefreshReport,
            Metric, OlapCube, SuperCube, Project, Report, dict): First object to
            compare VLDB settings with.
        obj_2(Dashboard, DatasourceInstance, Document, IncrementalRefreshReport,
            Metric, OlapCube, SuperCube, Project, Report, dict): Second object
            to compare VLDB settings with.
        verbose(bool, optional): Controls the verbosity of the output. False by
            default.
        comparison_level(int, optional): Level comparison made inside the
            function. There are three levels:
                0 - for every setting compares only the value under the key
                    'value' and prints/exports if differs
                1 - compares all dict under the key and prints/exports only the
                    part that differs
                2 - compares all dict under the key and prints/exports all info
                    under that key if any difference is found
        export_file(str, optional): Path to a csv file where the differences
        will be exported if provided.

    Returns:
        List of keys with different settings.
    """

    if comparison_level not in [0, 1, 2]:
        comparison_level = 0

    obj_1_vldbs = get_vldb_settings_dict(obj_1)
    obj_2_vldbs = get_vldb_settings_dict(obj_2)

    if obj_1_vldbs.keys() != obj_2_vldbs.keys():
        if verbose:
            print(
                "Provided objects have different VLDB settings keys. Will "
                "compare only common keys."
            )
    else:
        if verbose:
            print("Provided objects have the same VLDB settings keys.")
    common_keys = obj_1_vldbs.keys() & obj_2_vldbs.keys()
    diff_keys = []

    for key in common_keys:
        if comparison_level == 0:
            if obj_1_vldbs[key].get('value') != obj_2_vldbs[key].get('value'):
                diff_keys.append(key)
        else:
            if obj_1_vldbs[key] != obj_2_vldbs[key]:
                diff_keys.append(key)
    if verbose:
        print("Keys with different values:")
        pprint(diff_keys)

    obj_1_header = (
        f'Object 1: {obj_1.name} | {obj_1.id}'
        if not isinstance(obj_1, dict)
        else 'Object 1'
    )

    obj_2_header = (
        f'Object 2: {obj_2.name} | {obj_2.id}'
        if not isinstance(obj_2, dict)
        else 'Object 2'
    )

    for key in diff_keys:
        if verbose:
            print(f"Difference for key '{key}':")
            if comparison_level == 0:
                print(obj_1_header)
                pprint(obj_1_vldbs[key]['value'])
                print(obj_2_header)
                pprint(obj_2_vldbs[key]['value'])
            elif comparison_level == 1:
                print(obj_1_header)
                pprint(get_differing_part(obj_1_vldbs[key], obj_2_vldbs[key]))
                print(obj_2_header)
                pprint(get_differing_part(obj_2_vldbs[key], obj_1_vldbs[key]))
            elif comparison_level == 2:
                print(obj_1_header)
                pprint(obj_1_vldbs[key])
                print(obj_2_header)
                pprint(obj_2_vldbs[key])
            print("\n")

    if export_file:
        with open(export_file, mode='w', newline='') as file:
            file_writer = csv.writer(
                file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            file_writer.writerow(
                [
                    'Key',
                    obj_1_header,
                    obj_2_header,
                ]
            )
            for key in diff_keys:
                if comparison_level == 0:
                    file_writer.writerow(
                        [key, obj_1_vldbs[key]['value'], obj_2_vldbs[key]['value']]
                    )
                elif comparison_level == 1:
                    file_writer.writerow(
                        [
                            key,
                            get_differing_part(obj_1_vldbs[key], obj_2_vldbs[key]),
                            get_differing_part(obj_2_vldbs[key], obj_1_vldbs[key]),
                        ]
                    )
                elif comparison_level == 2:
                    file_writer.writerow([key, obj_1_vldbs[key], obj_2_vldbs[key]])
    return diff_keys


PROJECT_NAME = 'MicroStrategy Tutorial'  # Project to connect to
# Connect to environment without providing user credentials
# Variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Create an environment object
env = Environment(conn)
# List projects in the environment
projects = env.list_projects()

# Select two projects for comparison
project_1 = projects[0]
project_2 = projects[1]

# Compare VLDB settings of two projects
# Define export_file where exported data will be saved. In Workstation you need
# to provide absolute path to the file remembering about double backslashes on
# WIN for example: 'C:\\Users\\admin\\Documents\\data\\projects_vldbs_diff.csv'
FILE_PATH_PROJECT = '<PATH_TO_FILE>'
compare_obj_vldbs(
    project_1,
    project_2,
    verbose=True,
    comparison_level=1,
    export_file=FILE_PATH_PROJECT,
)

# List datasource instances
ds_instances = list_datasource_instances(connection=conn)

# Select two datasource instances for comparison
ds_1 = ds_instances[0]
ds_2 = ds_instances[1]

# Compare VLDB settings of two datasource instances
FILE_PATH_DATASOURCE = '<PATH_TO_FILE>'
compare_obj_vldbs(ds_1, ds_2, comparison_level=2, export_file=FILE_PATH_DATASOURCE)

# List OLAP cubes
olap_cubes = list_olap_cubes(connection=conn)

# Select two OLAP cubes for comparison
olap_cube_1 = olap_cubes[0]
olap_cube_2 = olap_cubes[1]

# Compare VLDB settings of two OLAP cubes
diff_keys = compare_obj_vldbs(olap_cube_1, olap_cube_2, comparison_level=1)
print(diff_keys)

# List SuperCubes
super_cubes = list_super_cubes(connection=conn)

# Select two SuperCubes for comparison
super_cube_1 = super_cubes[0]
super_cube_2 = super_cubes[1]
super_cube_1_vldbs = super_cube_1.vldb_settings

# Compare VLDB settings of two SuperCubes
compare_obj_vldbs(super_cube_1_vldbs, super_cube_2, verbose=True)
