from dataclasses import dataclass
from enum import auto
import logging
from typing import Optional

from requests import Response

from mstrio import config
from mstrio.api import monitors
from mstrio.connection import Connection
from mstrio.utils.cache import Cache, ContentCacheMixin
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import camel_to_snake, Dictable
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


class ContentCacheFormat(AutoName):
    EXCEL = auto()
    PDF = auto()
    CSV = auto()
    HTML = auto()
    XML = auto()
    PLAIN_TEXT = auto()
    BINARY_DEFINITION = auto()
    BINARY_DATA = auto()
    HTML5 = auto()
    FLASH = auto()
    TRANSACTION = auto()


@class_version_handler('11.3.0700')
class ContentCache(Cache, ContentCacheMixin):
    """
    Manage content cache.

    _CACHE_TYPE is a variable used by ContentCache class for cache filtering
    purposes.
    """
    _CACHE_TYPE = None

    def __init__(
        self, connection: "Connection", id: str, content_cache_dict: Optional[dict] = None
    ):
        """Initialize the ContentCache object. If content_cache_dict is provided
        no I-Server request will be sent.

        Args:
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`.
            id (string): content cache id
            content_cache_dict (dict, optional): dictionary with properties of
                content cache object. If it is provided then cache dictionary
                will not be retrieved from I-Server.
        """
        super().__init__(connection, id)

        self._nodes = ContentCacheMixin.fetch_nodes(self._connection, self._project_id)
        if not content_cache_dict:
            self.fetch()
        else:
            self._init_variables(**content_cache_dict)

    def _init_variables(self, **kwargs) -> None:
        kwargs = camel_to_snake(kwargs)
        super()._init_variables(**kwargs)
        self._status = ContentCacheStatus.from_dict(status) if (
            status := kwargs.get('status')
        ) else None
        self._format = ContentCacheFormat(format_) if (format_ := kwargs.get('format')) else None
        self._combined_id = combined_id if (combined_id := kwargs.get('combined_id')) else None
        self._chapter = kwargs.get('chapter')
        self._report_caches_used = kwargs.get('report_caches_used')
        self._host = kwargs.get('host')
        self._warehouse_tables_used = kwargs.get('warehouse_tables_used')
        self._last_load_time = kwargs.get('last_load_time')
        self._security_filter_id = kwargs.get('security_filter_id')
        self._prompt_answer = kwargs.get('prompt_answer')
        self._result_cache_type = kwargs.get('result_cache_type')
        self._expiration_time = kwargs.get('expiration_time')
        self._database_connection_id = kwargs.get('database_connection_id')
        self._database_login_id = kwargs.get('database_login_id')
        self._cache_location = kwargs.get('cache_location')
        self._location = kwargs.get('location')
        self._data_language = kwargs.get('data_language')
        self._metadata_language = kwargs.get('metadata_language')
        self._group_by = kwargs.get('group_by')
        self._xml_content = kwargs.get('xml_content', [])

    def __repr__(self):
        return f"ContentCache(id='{self.id}', source={self.source})"

    def fetch(self):
        """Fetches the cache from the server, refreshing the variables to match
        those currently stored on the server."""
        res = ContentCache.list_caches(
            connection=self._connection,
            project_id=self._project_id,
            nodes=self._nodes,
            id=self.id,
            to_dictionary=True
        )
        if res:
            self._init_variables(**res[0])

    def __alter_status(
        self,
        op: str,
        value: Optional[bool] = None,
        status: Optional[str] = None,
        nodes: Optional[list[str]] = None
    ) -> Response:
        """Engine for altering ContentCache status

        Args:
            op (str): Replace or Remove operation to be performed
            value (bool, optional): Value used by operation [new value used to
                replace existing value]
            status (str, optional): Status on which the value should be changed
            nodes (list, optional): list of node names for the specified project

        Returns:
            Response object
        """
        if not nodes:
            nodes = ContentCacheMixin.fetch_nodes(self._connection, self._connection.project_id)
        body = {'operationList': [
            {
                'op': op,
                'path': f'/contentCaches/{self.combined_id}/status/{status}'
                if status else f'/contentCaches/{self.combined_id}',
                'value': value
            }
        ]}
        return monitors.update_contents_caches(self._connection, nodes, body)

    def load(self):
        """Load content cache."""
        nodes = self._nodes
        response = self.__alter_status(
            op='replace',
            value=True,
            status='loaded',
            nodes=nodes
        )

        if config.verbose and response.ok:
            logger.info(f'Successfully loaded content cache with id: {self.id}')
        if response.ok:
            self.fetch()
            return True
        return False

    def unload(self):
        """Unload content cache."""
        nodes = self._nodes
        response = self.__alter_status(
            op='replace',
            value=False,
            status='loaded',
            nodes=nodes
        )
        if config.verbose and response:
            logger.info(f'Successfully unloaded content cache with id: {self.id}')
        if response.ok:
            self.fetch()
            return True
        return False

    def delete(self, force: Optional[bool] = None) -> Response:
        """Delete content cache.

        Args:
            force (bool, optional): If True, then no additional prompt will be
                shown before deleting object.

        Returns:
            Response object."""
        if not force:
            user_input = input(
                f"Are you sure you want to delete content cache"
                f"with ID: '{self.id}'? [Y/N]: "
            ) or 'N'
        if force or user_input == 'Y':
            nodes = self._nodes
            response = self.__alter_status(
                op='remove', nodes=nodes
            )
            if config.verbose and response:
                logger.info(f"Successfully deleted content cache with ID: '{self.id}'.")
            return response

    @classmethod
    def from_dict(cls, connection: "Connection", caches: list[dict]) -> list["ContentCache"]:
        """Creates Caches from a provided dictionary.

        Args:
            cls (object): Class type for objects to be created
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            caches (list[dict]): list of dictionaries the Caches will be created
                from

        Returns:
            List of Caches created from the provided dictionaries."""
        return [ContentCache(connection, cache_dict['id'], cache_dict) for cache_dict in caches]

    def list_properties(self):
        """List properties for content cache."""
        return {
            **super().list_properties(),
            'status': self.status,
            'format': self.format,
            'chapter': self.chapter,
            'report_cache_used': self.report_caches_used,
            'host': self.host,
            'warehouse_tables_used': self.warehouse_tables_used,
            'last_load_time': self.last_load_time,
            'security_filter_id': self.security_filter_id,
            'promt_answer': self.prompt_answer,
            'result_cashe_type': self.result_cache_type,
            'expiration_time': self.expiration_time,
            'database_connection_id': self.database_connection_id,
            'database_login_id': self.database_login_id,
            'cache_location': self.cache_location,
            'location': self.location,
            'data_language': self.data_language,
            'metadata_language': self.metadata_language,
            'group_by': self.group_by,
            'xml_content': self.xml_content,
        }

    @property
    def status(self):
        return self._status

    @property
    def format(self):
        return self._format

    @property
    def combined_id(self):
        return self._combined_id

    @property
    def chapter(self):
        return self._chapter

    @property
    def report_caches_used(self):
        return self._report_caches_used

    @property
    def host(self):
        return self._host

    @property
    def warehouse_tables_used(self):
        return self._warehouse_tables_used

    @property
    def last_load_time(self):
        return self._last_load_time

    @property
    def security_filter_id(self):
        return self._security_filter_id

    @property
    def prompt_answer(self):
        return self._prompt_answer

    @property
    def result_cache_type(self):
        return self._result_cache_type

    @property
    def expiration_time(self):
        return self._expiration_time

    @property
    def database_connection_id(self):
        return self._database_connection_id

    @property
    def database_login_id(self):
        return self._database_login_id

    @property
    def cache_location(self):
        return self._cache_location

    @property
    def location(self):
        return self._location

    @property
    def data_language(self):
        return self._data_language

    @property
    def metadata_language(self):
        return self._metadata_language

    @property
    def group_by(self):
        return self._group_by

    @property
    def xml_content(self):
        return self._xml_content


@dataclass
class ContentCacheStatus(Dictable):

    ready: bool
    processing: bool
    invalid: bool
    expired: bool
    loaded: bool
    filed: bool
    dirty: bool
