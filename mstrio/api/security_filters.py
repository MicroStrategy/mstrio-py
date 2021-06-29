from enum import Enum
from mstrio.utils.helper import response_handler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mstrio.connection import Connection


class ShowExpressionAs(Enum):
    TEXT = None,
    TREE = "tree",
    TOKENS = "tokens"


class UpdateOperator(Enum):
    APPLY = "addElements"
    REVOKE = "removeElements"


def get_security_filter_members(connection: "Connection", id: str, project_id: str = None,
                                error_msg: str = None):
    """Get the users and user groups that the specified security filter is
    applied to."""
    if project_id is None:
        connection._validate_application_selected()
        project_id = connection.application_id
    response = connection.session.get(
        url=f"{connection.base_url}/api/securityFilters/{id}/members",
        headers={'X-MSTR-ProjectID': project_id})
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting members of security filter."
        response_handler(response, error_msg)
    return response


def update_security_filter_members(connection: "Connection", id: str, body: dict,
                                   project_id: str = None, error_msg: str = None,
                                   throw_err: bool = True):
    """Update members information for a specific security filter."""
    if project_id is None:
        connection._validate_application_selected()
        project_id = connection.application_id
    response = connection.session.patch(
        url=f"{connection.base_url}/api/securityFilters/{id}/members",
        headers={'X-MSTR-ProjectID': project_id}, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error updating members of security filter."
        response_handler(response, error_msg, throw_err)
    return response


def create_security_filter(connection: "Connection", changeset_id: str, body: dict,
                           show_filter_tokens: bool = False, show_expression_as: str = None,
                           error_msg: str = None, throw_error: bool = True, **kwargs):
    """Create a security filter."""
    response = connection.session.post(
        url=f"{connection.base_url}/api/model/securityFilters",
        headers={'X-MSTR-MS-Changeset': changeset_id}, json=body, params={
            'showFilterTokens': str(show_filter_tokens).lower(),
            'showExpressionAs': show_expression_as
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error creating security filter."
        response_handler(response, error_msg, throw_error)
    return response


def read_security_filter(connection: "Connection", id: str, project_id: str = None,
                         changeset_id: str = None, show_expression_as: str = None,
                         show_fields: str = None, show_filter_tokens: bool = False,
                         error_msg: str = None):
    """Read security filter."""
    response = connection.session.get(
        url=f"{connection.base_url}/api/model/securityFilters/{id}", headers={
            'X-MSTR-ProjectID': project_id,
            'X-MSTR-MS-Changeset': changeset_id
        }, params={
            'showExpressionAs': show_expression_as,
            'showFields': show_fields,
            'showFilterTokens': str(show_filter_tokens).lower()
        })
    if not response.ok:
        if error_msg is None:
            error_msg = "Error getting security filter definition."
        response_handler(response, error_msg)
    return response


def update_security_filter(connection: "Connection", id: str, changeset_id: str, body: dict,
                           show_expression_as: str = None, show_fields: str = None,
                           show_filter_tokens: bool = False, error_msg: str = None,
                           throw_error: bool = True):
    """Update security filter."""
    response = connection.session.put(
        url=f"{connection.base_url}/api/model/securityFilters/{id}",
        headers={'X-MSTR-MS-Changeset': changeset_id}, params={
            'showExpressionAs': show_expression_as,
            'showFields': show_fields,
            'showFilterTokens': str(show_filter_tokens).lower()
        }, json=body)
    if not response.ok:
        if error_msg is None:
            error_msg = "Error updating security filter."
        response_handler(response, error_msg, throw_error)
    return response
