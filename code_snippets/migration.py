"""This is the demo script meant to show how administrator can perform a
migration of objects from one environment to another.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.

`mstrio.object_management.migration` module is available as a Functionality Preview.
It is subject to change until it is released as Generally Available.
"""

from mstrio.access_and_security.privilege import Privilege
from mstrio.connection import Connection
from mstrio.object_management.migration import (
    bulk_full_migration,
    bulk_migrate_package,
    Migration,
    PackageConfig,
    PackageContentInfo,
    PackageSettings
)
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User

# Define variables which can be later used in a script
PROJECT_NAME = $project_name
SOURCE_BASE_URL = $source_base_url  # usually ends with /MicroStrategyLibrary/api
SOURCE_USERNAME = $source_username
SOURCE_PASSWORD = $source_password
TARGET_BASE_URL = $target_base_url  # usually ends with /MicroStrategyLibrary/api
TARGET_USERNAME = $target_username
TARGET_PASSWORD = $target_password

# Create connections to both source and target environments
source_conn = Connection(
    SOURCE_BASE_URL, SOURCE_USERNAME, SOURCE_PASSWORD, project_name=PROJECT_NAME, login_mode=1
)
target_conn = Connection(
    TARGET_BASE_URL, TARGET_USERNAME, TARGET_PASSWORD, project_name=PROJECT_NAME, login_mode=1
)

# Define a variable which can be later used iin a script
USERNAME = $username  # user that is executing the migration

# Make sure the current user have the following privileges:
#   'Create package', id: 295
#   'Manage Migration Packages'(IServer >=11.3.7) or 'Apply package' (IServer <11.3.7),  id: 296
# They can be granted by admin with the following commands:
user = User(source_conn, username=USERNAME)
Privilege(source_conn, id=295).add_to_user(user)
Privilege(source_conn, id=296).add_to_user(user)

# Or by name:
user2 = User(target_conn, username=USERNAME)
Privilege(target_conn, name='Create package').add_to_user(user2)
Privilege(target_conn, name='Manage Migration Packages').add_to_user(user2)

# Define variables which can be later used in a script
DOSSIER_ID = $dossier_id
REPORT_ID = $report_id

# Create PackageConfig with information what object should be migrated and how.
# The options are of type Enum with all possible values listed.
package_settings = PackageSettings(
    PackageSettings.DefaultAction.USE_EXISTING,
    PackageSettings.UpdateSchema.RECAL_TABLE_LOGICAL_SIZE,
    PackageSettings.AclOnReplacingObjects.REPLACE,
    PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
)
package_content_info = PackageContentInfo(
    id=REPORT_ID,
    type=ObjectTypes.REPORT_DEFINITION,
    action=PackageContentInfo.Action.USE_EXISTING,
    include_dependents=True,
)
package_content_info2 = PackageContentInfo(
    id=DOSSIER_ID,
    type=ObjectTypes.DOCUMENT_DEFINITION,
    action=PackageContentInfo.Action.USE_EXISTING,
    include_dependents=True,
)

package_config = PackageConfig(
    PackageConfig.PackageUpdateType.PROJECT, package_settings, package_content_info
)
package_config2 = PackageConfig(
    PackageConfig.PackageUpdateType.PROJECT, package_settings, package_content_info2
)

# Define variables which can be later used in a script
SAVE_PATH = $save_path
CUSTOM_PACKAGE_PATH = $custom_package_path

# Create Migrations objects that can use all the functionalities
mig = Migration(
    save_path=SAVE_PATH,
    source_connection=source_conn,
    target_connection=target_conn,
    configuration=package_config,
)

# Create Migration object that can only use `create_package()`
mig2 = Migration(
    save_path=SAVE_PATH,
    source_connection=source_conn,
    configuration=package_config2,
)

# Create Migration object that can only be used for `migrate_package()`
mig3 = Migration(
    target_connection=target_conn,
    custom_package_path=CUSTOM_PACKAGE_PATH,
)

# Short version
# Create import package and save it to the file
mig.create_package()
# or
mig2.create_package()

# Migrate downloaded package to the target environment.
# Create undo package and save it to file
mig.migrate_package()
# or
mig3.migrate_package()

# End to end migration
mig.perform_full_migration()

# Detailed version
# Create import package and save it to the file specified with `save_path`
# argument during creation of migration object
mig.create_package()
mig2.create_package()

# Migrate downloaded package to the target environment
# `migrate_package()` by default uses a package binary saved to a variable
# during `create_package()`
mig.migrate_package()

# or a custom package binary specified with `custom_package_path`
# during Migration object creation, if `create_package()` was not called.
mig3.migrate_package()

# It is also possible to respecify `custom_package_path` at this stage
mig3.migrate_package(custom_package_path=CUSTOM_PACKAGE_PATH)

# Perform end to end migration. `perform_full_migration()` encapsulates
# `create_package()` and `migrate_package()` from the previous steps
# In order to be able to use, Migration object needs `source_connection`,
# `configuration` and `target_connection` parameters filled during creation
mig.perform_full_migration()

# Perform many full migrations at once
bulk_full_migration([mig])

# Perform many migrations at once
bulk_migrate_package([mig, mig3])

# If the migration needs to be reverted use `undo_migration()`
mig.undo_migration()

# Define a variable which can be later used in a script
UNDO_PACKAGE_PATH = $undo_package_path

# or run `migrate_package()` with path to the custom undo package
Migration(
    save_path=SAVE_PATH, target_connection=target_conn, custom_package_path=UNDO_PACKAGE_PATH
).migrate_package()

# Status of the migration can be checked by checking the `status` property
status = mig.status
