from typing import TYPE_CHECKING

from mstrio.connection import Connection
from mstrio.object_management import search_operations
from mstrio.object_management.search_enums import (
    SearchDomain,
    SearchPattern,
    SearchScope,
)
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
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


@method_version_handler('11.5.0400')
def list_ai_dataset_collections(
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
) -> list['AIDatasetCollection'] | list[dict]:
    """Get a list of AI Dataset Collections.

    Args:
        connection (Connection): Strategy connection object returned
            by `connection.Connection()`
        name (str, optional): characters that the AI Dataset Collection name
            must contain
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
        to_dictionary (bool, optional): if True, return AI Dataset Collections
            as a list of dicts
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version',
            'owner', 'ext_type', 'view_media', 'certified_info']

    Returns:
        A list of AIDatasetCollection objects or dictionaries.
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
        object_types=ObjectSubTypes.AI_DATASET_COLLECTION,
        name=name,
        pattern=SearchPattern.CONTAINS,
        domain=SearchDomain.PROJECT,
        scope=SearchScope.ALL,
        include_hidden=True,
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

    return [
        AIDatasetCollection.from_dict(source=obj, connection=connection)
        for obj in objects
    ]


@class_version_handler('11.5.0400')
class AIDatasetCollection(
    Entity,
    CertifyMixin,
    CopyMixin,
    DeleteMixin,
    MoveMixin,
):
    """Represents an AI Dataset Collection.

    Attributes:
        connection: A Strategy connection object.
        id: Object ID.
        name: Object name.
        description: Object description.
        abbreviation: Object abbreviation.
        type: Object type.
        subtype: Object subtype.
        ext_type: Object extended type.
        date_created: Creation time, as a `datetime` object.
        date_modified: Last modification time, as a `datetime` object.
        version: Version ID.
        owner: Owner ID and name.
        view_media: View media settings.
        ancestors: List of ancestor folders.
        certified_info: Certification status, time of certification, and
            information about the certifier.
        acg: Access rights (see `EnumDSSXMLAccessRightFlags` for possible
            values).
        acl: Object access control list.
        hidden: Specifies if the object is hidden.
    """

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION
    _OBJECT_SUBTYPES = [ObjectSubTypes.AI_DATASET_COLLECTION]

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
        self, connection: Connection, id: str | None = None, name: str | None = None
    ) -> None:
        """Initialize AIDatasetCollection object by passing name or id.

        Args:
            connection (object): Strategy connection object returned
                by `connection.Connection()`
            name (string, optional): name of AI Dataset Collection
            id (string, optional): ID of AI Dataset Collection
        """
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")

            obj = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_ai_dataset_collections,
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
        """Alter the AI Dataset Collection.

        Args:
            name (str, optional): New name for the AI Dataset Collection
            description (str, optional): New description for the AI Dataset
                Collection
            abbreviation (str, optional): New abbreviation for the AI Dataset
                Collection
            hidden (bool, optional): Hidden status of the AI Dataset Collection
            comments (str, optional): New long description for the AI Dataset
                Collection
            owner: (str, User, optional): owner of the AI Dataset Collection
            journal_comment: (str, optional): Comment that will be added
                to the object's change journal entry
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)
