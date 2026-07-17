"""
Flow Step Template: Execute Migration
Script Result Type: ---

This workflow template works OOTB after providing values for all required
Variables.

It represents Executing existing Migration action.

Either `$migration_id` or `$migration_name` is required.

The workflow currently assumes:
- That the source connection will be established via `get_connection`
- That the target connection will be established via URL / Username / Password,
    all provided via Variables
- Storage service has been configured for both source and target environments.
"""

from time import sleep

from mstrio.connection import get_connection, Connection
from mstrio.object_management.migration import Migration
from mstrio.object_management.migration.package import ImportStatus

SOURCE_PROJECT_NAME = $source_project_name or None
TARGET_PROJECT_NAME = $target_project_name or None

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
source_conn = get_connection(connectionData, project=SOURCE_PROJECT_NAME)

target_conn = Connection(
    base_url=$target_base_url,
    username=$target_username,
    password=$target_password,
    project=TARGET_PROJECT_NAME,
)

MIGRATION_ID = $migration_id or None
MIGRATION_NAME = $migration_name or None

migration = Migration(source_conn, id=MIGRATION_ID, name=MIGRATION_NAME)

migration.migrate(target_conn, target_project=TARGET_PROJECT_NAME)

target_migration = Migration(target_conn, id=migration.id)

while target_migration.import_info.status in [
    ImportStatus.IMPORTING,
    ImportStatus.PENDING,
]:
    sleep(2)
    target_migration.fetch()

if target_migration.import_info.status != ImportStatus.IMPORTED:
    raise RuntimeError(
        f"Migration execution failed on target env with "
        f"status {target_migration.import_info.status}."
    )

print(f"Successfully migrated objects via migration ID '{target_migration.id}'")
