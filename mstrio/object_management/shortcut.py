from enum import IntFlag
from typing import Any, TypeVar

from mstrio.api import browsing
from mstrio.connection import Connection
from mstrio.object_management.search_enums import SearchDomain
from mstrio.object_management.search_operations import full_search
from mstrio.server.project import Project
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin, ObjectTypes
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    fetch_objects,
    get_default_args_from_func,
    get_valid_project_id,
)
from mstrio.utils.response_processors import objects as objects_processors


class ShortcutInfoFlags(IntFlag):
    DssDashboardShortcutInfoBookmark = 0b10
    DssDashboardShortcutInfoTOC = 0b01
    DssDashboardShortcutInfoDefault = 0b00


def list_shortcuts(
    connection: Connection,
    project_id: str | None = None,
    project_name: str | None = None,
    project: Project | None = None,
    to_dictionary: bool = False,
):
    """List all shortcuts in a project.

    The project may be specified by either `project_id`, `project_name` or
        `project`. If the project is not specified in either way, the project
        from the `connection` object is used.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`.
        project_id (str, optional): ID of the project to search in.
        project_name (str, optional): Name of the project to search in.
            May be used instead of `project_id`.
        project (Project, optional): Project object specifying the project to
            search in. May be used instead of `project_id`.
        to_dictionary (bool, optional): If True, the method will return
            dictionaries with the shortcuts' properties instead of Shortcut
            objects. Defaults to False.

    """

    if project_id is None and project is not None:
        project_id = project.id
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=True,
    )

    # No endpoint for listing shortcuts. Using full_search instead.
    objects = full_search(
        connection,
        object_types=[ObjectTypes.SHORTCUT_TYPE],
        domain=SearchDomain.PROJECT,
        project=project_id,
    )

    if to_dictionary:
        return objects

    return Shortcut.bulk_from_dict(source_list=objects, connection=connection)


class Shortcut(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Representation of a Shortcut object. It points to another object in
    the metadata, and for Library objects it stores additional information
    related to browsing the Library.

    Attributes:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`.
        id (str): ID of the shortcut object
        name (str): Name of the shortcut
        project_id (str): ID of the project that the shortcut is in
        type (ObjectTypes): object type (SHORTCUT_TYPE)
        date_created (DateTime): creation time
        date_modified (DateTime): last modification time
        version (str): object version ID
        acg (Rights): access rights
            (See EnumDSSXMLAccessRightFlags for possible values)
        acl (list[ACE]): object access control list
        hidden (bool): Specifies whether the object is hidden
        owned_by_current_user (bool): whether the current user owns the shortcut
        target (dict): metadata of the target object related to viewing
            in Library
        target_info (dict): general metadata of the target object
        encode_html_content (bool): Flag indicating whether to encode
            HTML content
        current_page_key (str): Current page node key
        stid (int): Shortcut Sate ID
        current_bookmark (dict): Name and ID of the current bookmark
        prompted (bool): Flag indicating whether the target object has prompts
        datasets_cache_info_hash (str): The hash value for the Dashboard dataset
            cache info
        shortcut_info_flag (bool): flag indicating what information about
            the shortcut should be loaded
    """

    _OBJECT_TYPE = ObjectTypes.SHORTCUT_TYPE
    _API_GETTERS = {
        (
            'name',
            'id',
            'project_id',
            'owned_by_current_user',
            'target',
            'encode_html_content',
            'current_page_key',
            'shared_time',
            'last_viewed_time',
            'last_modified_time',
            'stid',
            'current_bookmark',
            'prompted',
            'datasets_cache_info_hash',
            'shortcut_info_flag',
            'dossier_version_hash',
        ): browsing.get_shortcut,
        (
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl',
            'target_info',
            'hidden',
        ): objects_processors.get_info,
    }
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'shortcut_info_flag': ShortcutInfoFlags}
    _API_PATCH: dict = {
        (
            'name',
            'description',
            'abbreviation',
            'hidden',
            'folder_id',
            'comments',
            'owner',
        ): (
            objects_processors.update,
            'partial_put',
        )
    }

    def __init__(
        self,
        connection: Connection,
        id: str,
        project_id: str = None,
        project_name: str = None,
        shortcut_info_flag: (
            ShortcutInfoFlags | int
        ) = ShortcutInfoFlags.DssDashboardShortcutInfoTOC,
    ):
        """Initialize the Shortcut object and populate it with I-Server data.

        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.

        Note:
            When `project_id` is `None` and `project_name` is `None`, then
            its value is overwritten by `project_id` from `connection` object.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`.
            id: Shortcut ID
            project_id: ID of the project that the shortcut is in
            project_name: Project name
            shortcut_info_flag: flag indicating what information about shortcut
                should be loaded
        """
        if id is None:
            raise AttributeError("Please specify 'id' parameter in the constructor.")
        else:
            project_id = get_valid_project_id(
                connection=connection,
                project_id=project_id,
                project_name=project_name,
                with_fallback=not project_name,
            )
            super().__init__(
                connection=connection,
                object_id=id,
                project_id=project_id,
                shortcut_info_flag=get_enum_val(shortcut_info_flag, ShortcutInfoFlags),
            )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._owned_by_current_user = kwargs.get('owned_by_current_user')
        self._target = kwargs.get('target')
        self._encode_html_content = kwargs.get('encode_html_content')
        self._shortcut_info_flag = (
            ShortcutInfoFlags(kwargs["shortcut_info_flag"])
            if kwargs.get("shortcut_info_flag")
            else None
        )
        self._current_page_key = kwargs.get('current_page_key')
        self._shared_time = kwargs.get('shared_time')
        self._last_viewed_time = kwargs.get('last_viewed_time')
        self._last_modified_time = kwargs.get('last_modified_time')
        self._stid = kwargs.get('stid')
        self._current_bookmark = kwargs.get('current_bookmark')
        self._prompted = kwargs.get('prompted')
        self._datasets_cache_info_hash = kwargs.get('datasets_cache_info_hash')
        self._dashboard_version_hash = kwargs.get('dossier_version_hash')

    T = TypeVar('T')

    @classmethod
    def from_dict(
        cls: T,
        source: dict[str, Any],
        connection: Connection,
        to_snake_case: bool = True,
        with_missing_value: bool = False,
    ) -> T:
        """Instantiate a Shortcut from a dict source."""
        return super(Entity, cls).from_dict(
            source=source,
            connection=connection,
            to_snake_case=to_snake_case,
            with_missing_value=with_missing_value,
        )

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ):
        """Alter the shortcut's properties.

        Args:
            name (str, optional): name of the shortcut object
            description (str, optional): description of the shortcut object
            abbreviation (str, optional): abbreviation of the shortcut object
            hidden (bool, optional): specifies whether the shortcut is hidden
            comments (str, optional): long description of the shortcut
            owner: (str, User, optional): owner of the shortcut object
        """
        if isinstance(owner, User):
            owner = owner.id
        func = self.alter
        default_dict = get_default_args_from_func(func)
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def create_shortcut(
        self,
        target_folder_id=None,
        target_folder_path=None,
        target_folder=None,
        project_id=None,
        project_name=None,
        project=None,
        to_dictionary=False,
    ):
        raise ValueError("Shortcut cannot refer to another shortcut.")

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
    def dashboard_version_hash(self):
        return self._dashboard_version_hash


def get_shortcuts(
    connection: Connection,
    shortcut_ids: list[str],
    project_id: str = None,
    project_name: str = None,
    shortcut_info_flag: (
        ShortcutInfoFlags | int
    ) = ShortcutInfoFlags.DssDashboardShortcutInfoDefault,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list[dict] | list[Shortcut]:
    """Retrieve information about specific published shortcuts
     in specific project.

     Specify either `project_id` or `project_name`.
     When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
         When `project_id` is `None` and `project_name` is `None`,
         then its value is overwritten by `project_id` from `connection`
         object.

     Args:
         shortcut_ids: ids of target shortcuts
         project_id: id of project that the shortcuts are in
         project_name: Project name
         shortcut_info_flag: a single ShortcutInfoFlags that describes what
           exact info are to be fetched
         to_dictionary: parameter describing output format
         limit (int): limit the number of elements returned.
             If `None` (default), all objects are returned.
     Return:
         list of dictionaries or Shortcut objects,
           depending on `to_dictionary` parameter
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=not project_name,
    )

    shortcuts = fetch_objects(
        connection=connection,
        api=browsing.get_shortcuts,
        dict_unpack_value="shortcuts",
        limit=limit,
        filters=filters,
        body=[{"projectId": project_id, "shortcutIds": shortcut_ids}],
        shortcut_info_flag=get_enum_val(shortcut_info_flag, ShortcutInfoFlags),
    )

    if to_dictionary:
        return shortcuts
    else:
        return [
            Shortcut.from_dict(source=short, connection=connection)
            for short in shortcuts
        ]
