"""
Flow Step Template: Project Merge
Script Result Type: ---

This workflow template works OOTB after providing values for all required
Variables.

It represents Projects Merging action.

The workflow currently assumes:
- That the source connection will be established via `get_connection`
- That the target connection will be established via URL / Username / Password,
    all provided via Variables
- Actions set for `ProjectMergePackageSettings` are hardcoded in the code below
    to their default values ("REPLACE").
"""

from time import sleep

from mstrio.connection import get_connection, Connection
from mstrio.object_management.migration import Migration, PackageSettings
from mstrio.object_management.migration.package import (
    Action,
    ImportStatus,
    PackageStatus,
    ProjectMergePackageSettings,
    ProjectMergePackageTocView,
    TranslationAction,
    ValidationStatus,
)

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
source_conn = get_connection(connectionData)

target_conn = Connection(
    base_url=$target_base_url,
    username=$target_username,
    password=$target_password,
)

PROJECT_NAME = $source_project_name
TARGET_PROJECT_NAME = $target_project_name

# Both required and optional properties below are set to their defaults.
# Feel free to change them to your needs. See `ProjectMergePackageSettings` in
# mstrio-py documentation or source code for more details.
proj_merge_settings = ProjectMergePackageSettings(
    translation_action=TranslationAction.REPLACE,
    acl_on_replacing_objects=PackageSettings.AclOnReplacingObjects.REPLACE,
    acl_on_new_objects=PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
    default_action=Action.REPLACE,
    validate_dependencies=False,
)

proj_merge_toc_view = ProjectMergePackageTocView(proj_merge_settings)

my_proj_merge_mig = Migration.create_project_merge_migration(
    connection=source_conn,
    toc_view=proj_merge_toc_view,
    name="project_merge_migration",
    project_name=PROJECT_NAME,
)

while my_proj_merge_mig.package_info.status == PackageStatus.CREATING:
    sleep(2)
    my_proj_merge_mig.fetch()

if my_proj_merge_mig.package_info.status != PackageStatus.CREATED:
    raise RuntimeError(f"Creating Project Merge migration failed with status {my_proj_merge_mig.package_info.status}")

my_proj_merge_mig.trigger_validation(
    target_env=target_conn, target_project_name=TARGET_PROJECT_NAME
)

while my_proj_merge_mig.validation.status == ValidationStatus.VALIDATING:
    sleep(2)
    my_proj_merge_mig.fetch()

if my_proj_merge_mig.validation.status != ValidationStatus.VALIDATED:
    raise RuntimeError(f"Validating Project Merge migration failed with status {my_proj_merge_mig.validation.status}")

my_proj_merge_mig.migrate(
    target_env=target_conn, target_project_name=TARGET_PROJECT_NAME
)

my_proj_merge_mig_target = Migration(target_conn, id=my_proj_merge_mig.id)


while my_proj_merge_mig_target.import_info.status in [
    ImportStatus.IMPORTING,
    ImportStatus.PENDING,
]:
    sleep(2)
    my_proj_merge_mig_target.fetch()

if my_proj_merge_mig_target.import_info.status != ImportStatus.IMPORTED:
    raise RuntimeError(f"Migrating Project Merge package to target environment failed with status {my_proj_merge_mig_target.import_info.status}")

print("Project merge migration finished successfully.")
