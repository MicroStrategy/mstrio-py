from typing import Optional

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_decorator, unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.wip import module_wip, WipLevels

module_wip(globals(), level=WipLevels.WARNING)


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error creating a metric')
def create_metric(
    connection: Connection,
    changeset_id: str,
    body: dict,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: bool = False
):
    """Create a new metric in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        changeset_id: ID of a changeset
        body: Metric creation data
        show_expression_as: Specifies the format in which the expressions are
           returned in response
           Available values: "tokens", "tree"
           If omitted, the expression is returned in "text" format
           If "tree", the expression is returned in "text" and "tree" formats.
           If "tokens", the expression is returned in "text" and "tokens"
           formats.
        show_filter_tokens: Specifies whether the "condition" in threshold is
            returned in "tokens" format, along with "text" and "tree" formats.
            If omitted or false, only "text" and "tree" formats are returned.
            If true, all "text", "tree" and "tokens" formats are returned.
    Return:
        HTTP response object. Expected status: 201
    """
    return connection.post(
        url=f"{connection.base_url}/api/model/metrics",
        headers={"X-MSTR-MS-Changeset": changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower()
        },
        json=body,
    )


@unpack_information
@ErrorHandler(err_msg='Error getting metric with ID: {id}')
def get_metric(
    connection: Connection,
    id: str,
    changeset_id: Optional[str] = None,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: bool = False
):
    """Get definition of a single metric by id

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a metric
        changeset_id: ID of a changeset
        show_expression_as: Specifies the format in which the expressions
           are returned in response
           Available values: "tokens", "tree"
           If omitted, the expression is returned in "text" format
           If "tree", the expression is returned in "text" and "tree" formats.
           If "tokens", the expression is returned in "text" and "tokens"
           formats.
        show_filter_tokens: Specifies whether the "condition" in threshold is
            returned in "tokens" format, along with "text" and "tree" formats.
            If omitted or false, only "text" and "tree" formats are returned.
            If true, all "text", "tree" and "tokens" formats are returned.

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        url=f'{connection.base_url}/api/model/metrics/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower()
        }
    )


@changeset_decorator
@unpack_information
@ErrorHandler(err_msg='Error updating metric with ID: {id}')
def update_metric(
    connection: Connection,
    id: str,
    changeset_id: str,
    body: dict,
    show_expression_as: Optional[list[str]] = None,
    show_filter_tokens: bool = False
):
    """Update a specific metric in the changeset,
    based on the definition provided in request body.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a metric
        changeset_id: ID of a changeset
        body: Metric creation data
        show_expression_as: Specifies the format in which the expressions are
           returned in response
           Available values: "tokens", "tree"
           If omitted, the expression is returned in "text" format
           If "tree", the expression is returned in "text" and "tree" formats.
           If "tokens", the expression is returned in "text" and "tokens"
           formats.
        show_filter_tokens: Specifies whether the "condition" in threshold is
            returned in "tokens" format, along with "text" and "tree" formats.
            If omitted or false, only "text" and "tree" formats are returned.
            If true, all "text", "tree" and "tokens" formats are returned.

    Return:
        HTTP response object. Expected status: 201
    """
    return connection.put(
        url=f'{connection.base_url}/api/model/metrics/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower()
        },
        json=body
    )
