# Create an administration package with list of active users
# Leave action "use existing"

from mstrio.connection import get_connection


from mstrio.object_management.migration.migration import Migration
from mstrio.object_management.migration.package import (
    PackageConfig,
    PackageContentInfo,
    PackageSettings,
)
from mstrio.users_and_groups.user import list_users

conn = get_connection(workstationData, project_name='Project Analytics')

all_users = list_users(connection=conn)
active_users = [u for u in all_users if u.enabled]

# If no settings are specified, defaults will be used:
# - action: "use existing"
# - acl on replacing objects: "use existing"
# - acl on new objects: "keep acl as source object"
package_settings = PackageSettings()

# For each of the migrated objects, create a PackageContentInfo entry
# An entry can have its own action defined. It will override the default action
# If not specified, the default action will be used
# In this case, we will not set include_dependents to True. This will cause
# I-Server to include all dependent objects, without options to include or
# exclude them.
content_info = [PackageContentInfo(id=obj.id, type=obj.type) for obj in active_users]

package_config = PackageConfig(package_settings, content_info)

my_obj_mig_alt = Migration.create_object_migration(
    connection=conn,
    toc_view=package_config,
    name="test_object_mig",
    project_id=conn.project_id,
)
