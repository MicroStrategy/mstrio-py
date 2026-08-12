from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error getting MDX catalog cubes for datasource {id}.')
def get_mdx_catalog(
    connection: 'Connection',
    id: str,
    project_id: str | None = None,
    error_msg: str | None = None,
):
    """Get cubes in an MDX datasource catalog.

    Uses the legacy GetMDXCubes XML command to maintain parity with
    Command Manager and preserve the DBRole → Catalog → Cube hierarchy.
    This may be replaced with REST/JSON-based MDX cube catalog APIs
    which fetches MDX catalog cubes based on schema in the future.

    Args:
        connection (Connection): Strategy REST API connection object.
        id (str): MDX datasource ID.
        project_id (str, optional): Project ID.
        error_msg (str, optional): Custom Error Message for Error Handling.

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/mdxDataSources/{id}',
        headers={'X-MSTR-ProjectID': project_id},
    )


@ErrorHandler(
    err_msg='Error altering MDX catalog cube with ID: {id} '
    'for datasource {datasource_id}.'
)
def alter_mdx_cube(
    connection: 'Connection',
    datasource_id: str,
    id: str,
    body: dict,
    project_id: str | None = None,
    error_msg: str | None = None,
):
    """Retarget imported MDX cube to another catalog and/or cube.

    Args:
        connection (Connection): Strategy REST API connection object.
        datasource_id (str): MDX datasource ID.
        id (str): Imported MDX cube ID.
        body (dict): PATCH request body.
        project_id (str, optional): Project ID.
        error_msg (str, optional): Custom Error Message for Error Handling.

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.patch(
        endpoint=f'/api/mdxDataSources/{datasource_id}/cubes/{id}',
        json=body,
        headers={'X-MSTR-ProjectID': project_id},
    )
