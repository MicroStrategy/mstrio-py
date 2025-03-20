# Create an object package using results of search for last modified objects
# Add dataset components for Dashboard object
# Set up action "Replace" to all of the objects

from datetime import UTC, datetime, timedelta

from mstrio.connection import get_connection


from mstrio.object_management.migration.migration import Migration
from mstrio.object_management.migration.package import (
    Action,
    PackageConfig,
    PackageContentInfo,
    PackageSettings,
)
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectTypes

conn = get_connection(workstationData, project_name='Project Analytics')

DATE_CUTOFF = datetime.now(tz=UTC) - timedelta(days=30)
# format to str; example output: 2023-04-04T06:33:32Z
DATE_CUTOFF_STR = DATE_CUTOFF.strftime('%Y-%m-%dT%H:%M:%SZ')

search_results = full_search(
    conn, conn.project_id, begin_modification_time=DATE_CUTOFF_STR
)
datasets = []
for obj in search_results:
    if obj.type == ObjectTypes.DOCUMENT_DEFINITION:
        dependent_datasets = obj.list_dependents(object_types=[ObjectTypes.DBROLE])
        datasets += dependent_datasets

migrated_objects = search_results + datasets

# You can set the default action for all migrated objects
# using the PackageSettings object
package_settings = PackageSettings(Action.REPLACE)

# For each of the migrated objects, create a PackageContentInfo entry
# An entry can have its own action defined. It will override the default action
# If not specified, the default action will be used
# In this case, we will not set include_dependents to True. This will cause
# I-Server to include all dependent objects, without options to include or
# exclude them.
content_info = [
    PackageContentInfo(id=obj.id, type=obj.type, action=Action.REPLACE)
    for obj in migrated_objects
]

package_config = PackageConfig(package_settings, content_info)

my_obj_mig_alt = Migration.create_object_migration(
    connection=conn,
    toc_view=package_config,
    name="test_object_mig",
    project_id=conn.project_id,
)
