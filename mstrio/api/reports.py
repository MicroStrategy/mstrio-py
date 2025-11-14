from typing import TYPE_CHECKING

from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.version_helper import is_server_min_version

if TYPE_CHECKING:
    from mstrio.utils.sessions import FuturesSessionWithRenewal

CUBE_FIELDS = '-data.metricValues.extras,-data.metricValues.formatted'


@ErrorHandler(err_msg="Error getting SQL for report {report_id}.")
def report_sql(
    connection: 'Connection', report_id: str, instance_id: str
) -> 'Response':
    """Get the SQL code for a specific report. This is the SQL that is sent to
    the data warehouse to retrieve the data for the report.

    Args:
        connection: Strategy One REST API connection object
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
def report_definition(connection: 'Connection', report_id: str) -> 'Response':
    """Get the definition of a specific report, including attributes and
    metrics. This in-memory report definition provides information about all
    available objects without actually running any data query/report. The
    results can be used by other requests to help filter large datasets and
    retrieve values dynamically, helping with performance and scalability.

    Args:
        connection: Strategy One REST API connection object
        report_id (str): Unique ID of the report

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    return connection.get(endpoint=f'/api/v2/reports/{report_id}')


@ErrorHandler(err_msg="Error getting report {report_id} contents.")
def report_instance(
    connection: 'Connection',
    report_id: str,
    project_id: str | None = None,
    body: dict | None = None,
    offset: int = 0,
    limit: int = 5000,
    execution_stage: str | None = None,
) -> 'Response':
    """Get the results of a newly created report instance. This in-memory
    report instance can be used by other requests.

    Args:
        connection: Strategy One REST API connection object.
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
    headers = {'X-MSTR-ProjectID': project_id} if project_id else {}

    return connection.post(
        endpoint=f'/api/v2/reports/{report_id}/instances/',
        json=body,
        params=params,
        headers=headers,
    )


@ErrorHandler(err_msg="Error getting report contents.")
def report_instance_id(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    offset: int = 0,
    limit: int = 5000,
) -> 'Response':
    """Get the results of a previously created report instance, using the in-
    memory report instance created by a POST /api/reports/{reportId}/instances
    request.

    Args:
        connection: Strategy One REST API connection object
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
    report_id: str,
    instance_id: str,
    offset: int = 0,
    limit: int = 5000,
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
    connection: 'Connection',
    report_id: str,
    attribute_id: str,
    offset: int = 0,
    limit: int = 200000,
) -> 'Response':
    """Get elements of a specific attribute of a specific report.

    Args:
        connection: Strategy One REST API connection object.
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
    report_id: str,
    attribute_id: str,
    offset: int = 0,
    limit: int = 200000,
):
    """Get elements of a specific attribute of a specific report.

    Args:
        future_session(object): Future Session object to call Strategy One REST
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
def get_report_prompts(
    connection: 'Connection',
    report_id: str,
    closed: bool | None = None,
    fields: str | None = None,
) -> 'Response':
    """Get the collection of prompts and their respective definitions from a
    report.

    Args:
        connection: Strategy One REST API connection object.
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
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    body: dict,
    project_id: str | None = None,
) -> 'Response':
    """Provide answers to the prompts in a report instance.

    Args:
        connection (Connection): Strategy One REST API connection object.
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
        project_id (str, optional): Project ID.

    Returns:
        HTTP response object returned by the Strategy One REST server.
    """
    if not project_id:
        project_id = connection.project_id
    endpoint = f'/api/reports/{report_id}/instances/{instance_id}/prompts/answers'
    return connection.put(
        endpoint=endpoint, json=body, headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg="Error getting prompted report {report_id} instance.")
def get_prompted_instance(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    closed: bool | None = None,
    fields: str | None = None,
    project_id: str | None = None,
) -> 'Response':
    """Get the collection of prompts and their respective definitions from a
    report instance. This endpoint will return data only when the report
    instance has prompt which need to be answered.

    Args:
        connection: Strategy One REST API connection object.
        report_id (str): Unique ID of the report you wish
            to extract information from.
        instance_id (str): Unique ID of the in-memory instance of a published
            report.
        closed(bool, optional): Prompt status, true means get closed prompt,
            false means get open prompt
        fields (str, optional): Comma-separated, top-level field whitelist
            that allows the client to selectively retrieve
            part of the response model.

    """
    if not project_id:
        project_id = connection.project_id
    endpoint = f'/api/reports/{report_id}/instances/{instance_id}/prompts'
    return connection.get(
        endpoint=endpoint,
        params={'closed': closed, 'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
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
) -> 'Response':
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


@ErrorHandler(err_msg="Error getting status of report instance {instance_id}")
def get_report_status(
    connection: 'Connection',
    report_id: str,
    instance_id: str,
    project_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get the status of a report instance.

    Args:
        connection (Connection): Strategy One REST API connection object.
        report_id (str): Report ID
        instance_id (str): Report Instance ID
        project_id (str, optional): Project ID
        fields (str, optional): A whitelist of top-level fields separated by
            commas. Allow the client to selectively retrieve fields in the
            response.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """
    endpoint = f'/api/reports/{report_id}/instances/{instance_id}/status'
    headers = {'X-MSTR-ProjectID': project_id} if project_id else {}

    return connection.get(
        endpoint=endpoint,
        headers=headers,
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error getting VLDB settings for report with ID: {id}")
def get_vldb_settings(
    connection: 'Connection',
    id: str,
    instance_id: str | None = None,
    error_msg: str | None = None,
):
    """Get advanced VLDB settings for a report.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (string): Datasource ID
        instance_id (string, optional): Report Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        endpoint=f'/api/model/reports/{id}?showAdvancedProperties=true',
        headers={'X-MSTR-MS-Instance': instance_id},
    )


@ErrorHandler(err_msg="Error updating VLDB settings for report with ID {id}")
def update_vldb_settings(
    connection: 'Connection',
    id: str,
    body: dict,
    instance_id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
):
    """Update metadata of advanced VLDB settings for a report.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (string): Report ID
        instance_id (string): Report Instance ID
        body (dict): JSON-formatted data used to update VLDB settings
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.put(
        endpoint=f'/api/model/reports/{id}',
        headers={'X-MSTR-MS-Instance': instance_id, 'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error getting metadata of VLDB settings for report with ID {id}")
def get_applicable_vldb_settings(
    connection: 'Connection',
    id: str,
    instance_id: str | None = None,
    error_msg: str | None = None,
):
    """Get metadata of advanced VLDB settings for a report.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (string): Report ID
        instance_id (string, optional): Report Instance ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        endpoint=f'/api/model/reports/{id}/applicableVldbProperties',
        headers={'X-MSTR-MS-Instance': instance_id},
    )


@ErrorHandler(err_msg="Error executing report {report_id}.")
def execute_report(
    connection: 'Connection',
    report_id: str,
    prefer: str = 'respond-async',
    instance_id: str | None = None,
    project_id: str | None = None,
    execution_stage: str | None = None,
    error_msg: str | None = None,
):
    """Execute a report. A project_id is required to execute the request if
    instance_id is not provided in the header. Set "Prefer" to respond-async to
    execute this API asynchronously.

    Args:
        connection (Connection): Strategy One REST API connection object.
        report_id (str): Unique ID of the report you wish to execute.
        prefer (str, optional): Response preference. Default is 'respond-async'.
        instance_id (str, optional): Unique ID of an existing in-memory instance
            of a published report.
        project_id (str, optional): Unique ID of the project containing the
            report.
        execution_stage (str, optional): Execution stage the report is executed
            to. Available values: 'resolve_prompts', 'execute_data', 'no_action'
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    headers = {'Prefer': prefer}
    params = {}
    if project_id:
        headers['X-MSTR-ProjectID'] = project_id
    if instance_id:
        headers['X-MSTR-MS-Instance'] = instance_id
    if execution_stage:
        params['executionStage'] = execution_stage
    return connection.post(
        endpoint=f'/api/model/reports/{report_id}/instances',
        headers=headers,
        params=params,
    )


@ErrorHandler(
    err_msg="Error getting available page-by elements for report {report_id}."
)
def get_available_page_by_elements(
    connection: 'Connection',
    project_id: str,
    report_id: str,
    instance_id: str,
    offset: int | None = None,
    limit: int | None = None,
    fields: list[str] | None = None,
) -> 'Response':
    """Get available page-by elements for a specific report.

    Args:
        connection: Strategy One REST API connection object.
        project_id (str): Unique ID of the project containing the report.
        report_id (str): Unique ID of the report you wish to extract information
            from.
        instance_id (str): Unique ID of the report instance.
        offset (int, optional): Starting point within the collection of returned
            results. Default is 0.
        limit (int, optional): Maximum number of results to return. Default is
            1000. Use -1 to return all available results.
        fields (list, optional): List of top-level fields to return. If None,
            all fields are returned.

    Returns:
        Complete HTTP response object.

    """

    connection._validate_project_selected()
    if not project_id:
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/v2/reports/{report_id}/instances/{instance_id}/pageBy/elements',
        params={'offset': offset, 'limit': limit, 'fields': fields},
        headers={'X-MSTR-ProjectID': project_id},
    )
