"""This is the demo script to show how to manage Integrity Tests

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.object_management.object import Object
from mstrio.server.test_center.baseline import (
    Baseline,
    BaselineTest,
    BaselineTestSettings,
    PromptAnswerSource,
    list_baseline_results,
    list_baseline_tests,
)
from mstrio.server.test_center.comparison import (
    ComparisonTest,
    ComparisonTestResult,
    list_comparison_test_results,
    list_comparison_tests,
)

# Define variables which can be later used in a script
BASELINE_TEST_ID = $baseline_test_id
COMPARISON_TEST_ID = $comparison_test_id
SOURCE_BASELINE_TEST_ID = $source_baseline_test_id
TARGET_BASELINE_ID = $target_baseline_id
TARGET_BASELINE_ID_2 = $target_baseline_id_2
TEST_OBJECT_TYPE = $test_object_type
TEST_OBJECT_ID = $test_object_id
BASELINE_TEST_NAME = $baseline_test_name
BASELINE_TEST_NAME_2 = $baseline_test_name_2
COMPARISON_TEST_NAME = $comparison_test_name
COMPARISON_TEST_NAME_2 = $comparison_test_name_2

# Create connection based on connection data
conn = get_connection(connectionData)


#### Baseline Tests

# List all Baseline Tests
baseline_tests = list_baseline_tests(conn)

# Run a Baseline Test. This will create a Baseline (Baseline Test result)
bl_test = BaselineTest(conn, id=BASELINE_TEST_ID)
bl_result: Baseline = bl_test.execute()

# Check status of the Baseline Test result generation
bl_result.fetch()
print("Status:", bl_result.status)

# List test results per object
object_results = bl_result.object_results

# List all Baselines (Baseline Test results)
baseline_results = list_baseline_results(conn)

# Create or alter a Baseline Test
bl_test_2 = BaselineTest.create(
    conn,
    name=BASELINE_TEST_NAME,
    test_objects=[
        # Report, Dashboard etc.
        Object(conn, type=TEST_OBJECT_TYPE, id=TEST_OBJECT_ID),
    ],
)

bl_test_2.alter(
    name=BASELINE_TEST_NAME_2,
    settings=BaselineTestSettings(
        prompt_answer_source_precedence=[
            PromptAnswerSource.DEFAULT_ANSWER,
            PromptAnswerSource.PERSONAL_ANSWER,
        ]
    ),
)


### Comparison Tests

# List all Comparison Tests
comparison_tests = list_comparison_tests(conn)

# Run a Comparison Test. This will create a Comparison (Comparison Test result)
cmp_test = ComparisonTest(conn, id=COMPARISON_TEST_ID)
cmp_result: ComparisonTestResult = cmp_test.execute()

# Check status of the Comparison Test result generation
cmp_result.fetch()
print("Status:", cmp_result.status)

# List test results per object
object_results = bl_result.object_results

# List all Comparisons (Comparison Test results)
comparison_results = list_comparison_test_results(conn)

# Create or alter a Comparison Test
cmp_test_2 = ComparisonTest.create(
    conn,
    name=COMPARISON_TEST_NAME,
    source=BaselineTest(conn, id=SOURCE_BASELINE_TEST_ID),
    target=Baseline(conn, id=TARGET_BASELINE_ID),
)

cmp_test_2.alter(
    name=COMPARISON_TEST_NAME_2,
    target=Baseline(conn, id=TARGET_BASELINE_ID_2),
)