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

from mstrio.connection import get_connection
from mstrio.object_management.folder import Folder
from mstrio.object_management.object import Object
from mstrio.object_management.search_enums import SearchResultsFormat
from mstrio.object_management.search_operations import SearchObject
from mstrio.object_management.shortcut import Shortcut
from mstrio.server.test_center.baseline import (
    BaselineTest,
    BaselineTestSettings,
    is_supported_test_center_object,
)
from mstrio.types import ObjectTypes

PROJECT_NAME = $project_name

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData, project=PROJECT_NAME)

BT_NAME = $baseline_test_name
SEARCH_IDS = $list_of_search_object_ids or []
FOLDER_IDS = $list_of_folder_ids or []
REPORT_IDS = $list_of_report_ids or []
DOCUMENT_IDS = $list_of_document_ids or []
SHORTCUT_IDS = $list_of_shortcut_ids or []
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

for rid in REPORT_IDS:
    objects.append(Object(conn, type=ObjectTypes.REPORT_DEFINITION, id=rid))

for did in DOCUMENT_IDS:
    objects.append(Object(conn, type=ObjectTypes.DOCUMENT_DEFINITION, id=did))

for sid in SHORTCUT_IDS:
    target_info = Shortcut(conn, id=sid).target_info
    target_id = target_info.get("id")
    target_type_value = target_info.get("type")
    if not target_id or target_type_value is None:
        raise ValueError("Shortcut target metadata is incomplete.")
    target_type = ObjectTypes(int(target_type_value))
    objects.append(Object(conn, type=target_type, id=target_id))

supported_objects = {}
unsupported_object_ids = []
for obj in objects:
    if is_supported_test_center_object(obj):
        supported_objects.setdefault(obj.id, obj)
    else:
        unsupported_object_ids.append(str(obj.id))

if unsupported_object_ids:
    print(
        "Skipped objects not supported by Test Center: "
        + ", ".join(unsupported_object_ids)
    )

objects = list(supported_objects.values())

if not objects:
    raise RuntimeError(
        "The provided selections yielded no supported objects for Baseline creation."
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
