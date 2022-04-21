from enum import IntFlag
from typing import Any, Dict, List, Optional, TypeVar, Union

from mstrio.api import browsing, objects
from mstrio.connection import Connection
from mstrio.utils.entity import Entity, ObjectTypes
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import fetch_objects


class ShortcutInfoFlags(IntFlag):
    DssDossierShortcutInfoBookmark = 0b10
    DssDossierShortcutInfoTOC = 0b01
    DssDossierShortcutInfoDefault = 0b00


class Shortcut(Entity):
    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.SHORTCUT_TYPE
    _API_GETTERS = {
        ('name', 'id', 'project_id', 'owned_by_current_user', 'target', 'encode_html_content',
         'current_page_key', 'shared_time', 'last_viewed_time', 'last_modified_time', 'stid',
         'current_bookmark', 'prompted', 'datasets_cache_info_hash', 'shortcut_info_flag',
         'dossier_version_hash'): browsing.get_shortcut,
        ('abbreviation', 'type', 'subtype', 'ext_type', 'date_created', 'date_modified', 'version',
         'owner', 'icon_path', 'view_media', 'ancestors', 'certified_info', 'acg', 'acl',
         'target_info'): objects.get_object_info
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'shortcut_info_flag': ShortcutInfoFlags,
    }

    def __init__(
            self, connection: Connection, id: str, project_id: str,
            shortcut_info_flag: Union[ShortcutInfoFlags, int] =
            ShortcutInfoFlags.DssDossierShortcutInfoTOC):
        """Initialize the Shortcut object and populate it with I-Server data.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Shortcut ID
            project_id: ID of the project that the shortcut is in
            shortcut_info_flag: flag indicating what information about shortcut
                should be loaded
        """
        if id is None or project_id is None:
            raise AttributeError(
                "Please specify 'id' and 'project_id' parameters in the constructor.")
        else:
            super().__init__(
                connection=connection,
                object_id=id,
                project_id=project_id,
                shortcut_info_flag=get_enum_val(shortcut_info_flag, ShortcutInfoFlags)
            )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._owned_by_current_user = kwargs.get('owned_by_current_user')
        self._target = kwargs.get('target')
        self._encode_html_content = kwargs.get('encode_html_content')
        self._shortcut_info_flag = ShortcutInfoFlags(
            kwargs["shortcut_info_flag"]) if kwargs.get("shortcut_info_flag") else None
        self._current_page_key = kwargs.get('current_page_key')
        self._shared_time = kwargs.get('shared_time')
        self._last_viewed_time = kwargs.get('last_viewed_time')
        self._last_modified_time = kwargs.get('last_modified_time')
        self._stid = kwargs.get('stid')
        self._current_bookmark = kwargs.get('current_bookmark')
        self._prompted = kwargs.get('prompted')
        self._datasets_cache_info_hash = kwargs.get('datasets_cache_info_hash')
        self._dossier_version_hash = kwargs.get('dossier_version_hash')

    T = TypeVar('T')

    @classmethod
    def from_dict(cls: T, source: Dict[str, Any], connection: Connection) -> Union[T, dict]:
        """Instantiate a Shortcut from a dict source.
           If `projectId` not present in source, return dict."""
        # Without projectId the fetching functionality will fail
        if source.get("project_id") or source.get("projectId"):
            return super(Entity, cls).from_dict(source=source, connection=connection)
        return source

    @property
    def owned_by_current_user(self):
        return self._owned_by_current_user

    @property
    def target(self):
        return self._target

    @property
    def encode_html_content(self):
        return self._encode_html_content

    @property
    def shortcut_info_flag(self):
        return self._shortcut_info_flag

    @property
    def current_page_key(self):
        return self._current_page_key

    @property
    def shared_time(self):
        return self._shared_time

    @property
    def last_viewed_time(self):
        return self._last_viewed_time

    @property
    def last_modified_time(self):
        return self._last_modified_time

    @property
    def stid(self):
        return self._stid

    @property
    def current_bookmark(self):
        return self._current_bookmark

    @property
    def prompted(self):
        return self._prompted

    @property
    def datasets_cache_info_hash(self):
        return self._datasets_cache_info_hash

    @property
    def dossier_version_hash(self):
        return self._dossier_version_hash


def get_shortcuts(
        connection: Connection, project_id: str, shortcut_ids: List[str],
        shortcut_info_flag: Union[ShortcutInfoFlags, int] =
        ShortcutInfoFlags.DssDossierShortcutInfoDefault,
        to_dictionary: bool = False, limit: Optional[int] = None,
        **filters) -> Union[List[dict], List[Shortcut]]:
    """Retrieve information about specific published shortcuts
    in specific project.

    Args:
        shortcut_ids: ids of target shortcuts
        project_id: id of project that the shortcuts are in
        shortcut_info_flag: a single ShortcutInfoFlags that describes what
          exact info are to be fetched
        to_dictionary: parameter describing output format
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
    Return:
        list of dictionaries or Shortcut objects,
          depending on `to_dictionary` parameter
    """

    shortcuts = fetch_objects(
        connection=connection,
        api=browsing.get_shortcuts,
        dict_unpack_value="shortcuts",
        limit=limit,
        filters=filters,
        body=[{
            "projectId": project_id,
            "shortcutIds": shortcut_ids
        }],
        shortcut_info_flag=get_enum_val(shortcut_info_flag, ShortcutInfoFlags),
    )

    if to_dictionary:
        return shortcuts
    else:
        return [Shortcut.from_dict(source=short, connection=connection) for short in shortcuts]
