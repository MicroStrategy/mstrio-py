import logging
from dataclasses import dataclass
from enum import auto
from typing import TYPE_CHECKING

from requests import Response

from mstrio import config
from mstrio.api import monitors
from mstrio.connection import Connection
from mstrio.server import Cluster
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable, camel_to_snake, validate_param_value
from mstrio.utils.response_processors.monitors import get_contents_caches_loop

if TYPE_CHECKING:
    from mstrio.project_objects import ContentCache

logger = logging.getLogger(__name__)

NO_CACHE_LOG = 'There are no caches meeting the criteria.'


class Cache:
    """
    Base class for managing cache.
    """

    def __init__(
        self, connection: Connection, cache_id: str, cache_dict: dict | None = None
    ) -> None:
        """Initialize the Cache object.

        Args:
            connection (Connection): Strategy One connection object returned by
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
        self._source = (
            CacheSource.from_dict(source) if (source := kwargs.get('source')) else None
        )
        self._last_update_time = kwargs.get('last_update_time')
        self._last_hit_time = kwargs.get('last_hit_time')
        self._hit_count = kwargs.get('hit_count')
        self._size = kwargs.get('size')
        self._creator_name = kwargs.get('creator_name') or kwargs.get('creator')
        self._creation_time = kwargs.get('creation_time')

    def list_properties(self) -> dict:
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
        DASHBOARD = 'dossier'
        DOCDASHBOARD = 'docdossier'
        CUBE = auto()

    _FROM_DICT_MAP = {
        'type': Type,
    }

    id: str
    name: str
    type: Type

    def __repr__(self):
        return (
            f"CacheSource(id='{self.id}', name='{self.name}', type='{self.type.value}')"
        )


class ContentCacheMixin:
    """ContentCacheMixin class adds ContentCache management for supporting cache

    Objects currently supported are ContentCache for dashboards, documents
    and reports.
    """

    @staticmethod
    def fetch_nodes(connection: 'Connection', project_id: str) -> list[str]:
        """Fetches the nodes for the specified connection and project.

        Args:
            connection (Connection): Strategy One connection object returned
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
        connection: 'Connection',
        op: str,
        cache_ids: list[str],
        value: bool | None = None,
        status: str | None = None,
        nodes: list[str] | None = None,
    ) -> Response | None:
        """Engine for altering ContentCache status

        Args:
            connection (object): Strategy One connection object returned
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
            'remove/None/None': 'delete',
            'replace/invalid/True': 'invalidate',
        }.get(f'{op}/{status}/{value}')

        for cache_id in cache_ids:
            content_cache = ContentCache(connection, cache_id)
            if not content_cache.combined_id and config.verbose:
                logger.info(
                    f"Could not perform '{logger_message}' operation on deleted cache "
                    f"with ID '{content_cache.id}'."
                )
                if logger_message == 'load':
                    raise ValueError(
                        f"Could not perform 'load' operation on deleted cache "
                        f"with ID '{content_cache.id}'."
                    )
                return
            body['operationList'].append(
                {
                    'op': op,
                    'path': (
                        (f'/contentCaches/{content_cache.combined_id}/status/{status}')
                        if status
                        else f'/contentCaches/{content_cache.combined_id}'
                    ),
                    'value': value,
                }
            )
        if body['operationList']:
            return monitors.update_contents_caches(connection, nodes, body)
        elif config.verbose:
            logger.info(NO_CACHE_LOG)

    @staticmethod
    def load_caches(connection: 'Connection', cache_ids: list[str]) -> Response | None:
        """Bulk load caches.

        Args:
            connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be loaded

        Returns:
            Response object."""
        result = ContentCacheMixin.__alter_status(
            connection=connection,
            op='replace',
            cache_ids=cache_ids,
            value=True,
            status='loaded',
        )
        if config.verbose and result:
            logger.info('Successfully loaded content caches')
        return result

    @staticmethod
    def unload_caches(
        connection: 'Connection', cache_ids: list[str]
    ) -> Response | None:
        """Bulk unload caches.

        Args:
            connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be unloaded

        Returns:
            Response object."""
        result = ContentCacheMixin.__alter_status(
            connection=connection,
            op='replace',
            cache_ids=cache_ids,
            value=False,
            status='loaded',
        )
        if config.verbose and result:
            logger.info('Successfully unloaded content caches')
        return result

    @staticmethod
    def delete_caches(
        connection: 'Connection', cache_ids: list[str], force: bool | None = None
    ) -> Response | None:
        """Bulk delete caches.

        Args:
            connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): list of cache ids to be deleted
            force (bool, optional): If True, then no additional prompt will be
                shown before deleting objects.

        Returns:
            Response object."""
        user_input = 'N'
        if not force:
            user_input = (
                input(
                    'Are you sure you want to delete all content caches with '
                    'provided IDs? [Y/N]: '
                )
                or 'N'
            )
        if force or user_input == 'Y':
            result = ContentCacheMixin.__alter_status(
                connection=connection, op='remove', cache_ids=cache_ids
            )
            if config.verbose and result:
                logger.info('Successfully deleted content caches')
            return result

    @staticmethod
    def invalidate_caches(
        connection: 'Connection', cache_ids: list[str]
    ) -> Response | None:
        """Bulk invalidate caches.

        Args:
            connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
            cache_ids (list[str]): List of cache ids to be invalidated

        Returns:
            Response object."""
        result = ContentCacheMixin.__alter_status(
            connection=connection,
            op='replace',
            cache_ids=cache_ids,
            value=True,
            status='invalid',
        )
        if config.verbose and result:
            logger.info('Successfully invalidated content caches')
        return result

    @classmethod
    def list_caches(
        cls,
        connection: 'Connection',
        to_dictionary: bool = False,
        status: str | None = 'ready',
        project_id: str | None = None,
        nodes: list[str] | str | None = None,
        content_type: CacheSource.Type | str | None = None,
        limit: int | None = None,
        db_connection_id: str | None = None,
        db_login_id: str | None = None,
        id: str | None = None,
        owner: str | None = None,
        size: str | None = None,
        wh_tables: str | None = None,
        security_filter_id: str | None = None,
    ) -> list['ContentCache'] | list[dict]:
        """List content caches. You can filter them by id, database
        connection (`db_connection_id`) and project (`project_id`).

        You can specify from which `nodes` caches will be retrieved. If `nodes`
        are `None` then all nodes are retrieved from the cluster.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`.
            to_dictionary (bool, optional): If True returns dict, by default
                (False) returns ContentCache objects
            status (str, optional): When provided, only caches with given
                status will be returned (if any). Default value `ready`
            project_id (str, optional): When provided only caches
                for project with given ID will be returned (if any).
            nodes (list[str] | str, optional): names of nodes on which
                caches will be searched. By default, it equals `None` and in
                that case all nodes names are loaded from the cluster.
            content_type (str | CacheSource.Type, optional): When provided,
                only caches of given type will be returned (if any).
            limit (int, optional): Cut-off value for the number of objects
                returned. This is a local limit as we always need to fetch all
                caches first to allow proper filtering on mstrio-py side.
            db_connection_id (str, optional): When provided, only caches for
                the database connection with given ID will be returned (if any).
            db_login_id (str, optional): When provided, only caches for
                the database login with given ID will be returned (if any).
            id (str, optional): When provided, only cache with
                given ID will be returned (if any).
            owner (str, optional): Owner of the content cache. Exact match on
                the owner's full name.
            size (str, optional): Size condition for the content cache
                (in KB). When provided, only caches which satisfy the condition
                will be returned (if any).
            wh_tables (str | list[str], optional):  When provided, only caches
                using any of given warehouse tables will be returned (if any).
            security_filter_id (str, optional): When provided, only caches
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
        if isinstance(wh_tables, str):
            wh_tables = [wh_tables]
        unloaded = False
        if status == 'unloaded':
            unloaded = True
            status = 'ready'
        if isinstance(content_type, CacheSource.Type):
            content_type = get_enum_val(content_type, CacheSource.Type)
        caches = get_contents_caches_loop(
            connection=connection,
            project_id=project_id,
            node=nodes,
            status=status,
            content_type=content_type,
            size=size,
            owner=owner,
        )

        validate_param_value('limit', limit, int, min_val=1, special_values=[None])
        # This is a result limitation because every time we list caches, we need
        # to fetch them all first to do proper filtering on the mstrio-py side

        # apply filtering
        def filtered_caches(str_arg, arg):
            return [cache for cache in caches if cache.get(str_arg, '') == arg]

        if id:
            caches = filtered_caches('id', id)
        if db_connection_id:
            caches = filtered_caches('databaseConnectionId', db_connection_id)
        if db_login_id:
            caches = filtered_caches('databaseLoginId', db_login_id)
        if security_filter_id:
            caches = filtered_caches('securityFilterId', security_filter_id)
        if wh_tables:
            caches = [
                cache
                for cache in caches
                if any(
                    wh_table in cache.get('warehouseTablesUsed', [])
                    for wh_table in wh_tables
                )
            ]
        if unloaded:
            caches = [
                cache for cache in caches if not cache.get('status').get('loaded')
            ]
        if limit:
            caches = caches[:limit]

        if to_dictionary:
            return caches
        else:
            from mstrio.project_objects import ContentCache

            return ContentCache.from_dict(connection, caches)

    @classmethod
    def load_all_caches(
        cls,
        connection: 'Connection',
        **filters,
    ) -> None:
        """
        Load all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): Strategy One connection object returned by
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
        connection: 'Connection',
        **filters,
    ) -> None:
        """
        Unload all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): Strategy One connection object returned by
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
        connection: 'Connection',
        force: bool | None = None,
        **filters,
    ) -> None:
        """
        Delete all content caches filtered by the class type.
        Optionally filter by additional conditions.

        Args:
            cls (object): Class type for objects to be filtered by
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            force (bool, optional): If True, then no additional prompt will be
                shown before deleting objects.
            **filters: Available filter parameters: ['db_connection_id',
                'db_login_id', 'owner', 'status', 'size', 'wh_tables',
                'security_filter_id']
        """
        cache_ids = [
            cache.id
            for cache in cls.list_caches(connection, **filters)
            if cache.status.ready
        ]
        if cache_ids:
            cls.delete_caches(
                connection=connection,
                cache_ids=cache_ids,
                force=force,
            )
        elif config.verbose:
            logger.info(NO_CACHE_LOG)
