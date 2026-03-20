"""This is the demo script to show how administrator can duplicate projects
on same and different environments.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.server import (
    AdminObjectRule,
    CrossDuplicationConfig,
    DuplicationConfig,
    Environment,
    Project,
    ProjectDuplication,
    ProjectDuplicationRule,
    list_languages,
)
from mstrio.server.environment import StorageType
from mstrio.types import ObjectTypes

# Define connection to source environment
ENV_URL_SOURCE = $env_url_source
U_NAME_SOURCE = $u_name_source
U_PASS_SOURCE = $u_pass_source
conn_source = Connection(
    base_url=ENV_URL_SOURCE,
    username=U_NAME_SOURCE,
    password=U_PASS_SOURCE,
)

# Define connection to target environment
ENV_URL_TARGET = $env_url_target
U_NAME_TARGET = $u_name_target
U_PASS_TARGET = $u_pass_target
conn_target = Connection(
    base_url=ENV_URL_TARGET,
    username=U_NAME_TARGET,
    password=U_PASS_TARGET,
)

# Define Environment objects for source and target environments
env_source = Environment(conn_source)
env_target = Environment(connection=conn_target)

# Define name of project to interact with
PROJECT_NAME = $project_name

# get project with a given name
project = Project(connection=conn_source, name=PROJECT_NAME)

# Same environment project duplication

# Duplicate a project with default settings
DUPLICATION_NAME = $duplication_name
same_env_dup_1 = project.duplicate(target_name=(DUPLICATION_NAME + '_default'))

# Wait for duplication to finish
same_env_dup_1.wait_for_stable_status()
print(same_env_dup_1.status)

# Duplicate the project with no default settings
# List languages to select from in duplication settings
langs = list_languages(conn_source)

selected_langs = langs[:5]  # Select first 5 languages for duplication
selected_default_project_lang = langs[0].lcid  # Select first language as default locale

# Define not default duplication settings
duplication_config = DuplicationConfig(
    schema_objects_only=False,
    skip_empty_profile_folders=False,
    skip_all_profile_folders=False,
    include_user_subscriptions=False,
    include_contact_subscriptions=False,
    include_contacts_and_contact_groups=False,
    import_description="test duplication with languages",
    import_default_locale=selected_default_project_lang,
    import_locales=[lang.lcid for lang in selected_langs],
)

# Perform duplication
same_env_dup_2 = project.duplicate(
    target_name=(DUPLICATION_NAME + '_non_default'),
    duplication_config=duplication_config,
)

# Wait for duplication to finish
same_env_dup_2.wait_for_stable_status()
print(same_env_dup_2.status)


# Cross-environment project duplication

# Configuration for Storage Service is stored in the storage_service attribute
# of the Environment object.
# This step should be done for source and target environments

STORAGE_TYPE = StorageType.S3
S3_LOCATION = $s3_location
S3_REGION = $s3_region
S3_ACCESS_ID = $s3_access_id
S3_SECRET_KEY = $s3_secret_key

# For source environment
print(env_source.storage_service)

# Apply changes
env_source.update_storage_service(
    storage_type=STORAGE_TYPE,
    location=S3_LOCATION,
    s3_region=S3_REGION,
    aws_access_id=S3_ACCESS_ID,
    aws_secret_key=S3_SECRET_KEY,
)

# For target environment
env_target = conn_target.environment
# Apply changes
env_target.update_storage_service(
    storage_type=STORAGE_TYPE,
    location=S3_LOCATION,
    s3_region=S3_REGION,
    aws_access_id=S3_ACCESS_ID,
    aws_secret_key=S3_SECRET_KEY,
)


# Now we can perform cross-environment duplication with auto sync
CROSS_DUPLICATION_NAME = $cross_duplication_name

# Define admin objects to be included in duplication by their IDs
CALENDAR_ID = $calendar_id
DBLOGIN_ID = $dblogin_id

# Select properties for cross-duplication configuration
cross_dup_config = CrossDuplicationConfig(
    schema_objects_only=False,
    skip_empty_profile_folders=False,
    include_user_subscriptions=False,
    include_contact_subscriptions=True,
    include_contacts_and_contact_groups=True,
    include_all_user_groups=True,
    match_users_by_login=True,
    admin_objects_rules=[
        AdminObjectRule(type=34, rule=ProjectDuplicationRule.MERGE),
        AdminObjectRule(type=ObjectTypes.CALENDAR, rule=ProjectDuplicationRule.REPLACE),
        AdminObjectRule(type=ObjectTypes.DBLOGIN, rule=1),
    ],
    admin_objects=[CALENDAR_ID, DBLOGIN_ID],
)
dup_obj_1 = project.duplicate_to_other_environment(
    target_name=(CROSS_DUPLICATION_NAME + '_auto_sync_on'),
    target_env=conn_target,
    cross_duplication_config=cross_dup_config,
)

# Wait for duplication to finish
dup_obj_1.wait_for_stable_status()
print(dup_obj_1.status)

# Get same duplication object from the target environment
dup_obj_1_target = ProjectDuplication(conn_target, id=dup_obj_1.id)
# Wait for duplication to finish synchronization
dup_obj_1_target.wait_for_stable_status()
print(dup_obj_1_target.status)

# Get project from the target environment
project_target = Project(connection=conn_target, name=(CROSS_DUPLICATION_NAME + '_auto_sync_on'))


# Define name of second project to interact with
PROJECT_NAME_2 = $project_name_2

project_2 = Project(connection=conn_source, name=PROJECT_NAME_2)

# Duplicate cross-environment with default settings without syncing
dup_obj_2 = project_2.duplicate_to_other_environment(
    target_name=CROSS_DUPLICATION_NAME + '_auto_sync_off',
    target_env=conn_target,
    sync_with_target_env=False,
)

# Wait for duplication to finish export
dup_obj_2.wait_for_stable_status()
print(dup_obj_2.status)

# Get duplication package backup and save it locally
SAVE_PATH = $save_path

binary_package = dup_obj_2.get_backup_package(save_path=SAVE_PATH)

print(binary_package.get('filepath'))

# Restore duplication package on the target environment

dup_on_target = Project.restore_project_from_backup(
    connection=conn_target,
    backup_file=binary_package.get('filepath'),
    target_name=CROSS_DUPLICATION_NAME + '_auto_sync_off',
)

# Wait for duplication to finish restoration
dup_on_target.wait_for_stable_status()
print(dup_on_target.status)

# Get project from the target environment
project_2_target = Project(connection=conn_target, name=CROSS_DUPLICATION_NAME + '_auto_sync_off')

# Delete duplication records
dup_obj_2.delete(force=True)
dup_on_target.delete(force=True)
