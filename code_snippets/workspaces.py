"""This is the demo script to show how to manage Mosaic data-server
workspaces, pipelines and pipeline tables. Its basic goal is to present
what can be done with this module and to ease its usage.

Note: there is no collection-GET endpoint for workspaces, pipelines or
tables, so listing them is not supported. Obtain workspace and pipeline
IDs from Studio or from data-model pipeline table definitions.
"""

from mstrio.connection import get_connection
from mstrio.project_objects.workspace import Pipeline, PipelineTable, Workspace

# Define a variable which can be later used in a script
PROJECT_ID = $project_id  # Insert ID of project here

conn = get_connection(connectionData, project_id=PROJECT_ID)

# Create a workspace
# Available dataset serve modes: 'in_memory', 'connect_live', 'off_memory'
ws = Workspace.create(
    connection=conn,
    dataset_serve_mode='connect_live',
    sampling={'type': 'first', 'rowCount': 1000},
    project_id=PROJECT_ID,
)

# Define a variable which can be later used in a script
WORKSPACE_ID = $workspace_id  # Insert ID of workspace here

# Get a workspace by its ID
ws = Workspace(connection=conn, id=WORKSPACE_ID)

# Alter a workspace
ws.alter(dataset_serve_mode='in_memory')
ws.alter(sampling={'type': 'random', 'rowCount': 500})

# List pipelines of a workspace (built from the workspace's definition)
pipelines = ws.pipelines
print(pipelines)

# Create an empty pipeline in a workspace
pipeline = ws.create_pipeline()

# Define variables which can be later used in a script
PIPELINE_NAME = $pipeline_name  # Insert name of pipeline here
PIPELINE_ROOT_TABLE = $pipeline_root_table  # Insert root table definition here

# Create a pipeline with a definition
# `name` and `root_table` are required by the server when creating
# a pipeline with a definition
pipeline = ws.create_pipeline(
    name=PIPELINE_NAME,
    root_table=PIPELINE_ROOT_TABLE,
)

# Define a variable which can be later used in a script
PIPELINE_ID = $pipeline_id  # Insert ID of pipeline here

# Get a pipeline by its ID
pipeline = ws.get_pipeline(pipeline_id=PIPELINE_ID)
pipeline = Pipeline(
    connection=conn, workspace_id=WORKSPACE_ID, id=PIPELINE_ID
)

# Define a variable which can be later used in a script
PIPELINE_NAME_ALTERED = $pipeline_name_altered

# Alter a pipeline
pipeline.alter(name=PIPELINE_NAME_ALTERED)

# Refresh a pipeline to update its data and structure
pipeline.refresh()

# Create an empty table in a pipeline
table = pipeline.create_table()

# Define a variable which can be later used in a script
SOURCE_TABLE_BODY = $source_table_body  # Insert source table definition here

# Create a table with a definition
# The body is either a source table (`{'type': 'source', ...}` with
# 'columns', 'importSource', 'filter', 'sampling') or a wrangle table
# (`{'type': 'wrangle', ...}` with 'operations', 'columns', 'children')
table = pipeline.create_table(body=SOURCE_TABLE_BODY)

# Define a variable which can be later used in a script
TABLE_ID = $table_id  # Insert ID of table here

# Get a table by its ID, optionally with preview or raw data
table = pipeline.get_table(table_id=TABLE_ID)
table = pipeline.get_table(
    table_id=TABLE_ID, show_preview_data=True, show_raw_data=True
)
table = PipelineTable(
    connection=conn,
    workspace_id=WORKSPACE_ID,
    pipeline_id=PIPELINE_ID,
    id=TABLE_ID,
)

# Fetch the latest table definition, optionally with preview data
table.fetch(show_preview_data=True)

# Define a variable which can be later used in a script
TABLE_BODY_ALTERED = $table_body_altered  # Insert updated table definition

# Alter a table
table.alter(body=TABLE_BODY_ALTERED)

# Delete a table without prompt
table.delete(force=True)

# Delete a pipeline without prompt
pipeline.delete(force=True)

# Delete a workspace without prompt
ws.delete(force=True)
