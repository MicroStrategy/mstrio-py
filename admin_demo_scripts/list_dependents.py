from typing import List, Union

from mstrio.connection import Connection
from mstrio.object_management.search_operations import (SearchPattern, SearchResultsFormat,
                                                        full_search)
from mstrio.types import ObjectTypes
from mstrio.project_objects.report import Report


def list_dependents_example():
    # Insert valid credentials
    username = 'username'
    base_url = 'https://env-******.customer.cloud.microstrategy.com/MicroStrategyLibrary'
    password = 'password'

    project_name = 'MicroStrategy Tutorial'  # Just example
    project_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'  # Just example
    metric_id = '08F9966749975B5C1A4980A3FA8CE3E7'  # Just example
    report_id = 'CAEA8BC44296BB6A89849FBD1161703B'  # Just example

    connection = Connection(base_url, username, password, project_name=project_name)

    # List dependents of a metric
    metric_dependents = list_dependents_of_metric(connection, project_id, metric_id)

    # or List dependents of a metric using more capabilities of `full_search()`
    object_dependents = full_search(connection, project_id, uses_object_id=metric_id,
                                    uses_object_type=ObjectTypes.METRIC, name='Graph',
                                    pattern=SearchPattern.CONTAINS,
                                    results_format=SearchResultsFormat.LIST, to_dictionary=False)

    # It is also posible to list dependencies of a metric
    metric_dependencies = full_search(connection, project_id, used_by_object_id=metric_id,
                                      used_by_object_type=ObjectTypes.METRIC,
                                      results_format=SearchResultsFormat.TREE)

    # Other objects, that already have dedicated class, can use premade methods
    report = Report(connection, report_id)
    rep_dependents = report.list_dependents()
    rep_dependencies = report.list_dependencies(to_dictionary=False)

    return (metric_dependents, object_dependents, metric_dependencies, rep_dependents,
            rep_dependencies)


def list_dependents_of_metric(
        connection: Connection, project_id: str, metric_id: str,
        results_format: SearchResultsFormat = SearchResultsFormat.LIST) -> Union[List[dict], dict]:
    """List dependents of a metric.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        project_id: ID of the project where the metric is located
        metric_id: ID of a metric of which the list of dependents is needed
        results_format: format of the result. Either list or a tree dict.

    Returns:
        all found dependents in a form of a list or a tree dict, depending on
          `results_format` parameter.
    """

    return full_search(
        connection=connection,
        project=project_id,
        uses_object_id=metric_id,
        uses_object_type=ObjectTypes.METRIC,
        results_format=results_format,
    )
