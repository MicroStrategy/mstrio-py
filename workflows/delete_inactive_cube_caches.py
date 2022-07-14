"""Delete inactive caches which were not used for 30 days. IDs of deleted caches
will be printed."""

from datetime import datetime, timezone
from typing import List, Union

from mstrio.connection import Connection, get_connection
from mstrio.project_objects import CubeCache, list_cube_caches


def _get_datetime(date):
    """String to date time conversion"""
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.000%z')


def delete_inactive_caches(
    connection: "Connection", days_diff: str = 30, nodes: Union[str, List[str]] = None
) -> List["CubeCache"]:
    """Delete inactive caches which have `hit_count` equals 0 and their
    `last_time_updated` was earlier than `days_diff` before.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        days_diff (int, optional): number of days to determine whether to delete
            cache when its `hit_count` equals 0. Default value is 30.
        nodes (list of strings or string, optional): names of nodes from which
            caches will be deleted. By default, it equals `None` and in that
            case all nodes' names are loaded from the cluster.

    Return:
        list with cache objects which were deleted
    """
    connection._validate_project_selected()
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


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# execute deletion of inactive cube caches
deleted_caches = delete_inactive_caches(conn)

print('IDs of deleted caches')
for deleted_cache in deleted_caches:
    print(deleted_cache.id)
