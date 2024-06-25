from typing import TYPE_CHECKING

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.version_helper import is_server_min_version

if TYPE_CHECKING:
    from mstrio.utils.sessions import FuturesSessionWithRenewal

CUBE_FIELDS = '-data.metricValues.extras,-data.metricValues.formatted'


@ErrorHandler(err_msg="Error getting SQL for report {report_id}.")
def report_sql(connection, report_id, instance_id):
    """Get the SQL code for a specific report. This is the SQL that is sent to
    the data warehouse to retrieve the data for the report.

    Args:
        connection: MicroStrategy REST API connection object
        report_id (str): Unique ID of the report
        instance_id (str): Unique ID of the in-memory instance of a published
            report.

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    return connection.get(
        endpoint=f'/api/v2/reports/{report_id}/instances/{instance_id}/sqlView'
    )


@ErrorHandler(err_msg="Error getting report {report_id} definition. Check report ID.")
def report_definition(connection, report_id):
    """Get the definition of a specific report, including attributes and
    metrics. This in-memory report definition provides information about all
    available objects without actually running any data query/report. The
    results can be used by other requests to help filter large datasets and
    retrieve values dynamically, helping with performance and scalability.

    Args:
        connection: MicroStrategy REST API connection object
        report_id (str): Unique ID of the report

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    return connection.get(endpoint=f'/api/v2/reports/{report_id}')


@ErrorHandler(err_msg="Error getting report {report_id} contents.")
def report_instance(
    connection, report_id, body=None, offset=0, limit=5000, execution_stage=None
):
    """Get the results of a newly created report instance. This in-memory
    report instance can be used by other requests.

    Args:
        connection: MicroStrategy REST API connection object.
        report_id (str): Unique ID of the report you wish to extract information
            from.
        offset (int, optional): Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As
            an example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.
        execution_stage (str, optional): Execution stage of the report
            Available values: 'resolve_prompts', 'execute_data'

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    if body is None:
        body = {}
    params = {'offset': offset, 'limit': limit}
    if is_server_min_version(connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS
    if execution_stage:
        params['executionStage'] = execution_stage

    return connection.post(
        endpoint=f'/api/v2/reports/{report_id}/instances/', json=body, params=params
    )


@ErrorHandler(err_msg="Error getting cube contents.")
def report_instance_id(connection, report_id, instance_id, offset=0, limit=5000):
    """Get the results of a previously created report instance, using the in-
    memory report instance created by a POST /api/reports/{reportId}/instances
    request.

    Args:
        connection: MicroStrategy REST API connection object
        report_id (str): Unique ID of the report you wish to extract information
            from.
        instance_id (str): Unique ID of the in-memory instance of a published
            report.
        offset (int): Optional. Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As
            an example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    params = {'offset': offset, 'limit': limit}
    if is_server_min_version(connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS

    return connection.get(
        endpoint=f'/api/v2/reports/{report_id}/instances/{instance_id}', params=params
    )


def report_instance_id_coroutine(
    future_session: "FuturesSessionWithRenewal",
    report_id,
    instance_id,
    offset=0,
    limit=5000,
):
    """Get the future of a previously created instance for a specific report
    asynchronously, using the in-memory instance created by report_instance().

    Returns:
        Complete Future object.
    """
    params = {'offset': offset, 'limit': limit}
    if is_server_min_version(future_session.connection, '11.2.0200'):
        params['fields'] = CUBE_FIELDS

    endpoint = f'/api/v2/reports/{report_id}/instances/{instance_id}'
    future = future_session.get(endpoint=endpoint, params=params)
    return future


@ErrorHandler(err_msg="Error retrieving attribute {attribute_id} elements.")
def report_single_attribute_elements(
    connection, report_id, attribute_id, offset=0, limit=200000
):
    """Get elements of a specific attribute of a specific report.

    Args:
        connection: MicroStrategy REST API connection object.
        report_id (str): Unique ID of the report you wish to extract information
            from.
        attribute_id (str): Unique ID of the attribute in the report.
        offset (int): Optional. Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As
            an example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.
    Returns:
        Complete HTTP response object
    """
    endpoint = f'/api/reports/{report_id}/attributes/{attribute_id}/elements'
    return connection.get(endpoint=endpoint, params={'offset': offset, 'limit': limit})


def report_single_attribute_elements_coroutine(
    future_session: "FuturesSessionWithRenewal",
    report_id,
    attribute_id,
    offset=0,
    limit=200000,
):
    """Get elements of a specific attribute of a specific report.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
        report_id (str): Unique ID of the report you wish to extract information
            from.
        attribute_id (str): Unique ID of the attribute in the report.
        offset (int): Optional. Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Used to control data extract behavior on datasets
            which have a large number of rows. The default is 1000. As
            an example, if the dataset has 50,000 rows, this function will
            incrementally extract all 50,000 rows in 1,000 row chunks. Depending
            on system resources, using a higher limit setting (e.g. 10,000) may
            reduce the total time required to extract the entire dataset.
    Returns:
        Complete Future object
    """
    endpoint = f'/api/reports/{report_id}/attributes/{attribute_id}/elements'
    future = future_session.get(
        endpoint=endpoint, params={'offset': offset, 'limit': limit}
    )
    return future


@ErrorHandler(err_msg="Error getting collection of prompts for report {report_id}")
def get_report_prompts(connection, report_id, closed=None, fields=None):
    """Get the collection of prompts and their respective definitions from a
    report.

    Args:
        connection: MicroStrategy REST API connection object.
        report_id (str): Unique ID of the report you wish
            to extract information from.
        closed: Prompt status, true means get closed prompt,
            false means get open prompt
        fields: Comma-separated, top-level field whitelist
            that allows the client to selectively retrieve
            part of the response model.

    """
    endpoint = f'/api/reports/{report_id}/prompts'
    return connection.get(
        endpoint=endpoint, params={'closed': closed, 'fields': fields}
    )


@ErrorHandler(err_msg="Error providing prompt answers for report {report_id}.")
def answer_report_prompts(
    connection: 'Connection', report_id: str, instance_id: str, body: dict
):
    """Provide answers to the prompts in a report instance.

    Args:
        connection (Connection): MicroStrategy REST API connection object.
        report_id (str): Unique ID of the report
        instance_id (str): Unique ID of the in-memory instance of a published
            report
        body (dict): dict containing the prompt answers
            A proper body for this request needs the following structure
            (answers are only needed if useDefault is False)
            (only one between key, name and id is required):
                {
                    "prompts": [
                        {
                            "key": "prompt_key",
                            "name": "prompt_name",
                            "id": "prompt_id",
                            "type": "prompt_type",
                            "useDefault": False,
                            "answers": [],
                        }
                    ]
                }
            The available prompt types are:
                    UNSUPPORTED, VALUE, ELEMENTS, EXPRESSION, OBJECTS, LEVEL

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    endpoint = f'/api/reports/{report_id}/instances/{instance_id}/prompts/answers'
    return connection.put(endpoint=endpoint, json=body)


@ErrorHandler(err_msg="Error getting prompted report {report_id} instance.")
def get_prompted_instance(connection, report_id, instance_id, closed=None, fields=None):
    """Get the collection of prompts and their respective definitions from a
    report instance. This endpoint will return data only when the report
    instance has prompt which need to be answered.

    Args:
        connection: MicroStrategy REST API connection object.
        report_id (str): Unique ID of the report you wish
            to extract information from.
        instance_id (str): Unique ID of the in-memory instance of a published
            report.
        closed(bool): Prompt status, true means get closed prompt,
            false means get open prompt
        fields: Comma-separated, top-level field whitelist
            that allows the client to selectively retrieve
            part of the response model.

    """
    endpoint = f'/api/reports/{report_id}/instances/{instance_id}/prompts'
    return connection.get(
        endpoint=endpoint, params={'closed': closed, 'fields': fields}
    )


@ErrorHandler(
    err_msg="Error getting prompted report {report_id} attribute element prompt."
)
def get_report_attribute_element_prompt(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    prompt_id: str,
    offset: int = 0,
    limit: int = 100,
    search_pattern: str | None = None,
    fields: str | None = None,
):
    """Get available attribute element for attribute element prompt"""
    endpoint = (
        f'/api/reports/{report_id}/instances/{instance_id}/prompts/{prompt_id}/elements'
    )
    return connection.get(
        endpoint=endpoint,
        params={
            'offset': offset,
            'limit': limit,
            'searchPattern': search_pattern,
            'fields': fields,
        },
    )
