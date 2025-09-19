from requests import Response

from mstrio.connection import Connection
from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler


@unpack_information
@ErrorHandler(err_msg='Error getting prompt with ID: {id}.')
def get_prompt(
    connection: Connection,
    id: str,
    project_id: str | None = None,
    changeset_id: str | None = None,
    show_expression_as: list[str] | None = None,
    error_msg: str | None = None,
) -> Response:
    """Get a prompt by its ID.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        id (str): ID of the prompt to get
        project_id (str, optional): ID of the project to which the prompt
            belongs
        changeset_id (str, optional): ID of the changeset to use. Needed to
            return a prompt's definition within a specific changeset
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats
        error_msg (str, optional): Custom error message

    Returns:
        HTTP response object. Returns 200 on success.
    """
    if project_id is None:
        connection._validate_project_selected()
        project_id = connection.project_id
    return connection.get(
        endpoint=f'/api/model/prompts/{id}',
        params={'showExpressionAs': show_expression_as},
        headers={'X-MSTR-ProjectID': project_id, 'X-MSTR-MS-Changeset': changeset_id},
    )


@unpack_information
@ErrorHandler(err_msg='Error creating prompt with name: {name}.')
def create_prompt(
    connection: Connection,
    body: dict,
    show_expression_as: list[str] | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create a new prompt.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the new prompt
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats.

    Returns:
        HTTP response object. Returns 201 on success.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint='/api/model/prompts',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={'showExpressionAs': show_expression_as},
            json=body,
        )


@unpack_information
@ErrorHandler(err_msg='Error updating prompt with ID: {id}.')
def update_prompt(
    connection: Connection,
    id: str,
    body: dict,
    show_expression_as: list[str] | None = None,
    error_msg: str | None = None,
) -> Response:
    """Update an existing prompt.

    Args:
        connection (Connection): Strategy One connection object
        id (str): ID of the prompt to update
        body (dict): JSON-formatted body with updated prompt data
        show_expression_as (list[str], optional): Specifies the format in
            which the expressions are returned in response
            Available values: 'tokens', 'tree'
            If omitted, the expression is returned in 'text' format
            If 'tree', the expression is returned in 'text' and 'tree' formats.
            If 'tokens', the expression is returned in 'text' and 'tokens'
            formats.

    Returns:
        HTTP response object. Returns 200 on success.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.put(
            endpoint=f'/api/model/prompts/{id}',
            headers={
                'X-MSTR-MS-Changeset': changeset_id,
                'showExpressionAs': show_expression_as,
            },
            json=body,
        )


@ErrorHandler(err_msg='Error creating personal answer for prompt with ID: {id}.')
def create_personal_answer(
    connection: Connection,
    id: str,
    project_id: str,
    body: dict,
    instance_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Create personal answers for a prompt.

    Args:
        connection (Connection): Strategy One connection object
        id (str): ID of the prompt to create a personal answer for
        project_id (str): ID of the project to which the prompt belongs
        body (dict): JSON-formatted body with personal answer data
        instance_id (str, optional): ID of the instance. Only needed for
            embedded prompts, not for standalone prompts
        fields (str, optional): Fields to include in the response
        error_msg (str, optional): Custom error message

    Returns:
        HTTP response object. Returns 201 on success.
    """
    return connection.post(
        endpoint=f'/api/prompts/{id}/personalAnswers',
        headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-InstanceID': instance_id,
            'fields': fields,
        },
        json=body,
    )


@ErrorHandler(err_msg='Error editing personal answer for prompt with ID: {id}.')
def edit_personal_answer(
    connection: Connection,
    id: str,
    project_id: str,
    personal_answer_id: str,
    body: dict,
    instance_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> Response:
    """Edit a personal answer for a prompt.

    Args:
        connection (Connection): Strategy One connection object
        id (str): ID of the prompt to edit a personal answer for
        project_id (str): ID of the project containing the prompt
        personal_answer_id (str): ID of the personal answer to edit
        body (dict): JSON-formatted body with updated personal answer data
        instance_id (str, optional): ID of the instance. Only needed for
            embedded prompts, not for standalone prompts
        fields (str, optional): Fields to include in the response
        error_msg (str, optional): Custom error message

    Returns:
        HTTP response object. Returns 200 on success."""
    return connection.patch(
        endpoint=f'/api/prompts/{id}/personalAnswers/{personal_answer_id}',
        headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-InstanceID': instance_id,
            'fields': fields,
        },
        json=body,
    )
