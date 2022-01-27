"""This is the demo script meant to show how administrator can perform a
migration of objects from one environment to another.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.

`mstrio.server.migration` module is still work in progress. We plan to release all
functionalities in 03.2022
"""

from mstrio.connection import Connection
from mstrio.access_and_security.privilege import Privilege
from mstrio.users_and_groups.user import User
from mstrio.server.migration import (bulk_migrate_package, bulk_full_migration, Migration,
                                     PackageConfig, PackageContentInfo, PackageSettings)
from mstrio.types import ObjectTypes

# Create connection to the source environment
source_base_url = "https://<>/MicroStrategyLibrary/api"
source_username = "some_username"
source_password = "some_password"
source_conn = Connection(source_base_url, source_username, source_password,
                         project_name="MicroStrategy Tutorial", login_mode=1)

# Create connection to the target environment
target_base_url = "https://<>/MicroStrategyLibrary/api"
target_username = "some_username"
target_password = "some_password"
target_conn = Connection(target_base_url, target_username, target_password,
                         project_name="MicroStrategy Tutorial", login_mode=1)

# Make sure the current user have the following privileges:
#   'Create package', id: 295
#   'Apply package',  id: 296
# They can be granted by admin with the following commands:
user = User(source_conn, username='some_username')
Privilege(source_conn, id=295).add_to_user(user)
Privilege(source_conn, id=296).add_to_user(user)

# Or by name:
user2 = User(target_conn, username='some_username')
Privilege(target_conn, name='Create package').add_to_user(user2)
Privilege(target_conn, name='Apply package').add_to_user(user2)

# Create PackageConfig with information what object should be migrated and how.
# The options are of type Enum with all possible values listed.
dossier_id = 'some dossier id'
document_id = 'some document id'
report_id = 'some report id'

package_settings = PackageSettings(
    PackageSettings.DefaultAction.USE_EXISTING,
    PackageSettings.UpdateSchema.RECAL_TABLE_LOGICAL_SIZE,
    PackageSettings.AclOnReplacingObjects.REPLACE,
    PackageSettings.AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
)
package_content_info = PackageContentInfo(
    id=report_id,
    type=ObjectTypes.REPORT_DEFINITION,
    action=PackageContentInfo.Action.USE_EXISTING,
    include_dependents=True,
)
package_content_info2 = PackageContentInfo(
    id=dossier_id,
    type=ObjectTypes.DOCUMENT_DEFINITION,
    action=PackageContentInfo.Action.USE_EXISTING,
    include_dependents=True,
)

package_config = PackageConfig(PackageConfig.PackageUpdateType.PROJECT, package_settings,
                               package_content_info)
package_config2 = PackageConfig(PackageConfig.PackageUpdateType.PROJECT, package_settings,
                                package_content_info2)

save_path = 'some/path/import_package.mmp'
custom_package_path = 'some/other/path/other_import_package.mmp'

# Create Migrations objects that can use all the funcionalities
mig = Migration(
    save_path=save_path,
    source_connection=source_conn,
    target_connection=target_conn,
    configuration=package_config,
)

# Create Migration object that can only use `create_package()`
mig2 = Migration(
    save_path=save_path,
    source_connection=source_conn,
    configuration=package_config2,
)

# Create Migration object that can only be used for `migrate_package()`
mig3 = Migration(
    target_connection=target_conn,
    custom_package_path=custom_package_path,
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
# Create import package and save it to the file sepecified with `save_path`
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
mig3.migrate_package(custom_package_path='path/to/some_package.mmp')

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

# or run `migrate_package()` with path to the custom undo package
Migration(save_path=save_path, target_connection=target_conn,
          custom_package_path='path/to/some_package_undo.mmp').migrate_package()

# Status of the migration can be checked by checking the `status` property
status = mig.status
