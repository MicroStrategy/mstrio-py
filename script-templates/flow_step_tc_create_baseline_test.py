"""
Flow Step Template: Test Center -> Create Baseline Test definition for Comparison Tests
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents Test Center sub-step -> creating baseline test action.

The Script will return BaselineTest ID as string.

`$execute_content` is a list of strings.
Only valid values are "SQL" and "DATA" and at least one is required.

The workflow currently assumes:
- That the connection will be established via `get_connection`
- That the `$execute_content` property will determine the rest of Baseline
    Settings and otherwise defaults will be kept.
"""

from mstrio.connection import get_connection, Connection
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchResultsFormat
from mstrio.object_management.search_operations import SearchObject
from mstrio.server.test_center.baseline import BaselineTest, BaselineTestSettings
from mstrio.types import ObjectTypes

PROJECT_NAME = $project_name

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData, project=PROJECT_NAME)

BT_NAME = $baseline_test_name
SEARCH_IDS = $list_of_search_object_ids or []
FOLDER_IDS = $list_of_folder_ids or []
CONTENT = $execute_content or []

is_sql = "SQL" in CONTENT
is_data = "DATA" in CONTENT

if not is_sql and not is_data:
    raise ValueError(
        "`$execute_content` variable must contain at least 'SQL' or 'DATA' (or both)."
    )

objects = []

for sid in SEARCH_IDS:
    obj = SearchObject(conn, id=sid)
    objects += obj.run(results_format=SearchResultsFormat.LIST)

for fid in FOLDER_IDS:
    obj = Folder(conn, id=fid)
    objects += [
        o
        for o in obj.get_contents(include_subfolders=True)
        if o.type != ObjectTypes.FOLDER
    ]

if not objects:
    raise RuntimeError(
        "Provided SEARCH_IDS and FOLDER_IDS yielded no objects for Baseline creation."
    )

bt = BaselineTest.create(
    connection=conn,
    name=BT_NAME,
    test_objects=objects,
    # Both required and optional properties below are set to their defaults
    # (only reconfigured based on provided minimal parameters). Feel free to
    # change them to your needs. See `BaselineTestSettings` in mstrio-py
    # documentation or source code for more details.
    settings=BaselineTestSettings(
        dashboard_sql_enabled=is_sql,
        dashboard_data_enabled=is_data,
        cube_sql_enabled=is_sql,
        cube_data_enabled=is_data,
        report_sql_enabled=is_sql,
        report_data_enabled=is_data,
        execute_content=CONTENT,
    ),
    execute_sql=is_sql,
    execute_data=is_data,
)


def get_results():
    return bt.id
