from mstrio.application_objects.datasets.cube_cache import CubeCache, list_cube_caches
from mstrio.connection import Connection

from datetime import datetime, timezone

from typing import List, Union


def _get_datetime(date):
    """String to date time conversion"""
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.000%z')


def delete_inactive_caches(connection: "Connection", days_diff: str = 30,
                           nodes: Union[str, List[str]] = None) -> List["CubeCache"]:
    """Delete inactive caches which have `hit_count` equals 0 and their
    `last_time_updated` was earlier than `days_diff` before from given `nodes`.

    When `nodes` are `None` (default value) then all nodes are retrieved from
    the cluster.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        days_diff (int, optional): number of days to determine whether to delete
            cache when its `hit_count` equals 0. Default value is 30.
        nodes (list of strings or string, optional): names of nodes from which
            caches will be deleted. By default it equals `None` and in that
            case all nodes' names are loaded from the cluster.

    Return:
        list with cache objects which were deleted
    """
    connection._validate_application_selected()
    caches = list_cube_caches(connection, nodes)
    # delete caches which fulfill requirements to be treated as inactive
    deleted_caches = []
    for cache in caches:
        today = datetime.now(timezone.utc)
        if (cache.hit_count == 0
                and (today - _get_datetime(cache.last_update_time)).days > days_diff):
            cache.delete(force=True)
            deleted_caches.append(cache)

    return deleted_caches
