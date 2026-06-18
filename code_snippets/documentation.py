"""Demo script for the Documentation module.

This script will not work without replacing parameters with real values.
Its goal is to present the module usage and make it easier to start.
"""

from mstrio.connection import get_connection
from mstrio.server.documentation import (
    DocExportFormat,
    DocObjectType,
    Documentation,
    DocumentationDefinition,
    get_documentations_statuses,
    list_documentation_definitions,
    list_documentations,
)

# Define variables which can be later used in a script
PROJECT_NAME = $project_name  # Insert project name here
DEFINITION_NAME = $definition_name  # Insert definition name here

# Get connection to the environment
conn = get_connection(connectionData, project_name=PROJECT_NAME)

# Create documentation definition
# Note: project can also be provided as project_id or project_name.
definition = DocumentationDefinition.create(
    connection=conn,
    name=DEFINITION_NAME,
    project=PROJECT_NAME,
)

# Execute definition to create a documentation job.
documentation = definition.execute()

# IMPORTANT:
# Save this ID as soon as execute() returns.
# If your script/session times out,
# the server-side execution can still continue,
# and you can reconnect later and monitor the same job by this ID.
documentation_id = documentation.id

# You can wait for completion.
# Note: wait_for_execution_finish() polls status.
# Depending on environment and documentation size
# script/session timeout may happen so it's safer to save ID
# and reconnect later to check status.
final_status = documentation.wait_for_execution_finish(interval=10)
print(final_status.status)

# Export finished documentation.
documentation.export_to_file(
    file_path=$export_file_path,  # Insert export file path here
    export_format=DocExportFormat.JSON,
)

# Recovery flow after timeout / disconnected script:
# 1) Reconnect.
# 2) Use saved documentation ID to check status.
recovered_documentation = Documentation(connection=conn, id=documentation_id)
recovered_status = recovered_documentation.get_status()
print(recovered_status.status)

# Alternative recovery if you do not have saved ID:
# list all documentation jobs and find one by name / definition / status.
all_docs = list_documentations(connection=conn, to_dictionary=True)
print(f"Found {len(all_docs)} documentation jobs")

# Example: list definitions and documentations in object mode.
definitions = list_documentation_definitions(connection=conn)
jobs = list_documentations(connection=conn)

# Example: get statuses for multiple jobs at once.
if jobs:
    statuses = get_documentations_statuses(
        connection=conn,
        documentations=jobs,
        to_dictionary=True,
    )
    print(f"Fetched statuses for {len(statuses)} jobs")

# Alter documentation definition name and description.
definition.alter(
    name='Updated Documentation Definition Name',
    description='Updated description for the definition',
)

# Alter documentation job name.
if documentation.status.value == 'Ready':
    documentation.alter(name='Updated Documentation Job Name')

# List objects included in documentation.
# Can be filtered by object type and sorted by various fields.
objects = documentation.list_objects(
    doc_object_type=DocObjectType.METRIC,
    limit=100,
    to_dictionary=False,
)
print(f"Found {len(objects)} metrics in documentation")

# Get detailed information about a specific resource.
# Resource can be provided as a Folder, Project object or resource ID.
resource = documentation.get_resource(
    resource='8D679D3811D3E4981000E787EC6DE8A4',
    to_dictionary=False,
)
if resource and resource.paths:
    print(f"Resource: {resource.paths.name}")

# Get detailed status information.
status = documentation.get_status(to_dictionary=False)
print(f"Progress: {status.progress}%")
print(f"Status: {status.status}")
if status.message:
    print(f"Message: {status.message}")

# Delete documentation job when no longer needed.
# This will remove the documentation from the server.
documentation.delete()
print("Documentation deleted")

# Delete documentation definition when no longer needed.
definition.delete()
print("Documentation definition deleted")
