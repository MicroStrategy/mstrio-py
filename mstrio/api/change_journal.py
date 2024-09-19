from requests import Response

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler


@ErrorHandler(err_msg="Error creating a Change Journal search instance.")
def create_change_journal_search_instance(
    connection: Connection, body: dict, fields: str | None = None
) -> Response:
    """Create a Change Journal search instance.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        body (dict): JSON-formatted body of the search instance
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.post(
        endpoint='/api/changeJournal', json=body, params={'fields': fields}
    )


@ErrorHandler(err_msg="Error getting Change Journal search results")
def get_change_journal_search_results(
    connection: Connection,
    search_id: str,
    offset: int = 0,
    limit: int = -1,
    fields: str | None = None,
) -> Response:
    """Get Change Journal search results.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        search_id (str): ID of the search instance
        offset (int, optional): Starting point within the collection of
            returned search results
        limit (int, optional): Maximum number of items returned for a single
            search request
        fields (str, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model

    Returns:
        HTTP response object returned by the MicroStrategy REST server.
    """
    return connection.get(
        endpoint=f'/api/changeJournal/{search_id}',
        params={'limit': limit, 'offset': offset, 'fields': fields},
    )
