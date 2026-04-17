from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error removing members from tenant.")
def remove_tenant_members(
    connection: "Connection",
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Remove members from a tenant.

    Args:
        connection: Strategy One REST API connection object
        body (dict): Dictionary containing members to be removed.
            Expected format:
            {
                "members": [
                    {
                        "memberId": "string",
                        "memberTypeValue": int
                    }
                ]
            }
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """

    return connection.post(
        endpoint="/api/multitenant/tenant/removeMembers",
        json=body,
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error adding members to tenant with ID: {tenant_id}.")
def add_tenant_members(
    connection: "Connection",
    tenant_id: str,
    body: dict,
    error_msg: str | None = None,
) -> Response:
    """Add members to a specific tenant.

    Args:
        connection: Strategy One REST API connection object
        tenant_id (str): Tenant ID
        body (dict): Dictionary containing members to be added.
            Expected format:
            {
                "members": [
                    {
                        "memberId": "string",
                        "memberTypeValue": int
                    }
                ]
            }
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """

    return connection.post(
        endpoint=f"/api/multitenant/tenant/{tenant_id}/addMembers",
        json=body,
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error changing status for tenant with ID: {tenant_id}.")
def update_tenant_status(
    connection: "Connection",
    tenant_id: str,
    enabled: bool,
    error_msg: str | None = None,
) -> Response:
    """Update the enabled/disabled status of a tenant.

    Args:
        connection: Strategy One REST API connection object
        tenant_id (str): Tenant ID
        enabled (bool): Whether the tenant should be enabled or disabled
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        endpoint=f"/api/multitenant/tenant/{tenant_id}/status",
        params={"enabled": enabled},
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error updating suffix for tenant with ID: {tenant_id}.")
def update_tenant_suffix(
    connection: "Connection",
    tenant_id: str,
    tenant_suffix: str,
    error_msg: str | None = None,
) -> Response:
    """Update the tenant suffix for a specific tenant.

    Args:
        connection: Strategy One REST API connection object
        tenant_id (str): Tenant ID
        tenant_suffix (str): Tenant suffix passed as query parameter.
            Empty string removes existing suffix.
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.patch(
        endpoint=f"/api/multitenant/tenant/{tenant_id}/suffix",
        params={'tenantSuffix': tenant_suffix},
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error deleting tenant with ID: {id}.")
def delete_tenant(
    connection: "Connection",
    id: str,
    error_msg: str | None = None,
) -> Response:
    """Delete a specific tenant.

    Args:
        connection: Strategy One REST API connection object
        id (str): Tenant ID
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    return connection.delete(
        endpoint=f"/api/multitenant/tenant/{id}",
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error getting tenant data with ID: {tenant_id}.")
def get_tenant_data(
    connection: "Connection",
    tenant_id: str,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get data for a specific tenant.

    Args:
        connection: Strategy One REST API connection object
        tenant_id (str): Tenant ID
        fields (str, optional): Comma-separated list of fields to retrieve
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    return connection.get(
        endpoint=f"/api/multitenant/tenant/{tenant_id}",
        params={"fields": fields},
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error creating tenant.")
def create_tenant(
    connection: "Connection",
    body: dict,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create a new tenant.

    Args:
        connection: Strategy One REST API connection object
        body (dict): Dictionary representing the tenant to be created.
            Expected format:
            {
                "name": "string",
                "tenantSuffix": "string"
            }
        fields (str, optional): Comma-separated list of fields to retrieve
            in the response
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    return connection.post(
        endpoint="/api/multitenant/tenant",
        json=body,
        params={"fields": fields},
        headers={'X-MSTR-ProjectID': None},
    )
