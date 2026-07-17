from typing import TYPE_CHECKING

from mstrio.connection import Connection
from mstrio.object_management import search_operations
from mstrio.object_management.search_enums import (
    SearchDomain,
    SearchPattern,
    SearchScope,
)
from mstrio.types import ExtendedType, ObjectSubTypes, ObjectTypes, ViewMedia
from mstrio.users_and_groups import User
from mstrio.utils.ai import EnableForAiMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.helper import filter_params_for_func, find_object_with_name
from mstrio.utils.resolvers import (
    FolderPathType,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.object_management.folder import Folder
    from mstrio.server.project import Project


@method_version_handler('11.5.0800')
def list_mosaic_models(
    connection: Connection,
    name: str | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    folder: 'Folder | str | FolderPathType | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: 'FolderPathType | None' = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list['MosaicModel'] | list[dict]:
    """Get a list of Mosaic Models.

    Args:
        connection (Connection): Strategy connection object returned
            by `connection.Connection()`
        name (str, optional): characters that the mosaic model name must
            contain
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        folder (Folder | str | FolderPathType, optional): Folder object or ID
            or name or path specifying the folder. See `folder_id`,
            `folder_name` or `folder_path` for more info.
        folder_id (str, optional): ID of a folder as string.
        folder_name (str, optional): Name of a folder as string.
        folder_path (FolderPathType, optional): Path of the folder. It can be
            a string with "/" as path separator
            (e.g. "folder/subfolder1/subfolder2") or a tuple or list of path
            parts (e.g. `("folder", "subfolder1", "subfolder2")`).

            The path has to be provided in the following format,
            always starting with the project name,
            for example /MicroStrategy Tutorial/Public Objects/Metrics.
        to_dictionary (bool, optional): if True, return Mosaic Models as a
            list of dicts
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version',
            'owner', 'ext_type', 'view_media', 'certified_info']

    Returns:
        A list of MosaicModel objects or dictionaries.
    """
    validate_owner_key_in_filters(filters)

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    objects = search_operations.full_search(
        connection=connection,
        object_types=ObjectSubTypes.SUPER_CUBE,
        name=name,
        pattern=SearchPattern.CONTAINS,
        domain=SearchDomain.PROJECT,
        scope=SearchScope.ALL,
        include_hidden=True,
        ext_type=ExtendedType.DATA_IMPORT_DATASET,
        limit=limit,
        project=proj_id,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        **filters,
    )

    if to_dictionary:
        return objects

    return [MosaicModel.from_dict(source=obj, connection=connection) for obj in objects]


@class_version_handler('11.5.0800')
class MosaicModel(
    Entity,
    EnableForAiMixin,
    CertifyMixin,
    CopyMixin,
    DeleteMixin,
    MoveMixin,
):
    """Represents a Mosaic model.

    Attributes:
        connection: A Strategy connection object.
        id: Object ID.
        name: Object name.
        description: Object description.
        abbreviation: Object abbreviation.
        type: Object type.
        subtype: Object subtype.
        ext_type: Object extended type.
        date_created: Creation time, DateTime object.
        date_modified: Last modification time, DateTime object.
        version: Version ID.
        owner: Owner ID and name.
        icon_path: Object icon path.
        view_media: View media settings.
        ancestors: List of ancestor folders.
        location: Path to the Object.
        certified_info: Certification status, time of certification, and
            information about the certifier.
        acg: Access rights (see EnumDSSXMLAccessRightFlags for possible values).
        acl: Object access control list.
        hidden: Specifies if an object is hidden.
        connection_type: Connection type of the Mosaic model derived from
            `view_media`. Can be one of:
            - "in-memory"
            - "connect-live"
            - "off-memory"
            or None if it cannot be determined.
        is_linked_mosaic_model: Indicates whether this Mosaic model has one
            or more links (Mosaic linking).
    """

    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION
    _OBJECT_SUBTYPES = [ObjectSubTypes.SUPER_CUBE]

    _API_PATCH: dict = {
        **Entity._API_PATCH,
        ('folder_id', 'owner'): (objects_processors.update, 'partial_put'),
    }

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'certified_info': CertifiedInfo.from_dict,
        'owner': User.from_dict,
    }

    def __init__(
        self, connection: Connection, name: str | None = None, id: str | None = None
    ) -> None:
        """Initialize MosaicModel object by passing name or id.

        Args:
            connection (object): Strategy connection object returned
                by `connection.Connection()`
            name (string, optional): name of Mosaic Model
            id (string, optional): ID of Mosaic Model
        """
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")

            obj = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_mosaic_models,
            )
            id = obj['id']

        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
        )

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter the Mosaic model.

        Args:
            name (str, optional): New name for the Mosaic model
            description (str, optional): New description for the Mosaic model
            abbreviation (str, optional): New abbreviation for the Mosaic model
            hidden (bool, optional): Hidden status of the Mosaic model
            comments (str, optional): New long description for the Mosaic model
            owner: (str, User, optional): `User` object or ID
            journal_comment: (str, optional): Comment that will be added
                to the object's change journal entry
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @property
    def connection_type(self) -> str | None:
        """
        Connection type of the Mosaic model. Can be one of the following values:
        - 'in-memory'
        - 'connect-live'
        - 'off-memory'
        """
        vm = self.view_media
        if vm is None:
            return None

        if vm == ViewMedia.EMPTY:
            return "in-memory"
        if vm == ViewMedia.AVAILABLE_SERVE_AS_MODEL:
            return "connect-live"
        if vm == ViewMedia.AVAILABLE_OFF_MEMORY:
            return "off-memory"

        return None

    @property
    def is_linked_mosaic_model(self) -> bool:
        """True if this mosaic model has one or more links."""
        if self.view_media is None:
            return False
        return bool(self.view_media & ViewMedia.MOSAIC_LINKING.value)
