"""REST API wrappers for Mosaic data-server workspaces, pipelines and tables.

All endpoints live under `/api/dataServer/...`. The `X-MSTR-ProjectID` header
is sent when `project_id` is provided; otherwise the project selected on the
connection applies. There is NO collection-GET endpoint for workspaces,
pipelines or tables - nested definitions are returned inside the workspace
and pipeline GET payloads.
"""

from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error creating a workspace.")
def create_workspace(
    connection: Connection, body: dict, project_id: str | None = None
) -> Response:
    """Create a new workspace on the data server.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted definition of the new workspace
            (`ms-Workspace`), e.g. `{'datasetServeMode': 'connect_live',
            'sampling': {'type': 'first', 'rowCount': 1000}}`
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 201
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint='/api/dataServer/workspaces',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error getting workspace with ID: {id}.")
def get_workspace(
    connection: Connection, id: str, project_id: str | None = None
) -> Response:
    """Get the definition of a single workspace on the data server.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the workspace
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=f'/api/dataServer/workspaces/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error deleting workspace with ID: {id}.")
def delete_workspace(
    connection: Connection, id: str, project_id: str | None = None
) -> Response:
    """Delete a workspace on the data server.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the workspace
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.delete(
        endpoint=f'/api/dataServer/workspaces/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating workspace with ID: {id}.")
def update_workspace(
    connection: Connection, id: str, body: dict, project_id: str | None = None
) -> Response:
    """Update a workspace on the data server. Returns the workspace's
    updated definition.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the workspace
        body (dict): one or more top-level `ms-Workspace` fields with the new
            definition of the workspace (the endpoint also accepts
            `application/merge-patch+json`; plain `application/json` is sent)
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.patch(
        endpoint=f'/api/dataServer/workspaces/{id}',
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error creating a pipeline in workspace with ID: {workspace_id}.")
def create_pipeline(
    connection: Connection,
    workspace_id: str,
    body: dict | None = None,
    project_id: str | None = None,
) -> Response:
    """Create a new pipeline in the specified workspace.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        body (dict, optional): JSON-formatted definition of the new pipeline
            (`ms-Pipeline`, required fields on create-with-definition: `name`,
            `rootTable`); an empty object `{}` (the default) creates a new
            empty pipeline
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 201
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint=f'/api/dataServer/workspaces/{workspace_id}/pipelines',
        headers={'X-MSTR-ProjectID': project_id},
        json=body if body is not None else {},
    )


@ErrorHandler(err_msg="Error getting pipeline with ID: {pipeline_id}.")
def get_pipeline(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    project_id: str | None = None,
) -> Response:
    """Retrieve a specific pipeline by its ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=(f'/api/dataServer/workspaces/{workspace_id}/pipelines/{pipeline_id}'),
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error deleting pipeline with ID: {pipeline_id}.")
def delete_pipeline(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    project_id: str | None = None,
) -> Response:
    """Delete a specific pipeline.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.delete(
        endpoint=(f'/api/dataServer/workspaces/{workspace_id}/pipelines/{pipeline_id}'),
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating pipeline with ID: {pipeline_id}.")
def update_pipeline(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    body: dict,
    project_id: str | None = None,
) -> Response:
    """Update an existing pipeline. Returns the pipeline's updated definition.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        body (dict): JSON-formatted `ms-Pipeline` definition update
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.patch(
        endpoint=(f'/api/dataServer/workspaces/{workspace_id}/pipelines/{pipeline_id}'),
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )


@ErrorHandler(err_msg="Error refreshing pipeline with ID: {pipeline_id}.")
def refresh_pipeline(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    project_id: str | None = None,
) -> Response:
    """Refresh a pipeline to update its data and structure.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint=(
            f'/api/dataServer/workspaces/{workspace_id}'
            f'/pipelines/{pipeline_id}/refresh'
        ),
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error creating a table in pipeline with ID: {pipeline_id}.")
def create_pipeline_table(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    body: dict | None = None,
    project_id: str | None = None,
) -> Response:
    """Create a new table in the specified pipeline.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        body (dict): JSON-formatted definition of the new table. The server
            requires a typed table body: `ms-dataServerSourceTable` with
            `'type': 'source'` (and the corresponding fields, e.g.
            `columns`, `importSource`) or `ms-dataServerWrangleTable` with
            `'type': 'wrangle'` (e.g. `operations`, `columns`, `children`).
            An empty body `{}` fails with `8004d102 InvalidTypeIdException`
            (field-verified).
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 201
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.post(
        endpoint=(
            f'/api/dataServer/workspaces/{workspace_id}'
            f'/pipelines/{pipeline_id}/tables'
        ),
        headers={'X-MSTR-ProjectID': project_id},
        json=body if body is not None else {},
    )


@ErrorHandler(err_msg="Error getting table with ID: {table_id}.")
def get_pipeline_table(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    table_id: str,
    project_id: str | None = None,
    show_preview_data: bool = False,
    show_raw_data: bool = False,
) -> Response:
    """Retrieve a specific pipeline table by its ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        table_id (str): ID of the table
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used
        show_preview_data (bool, optional): whether to include preview data
            in the response, defaults to False
        show_raw_data (bool, optional): whether to include raw data in the
            response, defaults to False

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=(
            f'/api/dataServer/workspaces/{workspace_id}'
            f'/pipelines/{pipeline_id}/tables/{table_id}'
        ),
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'showPreviewData': show_preview_data,
            'showRawData': show_raw_data,
        },
    )


@ErrorHandler(err_msg="Error deleting table with ID: {table_id}.")
def delete_pipeline_table(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    table_id: str,
    project_id: str | None = None,
) -> Response:
    """Delete a specific pipeline table.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        table_id (str): ID of the table
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 204
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.delete(
        endpoint=(
            f'/api/dataServer/workspaces/{workspace_id}'
            f'/pipelines/{pipeline_id}/tables/{table_id}'
        ),
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(err_msg="Error updating table with ID: {table_id}.")
def update_pipeline_table(
    connection: Connection,
    workspace_id: str,
    pipeline_id: str,
    table_id: str,
    body: dict,
    project_id: str | None = None,
) -> Response:
    """Update an existing pipeline table. Returns the table's updated
    definition.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        workspace_id (str): ID of the workspace
        pipeline_id (str): ID of the pipeline
        table_id (str): ID of the table
        body (dict): JSON-formatted table definition update
            (`ms-dataServerSourceTable` or `ms-dataServerWrangleTable`)
        project_id (str, optional): ID of a project; if omitted, the project
            selected on the connection is used

    Return:
        HTTP response object. Expected status: 200
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.patch(
        endpoint=(
            f'/api/dataServer/workspaces/{workspace_id}'
            f'/pipelines/{pipeline_id}/tables/{table_id}'
        ),
        headers={'X-MSTR-ProjectID': project_id},
        json=body,
    )
