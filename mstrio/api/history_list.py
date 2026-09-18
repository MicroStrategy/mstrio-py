from typing import TYPE_CHECKING

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from requests import Response

    from mstrio.connection import Connection


@ErrorHandler(err_msg="Failed to list history list messages.")
def list_history_list_messages(
    connection: "Connection",
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
) -> "Response":
    """Lists history list messages, with optional filtering and pagination.

    Args:
        connection (Connection): Strategy REST API connection object.
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


@ErrorHandler(err_msg="Failed to send object to history list.")
def send_to_history_list(
    connection: "Connection",
    body: dict,
    project_id: str,
) -> "Response":
    """Sends a report, document, or dossier to history list.

    Args:
        connection (Connection): Strategy REST API connection object.
        body (dict): Request body with object ID, type, optional message ID,
            and optional display name.
        project_id (str): Project ID used in `X-MSTR-ProjectID` header.
    """

    headers = {"X-MSTR-ProjectID": project_id}

    return connection.post(
        endpoint="/api/historyList",
        headers=headers,
        json=body,
    )


@ErrorHandler(err_msg="Failed to get history list message.")
def get_history_list_message(
    connection: "Connection",
    message_id: str,
    type: str,
    project_id: str | None = None,
    scope: str | None = None,
) -> "Response":
    """Gets details of a history list message.

    Args:
        connection (Connection): Strategy REST API connection object.
        message_id (str): ID of a history list message.
        type (str): Type of target object. Available values include
            `report_definition` and `document_definition`.
        project_id (str | None): Project ID used in `X-MSTR-ProjectID` header.
        scope (str | None): History list retrieval scope. Available values:
            single_user, all_users, single_library_user.
    """

    params = {"objectType": type, "scope": scope}
    headers = {"X-MSTR-ProjectID": project_id}

    return connection.get(
        endpoint=f"/api/historyList/{message_id}",
        headers=headers,
        params=params,
    )


@ErrorHandler(err_msg="Failed to update history list message.")
def update_history_list_message(
    connection: "Connection",
    message_id: str,
    body: dict,
) -> "Response":
    """Updates a history list message.

    Note:
        The current admin-rest implementation supports only a `replace`
        operation on `/displayName`. Other patch paths are rejected by the
        server.

    Args:
        connection (Connection): Strategy REST API connection object.
        message_id (str): ID of a history list message.
        body (dict): Patch operations in the format:
            ```
                {
                    "operationList": [
                        {
                            "op": "replace",
                            "path": "/displayName",
                            "value": "<new display name>",
                        }
                    ]
                }
            ```
    """

    return connection.patch(endpoint=f"/api/historyList/{message_id}", json=body)


@ErrorHandler(err_msg="Failed to delete history list message.")
def delete_history_list_message(
    connection: "Connection",
    message_id: str,
    project_id: str | None = None,
    remove_others_message: bool = False,
) -> "Response":
    """Deletes a history list message.

    Args:
        connection (Connection): Strategy REST API connection object.
        message_id (str): ID of a history list message.
        project_id (str | None): Project ID used in `X-MSTR-ProjectID` header.
        remove_others_message (bool): Allow removing messages from other users
            than a requester as well. Defaults to False.
    """

    params = {"removeOthersMessage": remove_others_message}
    headers = {"X-MSTR-ProjectID": project_id}

    return connection.delete(
        endpoint=f"/api/historyList/{message_id}",
        headers=headers,
        params=params,
    )


@ErrorHandler(err_msg="Failed to delete history list messages in bulk.")
def delete_all_history_list_messages(
    connection: "Connection",
    body: dict,
    project_id: str | None = None,
    remove_others_message: bool = False,
) -> "Response":
    """Deletes history list messages in bulk.

    Note:
        This API deletes only messages that match provided `project_id`. All
        others are just silently ignored. Therefore when used, make sure to
        group the messages-to-remove by project ID.

    Args:
        connection (Connection): Strategy REST API connection object.
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


@ErrorHandler(err_msg="Failed to update history list message statuses in bulk.")
def update_history_list_messages_status(
    connection: "Connection",
    body: dict,
    project_id: str | None = None,
) -> "Response":
    """Updates statuses of history list messages in bulk.

    Args:
        connection (Connection): Strategy REST API connection object.
        body (dict): Request body containing message IDs and statuses, in the
            format:
            ```
                {
                    "messageIdList": [
                        {"id": "<id1>", "status": "read_message"}
                    ]
                }
            ```
        project_id (str | None): Project ID used in `X-MSTR-ProjectID` header.
    """

    headers = {"X-MSTR-ProjectID": project_id}

    return connection.post(
        endpoint="/api/historyList/updateMessages",
        headers=headers,
        json=body,
    )


@ErrorHandler(err_msg="Failed to send objects to history list in bulk.")
def bulk_send_to_history_list(
    connection: "Connection",
    body: dict,
) -> "Response":
    """Sends multiple reports, documents, or dossiers to history list.

    Args:
        connection (Connection): Strategy REST API connection object.
        body (dict): Request body containing project-scoped objects, in the
            format:
            ```
                {
                    "requests": [
                        {
                            "projectId": "<project_id>",
                            "objects": [
                                {
                                    "id": "<object_id>",
                                    "type": "report_definition",
                                }
                            ],
                        }
                    ]
                }
            ```
    """

    return connection.post(endpoint="/api/v2/historyList/bulk", json=body)


@ErrorHandler(err_msg="Failed to get history list messages by IDs.")
def get_history_list_messages_by_ids(
    connection: "Connection",
    body: dict,
    scope: str | None = None,
) -> "Response":
    """Gets history list messages by IDs.

    Args:
        connection (Connection): Strategy REST API connection object.
        body (dict): Request body containing message IDs, in the format:
            ```
                {"messageIds": ["<id1>", ...]}
            ```
        scope (str | None): History list retrieval scope. Available values:
            single_user, all_users, single_library_user.
    """

    headers = {"mstr-http-method-override": "GET"}
    params = {"scope": scope}

    return connection.post(
        endpoint="/api/v2/historyList/query",
        headers=headers,
        params=params,
        json=body,
    )
