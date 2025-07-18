from typing import Any, TypeVar

from mstrio.connection import Connection
from mstrio.object_management.folder import Folder

# Moved to library_shortcuts
from mstrio.object_management.library_shortcut import (  # noqa: F401
    ShortcutInfoFlags,
    get_shortcuts,
)
from mstrio.object_management.search_enums import SearchDomain
from mstrio.object_management.search_operations import full_search
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin, ObjectTypes
from mstrio.utils.helper import get_default_args_from_func, get_valid_project_id
from mstrio.utils.response_processors import objects as objects_processors


def list_shortcuts(
    connection: Connection,
    name: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    project: Project | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    folder: Folder | None = None,
    folder_id: str | None = None,
    folder_path: str | None = None,
    **filters,
):
    """List all shortcuts in a project.

    The project may be specified by either `project_id`, `project_name` or
        `project`. If the project is not specified in either way, the project
        from the `connection` object is used.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`.
        name (string, optional): The search pattern for listing shortcuts.
            Supports wildcards '*' (any number of characters) and '?' (exactly
            one character).
        project_id (str, optional): ID of the project to search in.
        project_name (str, optional): Name of the project to search in.
            May be used instead of `project_id`.
        project (Project, optional): Project object specifying the project to
            search in. May be used instead of `project_id`.
        to_dictionary (bool, optional): If True, the method will return
            dictionaries with the shortcuts' properties instead of Shortcut
            objects. Defaults to False.
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        folder (Folder, optional): Folder object specifying where the search
            will be performed.
        folder_id (string, optional): ID of a folder where the search
            will be performed. Can be provided as an alternative to `folder`
            parameter.
        folder_path (str, optional): Path of the folder in which the search
            will be performed. Can be provided as an alternative to `folder`
            and `folder_id` parameters. The path has to be provided in the
            forward-slash format, beginning with project name, e.g.
            "/MicroStrategy Tutorial/Public Objects/Metrics".
        **filters: Available filter parameters: ['id', 'type', 'subtype',
            'date_created', 'date_modified', 'version', 'owner', 'ext_type',
            'view_media', 'certified_info']

    """

    if project_id is None and project is not None:
        project_id = project.id
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=True,
    )
    if folder and not folder_id:
        folder_id = folder.id
    if folder_path and folder_id:
        folder_path = None

    # No endpoint for listing shortcuts. Using full_search instead.
    objects = full_search(
        connection,
        object_types=ObjectSubTypes.SHORTCUT,
        domain=SearchDomain.PROJECT,
        project=project_id,
        name=name,
        limit=limit,
        root=folder_id,
        root_path=folder_path,
        **filters,
    )

    if to_dictionary:
        return objects

    return Shortcut.bulk_from_dict(source_list=objects, connection=connection)


class Shortcut(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Representation of a Shortcut object. It points to another object in
    the metadata.
    DEPRECATION: This class no longer provides information about details of the
        target object's state in Library. For those details, please use
        `LibraryShortcut`.

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
        target_info (dict): general metadata of the target object
    """

    _OBJECT_TYPE = ObjectTypes.SHORTCUT_TYPE
    _OBJECT_SUBTYPES = [ObjectSubTypes.SHORTCUT]
    _API_GETTERS = {
        (
            'name',
            'id',
            'project_id',
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
            )

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
