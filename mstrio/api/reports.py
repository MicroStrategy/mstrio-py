from typing import TYPE_CHECKING

from packaging import version

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests_futures.sessions import FuturesSession

CUBE_FIELDS = '-data.metricValues.extras,-data.metricValues.formatted'


@ErrorHandler(err_msg='Error getting report {report_id} definition. Check report ID.')
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
    return connection.get(url=f'{connection.base_url}/api/v2/reports/{report_id}')


@ErrorHandler(err_msg='Error getting report {report_id} contents.')
def report_instance(connection, report_id, body=None, offset=0, limit=5000):
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

    Returns:
        Complete HTTP response object.
    """
    connection._validate_project_selected()
    if body is None:
        body = {}
    params = {'offset': offset, 'limit': limit}
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    return connection.post(
        url=f'{connection.base_url}/api/v2/reports/{report_id}/instances/',
        json=body,
        params=params,
    )


@ErrorHandler(err_msg='Error getting cube contents.')
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
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    return connection.get(
        url=f'{connection.base_url}/api/v2/reports/{report_id}/instances/{instance_id}',
        params=params,
    )


def report_instance_id_coroutine(
    future_session: "FuturesSession", connection, report_id, instance_id, offset=0, limit=5000
):
    """Get the future of a previously created instance for a specific report
    asynchronously, using the in-memory instance created by report_instance().

    Returns:
        Complete Future object.
    """
    params = {'offset': offset, 'limit': limit}
    if version.parse(connection.iserver_version) >= version.parse("11.2.0200"):
        params['fields'] = CUBE_FIELDS

    url = f'{connection.base_url}/api/v2/reports/{report_id}/instances/{instance_id}'
    future = future_session.get(url, params=params)
    return future


@ErrorHandler(err_msg='Error retrieving attribute {attribute_id} elements.')
def report_single_attribute_elements(connection, report_id, attribute_id, offset=0, limit=200000):
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
    url = f'{connection.base_url}/api/reports/{report_id}/attributes/{attribute_id}/elements'
    return connection.get(
        url=url,
        params={
            'offset': offset, 'limit': limit
        },
    )


def report_single_attribute_elements_coroutine(
    future_session: "FuturesSession", connection, report_id, attribute_id, offset=0, limit=200000
):
    """Get elements of a specific attribute of a specific report.

    Args:
        future_session(object): Future Session object to call MicroStrategy REST
            Server asynchronously
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
        Complete Future object
    """
    url = f'{connection.base_url}/api/reports/{report_id}/attributes/{attribute_id}/elements'
    future = future_session.get(url, params={'offset': offset, 'limit': limit})
    return future


@ErrorHandler(err_msg='Error getting collection of prompts for report {report_id}')
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
    url = f'{connection.base_url}/api/reports/{report_id}/prompts'
    return connection.get(
        url=url,
        params={
            'closed': closed, 'fields': fields
        },
    )


@ErrorHandler(err_msg='Error getting prompted report {report_id} instance.')
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
    url = f'{connection.base_url}/api/reports/{report_id}/instances/{instance_id}/prompts'
    return connection.get(
        url=url,
        params={
            'closed': closed, 'fields': fields
        },
    )
