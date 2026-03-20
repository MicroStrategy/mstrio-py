from typing import TYPE_CHECKING

from requests import Response

from mstrio.utils.error_handlers import ErrorHandler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@ErrorHandler(err_msg="Error gathering repository information.")
def get_repository_info(connection: 'Connection') -> Response:
    """Gets repository ID to uniquely identify the metadata connected by the
    I-Server.

    It includes data about Platform Analytics Project and Environment.

    Args:
        connection: Strategy connection object returned by
            `connection.Connection()`.

    Returns:
        Response object containing repository information.
    """

    return connection.get(
        endpoint="/api/configurations/repository",
        headers={'X-MSTR-ProjectID': None},
    )


@ErrorHandler(err_msg="Error updating repository information.")
def update_repository_info(connection: 'Connection', body: dict) -> Response:
    """Updates repository information.

    Args:
        connection: Strategy connection object returned by
            `connection.Connection()`.
        body: Dictionary containing the information to update the repository
            with.

    Returns:
        Response object containing updated repository information.
    """

    return connection.put(
        endpoint="/api/configurations/repository",
        headers={'X-MSTR-ProjectID': None},
        json=body,
    )
