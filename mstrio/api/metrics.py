from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@unpack_information
@ErrorHandler(err_msg="Error creating a metric")
def create_metric(
    connection: Connection,
    body: dict,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool = False,
):
    """Create a new metric in the changeset,
    based on the definition provided in request body.

    Args:
        connection: Strategy One REST API connection object
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
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint='/api/model/metrics',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': str(show_filter_tokens).lower(),
            },
            json=body,
        )


@unpack_information
@ErrorHandler(err_msg="Error getting metric with ID: {id}")
def get_metric(
    connection: Connection,
    id: str,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool = False,
):
    """Get definition of a single metric by id

    Args:
        connection: Strategy One REST API connection object
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
        endpoint=f'/api/model/metrics/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id},
        params={
            'showExpressionAs': show_expression_as,
            'showFilterTokens': str(show_filter_tokens).lower(),
        },
    )


@unpack_information
@ErrorHandler(err_msg="Error updating metric with ID: {id}")
def update_metric(
    connection: Connection,
    id: str,
    body: dict,
    show_expression_as: list[str] | None = None,
    show_filter_tokens: bool = False,
):
    """Update a specific metric in the changeset,
    based on the definition provided in request body.

    Args:
        connection: Strategy One REST API connection object
        id: ID of a metric
        body: Metric update data
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
    with changeset_manager(connection) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/metrics/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'showExpressionAs': show_expression_as,
                'showFilterTokens': str(show_filter_tokens).lower(),
            },
            json=body,
        )


@ErrorHandler(err_msg="Error getting VLDB settings for a metric with ID: {id}")
def get_vldb_settings(connection: Connection, id: str):
    """Get definition of VLDB settings for a metric with id

    Args:
        connection: Strategy One REST API connection object
        id: ID of a metric

    Return:
        HTTP response object. Expected status: 200
    """
    return connection.get(
        endpoint=f'/api/model/metrics/{id}?showAdvancedProperties=true'
    )


@ErrorHandler(err_msg="Error getting metadata of VLDB settings for metric with ID {id}")
def get_applicable_vldb_settings(
    connection: 'Connection', id: str, error_msg: str = None
):
    """Get metadata of advanced VLDB settings for a metric.

    Args:
        connection (Connection): Strategy One REST API connection object
        id (string): Metric ID
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object.
    """

    with changeset_manager(connection) as changeset_id:
        return connection.get(
            endpoint=f'/api/model/metrics/{id}/applicableAdvancedProperties',
            headers={'X-MSTR-MS-Changeset': changeset_id},
        )
