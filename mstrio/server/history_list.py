import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import history_list as hl_api
from mstrio.utils.wip import WipLevels, module_wip, wip

if TYPE_CHECKING:
    from mstrio.connection import Connection


module_wip(
    globals(),
    level=WipLevels.WARNING,
    message=(
        "Module `history_list` is not fully implemented yet. For now it "
        "contains only functionalities related to deleting all history list messages."
    ),
)  # explicitly no version declared


logger = logging.getLogger(__name__)


@wip(level=WipLevels.PREVIEW)
def list_history_list_messages(connection: 'Connection', limit: int = -1) -> list[dict]:
    """Lists all history list messages for all users.

    Args:
        connection (Connection): Strategy One connection object.
        limit (int): Maximum number of messages to retrieve.
            If `-1`, retrieves all messages.

    Returns:
        List of history list messages data dictionaries.
    """

    return (
        hl_api.list_history_list_messages(connection, scope='all_users', limit=limit)
        .json()
        .get("historyList")
        or []
    )


@wip(level=WipLevels.PREVIEW)
def delete_all_history_list_messages(connection: 'Connection') -> None:
    """Removes all History List messages from all the users.

    Args:
        connection (Connection): Strategy One connection object.
    """

    messages = list_history_list_messages(connection)

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

    if list_history_list_messages(connection, limit=1):
        logger.warning("Some History List messages were not removed.")
    elif config.verbose:
        logger.info("All History List messages removed successfully.")
