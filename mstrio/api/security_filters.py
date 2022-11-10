from typing import TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg='Error getting members of security filter with ID {id}')
def get_security_filter_members(
    connection: "Connection", id: str, project_id: str = None, error_msg: str = None
):
    """Get the users and user groups that the specified security filter is
    applied to."""
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        url=f"{connection.base_url}/api/securityFilters/{id}/members",
        headers={'X-MSTR-ProjectID': project_id}
    )


@ErrorHandler(err_msg='Error updating members of security filter with ID {id}')
def update_security_filter_members(
    connection: "Connection",
    id: str,
    body: dict,
    project_id: str = None,
    error_msg: str = None,
    throw_error: bool = True
):
    """Update members information for a specific security filter."""
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.patch(
        url=f"{connection.base_url}/api/securityFilters/{id}/members",
        headers={'X-MSTR-ProjectID': project_id},
        json=body
    )


@unpack_information
@ErrorHandler(err_msg='Error creating new security filter.')
def create_security_filter(
    connection: "Connection",
    body: dict,
    show_filter_tokens: bool = False,
    show_expression_as: str = None,
    error_msg: str = None,
    throw_error: bool = True,
    **kwargs
):
    """Creates a new security filter in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        body (dict): Security Filter creation body
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
            url=f"{connection.base_url}/api/model/securityFilters",
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
            params={
                'showFilterTokens': str(show_filter_tokens).lower(),
                'showExpressionAs': show_expression_as
            }
        )


@unpack_information
@ErrorHandler(err_msg='Error getting security filter {id} definition.')
def get_security_filter(
    connection: "Connection",
    id: str,
    project_id: str = None,
    changeset_id: str = None,
    show_expression_as: str = None,
    show_fields: str = None,
    show_filter_tokens: bool = False,
    error_msg: str = None
):
    """Get the definition of a security filter.
    The project ID is required to return a security filter's definition
    in metadata. The changeset ID is required to return a security filter's
    definition within a specific changeset. To execute the request,
    either the project ID or changeset ID needs to be provided.
    If both are provided, only the changeset ID is used.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Security Filter ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        show_expression_as (str, optional): specify how expressions should be
            presented
            Available values:
                - `tree` (default)
                - `tokens`
        show_fields: Specifies what additional information to return.
            Only 'acl' is supported.
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id

    return connection.get(
        url=f"{connection.base_url}/api/model/securityFilters/{id}",
        headers={
            'X-MSTR-ProjectID': project_id, 'X-MSTR-MS-Changeset': changeset_id
        },
        params={
            'showExpressionAs': show_expression_as,
            'showFields': show_fields,
            'showFilterTokens': str(show_filter_tokens).lower()
        }
    )


@unpack_information
@ErrorHandler(err_msg='Error updating security filter with ID {id}')
def update_security_filter(
    connection: "Connection",
    id: str,
    body: dict,
    show_expression_as: str = None,
    show_fields: str = None,
    show_filter_tokens: bool = False,
    error_msg: str = None,
    throw_error: bool = True
):
    """Updates a specific security filter in the changeset,
    based on the definition provided in the request body.

    Args:
        connection: MicroStrategy REST API connection object
        id (str): Security Filter ID. The ID can be:
            - the object ID used in the metadata.
            - the object ID used in the changeset, but not yet committed
            to metadata.
        body (dict): Security Filter update info
        show_expression_as (str, optional): specify how expressions should be
            presented
            Available values:
                - `tree` (default)
                - `tokens`
        show_fields: Specifies what additional information to return.
            Only 'acl' is supported.
        show_filter_tokens (bool, optional): specify whether `qualification`
            is returned in `tokens` format, along with `text` and `tree`
            format
        error_msg (str, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.put(
            url=f"{connection.base_url}/api/model/securityFilters/{id}",
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFields': show_fields,
                'showFilterTokens': str(show_filter_tokens).lower()
            },
            json=body
        )


@ErrorHandler(err_msg='Error getting information for set of security filters.')
def get_security_filters(
    connection: "Connection",
    project_id: str = None,
    name_contains: str = None,
    offset: int = 0,
    limit: int = -1,
    fields: str = None,
    error_msg: str = None
):
    """Get all list of Security Filters for a project.
    You can set the offset and limit for pagination function.

    Args:
        connection: MicroStrategy REST API connection object
        project_id (string, optional): id of project
        name_contains (string, optional): text that security filter's name
            must contain
        offset (int, optional): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
        fields: top-level field whitelist which allows client to selectively
            retrieve part of the response model
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    return connection.get(
        url=f'{connection.base_url}/api/securityFilters',
        headers={'X-MSTR-ProjectID': project_id},
        params={
            'nameContains': name_contains,
            'offset': offset,
            'limit': limit,
            'fields': fields
        }
    )
