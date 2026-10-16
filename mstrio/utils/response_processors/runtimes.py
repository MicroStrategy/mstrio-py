from typing import TYPE_CHECKING

from mstrio.api import runtimes as runtimes_api
from mstrio.utils.helper import get_response_json

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_runtimes(
    connection: "Connection",
    fields: str | None = None,
    error_msg: str | None = None,
) -> list[dict]:
    """Return runtime records from the list response."""

    response = runtimes_api.list_runtimes(
        connection=connection,
        fields=fields,
        error_msg=error_msg,
    )
    return get_response_json(response).get("runtimes", [])


def get_runtime(connection: "Connection", id: str, fields: str | None = None) -> dict:
    """Return one runtime record."""

    response = runtimes_api.get_runtime(connection=connection, id=id, fields=fields)
    return get_response_json(response)


def create_runtime(connection: "Connection", body: dict) -> dict:
    """Return the created runtime identifier."""

    response = runtimes_api.create_runtime(connection=connection, body=body)
    return get_response_json(response)


def get_runtime_versions(
    connection: "Connection", fields: str | None = None
) -> list[str]:
    """Return available runtime versions."""

    response = runtimes_api.get_runtime_versions(connection=connection, fields=fields)
    return get_response_json(response).get("versions", [])
