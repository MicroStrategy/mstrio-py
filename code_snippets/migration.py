"""This is the demo script meant to show how administrator can perform a
migration of objects from one environment to another.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from time import sleep

from mstrio.connection import Connection
from mstrio.object_management.migration import (
    Migration,
    list_migrations,
    list_migration_possible_content,
)
from mstrio.object_management import SearchObject, full_search
from mstrio.object_management.migration import (
    PackageType,
    MigrationPurpose,
    PackageSettings,
    PackageContentInfo,
    PackageConfig,
)
from mstrio.server.environment import StorageType
from mstrio.types import ObjectTypes
from mstrio.object_management.migration.package import (
    Action,
    ImportStatus,
    ProjectMergePackageTocView,
    ProjectMergePackageSettings,
    TranslationAction,
    PackageCertificationStatus,
    PackageStatus,
    ValidationStatus,
)
from mstrio.users_and_groups import User

# define connection to source environment
PROJECT_NAME = $project_name
ENV_URL_SOURCE = $env_url_source
U_NAME_SOURCE = $u_name_source
U_PASS_SOURCE = $u_pass_source
conn_source = Connection(
    base_url=ENV_URL_SOURCE,
    username=U_NAME_SOURCE,
    password=U_PASS_SOURCE,
    project_name=PROJECT_NAME,
)

# define connection to target environment
PROJECT_NAME = $project_name
ENV_URL_TARGET = $env_url_target
U_NAME_TARGET = $u_name_target
U_PASS_TARGET = $u_pass_target
conn_target = Connection(
    base_url=ENV_URL_TARGET,
    username=U_NAME_TARGET,
    password=U_PASS_TARGET,
    project_name=PROJECT_NAME,
)

# Configure Storage Service

# Configuration for Storage Service is stored in the storage_service attribute
# of the Environment object.
# This step should be done for source and target environments
env = conn_source.environment
print(env.storage_service)

# Make changes to the storage service configuration
env.storage_service.aws_access_id = "new_access_id"
env.storage_service.aws_secret_key = "new_secret_key"
env.storage_service.location = "new_s3_location"
env.storage_service.s3_region = "new_s3_region"
# Apply changes
env.update_storage_service()


# For target environment
env_target = conn_target.environment

# Make changes to the storage service configuration
env_target.storage_service.aws_access_id = "new_access_id"
env_target.storage_service.aws_secret_key = "new_secret_key"
env_target.storage_service.location = "new_s3_location"
env_target.storage_service.s3_region = "new_s3_region"
# Apply changes
env_target.update_storage_service()

# Alternatively, update the storage service configuration with a single call
STORAGE_ALIAS = $storage_alias
STORAGE_LOCATION = $storage_location
env_target.update_storage_service(
    storage_type=StorageType.FILE_SYSTEM, location=STORAGE_LOCATION, alias=STORAGE_ALIAS
)

# list_migrations
all_migs = list_migrations(conn_source)
first_5_migs = list_migrations(conn_source, limit=5)
only_file_migrations = list_migrations(
    conn_source, migration_purpose=MigrationPurpose.FROM_FILE
)
migrations_list_dict = list_migrations(conn_source, to_dictionary=True)

print(all_migs)

# Create an Object migration

# The PackageConfig object stores information on which objects should be
# migrated and how to resolve conflicts.
# The options are of type Enum with all possible values listed.
package_settings = PackageSettings(
    Action.USE_EXISTING,
    PackageSettings.UpdateSchema.RECAL_TABLE_LOGICAL_SIZE,
    PackageSettings.AclOnReplacingObjects.REPLACE,
    PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
)

# Check what object types are allowed to object migration
migrated_types = list_migration_possible_content(conn_source, PackageType.OBJECT)
print(migrated_types)

# Now try to list every elements that have word "Day" in name and can be
# migrated with object migration
search_results = full_search(
    conn_source, conn_source.project_id, object_types=migrated_types, name="Day"
)
print(search_results)
# We can select from there one element and add to new migration body
package_content_from_search = PackageContentInfo(
    id=search_results[0]['id'],
    type=search_results[0]['type'],
    action=Action.USE_EXISTING,
    include_dependents=False,
)

# Include objects by their ID and type
MIGRATED_METRIC_ID = $migrated_metric_id
package_content_from_object = PackageContentInfo(
    id=MIGRATED_METRIC_ID,
    type=ObjectTypes.METRIC,
    action=Action.USE_EXISTING,
    include_dependents=True,
)

package_config = PackageConfig(
    package_settings, [package_content_from_search, package_content_from_object]
)

print(package_config.to_dict())

# Also we can build PackageConfig from search results
# Specifying object_action_map and object_dependents_map
object_action_map=[(ObjectTypes.METRIC,Action.USE_OLDER), (ObjectTypes.ATTRIBUTE, Action.USE_NEWER)]
object_dependents_map=[(ObjectTypes.METRIC, True), (ObjectTypes.ATTRIBUTE, True)]
package_config_search_results = Migration.build_package_config(
    conn_source,
    search_results,
    package_settings,
    object_action_map,
    object_dependents_map)
print(package_config_search_results.to_dict())

# Another way to build PackageConfig is to use SearchObject
SEARCH_OBJ_ID = $search_obj_id
search_obj = SearchObject(connection=conn_source, id=SEARCH_OBJ_ID)

package_config_search_obj = Migration.build_package_config(
    conn_source,
    content=search_obj,
    package_settings=package_settings)
print(package_config_search_obj.to_dict())

# Create the migration
my_obj_mig = Migration.create_object_migration(
    connection=conn_source,
    toc_view=package_config,
    name="object_mig",
    project_id=conn_source.project_id,
)

# Wait for the migration to be created
while my_obj_mig.package_info.status == PackageStatus.CREATING:
    sleep(2)
    my_obj_mig.fetch()

# Check migration status
print(my_obj_mig.package_info.status)

my_obj_mig.alter_migration_info(name=f"{my_obj_mig.name}_altered")

# Certify the migration
my_obj_mig.certify(
    status=PackageCertificationStatus.CERTIFIED,
    creator=User(conn_source, 'Administrator'),
)

print(my_obj_mig.package_info.certification)

TARGET_PROJECT_NAME = $target_project_name
my_obj_mig.trigger_validation(
    target_env=conn_target, target_project_name=TARGET_PROJECT_NAME
)

# Wait for the validation to be completed
while my_obj_mig.validation.status == ValidationStatus.VALIDATING:
    sleep(2)
    my_obj_mig.fetch()

# Check migration validation status
print(my_obj_mig.validation)

# Migrate to target environment
my_obj_mig.migrate(target_env=conn_target, target_project_name=TARGET_PROJECT_NAME)

# Get migration object on target environment
my_obj_mig_target = Migration(conn_target, id=my_obj_mig.id)

# Waiting for migration to finish
while my_obj_mig_target.import_info.status in [ImportStatus.IMPORTING, ImportStatus.PENDING]:
    sleep(2)
    my_obj_mig_target.fetch()

# Print final ImportStatus here
print(my_obj_mig_target.import_info.status)

REUSE_TARGET_PROJECT_NAME = $reuse_target_project_name
my_obj_mig.reuse(target_env=conn_target, target_project_name=REUSE_TARGET_PROJECT_NAME)

REVERSE_TARGET_PROJECT_ID = $reverse_target_project_id
my_obj_mig.reverse(target_env=conn_target, target_project_id=REVERSE_TARGET_PROJECT_ID)

# Download migration package to local storage
downloaded = my_obj_mig.download_package(save_path="./")

# Import a migration package in target environment without use of S3 bucket
# or other shared folder
SOURCE_FILE_PATH = downloaded["filepath"]
FILE_MIG_TARGET_PROJECT_NAME = $file_mig_target_project_name
from_file_mig = Migration.migrate_from_file(
    connection=conn_target,
    file_path=SOURCE_FILE_PATH,
    package_type=PackageType.OBJECT,
    name="object_mig_from_local_storage",
    target_project_name=FILE_MIG_TARGET_PROJECT_NAME,
)

# Create an Administration migration

# Create PackageConfig with information what object should be migrated and how.
# The options are of type Enum with all possible values listed.
package_settings_adm = PackageSettings(
    default_action=Action.USE_EXISTING,
    acl_on_replacing_objects=PackageSettings.AclOnReplacingObjects.REPLACE,
    acl_on_new_objects=PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
)
MIGRATED_USER_ID = $migrated_user_id
package_content_info_adm = PackageContentInfo(
    id=MIGRATED_USER_ID,
    type=ObjectTypes.USER,
    action=Action.USE_EXISTING,
    include_dependents=True,
)

package_config_adm = PackageConfig(package_settings_adm, package_content_info_adm)

my_adm_mig = Migration.create_admin_migration(
    connection=conn_source, toc_view=package_config_adm, name="administration_mig"
)

# Wait for the migration to be created
while my_adm_mig.package_info.status == PackageStatus.CREATING:
    sleep(2)
    my_adm_mig.fetch()

# Check migration status
print(my_adm_mig.package_info.status)

my_adm_mig.trigger_validation(target_env=conn_target)

# Wait for the validation to be completed
while my_obj_mig.validation.status == ValidationStatus.VALIDATING:
    sleep(2)
    my_adm_mig.fetch()

# Check migration validation status
print(my_adm_mig.validation)

# Create a Project Merge migration

# Define project merge settings
proj_merge_settings = ProjectMergePackageSettings(
    translation_action=TranslationAction.NOT_MERGED,
    acl_on_replacing_objects=PackageSettings.AclOnReplacingObjects.USE_EXISTING,
    acl_on_new_objects=PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
    validate_dependencies=False,
    default_action=Action.USE_EXISTING,
    object_type_actions=[
        {"type": 3, "subtype": 776, "action": "replace"},
        {"type": 3, "subtype": 779, "action": "replace"},
        {"type": 55, "action": "keep_both"},
        {"type": 55, "action": "keep_both"},
    ],
)

proj_merge_toc_view = ProjectMergePackageTocView(proj_merge_settings)

print(proj_merge_toc_view.to_dict())

MERGE_TARGET_PROJECT_NAME = $merge_target_project_name
my_new_proj_merge_mig = Migration.create_project_merge_migration(
    connection=conn_source,
    toc_view=proj_merge_toc_view,
    name="merge_mig",
    project_name=MERGE_TARGET_PROJECT_NAME,
)

# Delete all migrations on source environment
migs = list_migrations(conn_source)
for mig in migs:
    mig.delete(force=True)

all_migs = list_migrations(conn_source)
print(all_migs)
