from typing import TYPE_CHECKING

from mstrio.api import history_list as history_list_api
from mstrio.utils.helper import get_response_json

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_history_list_messages(
    connection: "Connection",
    project_id: str | None = None,
    scope: str | None = "all_users",
    status: str | None = None,
    read_status: bool | None = None,
    application_type: str | None = None,
    target_info_name: str | None = None,
    target_info_object_id: str | None = None,
    target_info_object_creator: str | None = None,
    message_display_name: str | None = None,
    owner_id: str | None = None,
    type: str | None = None,
    offset: int = 0,
    limit: int | None = None,
    fields: str | None = None,
) -> list[dict]:
    """List history list message dictionaries."""

    response = history_list_api.list_history_list_messages(
        connection=connection,
        project_id=project_id,
        scope=scope,
        status=status,
        read_status=read_status,
        application_type=application_type,
        target_info_name=target_info_name,
        target_info_object_id=target_info_object_id,
        target_info_object_creator=target_info_object_creator,
        message_display_name=message_display_name,
        owner_id=owner_id,
        type=type,
        offset=offset,
        limit=-1 if limit is None else limit,
        fields=fields,
    )
    return get_response_json(response).get("historyList") or []


def get_history_list_message(
    connection: "Connection",
    message_id: str,
    type: str,
    project_id: str | None = None,
    scope: str | None = "all_users",
) -> dict:
    """Get a history list message dictionary."""

    response = history_list_api.get_history_list_message(
        connection=connection,
        message_id=message_id,
        type=type,
        project_id=project_id,
        scope=scope,
    )
    return get_response_json(response)


def get_history_list_messages_by_ids(
    connection: "Connection",
    message_ids: list[str],
    scope: str | None = "all_users",
) -> list[dict]:
    """Get history list message dictionaries by IDs."""

    response = history_list_api.get_history_list_messages_by_ids(
        connection=connection,
        body={"messageIds": message_ids},
        scope=scope,
    )
    return get_response_json(response).get("historyList") or []
