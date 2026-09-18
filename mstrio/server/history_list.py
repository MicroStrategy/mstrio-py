import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import history_list as hl_api
from mstrio.types import ObjectTypes
from mstrio.utils import helper
from mstrio.utils.entity import EntityBase
from mstrio.utils.response_processors import history_list as hl_processors

if TYPE_CHECKING:
    from mstrio.connection import Connection


logger = logging.getLogger(__name__)


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
    to_dictionary: bool = True,
) -> "list[HistoryList] | list[dict]":
    """List history list messages.

    Args:
        connection (Connection): Strategy connection object.
        project_id (str, optional): Project ID used to filter messages.
        scope (str, optional): History list retrieval scope. Available values:
            `single_user`, `all_users`, and `single_library_user`.
        status (str, optional): Message request status filter.
        read_status (bool, optional): Message read status filter.
        application_type (str, optional): Client application type filter.
        target_info_name (str, optional): Target object name partial-match
            filter.
        target_info_object_id (str, optional): Target object ID filter.
        target_info_object_creator (str, optional): Target object creator
            name partial-match filter.
        message_display_name (str, optional): Message display name
            partial-match filter.
        owner_id (str, optional): Message owner ID filter.
        type (str, optional): Content type filter. Available values include
            `report`, `document`, and `dossier`.
        offset (int, optional): Starting point within returned results.
        limit (int, optional): Maximum number of messages to retrieve. If
            `None`, retrieves all available messages.
        fields (str, optional): Comma-separated, top-level field whitelist.
        to_dictionary (bool, optional): If `True`, returns dictionaries.
            If `False`, returns `HistoryList` objects.

    Returns:
        List of history list message dictionaries or `HistoryList` objects.
    """

    message_dicts = hl_processors.list_history_list_messages(
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
        limit=limit,
        fields=fields,
    )

    if to_dictionary:
        return message_dicts

    return [
        HistoryList.from_dict(source=msg, connection=connection)
        for msg in message_dicts
    ]


def get_history_list_messages_by_ids(
    connection: "Connection",
    message_ids: list[str],
    scope: str | None = "all_users",
    to_dictionary: bool = True,
) -> "list[HistoryList] | list[dict]":
    """Get history list messages by IDs.

    Args:
        connection (Connection): Strategy connection object.
        message_ids (list[str]): IDs of history list messages.
        scope (str, optional): History list retrieval scope. Available values:
            `single_user`, `all_users`, and `single_library_user`.
        to_dictionary (bool, optional): If `True`, returns dictionaries.
            If `False`, returns `HistoryList` objects.

    Returns:
        List of history list message dictionaries or `HistoryList` objects.
    """

    message_dicts = hl_processors.get_history_list_messages_by_ids(
        connection=connection,
        message_ids=message_ids,
        scope=scope,
    )

    if to_dictionary:
        return message_dicts

    return [
        HistoryList.from_dict(source=msg, connection=connection)
        for msg in message_dicts
    ]


def send_to_history_list(
    connection: "Connection",
    object_id: str,
    object_type: str,
    project_id: str,
    message_id: str | None = None,
    display_name: str | None = None,
) -> dict:
    """Send a report, document, or dossier to history list.

    Args:
        connection (Connection): Strategy connection object.
        object_id (str): ID of the object to send.
        object_type (str): Object type accepted by REST API.
        project_id (str): Project ID used in `X-MSTR-ProjectID` header.
        message_id (str, optional): Optional report or document instance ID.
        display_name (str, optional): Optional display name.

    Returns:
        Response data dictionary.
    """

    body = {
        "id": object_id,
        "type": object_type,
        "msgId": message_id,
        "displayName": display_name,
    }
    body = {key: value for key, value in body.items() if value is not None}
    response = hl_api.send_to_history_list(
        connection=connection,
        body=body,
        project_id=project_id,
    )
    return helper.get_response_json(response)


def bulk_send_to_history_list(connection: "Connection", requests: list[dict]) -> dict:
    """Send multiple project-scoped objects to history list.

    Args:
        connection (Connection): Strategy connection object.
        requests (list[dict]): Project-scoped send requests accepted by REST
            API, each containing `projectId` and `objects`.

    Returns:
        Response data dictionary.
    """

    response = hl_api.bulk_send_to_history_list(
        connection=connection,
        body={"requests": requests},
    )
    return helper.get_response_json(response)


def update_history_list_messages_status(
    connection: "Connection",
    message_statuses: list[dict],
    project_id: str | None = None,
) -> dict:
    """Update statuses of history list messages in bulk.

    Args:
        connection (Connection): Strategy connection object.
        message_statuses (list[dict]): Message status updates in the format
            `{"id": "<message_id>", "status": "read_message"}`.
        project_id (str, optional): Project ID used in `X-MSTR-ProjectID`
            header.

    Returns:
        Response data dictionary.
    """

    response = hl_api.update_history_list_messages_status(
        connection=connection,
        body={"messageIdList": message_statuses},
        project_id=project_id,
    )
    return helper.get_response_json(response)


def delete_all_history_list_messages(connection: "Connection") -> None:
    """Removes all History List messages from all the users.

    Args:
        connection (Connection): Strategy connection object.
    """

    messages = list_history_list_messages(connection, to_dictionary=True)

    # Group them by project, as API requires for a project header to be present
    # when deleting multiple items and will remove only those that belong to the
    # project at hand and will just ignore all others silently
    grouped = defaultdict(list)
    for msg in messages:
        grouped[msg.get("projectId", "-")].append(msg.get("messageId"))

    # TODO: consider multithreading
    for project_id, items in grouped.items():
        project_id = None if project_id == "-" else project_id
        # TODO: on paper should always have `messageId` property
        # but could not verify it fully at this point, hence filtering
        items = [m for m in items if m]

        if items:
            hl_api.delete_all_history_list_messages(
                connection,
                body={"messageIdList": items},
                project_id=project_id,
                remove_others_message=True,
            )

    if list_history_list_messages(connection, limit=1, to_dictionary=True):
        logger.warning("Some History List messages were not removed.")
    elif config.verbose:
        logger.info("All History List messages removed successfully.")


class HistoryList(EntityBase):
    """Class representation of a Strategy history list message.

    Attributes:
        connection: A Strategy connection object.
        id: History list message ID.
        name: Message display name or title.
        title: Message title.
        display_name: Message display name.
        status: Message status.
        request_status: Request status.
        target_info: Information about the target object.
        project_id: Project ID.
        project_name: Project name.
        owner_id: Message owner ID.
        owner_name: Message owner name.
    """

    _OBJECT_TYPE = ObjectTypes.NOT_SUPPORTED
    _REST_ATTR_MAP = {
        **EntityBase._REST_ATTR_MAP,
        "message_id": "id",
    }
    _API_GETTERS_KEEP_PRIVATE = EntityBase._API_GETTERS_KEEP_PRIVATE | {"type"}

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        message_id: str | None = None,
        name: str | None = None,
        project_id: str | None = None,
        scope: str = "all_users",
    ) -> None:
        """Initialize a history list message by ID or name.

        Args:
            connection (Connection): Strategy connection object.
            id (str, optional): History list message ID.
            message_id (str, optional): Alias for `id`.
            name (str, optional): Message display name.
            project_id (str, optional): Project ID used to scope lookup and
                message operations.
            scope (str, optional): History list retrieval scope used to look up
                the message. Defaults to `all_users`.
        """

        message_id = id or message_id
        if not message_id and not name:
            raise ValueError("Please specify either 'id', 'message_id', or 'name'.")

        message = self._find_message(
            connection=connection,
            message_id=message_id,
            name=name,
            project_id=project_id,
            scope=scope,
        )
        self._init_variables(
            connection=connection,
            default_value=None,
            lookup_scope=scope,
            **message,
        )
        if config.verbose:
            logger.info(self)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        kwargs = helper.camel_to_snake(kwargs)
        kwargs = self._rest_to_python(kwargs)
        if kwargs.get("name") is None:
            kwargs["name"] = kwargs.get("display_name") or kwargs.get("title")
        super()._init_variables(default_value=default_value, **kwargs)
        self.title = kwargs.get("title", default_value)
        self.state_id = kwargs.get("state_id", default_value)
        self.save_state_id = kwargs.get("save_state_id", default_value)
        self.server_state_id = kwargs.get("server_state_id", default_value)
        self.message_type = kwargs.get("message_type", default_value)
        self.status = kwargs.get("status", default_value)
        self.sequence_number = kwargs.get("sequence_number", default_value)
        self.parent_id = kwargs.get("parent_id", default_value)
        self.client_type = kwargs.get("client_type", default_value)
        self.request_type = kwargs.get("request_type", default_value)
        self.request_status = kwargs.get("request_status", default_value)
        self.start_time = kwargs.get("start_time", default_value)
        self.start_time_utc = kwargs.get("start_time_utc", default_value)
        self.finish_time = kwargs.get("finish_time", default_value)
        self.finish_time_utc = kwargs.get("finish_time_utc", default_value)
        self.creation_time = kwargs.get("creation_time", default_value)
        self.target_info = kwargs.get("target_info", default_value)
        self.project_id = kwargs.get("project_id", default_value)
        self.project_name = kwargs.get("project_name", default_value)
        self.result_flags = kwargs.get("result_flags", default_value)
        self.cache_id = kwargs.get("cache_id", default_value)
        self.message_text = kwargs.get("message_text", default_value)
        self.display_name = kwargs.get("display_name", self.name)
        self.owner_name = kwargs.get("owner_name", default_value)
        self.owner_id = kwargs.get("owner_id", default_value)
        self.locale = kwargs.get("locale", default_value)
        self.language = kwargs.get("language", default_value)
        self.children = kwargs.get("children", default_value)
        self.view_media = kwargs.get("view_media", default_value)
        self.inbox_message_flag = kwargs.get("inbox_message_flag", default_value)
        self.job_stats = kwargs.get("job_stats", default_value)
        self.message_stats = kwargs.get("message_stats", default_value)
        self.report_details = kwargs.get("report_details", default_value)
        self._lookup_scope = kwargs.get("lookup_scope", "all_users")

    @classmethod
    def _find_message(
        cls,
        connection: "Connection",
        message_id: str | None = None,
        name: str | None = None,
        project_id: str | None = None,
        scope: str = "all_users",
    ) -> dict:
        if message_id:
            messages = hl_processors.get_history_list_messages_by_ids(
                connection=connection,
                message_ids=[message_id],
                scope=scope,
            )
        else:
            messages = hl_processors.list_history_list_messages(
                connection=connection,
                project_id=project_id,
                scope=scope,
                message_display_name=name,
            )
            messages = [
                msg
                for msg in messages
                if name in {msg.get("displayName"), msg.get("title")}
            ]

        if not messages:
            identifier = f"ID: '{message_id}'" if message_id else f"name: '{name}'"
            raise ValueError(
                f"There is no HistoryList message with the given {identifier}."
            )
        if len(messages) > 1:
            raise ValueError(
                f"There is more than one HistoryList message with name: '{name}'."
            )
        return messages[0]

    @staticmethod
    def list_HL_messages(
        connection: "Connection",
        **kwargs,
    ) -> "list[HistoryList] | list[dict]":
        """List history list messages.

        Args:
            connection (Connection): Strategy connection object.
            **kwargs: Parameters accepted by `list_history_list_messages`.

        Returns:
            List of history list message dictionaries or `HistoryList` objects.
        """

        return list_history_list_messages(connection=connection, **kwargs)

    @staticmethod
    def get_messages_by_ids(
        connection: "Connection",
        message_ids: list[str],
        **kwargs,
    ) -> "list[HistoryList] | list[dict]":
        """Get history list messages by IDs.

        Args:
            connection (Connection): Strategy connection object.
            message_ids (list[str]): IDs of history list messages.
            **kwargs: Parameters accepted by
                `get_history_list_messages_by_ids`.

        Returns:
            List of history list message dictionaries or `HistoryList` objects.
        """

        return get_history_list_messages_by_ids(
            connection=connection,
            message_ids=message_ids,
            **kwargs,
        )

    @staticmethod
    def send(
        connection: "Connection",
        object_id: str,
        object_type: str,
        project_id: str,
        message_id: str | None = None,
        display_name: str | None = None,
    ) -> dict:
        """Send a report, document, or dossier to history list."""

        return send_to_history_list(
            connection=connection,
            object_id=object_id,
            object_type=object_type,
            project_id=project_id,
            message_id=message_id,
            display_name=display_name,
        )

    @staticmethod
    def bulk_send(connection: "Connection", requests: list[dict]) -> dict:
        """Send multiple project-scoped objects to history list."""

        return bulk_send_to_history_list(connection=connection, requests=requests)

    @staticmethod
    def update_messages_status(
        connection: "Connection",
        message_statuses: list[dict],
        project_id: str | None = None,
    ) -> dict:
        """Update statuses of history list messages in bulk."""

        return update_history_list_messages_status(
            connection=connection,
            message_statuses=message_statuses,
            project_id=project_id,
        )

    def fetch(self) -> None:
        """Fetch history list message details from Strategy."""

        target_type = None
        if isinstance(self.target_info, dict):
            target_type = self.target_info.get("type")

        if not target_type:
            raise ValueError(
                "Cannot fetch message details because target object type is missing."
            )

        message = hl_processors.get_history_list_message(
            connection=self.connection,
            message_id=self.id,
            type=target_type,
            project_id=self.project_id,
            scope=self._lookup_scope,
        )
        self._set_object_attributes(**message)

    def list_properties(self, excluded_properties: list[str] | None = None) -> dict:
        """Fetch and list all properties of the history list message.

        Args:
            excluded_properties (list[str], optional): A list of object
                properties that should be excluded from the returned
                dictionary.

        Returns:
            Dictionary with history list message properties.
        """

        self.fetch()
        return super().list_properties(excluded_properties=excluded_properties)

    def alter(self, display_name: str) -> None:
        """Alter the history list message display name.

        Note:
            The current admin-rest implementation supports only a `replace`
            operation on `/displayName`. Other patch paths are rejected by
            the server.

        Args:
            display_name (str): New display name.
        """

        body = {
            "operationList": [
                {"op": "replace", "path": "/displayName", "value": display_name}
            ]
        }
        hl_api.update_history_list_message(
            connection=self.connection,
            message_id=self.id,
            body=body,
        )
        self.display_name = display_name
        self.name = display_name
        if config.verbose:
            logger.info(
                f"HistoryList message with ID: '{self.id}' display name updated."
            )

    def delete(
        self,
        force: bool = False,
        remove_others_message: bool = False,
    ) -> bool:
        """Delete the history list message.

        Args:
            force (bool, optional): If `True`, do not ask for confirmation.
            remove_others_message (bool, optional): Allow removing messages
                from other users than the requester. Defaults to `False`.

        Returns:
            True when the deletion request is sent. False when the confirmation
            prompt is rejected.
        """

        if not force:
            message = (
                f"Are you sure you want to delete HistoryList message "
                f"'{self.name}' with ID: {self.id}? [Y/N]: "
            )
            if input(message) != "Y":
                return False

        hl_api.delete_history_list_message(
            connection=self.connection,
            message_id=self.id,
            project_id=self.project_id,
            remove_others_message=remove_others_message,
        )
        if config.verbose:
            logger.info(f"HistoryList message with ID: '{self.id}' deleted.")
        return True
