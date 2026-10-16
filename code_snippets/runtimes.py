"""This is the demo script to show how to manage Python execution runtimes
in Strategy.

This script will not work without replacing parameters with real values.
Its goal is to present the main operations available in the runtimes module.
"""

from mstrio.connection import get_connection
from mstrio.python_execution.runtime import (
    Runtime,
    RuntimePackage,
    RuntimeResource,
    get_runtime_versions,
    list_runtimes,
)

PROJECT_NAME = $project_name
RUNTIME_ID = $runtime_id
RUNTIME_NAME = $runtime_name

conn = get_connection(connectionData, project_name=PROJECT_NAME)

# List runtimes as Runtime objects.
runtimes = list_runtimes(connection=conn)

# List runtimes as dictionaries and filter by name.
runtime_dicts = list_runtimes(
    connection=conn,
    to_dictionary=True,
    name=RUNTIME_NAME,
)

# Get versions supported by the Strategy environment.
runtime_versions = get_runtime_versions(connection=conn)

# Initialize a runtime by ID or name.
runtime = Runtime(connection=conn, id=RUNTIME_ID)
runtime = Runtime(connection=conn, name=RUNTIME_NAME)
print(runtime.to_dict())

# Create a runtime with resource limits and packages.
new_runtime = Runtime.create(
    connection=conn,
    name="My Runtime",
    description="Runtime for data preparation scripts.",
    whitelist=["10.10.10.0/24"],
    packages=[
        RuntimePackage(name="pandas", version="2.2.3"),
    ],
    resource=RuntimeResource(cpu="1", mem=2048),
    runtime_version=runtime_versions[-1],
)

# Alter selected runtime properties.
new_runtime.alter(
    description="Updated runtime description.",
    exec_timeout=900,
)

# Delete a runtime without an interactive confirmation prompt.
new_runtime.delete(force=True)
