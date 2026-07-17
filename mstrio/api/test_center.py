from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler

# region baseline tests


@ErrorHandler(err_msg="Error getting Baseline Test objects.")
def get_all_baseline_tests(
    connection: Connection, error_msg: str | None = None
) -> Response:
    """Get all Baseline Test objects.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint="/api/testCenters/integrityTests")


@ErrorHandler(err_msg="Error getting all Baseline Test execution results.")
def get_all_baseline_results(
    connection: Connection, error_msg: str | None = None
) -> Response:
    """Get all baseline execution results for all Baseline Tests.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint="/api/testCenters/integrityTests/baselines")


@ErrorHandler(err_msg="Error getting Baseline Test object with ID: {id}.")
def get_baseline_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get a Baseline Test object by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Baseline Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint=f"/api/testCenters/integrityTests/{id}")


@ErrorHandler(err_msg="Error creating Baseline Test.")
def create_baseline_test(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Create a Baseline Test object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): Dictionary containing Baseline Test definition
        error_msg (str, optional): Custom error message for error handling
    """

    return connection.post(endpoint="/api/testCenters/integrityTests", json=body)


@ErrorHandler(err_msg="Error updating Baseline Test object with ID: {id}.")
def update_baseline_test(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update a Baseline Test object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Baseline Test object
        body (dict): Dictionary containing Baseline Test updates
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.put(endpoint=f"/api/testCenters/integrityTests/{id}", json=body)


@ErrorHandler(err_msg="Error deleting Baseline Test object with ID: {id}.")
def delete_baseline_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a Baseline Test object by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Baseline Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.delete(endpoint=f"/api/testCenters/integrityTests/{id}")


@ErrorHandler(err_msg="Error getting Baseline Test execution results for ID: {id}.")
def get_baseline_results_by_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get all baseline execution results for a Baseline Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Baseline Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint=f"/api/testCenters/integrityTests/{id}/baselines")


@ErrorHandler(err_msg="Error running Baseline Test with ID: {id}.")
def run_baseline_test(
    connection: Connection,
    id: str,
    body: dict | None = None,
    error_msg: str | None = None,
) -> Response:
    """Trigger Baseline Test execution and create a Baseline result.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Baseline Test object
        body (dict, optional): Dictionary containing Baseline Test execution
            parameters.
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint=f"/api/testCenters/integrityTests/{id}/baselines", json=body
    )


@ErrorHandler(err_msg="Error bulk deleting Baseline Test objects.")
def bulk_delete_baseline_tests(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Bulk delete Baseline Test objects.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted payload containing Baseline Test IDs
            to delete
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint="/api/testCenters/integrityTests/bulkDelete", json=body
    )


# endregion

# region baseline results


@ErrorHandler(err_msg="Error getting Baseline Test result with ID: {id}:{test_id}.")
def get_baseline_result(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get Baseline Test result information by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}"
    )


@ErrorHandler(err_msg="Error deleting Baseline Test result with ID: {id}:{test_id}.")
def delete_baseline_result(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a Baseline Test result.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.delete(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}"
    )


@ErrorHandler(
    err_msg="Error canceling Baseline Test execution with ID: {id}:{test_id}."
)
def cancel_baseline_run(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Cancel a Baseline Test execution.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}/cancel"
    )


@ErrorHandler(
    err_msg="Error getting status of Baseline execution with ID: {id}:{test_id}."
)
def get_baseline_result_status(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get the Baseline Test execution status.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}/status"
    )


@ErrorHandler(err_msg="Error getting summary of Baseline with ID: {id}:{test_id}.")
def get_baseline_result_summary(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get the Baseline Test execution summary.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}/summary"
    )


@ErrorHandler(
    err_msg="Error syncing Baseline result with ID: {id}:{test_id} to Storage Service."
)
def sync_baseline_result(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Sync a Baseline result to Storage Service.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        id (str): ID of a Baseline execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/{id}/storageSync"
    )


# endregion

# region baseline result details


@ErrorHandler(err_msg="Error getting object result of Baseline with ID: {id}.")
def get_baseline_object_result(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get Baseline Test execution result of a cube.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}"
    )


@ErrorHandler(err_msg="Error getting object data of Baseline with ID: {id}.")
def get_baseline_object_result_data(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get data captured during Baseline Test execution of a cube.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/data"
    )


@ErrorHandler(err_msg="Error getting object SQL of Baseline with ID: {id}.")
def get_baseline_object_result_sql(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get SQL captured during Baseline Test execution of an object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/sql"
    )


@ErrorHandler(err_msg="Error getting visualization result of Baseline with ID: {id}.")
def get_baseline_visualization_result(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get Baseline Test execution result of a visualization.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        viz_key (str): Visualization key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/visualizations/{viz_key}"
    )


@ErrorHandler(err_msg="Error getting visualization data of Baseline with ID: {id}.")
def get_baseline_visualization_result_data(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get data captured during Baseline Test execution of a visualization.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        viz_key (str): Visualization key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/visualizations/{viz_key}/data"
    )


@ErrorHandler(
    err_msg="Error getting visualization query detail of Baseline with ID: {id}."
)
def get_baseline_visualization_result_query_detail(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get Baseline Test query detail result of a visualization.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        viz_key (str): Visualization key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/visualizations/"
        f"{viz_key}/queryDetail"
    )


@ErrorHandler(err_msg="Error getting visualization SQL of Baseline with ID: {id}.")
def get_baseline_visualization_result_sql(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get SQL captured during Baseline Test execution of a visualization.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Baseline Test object
        result_id (str): ID of a Baseline execution result object
        id (str): ID of a test object baseline
        viz_key (str): Visualization key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityTests/{test_id}/baselines/"
        f"{result_id}/testObjectBaselines/{id}/visualizations/{viz_key}/sql"
    )


@ErrorHandler(err_msg="Error bulk deleting Baseline Test execution results.")
def bulk_delete_baseline_results(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Bulk delete Baseline Test execution results.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted payload containing Baseline result IDs
            to delete
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint="/api/testCenters/integrityTests/baselines/bulkDelete", json=body
    )


# endregion

# region comparison tests


@ErrorHandler(err_msg="Error getting Comparison Test objects.")
def get_all_comparison_tests(
    connection: Connection, error_msg: str | None = None
) -> Response:
    """Get all Comparison Test objects.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint="/api/testCenters/integrityComparisons")


@ErrorHandler(err_msg="Error getting Comparison Test results.")
def get_all_comparison_results(
    connection: Connection, error_msg: str | None = None
) -> Response:
    """Get all comparison run results for all Comparison Tests.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint="/api/testCenters/integrityComparisons/comparisons")


@ErrorHandler(err_msg="Error getting Comparison Test object with ID: {id}.")
def get_comparison_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get a Comparison Test object by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Comparison Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint=f"/api/testCenters/integrityComparisons/{id}")


@ErrorHandler(err_msg="Error creating Comparison Test.")
def create_comparison_test(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Create a Comparison Test object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): Dictionary containing Comparison Test definition.
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(endpoint="/api/testCenters/integrityComparisons", json=body)


@ErrorHandler(err_msg="Error updating Comparison Test object with ID: {id}.")
def update_comparison_test(
    connection: Connection,
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Update a Comparison Test object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Comparison Test object
        body (dict): Dictionary containing Comparison Test updates.
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.put(
        endpoint=f"/api/testCenters/integrityComparisons/{id}", json=body
    )


@ErrorHandler(err_msg="Error deleting Comparison Test object with ID: {id}.")
def delete_comparison_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a Comparison Test object by ID.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Comparison Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.delete(endpoint=f"/api/testCenters/integrityComparisons/{id}")


@ErrorHandler(err_msg="Error getting Comparison Test results for ID: {id}.")
def get_comparison_results_by_test(
    connection: Connection,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get all comparison run results for a Comparison Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Comparison Test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{id}/comparisons"
    )


@ErrorHandler(err_msg="Error running Comparison Test with ID: {id}.")
def run_comparison_test(
    connection: Connection,
    id: str,
    body: dict | None = None,
    error_msg: str | None = None,
) -> Response:
    """Trigger a Comparison Test execution.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        id (str): ID of a Comparison Test object
        body (dict, optional): Dictionary containing Comparison Test
            execution parameters.
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint=f"/api/testCenters/integrityComparisons/{id}/comparisons", json=body
    )


@ErrorHandler(err_msg="Error bulk deleting Comparison Test objects.")
def bulk_delete_comparison_tests(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Bulk delete Comparison Test objects.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted payload containing Comparison Test IDs
            to delete
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint="/api/testCenters/integrityComparisons/bulkDelete", json=body
    )


# endregion

# region comparison results


@ErrorHandler(err_msg="Error getting Comparison Test result with ID: {id}:{test_id}.")
def get_comparison_result(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get details of a specific Comparison Test run.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}/comparisons/{id}",
        params={"includeStats": "true"},
    )


@ErrorHandler(err_msg="Error deleting Comparison Test result with ID: {id}:{test_id}.")
def delete_comparison_result(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a Comparison Test result.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.delete(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}/comparisons/{id}"
    )


@ErrorHandler(
    err_msg="Error canceling Comparison Test execution with ID: {id}:{test_id}."
)
def cancel_comparison_run(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Cancel a Comparison Test execution.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{id}/cancel"
    )


@ErrorHandler(
    err_msg="Error getting Comparison Test execution status with ID: {id}:{test_id}."
)
def get_comparison_result_status(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get Comparison Test execution status.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{id}/status"
    )


@ErrorHandler(
    err_msg="Error getting summary of Comparison Test result with ID: {id}:{test_id}."
)
def get_comparison_result_summary(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get Comparison Test execution summary.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{id}/summary"
    )


@ErrorHandler(
    err_msg="Error getting object results of Comparison Test with ID: {id}:{test_id}."
)
def get_comparison_object_results(
    connection: Connection,
    test_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get object comparisons in a Comparison Test result.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        id (str): ID of a Comparison execution result object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testcenters/integrityComparisons/{test_id}"
        f"/comparisors/{id}/testObjectComparisons"
    )


@ErrorHandler(
    err_msg="Error getting visualization data diff of Comparison Test with ID: {id}."
)
def get_comparison_node_result_data_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get node data differences in a Comparison Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        result_id (str): ID of a Comparison execution result object
        id (str): ID of a compared test object
        viz_key (str): Visualization node key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{result_id}/testObjectComparisons/{id}/"
        f"nodes/{viz_key}/dataDiff"
    )


@ErrorHandler(
    err_msg="Error getting object data diff of Comparison Test result with ID: {id}."
)
def get_comparison_result_data_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get data differences for a cube in a Comparison Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        result_id (str): ID of a Comparison execution result object
        id (str): ID of a compared test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{result_id}/testObjectComparisons/{id}/dataDiff"
    )


@ErrorHandler(
    err_msg="Error getting visualization SQL diff of Comparison Test with ID: {id}."
)
def get_comparison_node_result_sql_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    viz_key: str,
    error_msg: str | None = None,
) -> Response:
    """Get visualization SQL differences in a Comparison Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        result_id (str): ID of a Comparison execution result object
        id (str): ID of a compared test object
        viz_key (str): Visualization node key
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{result_id}/testObjectComparisons/{id}/"
        f"nodes/{viz_key}/sqlDiff"
    )


@ErrorHandler(
    err_msg="Error getting object SQL diff of Comparison Test result with ID: {id}."
)
def get_comparison_result_sql_diff(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get SQL differences for a cube in a Comparison Test.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        result_id (str): ID of a Comparison execution result object
        id (str): ID of a compared test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{result_id}/testObjectComparisons/{id}/sqlDiff"
    )


@ErrorHandler(
    err_msg="Error getting object summary of Comparison Test result with ID: {id}."
)
def get_comparison_result_object_summary(
    connection: Connection,
    test_id: str,
    result_id: str,
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Get summary result of a Comparison Test object.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        test_id (str): ID of a Comparison Test object
        result_id (str): ID of a Comparison execution result object
        id (str): ID of a compared test object
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(
        endpoint=f"/api/testCenters/integrityComparisons/{test_id}"
        f"/comparisons/{result_id}/testObjectComparisons/{id}/summary"
    )


@ErrorHandler(err_msg="Error bulk deleting Comparison Test execution results.")
def bulk_delete_comparison_results(
    connection: Connection,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Bulk delete Comparison Test execution results.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted payload containing Comparison result IDs
            to delete
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.post(
        endpoint="/api/testCenters/integrityComparisons/comparisons/bulkDelete",
        json=body,
    )


# endregion

# region settings


@ErrorHandler(err_msg="Error getting Test Center settings.")
def get_test_center_settings(
    connection: Connection, error_msg: str | None = None
) -> Response:
    """Get current Test Center settings.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.get(endpoint="/api/testCenters/settings")


@ErrorHandler(err_msg="Error updating Test Center settings.")
def update_test_center_settings(
    connection: Connection,
    body,
    error_msg: str | None = None,
) -> Response:
    """Partially update Test Center settings.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted payload containing request body
        error_msg (str, optional): Custom error message for error handling
    """
    return connection.patch(endpoint="/api/testCenters/settings", json=body)


# endregion
