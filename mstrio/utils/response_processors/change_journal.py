from typing import TYPE_CHECKING

from mstrio.api import change_journal as change_journal_api
from mstrio.utils.helper import camel_to_snake

if TYPE_CHECKING:
    from mstrio.connection import Connection


def get_change_journals_loop(
    connection: 'Connection',
    search_id: str,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
) -> list[dict]:
    """Fetch all change journal search results or up to the specified limit.

    Args:
        connection: Connection object to Strategy environment.
        search_id: ID of the change journal search to retrieve results for.
        offset: Starting offset for pagination.
        limit: Maximum number of results to return. If -1, fetch all results.
        fields: Comma-separated list of fields to include in response.

    Returns:
        List of change journal entry dictionaries.
    """
    limit_per_request = 100 if limit == -1 else min(limit, 100)

    response = change_journal_api.get_change_journal_search_results(
        connection, search_id, offset, limit_per_request, fields
    )
    new_entries = camel_to_snake(response.json().get('changeJournalEntries', []))
    all_entries = new_entries

    if limit != -1 and len(all_entries) >= limit:
        return all_entries[:limit]

    offset = 0
    while len(new_entries) == limit_per_request:
        offset += limit_per_request

        if limit != -1:
            remaining_needed = limit - len(all_entries)
            if remaining_needed <= 0:
                break
            current_limit = min(remaining_needed, 100)
        else:
            current_limit = 100

        response = change_journal_api.get_change_journal_search_results(
            connection, search_id, offset, current_limit, fields
        )
        results = response.json()
        new_entries = camel_to_snake(results.get('changeJournalEntries', []))
        all_entries += new_entries

    if limit != -1:
        return all_entries[:limit]

    return all_entries
