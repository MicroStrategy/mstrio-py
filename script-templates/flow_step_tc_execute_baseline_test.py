"""
Flow Step Template: Test Center -> Execute Baseline Test
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents Test Center sub-step -> executing existing baseline test action.

The Script will return Baseline result ID as string.

Either `$baseline_test_id` or `$baseline_test_name` is required.

The workflow currently assumes:
- That the connection will be established via `get_connection`
"""

from mstrio.connection import get_connection, Connection
from mstrio.server.test_center.baseline import BaselineTest

PROJECT_NAME = $project_name

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData, project=PROJECT_NAME)

BT_ID = $baseline_test_id or None
BT_NAME = $baseline_test_name or None

bt = BaselineTest(conn, id=BT_ID, name=BT_NAME)

result = bt.execute()


def get_results():
    return result.id
