from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error getting documentation list.")
def get_documentation_list(
    connection: "Connection",
    id: str | None = None,
    documentation_name: str | None = None,
    sort_by: str | None = None,
    documentation_definition_id: str | None = None,
    project_id: str | None = None,
    owner_id: str | None = None,
    status: str | None = None,
    date_created: str | None = None,
    size: str | None = None,
    fields: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get a list of documentation items with filtering and sorting options.

    Args:
        connection: Strategy REST API connection object
        id (str, optional): Comma-separated list of documentation IDs
        documentation_name (str, optional): Documentation name
        sort_by (str, optional): Sort by field with direction.
            Example: "+name,-size" sorts by name ascending and size
            descending. Supported fields: id, name, type,
            documentationDefinitionId, status, projectName, ownerName,
            dateCreated, and size.
        documentation_definition_id (str, optional): Comma-separated list
            of documentation definition IDs
        project_id (str, optional): Comma-separated list of project IDs
        owner_id (str, optional): Comma-separated list of owner IDs
        status (str, optional): Comma-separated list of statuses.
            Available values: Running, Ready, Error, Canceled
        date_created (str, optional): Date of documentation creation in
            ISO DATETIME ZULU format with milliseconds. Supports operators:
            'be:' (between), 'gt:' (greater than), 'lt:' (less than),
            'eq:' (equal). Example: "lt:2025-04-10T02:00:00.000Z" or
            "be:2025-04-10T02:00:00.000Z,2025-04-10T03:00:00.000Z"
        size (str, optional): Size of documentation in bytes. Supports
            operators: 'be:' (between), 'gt:' (greater than),
            'lt:' (less than), 'eq:' (equal). Example: "lt:2000" or
            "be:1000,3333"
        fields (str, optional): Comma-separated list of fields to return.
        offset (int, optional): Pagination offset
        limit (int, optional): Pagination limit
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint="/api/documentation",
        params={
            'id': id,
            'documentationName': documentation_name,
            'sortBy': sort_by,
            'documentationDefinitionId': documentation_definition_id,
            'projectId': project_id,
            'ownerId': owner_id,
            'status': status,
            'dateCreated': date_created,
            'size': size,
            'fields': fields,
            'offset': offset,
            'limit': limit,
        },
    )


@ErrorHandler(err_msg="Error creating documentation.")
def create_documentation(
    connection: "Connection",
    documentation_definition_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Create documentation based on documentation definition ID.

    Returns 201 with documentation ID which is fully created when status
    later is Ready from /api/documentation/status.

    Args:
        connection: Strategy REST API connection object
        documentation_definition_id (str): Documentation definition ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    return connection.post(
        endpoint="/api/documentation",
        json={'documentationDefinitionId': documentation_definition_id},
    )


@ErrorHandler(err_msg="Error deleting documentation with ID: {id}.")
def delete_documentation(
    connection: "Connection",
    id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Delete documentation by documentation ID.

    Args:
        connection: Strategy REST API connection object
        id (str): Documentation ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(
        endpoint=f"/api/documentation/{id}",
    )


@ErrorHandler(err_msg="Error updating documentation with ID: {id}.")
def update_documentation(
    connection: "Connection",
    id: str,
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Update documentation by documentation ID.

    Args:
        connection: Strategy REST API connection object
        id (str): Documentation ID
        body (dict): Dictionary containing documentation updates.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        endpoint=f"/api/documentation/{id}",
        json=body,
    )


@ErrorHandler(err_msg="Error getting resource from documentation.")
def get_documentation_resource(
    connection: "Connection",
    id: str,
    resource_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get resource file in documentation by resource ID.

    Args:
        connection: Strategy REST API connection object
        id (str): Documentation ID
        resource_id (str): Resource ID
        fields (str, optional): Comma-separated list of fields to return
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f"/api/documentation/{id}/{resource_id}",
        params={'fields': fields},
    )


@ErrorHandler(err_msg="Error exporting documentation.")
def export_documentation(
    connection: "Connection",
    id: str,
    export_format: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Export documentation by documentation ID as a downloadable file.

    This is a sync method so it can take a long time to finish.

    Args:
        connection: Strategy REST API connection object
        id (str): Documentation ID
        export_format (str, optional): Export format for the
            documentation file. Supported values: csv, json, excel
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f"/api/documentation/{id}/export",
        params={"exportType": export_format},
    )


@ErrorHandler(err_msg="Error getting documentation objects.")
def get_documentation_objects(
    connection: "Connection",
    id: str,
    documentation_object_name: str | None = None,
    object_type: str | None = None,
    sort_by: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get documentation objects.

    Args:
        connection: Strategy REST API connection object
        id (str): Documentation ID
        documentation_object_name (str, optional): Documentation object
            name filter
        object_type (str, optional): Object type filter. Available values:
            Dashboard, Document, HTMLDocument, Hypercard, MTDICube,
            DataMartReport, IntelligentCube, Report, CustomGroup, Filter,
            AutoStyle, BaseFormula, Consolidation, DerivedElement,
            DrillMap, Metric, Subtotal, PredictiveMetric, Prompt, Search,
            Shortcut, Template, Attribute, Fact, Function, Hierarchy,
            LogicalTable, MetadataPartitionMapping,
            WarehousePartitionMapping, SecurityFilter, Transformation,
            Folder, MDXAttribute, MDXSystemHierarchy, MDXMetric,
            MDXLogicalTable, MDXPrompt
        sort_by (str, optional): Sort by field with direction.
            Example: "+name,-size"
        offset (int, optional): Pagination offset
        limit (int, optional): Pagination limit
        fields (str, optional): Comma-separated list of fields to return
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f"/api/documentation/{id}/objects",
        params={
            'documentationObjectName': documentation_object_name,
            'objectType': object_type,
            'sortBy': sort_by,
            'offset': offset,
            'limit': limit,
            'fields': fields,
        },
    )


@ErrorHandler(err_msg="Error getting documentation job statuses.")
def get_documentation_status(
    connection: "Connection",
    documentation_ids: str | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get job statuses for a list of documentation jobs.

    Args:
        connection: Strategy REST API connection object
        documentation_ids (str, optional): Comma-separated list of
            documentation IDs to get statuses for
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint="/api/documentation/status",
        params={"documentationIds": documentation_ids},
    )
