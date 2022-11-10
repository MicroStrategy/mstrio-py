from dataclasses import dataclass
from enum import auto
import logging
from typing import Optional, TYPE_CHECKING

from requests import Response

from mstrio import config
from mstrio.api import monitors
from mstrio.connection import Connection
from mstrio.server import Cluster
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import camel_to_snake, Dictable, fetch_objects

if TYPE_CHECKING:
    from mstrio.project_objects import ContentCache

logger = logging.getLogger(__name__)

NO_CACHE_LOG = 'There are no caches meeting the criteria.'


class Cache:
    """
    Base class for managing cache.
    """

    def __init__(self, connection: Connection, cache_id: str, cache_dict: Optional[dict] = None):
        """Initialize the Cache object.

        Args:
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`.
            cache_id (string): cache id
            cache_dict (dict, optional): dictionary with properties of cache
                object.
        """
        if not cache_dict:
            cache_dict = {}
        self._id = cache_id
        self._connection = connection
        self._project_id = connection.project_id

        self._init_variables(**cache_dict)

    def _init_variables(self, **kwargs) -> None:
        """Initialize variables given cache_dict."""
        kwargs = camel_to_snake(kwargs)
        self._project_name = kwargs.get('project_name')
        self._source = CacheSource.from_dict(source) if (source := kwargs.get('source')) else None
        self._last_update_time = kwargs.get('last_update_time')
        self._last_hit_time = kwargs.get('last_hit_time')
        self._hit_count = kwargs.get('hit_count')
        self._size = kwargs.get('size')
        self._creator_name = kwargs.get('creator_name') or kwargs.get('creator')
        self._creation_time = kwargs.get('creation_time')

    def list_properties(self):
        """List properties for cache."""
        return {
            'id': self.id,
            'size': self.size,
            'source': self.source,
            'last_update_time': self.last_update_time,
            'last_hit_time': self.last_hit_time,
            'hit_count': self.hit_count,
            'creator_name': self.creator_name,
            'creation_time': self.creation_time,
        }

    @property
    def id(self):
        return self._id

    @property
    def project_id(self):
        return self._project_id

    @property
    def source(self):
        return self._source

    @property
    def size(self):
        return self._size

    @property
    def last_update_time(self):
        return self._last_update_time

    @property
    def last_hit_time(self):
        return self._last_hit_time

    @property
    def hit_count(self):
        return self._hit_count

    @property
    def creator_name(self):
        return self._creator_name

    @property
    def creation_time(self):
        return self._creation_time


@dataclass
class CacheSource(Dictable):

    class Type(AutoName):
        REPORT = auto()
        DOCUMENT = auto()
        DOSSIER = auto()
        DOCDOSSIER = auto()
        CUBE = auto()

    _FROM_DICT_MAP = {
        'type': Type,
    }

    id: str
    name: str
    type: Type

    def __repr__(self):
        return f"CacheSource(id='{self.id}, name='{self.name}, type='{self.type.value}')"


class ContentCacheMixin:
    """ContentCacheMixin class adds ContentCache management for supporting cache

    Objects currently supported are ContentCache for documents, dossiers and
    reports.
    """

    @staticmethod
    def fetch_nodes(connection: "Connection", project_id: str) -> list[str]:
        """Fetches the nodes for the specified connection and project.

        Args:
            connection (Connection): MicroStrategy connection object returned
                by 'connection.Connection()'
            project_id (string): id of the project to fetch the nodes from

        Returns:
            A list of node names for the specified project."""
        cluster_ = Cluster(connection)
        nodes = cluster_.list_nodes(project=project_id, to_dictionary=True)
        nodes = [node.get('name') for node in nodes if node.get('name')]
        return nodes

    @staticmethod
    def __alter_status(
        connection: "Connection",
        op: str,
        cache_ids: list[str],
        value: Optional[bool] = None,
        status: Optional[str] = None,
        nodes: Optional[list[str]] = None
    ) -> Response:
        """Engine for altering ContentCache status

        Args:
            connection (object): MicroStrategy connection object returned
                by `connection.Connection()`
            op (str): Replace or Remove operation to be performed
            cache_ids (list): list of cache ids on which the operation should be
                performed
            value (bool, optional): Value used by operation [new value used to
                replace existing value]
            status (str, optional): Status on which the value should be changed
            nodes (list, optional): list of node names for the specified project

        Returns:
            Response object
        """
        from mstrio.project_objects import ContentCache

        if not nodes:
            nodes = ContentCacheMixin.fetch_nodes(connection, connection.project_id)
        body = {'operationList': []}
        logger_message = {
            'replace/loaded/True': 'load',
            'replace/loaded/False': 'unload',
            'remove/None/None': 'delete'
        }.get(f'{op}/{status}/{value}')

        for cache_id in cache_ids:
            content_cache = ContentCache(connection, cache_id)
            if not content_cache.combined_id and config.verbose:
                logger.info(f'Could not {logger_message} cache {cache_id}')
                continue
            body['operationList'].append(
                {
                    'op': op,
                    'path': f'/contentCaches/{content_cache.combined_id}/status/{status}'
                    if status else f'/contentCaches/{content_cache.combined_id}',
                    'value': value
                }
            )
        if body['operationList']:
            return monitors.update_contents_caches(connection, nodes, body)
        elif config.verbose:
            logger.info(NO_CACHE_LOG)

    @staticmethod
    def load_caches(connection: "Connection", cache_ids: list[str]) -> Response:
        """Bulk load caches.

        Args:
            connection (Connection): MicroStrategy connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be loaded

        Returns:
            Response object."""
        res = ContentCacheMixin.__alter_status(
            connection=connection, op='replace', cache_ids=cache_ids, value=True, status='loaded'
        )
        if config.verbose and res:
            logger.info('Successfully loaded content caches')
        return res

    @staticmethod
    def unload_caches(connection: "Connection", cache_ids: list[str]) -> Response:
        """Bulk unload caches.

        Args:
            connection (Connection): MicroStrategy connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be unloaded

        Returns:
            Response object."""
        res = ContentCacheMixin.__alter_status(
            connection=connection, op='replace', cache_ids=cache_ids, value=False, status='loaded'
        )
        if config.verbose and res:
            logger.info('Successfully unloaded content caches')
        return res

    @staticmethod
    def delete_caches(
        connection: "Connection", cache_ids: list[str], force: Optional[bool] = None
    ) -> Response:
        """Bulk delete caches.

        Args:
            connection (Connection): MicroStrategy connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be deleted
            force (bool, optional): If True, then no additional prompt will be
                shown before deleting objects.

        Returns:
            Response object."""
        user_input = 'N'
        if not force:
            user_input = input(
                'Are you sure you want to delete all content caches with '
                'provided IDs? [Y/N]: '
            ) or 'N'
        if force or user_input == 'Y':
            res = ContentCacheMixin.__alter_status(
                connection=connection, op='remove', cache_ids=cache_ids
            )
            if config.verbose and res:
                logger.info('Successfully deleted content caches')
            return res

    @classmethod
    def list_caches(
        cls,
        connection: "Connection",
        to_dictionary: bool = False,
        status: str = 'ready',
        project_id: Optional[str] = None,
        nodes: Optional[list[str] | str] = None,
        content_type: Optional[CacheSource.Type | str] = None,
        limit: Optional[int] = None,
        db_connection_id: Optional[str] = None,
        db_login_id: Optional[str] = None,
        id: Optional[str] = None,
        owner: Optional[str] = None,
        size: Optional[str] = None,
        wh_tables: Optional[str] = None,
        security_filter_id: Optional[str] = None,
    ) -> list["ContentCache"] | list[dict]:
        """List content caches. You can filter them by id, database
        connection (`db_connection_id`) and project (`project_id`).

        You can specify from which `nodes` caches will be retrieved. If `nodes`
        are `None` then all nodes are retrieved from the cluster.

        Args:
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`.
            to_dictionary (bool, optional): If True returns dict, by default
                (False) returns ContentCache objects
            status (string, optional): When provided, only caches with given
                status will be returned (if any). Default value `ready`
            project_id (string, optional): When provided only caches
                for project with given ID will be returned (if any).
            nodes (list[string] | string, optional): names of nodes on which
                caches will be searched. By default, it equals `None` and in
                that case all nodes names are loaded from the cluster.
            content_type (string | CacheSource.Type, optional): When provided,
                only caches of given type will be returned (if any).
            limit (integer, optional): Cut-off value for the number of objects
                returned. Default value is `1000` which is a maximum value.
            db_connection_id (string, optional): When provided, only caches for
                the database connection with given ID will be returned (if any).
            db_login_id (string, optional): When provided, only caches for
                the database login with given ID will be returned (if any).
            id (string, optional): When provided, only cache with
                given ID will be returned (if any).
            owner (string, optional): Owner of the content cache. Exact match on
                the owner's full name.
            size (string, optional): Size condition for the content cache
                (in KB). When provided, only caches which satisfy the condition
                will be returned (if any).
            wh_tables (string, optional):  When provided, only caches using
                given warehouse tables will be returned (if any).
            security_filter_id (string, optional): When provided, only caches
                using given security filter will be returned (if any).

        Returns:
            List of ContentCache objects when parameter `to_dictionary` is set
            to False (default value) or list of dictionaries otherwise.
        """
        if not project_id:
            project_id = connection.project_id
        if not nodes:
            nodes = ContentCacheMixin.fetch_nodes(connection, project_id)
        if not content_type:
            content_type = cls._CACHE_TYPE
        unloaded = False
        if status == 'unloaded':
            unloaded = True
            status = 'ready'

        caches = fetch_objects(
            connection=connection,
            api=monitors.get_contents_caches,
            project_id=project_id,
            node=nodes,
            limit=None,
            status=status,
            content_type=content_type,
            size=size,
            owner=owner,
            filters={}
        )
        caches = [list(cache.items())[0] for cache in caches['content_caches']]
        if limit:
            caches = caches[:limit]

        caches = [{**cache[1], 'combined_id': cache[0]} for cache in caches]

        # apply filtering
        filtered_caches = (
            lambda str_arg, arg: [cache for cache in caches if cache.get(str_arg, '') == arg]
        )
        if id:
            caches = filtered_caches('id', id)
        if db_connection_id:
            caches = filtered_caches('databaseConnectionId', db_connection_id)
        if db_login_id:
            caches = filtered_caches('databaseLoginId', db_login_id)
        if wh_tables:
            caches = filtered_caches('warehouseTablesUsed', wh_tables)
        if security_filter_id:
            caches = filtered_caches('securityFilterId', security_filter_id)
        if unloaded:
            caches = [cache for cache in caches if not cache.get('status').get('loaded')]

        if to_dictionary:
            return caches
        else:
            from mstrio.project_objects import ContentCache
            return ContentCache.from_dict(connection, caches)

    @classmethod
    def load_all_caches(
        cls,
        connection: "Connection",
        **filters,
    ):
        """
        Load all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            **filters: Available filter parameters: ['db_connection_id',
                'db_login_id', 'owner', 'status', 'size', 'wh_tables',
                'security_filter_id']
        """
        cache_ids = [cache.id for cache in cls.list_caches(connection, **filters)]
        if cache_ids:
            cls.load_caches(
                connection=connection,
                cache_ids=cache_ids,
            )
        elif config.verbose:
            logger.info(NO_CACHE_LOG)

    @classmethod
    def unload_all_caches(
        cls,
        connection: "Connection",
        **filters,
    ):
        """
        Unload all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            **filters: Available filter parameters: ['db_connection_id',
                'db_login_id', 'owner', 'status', 'size', 'wh_tables',
                'security_filter_id']
        """
        cache_ids = [cache.id for cache in cls.list_caches(connection, **filters)]
        if cache_ids:
            cls.unload_caches(
                connection=connection,
                cache_ids=cache_ids,
            )
        elif config.verbose:
            logger.info(NO_CACHE_LOG)

    @classmethod
    def delete_all_caches(
        cls,
        connection: "Connection",
        force: Optional[bool] = None,
        **filters,
    ):
        """
        Delete all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            force (bool, optional): If True, then no additional prompt will be
                shown before deleting objects.
            **filters: Available filter parameters: ['db_connection_id',
                'db_login_id', 'owner', 'status', 'size', 'wh_tables',
                'security_filter_id']
        """
        cache_ids = [cache.id for cache in cls.list_caches(connection, **filters)
                     if cache.status.ready]
        if cache_ids:
            cls.delete_caches(
                connection=connection,
                cache_ids=cache_ids,
                force=force,
            )
        elif config.verbose:
            logger.info(NO_CACHE_LOG)
