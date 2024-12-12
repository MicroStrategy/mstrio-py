from typing import TYPE_CHECKING

from mstrio.api import monitors as monitors_api

if TYPE_CHECKING:
    from mstrio.connection import Connection


def get_contents_caches_loop(
    connection: 'Connection',
    project_id: str,
    node: str,
    offset: int = 0,
    limit_per_request: int = 1000,
    status: str | None = None,
    content_type: str | None = None,
    content_format: str | None = None,
    size: str | None = None,
    owner: str | None = None,
    expiration: str | None = None,
    last_updated: str | None = None,
    hit_count: str | None = None,
    sort_by: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
) -> list[dict]:
    response = monitors_api.get_contents_caches(
        connection,
        project_id,
        node,
        offset,
        limit_per_request,
        status,
        content_type,
        content_format,
        size,
        owner,
        expiration,
        last_updated,
        hit_count,
        sort_by,
        fields,
        error_msg,
    )
    caches = response.json()
    total_caches = caches.get('total')
    all_caches = caches.get('contentCaches')
    offset = 0
    while len(all_caches) < total_caches:
        offset += limit_per_request
        response = monitors_api.get_contents_caches(
            connection,
            project_id,
            node,
            offset,
            limit_per_request,
            status,
            content_type,
            content_format,
            size,
            owner,
            expiration,
            last_updated,
            hit_count,
            sort_by,
            fields,
            error_msg,
        )
        caches = response.json()
        all_caches += caches.get('contentCaches')
    return all_caches
