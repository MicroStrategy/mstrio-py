from typing import Optional

from mstrio.connection import Connection
from mstrio.utils.api_helpers import unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.wip import module_wip, WipLevels

module_wip(globals(), level=WipLevels.WARNING)


@unpack_information
@ErrorHandler(err_msg="Error getting an incremental refresh report")
def get_incremental_refresh_report(
    connection: Connection,
    id: str,
    project_id: Optional[str] = None,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: Optional[bool] = None,
    show_advanced_properties: Optional[bool] = None,
):
    """Get a definition of incremental refresh report

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        project_id (str, optional): ID of a project
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats.
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties.
            The advanced properties are presented in the following groups:
                "vldbProperties": A list of properties as determined by
                    the common infrastructure.
                "metricJoinTypes": A list of Metric Join Types, one for each
                    metric that appears in the template.
                "attributeJoinTypes": A list of Attribute Join Types, one for
                    each attribute that appears in the template.
            If omitted or false, nothing will be returned for the advanced
                properties.
            If true, all applicable advanced properties are returned.


    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/incrementalRefresh/{id}',
        headers={'X-MSTR-ProjectID': project_id} if project_id else None,
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower(),
            'showAdvancedProperties': str(show_advanced_properties).lower(),
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating an incremental refresh report")
def create_incremental_refresh_report(
    connection: Connection,
    body: dict,
    project_id: Optional[str] = None,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: Optional[bool] = None,
    show_advanced_properties: Optional[bool] = None,
):
    """Create a new incremental refresh report,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        body (dict): Incremental Refresh Report's creation data
        project_id (str, optional): ID of a project
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats.
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties.
            The advanced properties are presented in the following groups:
                "vldbProperties": A list of properties as determined by
                    the common infrastructure.
                "metricJoinTypes": A list of Metric Join Types, one for each
                    metric that appears in the template.
                "attributeJoinTypes": A list of Attribute Join Types, one for
                    each attribute that appears in the template.
            If omitted or false, nothing will be returned for the advanced
                properties.
            If true, all applicable advanced properties are returned.


    Return:
        HTTP response object. Expected status: 201
    """
    return connection.post(
        url=f'{connection.base_url}/api/model/incrementalRefresh',
        headers={'X-MSTR-ProjectID': project_id} if project_id else None,
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower(),
            'showAdvancedProperties': str(show_advanced_properties).lower(),
        },
        json=body,
    )


@unpack_information
@ErrorHandler(err_msg="Error updating an incremental refresh report")
def update_incremental_refresh_report(
    connection: Connection,
    id: str,
    body: dict,
    project_id: Optional[str] = None,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: Optional[bool] = None,
    show_advanced_properties: Optional[bool] = None,
):
    """Update a specified incremental refresh report,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        body (dict): Incremental Refresh Report's update data
        project_id (str, optional): ID of a project
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats.
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format
        show_advanced_properties (bool, optional): Specify whether to retrieve
            the values of the advanced properties.
            The advanced properties are presented in the following groups:
                "vldbProperties": A list of properties as determined by
                    the common infrastructure.
                "metricJoinTypes": A list of Metric Join Types, one for each
                    metric that appears in the template.
                "attributeJoinTypes": A list of Attribute Join Types, one for
                    each attribute that appears in the template.
            If omitted or false, nothing will be returned for the advanced
                properties.
            If true, all applicable advanced properties are returned.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.put(
        url=f'{connection.base_url}/api/model/incrementalRefresh/{id}',
        headers={'X-MSTR-ProjectID': project_id} if project_id else None,
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower(),
            'showAdvancedProperties': str(show_advanced_properties).lower(),
        },
        json=body,
    )


@unpack_information
@ErrorHandler(err_msg="Error getting an incremental refresh report's vldb properties")
def get_incremental_refresh_report_vldb_properties(
    connection: Connection,
    id: str,
    project_id: str,
):
    """Get vldb properties of an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        project_id (str): ID of a project

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/incrementalRefresh/{id}/applicableVldbProperties',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error executing an incremental refresh report")
def execute_incremental_refresh_report(
    connection: Connection, id: str, project_id: str, fields: Optional[str] = None
):
    """Execute an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        project_id (str): ID of a project
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 202
    """
    return connection.post(
        url=f'{connection.base_url}/api/incrementalRefresh/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error requesting preview data for an incremental refresh report")
def request_incremental_refresh_report_preview_data(
    connection: Connection,
    id: str,
    instance_id: str,
    project_id: str,
    fields: Optional[str] = None,
):
    """Request preview data for an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        instance_id (str): Instance's ID of an Incremental Refresh Report
        project_id (str): ID of a project
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 202
    """
    return connection.post(
        url=f'{connection.base_url}/api/incrementalRefresh/{id}/instances/{instance_id}/data',
        headers={'X-MSTR-ProjectID': project_id},
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error getting preview data for an incremental refresh report")
def get_incremental_refresh_report_preview_data(
    connection: Connection,
    id: str,
    instance_id: str,
    project_id: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    fields: Optional[str] = None,
):
    """Get preview data for an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        instance_id (str): Instance's ID of an Incremental Refresh Report
        project_id (str): ID of a project
        offset (int):
        limit (int):
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/incrementalRefresh/{id}/instances/{instance_id}/data',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'offset': offset,
            'limit': limit,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error creating instance of the incremental refresh report")
def create_incremental_refresh_report_instance(connection: Connection, id: str):
    """Create instance of an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID

        Return:
            HTTP response object. Expected status: 201
    """
    return connection.post(
        url=f'{connection.base_url}/api/model/incrementalRefresh/{id}/instances',
    )


@ErrorHandler(err_msg="Error deleting instance of the incremental refresh report")
def delete_incremental_refresh_report_instance(connection: Connection, id: str, instance_id: str):
    """Delete instance of an incremental refresh report.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Incremental Refresh Report's ID
        instance_id (str): Incremental Refresh Report Instance ID

        Return:
            HTTP response object. Expected status: 201
    """
    return connection.delete(
        url=f'{connection.base_url}/api/model/incrementalRefresh/{id}/instances',
        headers={
            'X-MSTR-MS-INSTANCE': instance_id,
        },
    )
