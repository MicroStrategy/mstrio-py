from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(err_msg="Failed to list history list messages.")
def list_history_list_messages(
    connection: 'Connection',
    project_id: str | None = None,
    scope: str | None = None,
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
    limit: int = -1,
    fields: str | None = None,
) -> 'Response':
    """Lists history list messages, with optional filtering and pagination.

    Args:
        connection (Connection): Strategy One REST API connection object.
        project_id (str | None): Field to filter on project ID of messages.
        scope (str | None): History list retrieval scope. Available values:
            single_user, all_users, single_library_user
        status (str | None): Message status. Available values: msg_id, result,
            prompt_xml, error_msg_xml, job_running, in_sql_engine,
            in_query_engine, in_analytical_engine, in_resolution,
            waiting_for_cache, updating_cache, waiting, waiting_on_governor,
            waiting_for_project, waiting_for_children, preparing_output,
            construct_result, html_result, xml_result, running_on_other_node,
            loading_prompt, in_export_engine, need_to_get_results,
            user_request_async_export, user_requested_object_deleted_from_md.
        read_status (bool | None): Message read status.
        application_type (str | None): Application type.
        target_info_name (str | None): Name of history list message target
            object, used for filtering as 'contains'.
        target_info_object_id (str | None): ID of history list message target
            object.
        target_info_object_creator (str | None): Name of object creator.
        message_display_name (str | None): Message Display Name.
        owner_id (str | None): Message Owner ID.
        type (str | None): Type of the content cache.
        offset (int): Starting point within the collection of returned results.
            Used to control paging behavior. Default value is 0.
        limit (int): Maximum number of items returned for a single request.
            Used to control paging behavior. Use -1 for no limit. Default value
            is -1.
        fields (str | None): Comma-separated, top-level field whitelist that
            allows the client to selectively retrieve part of the response.
    """

    params = {
        "projectId": project_id,
        "scope": scope,
        "status": status,
        "readStatus": read_status,
        "applicationType": application_type,
        "targetInfo.name": target_info_name,
        "targetInfo.objectId": target_info_object_id,
        "targetInfo.objectCreator": target_info_object_creator,
        "messageDisplayName": message_display_name,
        "ownerId": owner_id,
        "type": type,
        "offset": offset,
        "limit": limit,
        "fields": fields,
    }

    return connection.get(endpoint="/api/v2/historyList", params=params)


@ErrorHandler(err_msg="Failed to delete history list messages in bulk.")
def delete_all_history_list_messages(
    connection: 'Connection',
    body: dict,
    project_id: str | None = None,
    remove_others_message: bool = False,
) -> 'Response':
    """Deletes history list messages in bulk.

    Note:
        This API deletes only messages that match provided `project_id`. All
        others are just silently ignored. Therefore when used, make sure to
        group the messages-to-remove by project ID.

    Args:
        connection (Connection): Strategy One REST API connection object.
        body (dict): Request body containing list of message IDs to delete,
            in the format:
            ```
                {"messageIdList": ["<id1>", ...]}
            ```
        project_id (str | None): Applies delete only in a scope of project
            (if applicable).
        remove_others_message (bool): Allow removing messages from other users
            than a requester as well. Defaults to False.
    """

    params = {"removeOthersMessage": remove_others_message}
    headers = {"X-MSTR-ProjectID": project_id}

    return connection.post(
        endpoint="/api/historyList/deleteMessages",
        headers=headers,
        params=params,
        json=body,
    )
