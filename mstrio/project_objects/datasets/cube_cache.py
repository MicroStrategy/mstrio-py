import logging
from typing import Optional, TYPE_CHECKING

from mstrio import config
from mstrio.api import monitors
from mstrio.server.cluster import Cluster
from mstrio.utils.cache import Cache
from mstrio.utils.helper import camel_to_snake, exception_handler, fetch_objects_async
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0000')
def list_cube_caches(
    connection: "Connection",
    nodes: Optional[list[str] | str] = None,
    cube_id: Optional[str] = None,
    loaded: Optional[bool] = False,
    db_connection_id: Optional[str] = None,
    project_ids: Optional[list[str]] = None,
    to_dictionary: Optional[bool] = False,
    limit: Optional[int] = None
) -> list["CubeCache"] | list[dict]:
    """List cube caches. You can filter them by cube (`cube_id`), database
    connection (`db_connection_id`) and projects (`project_ids`). You can also
    obtain only loaded caches (`loaded=True`).

    You can specify from which `nodes` caches will be retrieved. If `nodes` are
    `None` then all nodes are retrieved from the cluster.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        nodes (list of strings or string, optional): names of nodes on which
            caches will be searched. By default it equals `None` and in that
            case all nodes' names are loaded from the cluster.
        cube_id (string, optional): When provided, only caches for the cube with
            given ID will be returned (if any).
        loaded (bool, optional): If True then only loaded caches will be
            retrieved. Otherwise all cubes will be returned.
        db_connection_id (string, optional): When provided, only caches for the
            database connection with given ID will be returned (if any).
        project_ids (list of string, optional): When provided only caches
            for projects with given IDs will be returned (if any).
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns CubeCache objects
        limit(integer, optional): Cut-off value for the number of objects
            returned. Default value is `None` which means no limit.

    Returns:
        List of CubeCache objects when parameter `to_dictionary` is set to False
        (default value) or list of dictionaries otherwise.
    """
    if project_ids is not None:
        project_ids = ','.join(project_ids)  # form accepted by request

    if nodes is None:
        cluster_ = Cluster(connection)
        nodes = cluster_.list_nodes(project=connection.project_id, to_dictionary=True)
        nodes = [node.get('name') for node in nodes]

    nodes = [nodes] if type(nodes) == str else nodes
    caches = []
    for node in nodes:
        caches += fetch_objects_async(
            connection=connection,
            api=monitors.get_cube_caches,
            async_api=monitors.get_cube_caches_async,
            dict_unpack_value='cubeCaches',
            node=node,
            limit=limit,
            project_ids=project_ids,
            chunk_size=1000,
            loaded=loaded,
            filters={}
        )
    if cube_id:
        caches = [cache for cache in caches if cache.get('source', {}).get('id', '') == cube_id]
    if db_connection_id:
        caches = [
            cache for cache in caches if db_connection_id in
            [db.get('id', '') for db in cache.get('databaseConnections', [])]
        ]
    if to_dictionary:
        return caches
    else:
        return CubeCache.from_dict(connection, caches)


def delete_cube_caches(
    connection: "Connection",
    loaded: bool = False,
    force: bool = False,
    nodes: Optional[list[str] | str] = None,
    cube_id: Optional[str] = None,
    db_connection_id: Optional[str] = None
) -> Optional[dict]:
    """Delete all cube caches on a given node.

    Optionally it is possible to specify for which cube or for which database
    connection caches will be deleted. It is also possible to delete only loaded
    caches.

    You can specify from which `nodes` caches will be deleted. If `nodes` are
    `None` then all nodes are retrieved from cluster.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        nodes (list of strings or string, optional): names of nodes from which
            caches will be deleted. By default it equals `None` and in that
            case all nodes names are loaded from the cluster.
        cube_id (string, optional): When provided, only caches for the cube with
            given ID will be deleted (if any).
        db_connection_id (string, optional): When provided, only caches for the
            database connection with given ID will be deleted (if any).
        loaded (bool, optional): If True then only loaded caches will be
            deleted. Otherwise all cubes will be returned.
        force (bool, optional): If True, then no additional prompt will be shown
            before deleting caches for given cube. Default is False.

    Returns:
        Dictionary with two keys:
         - 'succeeded' - list with IDs of caches which were deleted
         - 'failed' - list with IDS of caches which were not deleted
        or None when user doesn't agree for deletion when prompted
    """
    user_input = 'N'
    if not force:
        # construct meaningful message for deletion input
        tmp_msg = ['all']
        if loaded is True:
            tmp_msg.append('loaded')
        tmp_msg.append('caches')
        if cube_id:
            tmp_msg.append(f"for cube with ID: '{cube_id}'")
        if db_connection_id:
            tmp_msg.append(f"from database connection with ID: '{db_connection_id}'")
        msg = f"Are you sure you want to delete {' '.join(tmp_msg)}? [Y/N]:"
        user_input = input(msg) or 'N'
    if force or user_input == 'Y':
        caches = list_cube_caches(connection, nodes, cube_id, loaded, db_connection_id)
        succeeded = []
        failed = []
        for cache in caches:
            if cache.delete(force=True):
                succeeded.append(cache.id)
            else:
                failed.append(cache.id)
        return {'succeeded': succeeded, 'failed': failed}
    else:
        return None


def delete_cube_cache(connection: "Connection", id: str, force: bool = False):
    """Delete single cube cache.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id (string): cube cache ID
        force (bool, optional): If True, then no additional prompt will be shown
            before deleting caches for given cube. Default is False.

    Returns:
        True for success. False otherwise.
    """
    return CubeCache._delete(connection, id, force)


@class_version_handler('11.3.0000')
class CubeCache(Cache):
    """
    Manage cube cache.
    """

    def __init__(
        self,
        connection: "Connection",
        cache_id: str,
        cube_cache_dict: Optional[dict] = None
    ):
        """Initialize the CubeCache object. If cube_cache_dict provided
        no I-Server request will be sent.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            cache_id (string): cube cache id
            cube_cache_dict (dict, optional): dictionary with properties of cube
                cache object. If it is provided then cache dictionary will not
                be retrieved from I-Server.
        """
        super().__init__(connection, cache_id)

        if not cube_cache_dict:
            self.fetch()
        else:
            self._init_variables(**cube_cache_dict)

    def _init_variables(self, **cube_cache_dict):
        cube_cache_dict = camel_to_snake(cube_cache_dict)
        super()._init_variables(**cube_cache_dict)
        self._state = cube_cache_dict.get('state')
        self._last_update_job = cube_cache_dict.get('last_update_job')
        self._open_view_count = cube_cache_dict.get('open_view_count')
        self._historic_hit_count = cube_cache_dict.get('historic_hit_count')
        self._database_connections = cube_cache_dict.get('database_connections', [])
        self._file_name = cube_cache_dict.get('file_name')
        self._data_languages = cube_cache_dict.get('data_languages', [])
        self._row_count = cube_cache_dict.get('row_count')
        self._column_count = cube_cache_dict.get('column_count')
        self._creator_id = cube_cache_dict.get('creator_id')
        self._job_execution_statistics = cube_cache_dict.get('job_execution_statistics')

    def fetch(self):
        res = monitors.get_cube_cache_info(self._connection, self._id)
        self._init_variables(**res.json())

    @classmethod
    def from_dict(cls, connection: "Connection", caches: list[dict]) -> list["CubeCache"]:
        return [CubeCache(connection, cache_dict['id'], cache_dict) for cache_dict in caches]

    def __alter_status(self, active: bool = None, loaded: bool = None) -> str | None:
        if active is not None and loaded is not None:
            msg = 'You cannot set both states during one request'
            exception_handler(msg, UserWarning)
            return None
        res = monitors.alter_cube_cache_status(
            self._connection, self._id, active, loaded, False
        )
        return res.json()['manipulationId']

    def load(self):
        """Load cache."""
        return self.__alter_status(loaded=True)

    def unload(self):
        """Unload cache."""
        return self.__alter_status(loaded=False)

    def activate(self):
        """Activate cube cache."""
        return self.__alter_status(active=True)

    def deactivate(self):
        """Deactivate cube cache."""
        return self.__alter_status(active=False)

    def delete(self, force: bool = False):
        """Delete cube cache.

        Args:
            force: If True, then no additional prompt will be shown before
                deleting CubeCache.

        Returns:
            True for success. False otherwise.
        """
        return self._delete(self._connection, self._id, force)

    @staticmethod
    def _delete(connection: "Connection", id: str, force: bool = False):
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to delete cube cache"
                f"with ID: '{id}'? [Y/N]: "
            ) or 'N'
        if force or user_input == 'Y':
            response = monitors.delete_cube_cache(connection, id, False)
            if response.status_code == 204:
                if config.verbose:
                    logger.info(f"Successfully deleted cube cache with ID: '{id}'.")
                return True
            else:
                return False
        else:
            return False

    def list_properties(self):
        """List properties for cube cache."""
        return {
            **super().list_properties(),
            'row_count': self.row_count,
            'column_count': self.column_count,
            'historic_hit_count': self.historic_hit_count,
            'open_view_count': self.open_view_count,
            'creator_id': self.creator_id,
            'last_update_job': self.last_update_job,
        }

    def get_manipulation_status(self, manipulation_id: str) -> dict:
        """Get manipulation status of cube cache."""
        res = monitors.get_cube_cache_manipulation_status(self._connection, manipulation_id, False)
        return res.json()['status']

    @property
    def state(self):
        return self._state

    @property
    def database_connections(self):
        return self._database_connections

    @property
    def file_name(self):
        return self._file_name

    @property
    def data_languages(self):
        return self._data_languages

    @property
    def job_execution_statistics(self):
        if self._job_execution_statistics is None:
            self.fetch()
        return self._job_execution_statistics

    @property
    def row_count(self):
        return self._row_count

    @property
    def column_count(self):
        return self._column_count

    @property
    def historic_hit_count(self):
        return self._historic_hit_count

    @property
    def open_view_count(self):
        return self._open_view_count

    @property
    def creator_id(self):
        return self._creator_id

    @property
    def last_update_job(self):
        return self._last_update_job
