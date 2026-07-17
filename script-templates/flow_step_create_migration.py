"""
Flow Step Template: Create Migration
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents Creating Migration action.

The Script will return created Migration ID.

The workflow currently assumes:
- That the source connection will be established via `get_connection`
- Actions set for `PackageSettings` are hardcoded in the code below
    to their default values ("REPLACE").
- Storage service has been configured for source environment.
"""

from time import sleep

from mstrio.connection import get_connection, Connection
from mstrio.object_management import SearchObject
from mstrio.object_management.migration import (
    Action,
    Migration,
    PackageSettings,
)
from mstrio.object_management.migration.package import PackageStatus

PROJECT_NAME = $source_project_name or None

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
source_conn = get_connection(connectionData, project=PROJECT_NAME)

SEARCH_OBJECT_ID = $search_object_id
MIGRATION_NAME = $migration_name or "flow_step_migration"

# Both required and optional properties below are set to their defaults.
# Feel free to change them to your needs. See `PackageSettings` in
# mstrio-py documentation or source code for more details.
package_settings = PackageSettings(
    default_action=Action.REPLACE,
    update_schema=None,  # example: `PackageSettings.UpdateSchema.RECAL_TABLE_LOGICAL_SIZE`,
    acl_on_replacing_objects=PackageSettings.AclOnReplacingObjects.REPLACE,
    acl_on_new_objects=PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
)

content = SearchObject(connection=source_conn, id=SEARCH_OBJECT_ID)

package_config = Migration.build_package_config(
    source_conn,
    content=content,
    package_settings=package_settings,
)

my_obj_mig = Migration.create_object_migration(
    connection=source_conn,
    toc_view=package_config,
    name=MIGRATION_NAME,
    project_id=source_conn.project_id,
)

while my_obj_mig.package_info.status == PackageStatus.CREATING:
    sleep(2)
    my_obj_mig.fetch()

if my_obj_mig.package_info.status != PackageStatus.CREATED:
    raise RuntimeError(
        f"Migration creation failed on source env with "
        f"status {my_obj_mig.package_info.status}."
    )


def get_results():
    return my_obj_mig.id
