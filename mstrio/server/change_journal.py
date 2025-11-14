from dataclasses import dataclass
from datetime import datetime
from enum import auto
import logging
from typing import TYPE_CHECKING


from mstrio import config
from mstrio.api import change_journal
from mstrio.connection import Connection
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors.change_journal import get_change_journals_loop
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.utils.entity import Entity
    from mstrio.server import Project


logger = logging.getLogger(__name__)


@dataclass
class ChangeJournalEntry(Dictable):
    """Represents a single entry in the change journal."""

    project_id: str | None = None
    machine: str | None = None
    timestamp: str | None = None
    session_id: str | None = None
    transaction: dict | None = None
    user: dict | None = None
    changed_links: list[dict] | None = None
    changed_objects: list[dict] | None = None
    timestamp_iso: str | None = None


class TransactionType(AutoName):
    """Enumeration of possible transaction types in the change journal."""

    RESERVED = auto()
    ENABLE_CHANGE_JOURNAL = auto()
    DISABLE_CHANGE_JOURNAL = auto()
    PURGE_CHANGE_JOURNAL = auto()
    SAVE_OBJECT = auto()
    SAVE_OBJECTS = auto()
    SAVE_LINKITEMS = auto()
    DELETE_OBJECT = auto()
    DELETE_OBJECTS = auto()
    DELETE_PROJECT = auto()
    COPY_OBJECT = auto()
    MERGE_USER = auto()
    COLLECT_GARBAGE = auto()
    WRITE_SYSTEM_PROPERTY = auto()
    WRITE_DATABASE_PASSWORD = auto()


class ChangeType(AutoName):
    """Enumeration of possible change types in the change journal."""

    RESERVED = auto()
    CREATE_OBJECT = auto()
    CHANGE_OBJECT = auto()
    DELETE_OBJECT = auto()
    TOUCH_FOLDER = auto()
    CREATE_LINKITEM = auto()
    CHANGE_LINKITEM = auto()
    DELETE_LINKITEM = auto()
    CHANGE_JOURNAL_ENABLE = auto()
    CHANGE_JOURNAL_DISABLE = auto()
    CHANGE_JOURNAL_PURGE = auto()


@method_version_handler('11.4.0900')
def list_change_journal_entries(
    connection: Connection,
    transaction_sources: str | list[str] | None = None,
    transaction_types: (
        str | TransactionType | list[str | TransactionType] | None
    ) = None,
    change_types: str | ChangeType | list[str | ChangeType] | None = None,
    session_ids: str | list[str] | None = None,
    machines: str | list[str] | None = None,
    users: str | list[str] | None = None,
    affected_projects: str | list[str] | None = None,
    affected_objects: 'str | Entity | list[str | Entity] | None' = None,
    begin_transaction_id: int | None = None,
    end_transaction_id: int | None = None,
    begin_time: str | datetime | None = None,
    end_time: str | datetime | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
) -> list[ChangeJournalEntry]:
    """List change journal entries based on provided filters.

    Note: When listing all existing change journal entries across all projects,
        this function can take a considerable amount of time to execute,
        depending on the volume of data.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        transaction_sources (str | list[str], optional): Transaction sources to
            filter by. Can be a single string or list of strings.
        transaction_types (str | TransactionType | list[str | TransactionType],
            optional): Transaction types to filter by. Can be a single value or
            list of strings or TransactionType enums.
        change_types (str | ChangeType | list[str | ChangeType], optional):
            Change types to filter by. Can be a single value or list of strings
            or ChangeType enums.
        session_ids (str | list[str], optional): Session IDs to filter by. Can
            be a single session ID or list of session IDs.
        machines (str | list[str], optional): Machine names to filter by. Can
            be a single machine name or list of machine names.
        users (str | list[str], optional): User IDs to filter by. Can be a
            single user ID or list of user IDs.
        affected_projects (str | list[str], optional): Project IDs/names/objects
            to filter by. Can be a single element or list of elements.
        affected_objects (str | Entity | list[str | Entity], optional): Object
            IDs or Entity objects to filter by. Can be a single value or list of
            values.
        begin_transaction_id (int, optional): Start of the transaction ID range
            to filter by.
        end_transaction_id (int, optional): End of the transaction ID range to
            filter by.
        begin_time (str | datetime, optional): Start of the timestamp range to
            filter by. Format: 'MM/DD/YYYY HH:MM:SS AM/PM' for string input or a
            datetime object.
        end_time (str | datetime, optional): End of the timestamp range to
            filter by. Format: 'MM/DD/YYYY HH:MM:SS AM/PM' for string input or a
            datetime object.
        to_dictionary (bool, optional): If True, returns the results as a
            dictionary. Defaults to False.
        limit (int, optional): Maximum number of entries to return. If not
            specified, returns all matching entries.

    Returns:
        List of ChangeJournalEntry objects matching the filters.
    """

    from mstrio.utils.entity import Entity

    filter_criteria = {}

    if transaction_sources:
        filter_criteria['transactionSources'] = (
            transaction_sources
            if isinstance(transaction_sources, list)
            else [transaction_sources]
        )

    if transaction_types:
        if isinstance(transaction_types, (str, TransactionType)):
            transaction_types = [transaction_types]
        filter_criteria['transactionTypes'] = [
            item.value if isinstance(item, TransactionType) else item
            for item in transaction_types
        ]

    if change_types:
        if isinstance(change_types, (str, ChangeType)):
            change_types = [change_types]
        filter_criteria['changeTypes'] = [
            item.value if isinstance(item, ChangeType) else item
            for item in change_types
        ]

    if session_ids:
        filter_criteria['sessionIds'] = (
            session_ids if isinstance(session_ids, list) else [session_ids]
        )
    if machines:
        filter_criteria['machines'] = (
            machines if isinstance(machines, list) else [machines]
        )

    if users:
        filter_criteria['users'] = users if isinstance(users, list) else [users]

    if affected_projects:
        if not isinstance(affected_projects, list):
            affected_projects = [affected_projects]
        selected_projects = [
            get_project_id_from_params_set(
                connection,
                project=elem,
                no_fallback_from_connection=True,
            )
            for elem in affected_projects
        ]
        filter_criteria['affectedProjects'] = selected_projects

    if affected_objects:
        if not isinstance(affected_objects, list):
            affected_objects = [affected_objects]
        filter_criteria['affectedObjects'] = [
            {'id': obj.id} if isinstance(obj, Entity) else {'id': obj}
            for obj in affected_objects
        ]

    if begin_transaction_id:
        filter_criteria['beginTransactionId'] = begin_transaction_id

    if end_transaction_id:
        filter_criteria['endTransactionId'] = end_transaction_id

    if begin_time:
        if isinstance(begin_time, datetime):
            begin_time = begin_time.strftime("%m/%d/%Y %I:%M:%S %p")
        filter_criteria['beginTime'] = begin_time

    if end_time:
        if isinstance(end_time, datetime):
            end_time = end_time.strftime("%m/%d/%Y %I:%M:%S %p")
        filter_criteria['endTime'] = end_time

    with (
        config.temp_verbose_disable(),
        connection.temporary_project_change(project=None),
    ):
        search_id = (
            change_journal.create_change_journal_search_instance(
                connection, filter_criteria
            )
            .json()
            .get('searchId')
        )
        res = get_change_journals_loop(
            connection, search_id, offset=0, limit=limit or -1
        )

    if to_dictionary:
        return res
    return [ChangeJournalEntry(**entry) for entry in res]


@method_version_handler('11.4.0900')
def purge_change_journal_entries(
    connection: Connection,
    projects: 'list[str | Project] | Project | str | None' = None,
    comment: str | None = None,
    timestamp: str | datetime | None = None,
) -> None:
    """Purge change journal entries up to a specified timestamp for given
    projects.

    Note: If no projects are provided, all loaded projects will be targeted.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        projects (str | Project | list[str | Project]): Project(s) to purge
            change journal entries from. Can be a single project ID,
            project_name, Project object or a list of project
            IDs/names/objects.
        comment (str, optional): Comment for the purge operation.
        timestamp (str | datetime, optional): Timestamp up to which to purge
            entries. Format: 'MM/DD/YYYY HH:MM:SS AM/PM' for string input or a
            datetime object. If not provided, all entries will be purged.
    """

    if projects is None:
        projects = connection.environment.list_loaded_projects()

    if projects and not isinstance(projects, list):
        projects = [projects]
    selected_projects = [
        get_project_id_from_params_set(
            connection,
            project=elem,
            no_fallback_from_connection=True,
        )
        for elem in projects
    ]
    selected_projects = ",".join(selected_projects)

    if isinstance(timestamp, datetime):
        timestamp = _format_timestamp_for_api_purge(timestamp)

    res = change_journal.purge_change_journal_entries(
        connection, comment=comment, timestamp=timestamp, projects_ids=selected_projects
    )
    if config.verbose and res.ok:
        logger.info(
            "Request to purge change journal entries in selected projects was "
            "successfully sent."
        )


def _format_timestamp_for_api_purge(dt: datetime) -> str:
    """Format datetime for Strategy API timestamp requirements.

    Converts datetime to MM/DD/YYYY HH:MM:SS AM/PM format with proper
    constraints matching the API regex pattern. It requires to strip leading
    zeros from month, day, and hour components.

    Args:
        dt: Datetime object to format.

    Returns:
        Formatted timestamp string matching API requirements.
        Examples: '10/27/2025 4:37:20 PM', '1/5/2023 9:05:07 AM'
    """
    formatted = dt.strftime("%m/%d/%Y %I:%M:%S %p")

    parts = formatted.split(' ')
    date_part = parts[0]
    time_part = parts[1]
    ampm_part = parts[2]

    month, day, year = date_part.split('/')
    month = str(int(month))
    day = str(int(day))

    hour, minute, second = time_part.split(':')
    hour = str(int(hour))

    return f"{month}/{day}/{year} {hour}:{minute}:{second} {ampm_part}"
