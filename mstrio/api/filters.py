from typing import Optional, TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@unpack_information
@ErrorHandler(err_msg="Error creating the filter.")
def create_filter(
    connection: "Connection",
    body: dict,
    show_expression_as: Optional[str] = None,
    show_filter_tokens: bool = False,
    error_msg: Optional[str] = None,
):
    """Creates a new filter in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        body (dict): Filter creation body
        error_msg (str, optional): Custom Error Message for Error Handling
        show_expression_as (str, optional): specify how expressions should be
            presented
            Available values:
                - `tree` (default)
                - `tokens`
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            url=f"{connection.base_url}/api/model/filters",
            headers={"X-MSTR-MS-Changeset": changeset_id},
            json=body,
            params={
                "showExpressionAs": show_expression_as,
                "showFilterTokens": str(show_filter_tokens).lower(),
            },
        )


@unpack_information
@ErrorHandler(err_msg="Error getting the filter with ID: {id}.")
def get_filter(
    connection: "Connection",
    id: str,
    project_id: Optional[str] = None,
    changeset_id: Optional[str] = None,
    show_expression_as: Optional[str] = None,
    show_filter_tokens: bool = False,
    error_msg: Optional[str] = None,
):
    """Get the definition of a filter.
    The project ID is required to return a filter's definition
    in metadata. The changeset ID is required to return a filter's
    definition within a specific changeset. To execute the request,
    either the project ID or changeset ID needs to be provided.
    If both are provided, only the changeset ID is used.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Filter ID. The ID can be:
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
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/model/filters/{id}",
        headers={
            "X-MSTR-ProjectID": project_id, "X-MSTR-MS-Changeset": changeset_id
        },
        params={
            "showExpressionAs": show_expression_as,
            "showFilterTokens": str(show_filter_tokens).lower(),
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error updating the filter with ID: {id}.")
def update_filter(
    connection: "Connection",
    id: str,
    body: dict,
    show_expression_as: Optional[str] = None,
    show_filter_tokens: bool = False,
    error_msg: Optional[str] = None,
):
    """Updates a specific filter in the changeset,
    based on the definition provided in the request body.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Filter ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        body (dict): Filter update info
        error_msg (str, optional): Custom Error Message for Error Handling
        show_expression_as (str, optional): specify how expressions should be
            presented
            Available values:
                - `tree` (default)
                - `tokens`
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.put(
            url=f"{connection.base_url}/api/model/filters/{id}",
            headers={"X-MSTR-MS-Changeset": changeset_id},
            json=body,
            params={
                "showExpressionAs": show_expression_as,
                "showFilterTokens": str(show_filter_tokens).lower(),
            },
        )
