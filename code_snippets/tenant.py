"""This is the demo script to show how to manage tenants and
tenant-aware objects.

Tenants are available on Strategy environments with I-Server version
11.6.0100 and higher.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.content_group import ContentGroup
from mstrio.server.tenant import Tenant, list_tenants
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User, UserGroup

# Define variables which can be later used in a script
PROJECT_ID = $project_id  # Project to connect to
TENANT_NAME = $tenant_name
TENANT_SUFFIX = $tenant_suffix
TENANT_ID = $tenant_id
UPDATED_TENANT_NAME = $updated_tenant_name
UPDATED_TENANT_DESCRIPTION = $updated_tenant_description
UPDATED_TENANT_SUFFIX = $updated_tenant_suffix
USER_ID = $user_id
USER_GROUP_ID = $user_group_id
CONTENT_GROUP_ID = $content_group_id

# Create connection based on connection data
conn = get_connection(connectionData, project_id=PROJECT_ID)

# List tenants
all_tenants = list_tenants(connection=conn)
all_tenants_as_dicts = list_tenants(connection=conn, to_dictionary=True)
filtered_tenants = list_tenants(connection=conn, name=TENANT_NAME)

# Create a tenant
tenant = Tenant.create(
    connection=conn,
    name=TENANT_NAME,
    suffix=TENANT_SUFFIX,
)

# Get tenant by id or name
tenant = Tenant(connection=conn, id=TENANT_ID)
tenant = Tenant(connection=conn, name=TENANT_NAME)

# List tenant properties
properties = tenant.list_properties()
print(properties)

# Alter tenant properties
tenant.alter(
    name=UPDATED_TENANT_NAME,
    description=UPDATED_TENANT_DESCRIPTION,
    suffix=UPDATED_TENANT_SUFFIX,
)

# Enable or disable tenant
tenant.disable()
tenant.enable()

# Prepare members and tenant-aware objects
user = User(connection=conn, id=USER_ID)
user_group = UserGroup(connection=conn, id=USER_GROUP_ID)
content_group = ContentGroup(connection=conn, id=CONTENT_GROUP_ID)

# Add and remove tenant members
# Members can be passed as objects, IDs, or dicts with id and type
# Note: subtype is required only for remove_members when using dict
tenant.add_members([user, user_group])
tenant.add_members(USER_ID)
tenant.add_members({'id': USER_ID, 'type': ObjectTypes.USER.value})
tenant.remove_members([user, user_group])
tenant.remove_members(USER_ID)
tenant.remove_members(
    {
        'id': USER_ID,
        'type': ObjectTypes.USER.value,
        'subtype': ObjectSubTypes.USER_GROUP.value,
    }
)

# Assign and unassign tenant-aware configuration objects
# Objects can be passed as Entity objects or dicts with id and type
tenant.assign_to_tenant(content_group)
tenant.unassign_from_tenant(
    {
        'id': content_group.id,
        'type': content_group.type.value,
        'tenant_id': tenant.id,
    }
)

# Change tenant assignment directly from tenant-aware objects
user.change_tenant(tenant=tenant)
user.remove_from_tenant()

content_group.change_tenant(tenant_id=tenant.id)
content_group.remove_from_tenant()

# List tenant members
members = tenant.list_members()
users_only = tenant.list_members(object_types=ObjectTypes.USER)
member_dicts = tenant.list_members(to_dictionary=True)

# List configuration objects assigned to the tenant
content_groups = tenant.list_objects(
    object_types=ObjectTypes.CONTENT_BUNDLE,
    to_dictionary=False,
)
projects = tenant.list_projects(to_dictionary=True)

# Delete tenant without prompt
tenant.delete(force=True)
