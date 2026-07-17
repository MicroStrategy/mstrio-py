"""
Flow Step Template: Test Center -> Create Comparison Test definition
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents Test Center sub-step -> creating comparison test action.

The Script will return ComparisonTest ID as string.

Exactly one of `$source_baseline_result_id`, `$source_baseline_test_id` or
`$source_baseline_test_name` is required.

Analogically, exactly one of `$target_baseline_result_id`, `$target_baseline_test_id`
or `$target_baseline_test_name` is required.

`$compare_content` is a list of strings.
Only valid values are "SQL" and "DATA" and at least one is required.

The workflow currently assumes:
- That the connection will be established via `get_connection`
- That the `$compare_content` property will determine the rest of Comparison
    Settings and otherwise defaults will be kept.
"""

from mstrio.connection import get_connection, Connection
from mstrio.server.test_center.baseline import Baseline, BaselineTest
from mstrio.server.test_center.comparison import ComparisonTest, ComparisonTestSettings

PROJECT_NAME = $project_name

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData, project=PROJECT_NAME)

COMP_NAME = $comparison_test_name

SOURCE_BT_ID = $source_baseline_test_id or None
SOURCE_BT_NAME = $source_baseline_test_name or None
SOURCE_BT_RES_ID = $source_baseline_result_id or None

TARGET_BT_ID = $target_baseline_test_id or None
TARGET_BT_NAME = $target_baseline_test_name or None
TARGET_BT_RES_ID = $target_baseline_result_id or None


def is_set_exactly_one_of(btid: str, btn: str, brid: str) -> bool:
    return bool(btid) + bool(btn) + bool(brid) == 1


if not is_set_exactly_one_of(SOURCE_BT_ID, SOURCE_BT_NAME, SOURCE_BT_RES_ID):
    raise ValueError(
        "Invalid combination of source baseline parameters. "
        "Provide exactly one of `$source_baseline_result_id`, "
        "`$source_baseline_test_id` or `$source_baseline_test_name`."
    )

if not is_set_exactly_one_of(TARGET_BT_ID, TARGET_BT_NAME, TARGET_BT_RES_ID):
    raise ValueError(
        "Invalid combination of target baseline parameters. "
        "Provide exactly one of `$target_baseline_result_id`, "
        "`$target_baseline_test_id` or `$target_baseline_test_name`."
    )

CONTENT = $compare_content or []

is_sql = "SQL" in CONTENT
is_data = "DATA" in CONTENT

if not is_sql and not is_data:
    raise ValueError(
        "`$compare_content` variable must contain at least 'SQL' or 'DATA' (or both)."
    )

SOURCE = (
    Baseline(conn, id=SOURCE_BT_RES_ID)
    if SOURCE_BT_RES_ID
    else BaselineTest(conn, id=SOURCE_BT_ID, name=SOURCE_BT_NAME)
)
TARGET = (
    Baseline(conn, id=TARGET_BT_RES_ID)
    if TARGET_BT_RES_ID
    else BaselineTest(conn, id=TARGET_BT_ID, name=TARGET_BT_NAME)
)

ct = ComparisonTest.create(
    connection=conn,
    name=COMP_NAME,
    source=SOURCE,
    target=TARGET,
    # Both required and optional properties below are set to their defaults
    # (only reconfigured based on provided minimal parameters). Feel free to
    # change them to your needs. See `ComparisonTestSettings` in mstrio-py
    # documentation or source code for more details.
    settings=ComparisonTestSettings(compare_content=CONTENT),
    execute_sql=is_sql,
    execute_data=is_data,
)


def get_results():
    return ct.id
