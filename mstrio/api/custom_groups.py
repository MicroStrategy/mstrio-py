from typing import TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@unpack_information
@ErrorHandler(err_msg="Error getting the custom group with ID: {id}.")
def get_custom_group(
    connection: "Connection",
    id: str,
    project_id: str | None = None,
    changeset_id: str | None = None,
    show_expression_as: str | None = None,
    error_msg: str | None = None,
):
    """Get the definition of a Custom Group.
    The project ID is required to return a Custom Group object definition
    in metadata. The changeset ID is required to return the object definition
    within a specific changeset. To execute the request, either the project ID
    or changeset ID needs to be provided.
    If both are provided, only the changeset ID is used.

    Args:
        connection: Strategy One REST API connection object
        id (str): Custom Group ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        error_msg (str, optional): Custom Error Message for Error Handling
        show_expression_as (str, optional): specify how expressions should be
            presented
            Available values:
                - `tree` (default)
                - `tokens`

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        endpoint=f"/api/model/customGroups/{id}",
        headers={"X-MSTR-ProjectID": project_id, "X-MSTR-MS-Changeset": changeset_id},
        params={
            "showExpressionAs": show_expression_as,
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error creating the custom group.")
def create_custom_group(
    connection: "Connection",
    body: dict,
    project_id: str | None = None,
    show_expression_as: str | None = None,
    error_msg: str | None = None,
):
    """Create a Custom Group in the specified project.

    Args:
        connection: Strategy One REST API connection object
        body (dict): Dictionary representing the Custom Group to be created.
        project_id (str, optional): Project ID
        show_expression_as (str, optional): specify how expressions should be
            presented in the new Custom Group object in response
            Available values:
                - `tree` (default)
                - `tokens`
    """

    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    with changeset_manager(connection, body=body) as changeset_id:
        return connection.post(
            endpoint="/api/model/customGroups",
            headers={
                "X-MSTR-ProjectID": project_id,
                "X-MSTR-MS-Changeset": changeset_id,
            },
            params={
                "showExpressionAs": show_expression_as,
            },
            json=body,
        )
