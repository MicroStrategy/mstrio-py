from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error creating documentation definition.")
def create_documentation_definition(
    connection: "Connection",
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Create a documentation definition.

    Expected payload format:
        {
            "name": "string",
            "type": "PROJECT_DOCUMENTATION",
            "hiddenObjects": true,
            "defaults": true,
            "projectId": "string",
            "definition": true,
            "advancedDefinition": true,
            "dependents": true,
            "components": true,
            "folder": ["All"],
            "application": ["All"],
            "schema": ["All"],
            "mdxCubes": ["MDXAttribute"],
            "basicProperties": ["All"]
        }

    Args:
        connection: Strategy One REST API connection object
        body (dict): Dictionary representing documentation definition to create
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    return connection.post(
        endpoint="/api/documentationDefinition",
        json=body,
    )


@ErrorHandler(
    err_msg=(
        "Error deleting documentation definition with ID: "
        "{documentation_definition_id}."
    )
)
def delete_documentation_definition(
    connection: "Connection",
    documentation_definition_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Delete documentation definition by documentation definition ID.

    Args:
        connection: Strategy One REST API connection object
        documentation_definition_id (str): Documentation definition ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(
        endpoint=f"/api/documentationDefinition/{documentation_definition_id}",
    )


@ErrorHandler(
    err_msg=(
        "Error updating documentation definition with ID: "
        "{documentation_definition_id}."
    )
)
def update_documentation_definition(
    connection: "Connection",
    documentation_definition_id: str,
    body: dict,
    error_msg: str | None = None,
) -> 'Response':
    """Update documentation definition by documentation definition ID.

    Args:
        connection: Strategy One REST API connection object
        documentation_definition_id (str): Documentation definition ID
        body (dict): Dictionary containing documentation definition updates.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        endpoint=f"/api/documentationDefinition/{documentation_definition_id}",
        json=body,
    )


@ErrorHandler(err_msg="Error getting documentation definition list.")
def get_documentation_definition_list(
    connection: "Connection",
    id: str | None = None,
    name: str | None = None,
    sort_by: str | None = None,
    include_embedded: bool | None = None,
    tenant_id: str | None = None,
    owner_id: str | None = None,
    project_id: str | None = None,
    date_created: str | None = None,
    last_run: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    error_msg: str | None = None,
) -> 'Response':
    """Get list of documentation definitions with filtering and sorting.

    Args:
        connection: Strategy One REST API connection object
        id (str, optional): Comma-separated list of definition IDs
        name (str, optional): Documentation definition name
        sort_by (str, optional): Sort by field with direction
        include_embedded (bool, optional): Include embedded details in response
        tenant_id (str, optional): Tenant ID
        owner_id (str, optional): Comma-separated list of owner IDs
        project_id (str, optional): Comma-separated list of project IDs
        date_created (str, optional): Date of creation filter expression
        last_run (str, optional): Date of last run filter expression in ISO
            DATETIME ZULU format with milliseconds.
            Valid operators:
                - `be:` (between),
                example: `be:2025-04-10T02:00:00.000Z,`
                `2025-04-10T03:00:00.000Z`
                - `gt:` (greater than),
                example: `gt:2025-05-10T02:00:00.000Z`
                - `lt:` (less than),
                example: `lt:2025-04-10T02:00:00.000Z`
                - `eq:` (equal),
                example: `eq:2025-06-10T02:00:00.000Z`
            If left empty, the last-run filter is not applied.
        offset (int, optional): Pagination offset
        limit (int, optional): Pagination limit
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint="/api/documentationDefinitions",
        params={
            'id': id,
            'documentationDefinitionName': name,
            'sortBy': sort_by,
            'includeEmbedded': include_embedded,
            'tenantId': tenant_id,
            'ownerId': owner_id,
            'projectId': project_id,
            'dateCreated': date_created,
            'lastRun': last_run,
            'offset': offset,
            'limit': limit,
        },
    )


@ErrorHandler(
    err_msg=(
        "Error getting documentation definition with ID: "
        "{documentation_definition_id}."
    )
)
def get_documentation_definition(
    connection: "Connection",
    documentation_definition_id: str,
    error_msg: str | None = None,
) -> 'Response':
    """Get documentation definition details by documentation definition ID.

    Args:
        connection: Strategy One REST API connection object
        documentation_definition_id (str): Documentation definition ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f"/api/documentationDefinitions/{documentation_definition_id}",
    )
