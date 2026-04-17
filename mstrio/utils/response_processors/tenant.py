from typing import Any

from mstrio.api import tenant as tenant_api
from mstrio.api.tenant import (  # NOSONAR # noqa: F401
    delete_tenant,
    update_tenant_status,
    update_tenant_suffix,
)
from mstrio.connection import Connection
from mstrio.utils.helper import delete_none_values, rename_dict_keys

REST_ATTRIBUTES_MAP: dict[str, str] = {
    'tenantId': 'id',
    'tenantName': 'name',
    'tenantSuffix': 'suffix',
    'tenantDescription': 'description',
}


def get_tenant_data(
    connection: Connection,
    id: str,
    fields: str | None = None,
) -> dict[str, Any]:
    """Get tenant data and map REST response keys to Tenant attributes.

    Args:
        connection: Strategy One REST API connection object.
        id: Tenant ID.
        fields: Comma-separated list of fields to retrieve.

    Returns:
        Tenant payload with keys compatible with `Tenant` attributes.
    """
    tenant_data = tenant_api.get_tenant_data(
        connection=connection,
        tenant_id=id,
        fields=fields,
    ).json()

    return rename_dict_keys(tenant_data, REST_ATTRIBUTES_MAP)


def create_tenant(
    connection: Connection,
    name: str,
    suffix: str | None = None,
    fields: str | None = None,
) -> dict[str, Any]:
    """Create a new tenant.

    Args:
        connection: Strategy One REST API connection object.
        name: Name of the tenant to create.
        suffix: Tenant suffix. If None, the suffix is not sent.
        fields: Comma-separated list of fields to retrieve in the response.

    Returns:
        Tenant payload returned by the create operation.
    """
    body = {
        'name': name,
        'tenantSuffix': suffix,
    }
    body = delete_none_values(body, recursion=False)

    return tenant_api.create_tenant(
        connection=connection,
        body=body,
        fields=fields,
    ).json()


def add_tenant_members(
    connection: Connection,
    tenant_id: str,
    members: list[dict],
) -> None:
    """Add members to a specific tenant.

    Args:
        connection: Strategy One REST API connection object.
        tenant_id: Tenant ID.
        members: List of members to add. Expected shape for each item:
            {
                "memberId": "string",
                "memberTypeValue": int
            }
    """
    tenant_api.add_tenant_members(
        connection=connection,
        tenant_id=tenant_id,
        body={'members': members},
    )


def remove_tenant_members(
    connection: Connection,
    members: list[dict],
) -> None:
    """Remove members from a tenant.

    Args:
        connection: Strategy One REST API connection object.
        members: List of members to remove. Expected shape for each item:
            {
                "memberId": "string",
                "memberTypeValue": int
            }
    """
    tenant_api.remove_tenant_members(
        connection=connection,
        body={'members': members},
    )
