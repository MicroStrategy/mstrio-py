import logging
from typing import TYPE_CHECKING

from requests import Response

from mstrio import config
from mstrio.api import objects as objects_api
from mstrio.object_management.search_operations import (
    SearchDomain,
    SearchPattern,
    full_search,
)
from mstrio.types import ObjectTypes, TypeOrSubtype
from mstrio.users_and_groups.user import User
from mstrio.utils.acl import ACLMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    get_args_from_func,
    get_default_args_from_func,
    get_owner_id,
)
from mstrio.utils.resolvers import (
    FolderPathType,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.object_management.folder import Folder
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


def list_objects(
    connection: "Connection",
    object_type: TypeOrSubtype | int,
    name: str | None = None,
    project: "Project | str | None" = None,
    project_id: str | None = None,
    project_name: str | None = None,
    domain: SearchDomain | int = SearchDomain.CONFIGURATION,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    folder: 'Folder | str | FolderPathType | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: FolderPathType | None = None,
    to_dictionary: bool = False,
    limit: int = None,
    **filters,
) -> list["Object"] | list[dict]:
    """Get list of objects or dicts. Optionally filter the
    objects by specifying filters.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        object_type (TypeOrSubtype | int): Object type. Possible values can
            be found in EnumDSSXMLObjectTypes
        name (string, optional): value the search pattern is set to, which
            will be applied to the names of objects being searched
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        domain (SearchDomain | int, optional): domain where the search will be
            performed, such as Local or Project, possible values
            are defined in EnumDSSXMLSearchDomain
        search_pattern (SearchPattern | int, optional): pattern to search
            for, such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        folder (Folder | str | FolderPathType, optional): Folder object or ID or
            name or path specifying the folder. See `folder_id`, `folder_name`
            or `folder_path` for more info.
        folder_id (str, optional): ID of a folder as string.
        folder_name (str, optional): Name of a folder as string.
        folder_path (FolderPathType, optional): Path of the folder. It can
            be a string with "/" as path separator
            (e.g. "folder/subfolder1/subfolder2") or a tuple or list of path
            parts (e.g. `("folder", "subfolder1", "subfolder2")`).

            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    `/MicroStrategy Tutorial/Public Objects/Metrics`
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    `/CASTOR_SERVER_CONFIGURATION/Users`
        to_dictionary (bool, optional): If True returns dict, by default
            (False) returns Objects.
        limit (int, optional): limit the number of elements returned. If `None`
            (default), all objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg', 'owner', 'ext_type']

    Examples:
        >>> list_objects(connection, object_type=ObjectTypes.USER)
    """

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    result = Object._list_objects(
        connection=connection,
        object_type=object_type,
        name=name,
        project_id=proj_id,
        domain=domain,
        pattern=search_pattern,
        to_dictionary=to_dictionary,
        folder=folder,
        folder_id=folder_id,
        folder_name=folder_name,
        folder_path=folder_path,
        limit=limit,
        **filters,
    )

    if not result:
        logger.info(
            f"Search in the domain: {domain.name} returned empty result."
            " Try searching in different domain."
        )
    return result


def bulk_delete_objects(
    connection: "Connection",
    objects: list[Entity | dict | str],
    objects_type: ObjectTypes | int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    force: bool = False,
    journal_comment: str | None = None,
    success_msg: str | None = None,
    fail_msg: str | None = None,
) -> bool:
    """Delete multiple objects in bulk.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        objects (list[Object] | list[dict] | list[str]): List of objects to
            delete. Can be a list of Object instances, dicts with object
            information (must contain 'id' and 'type' keys), or object IDs
            as strings. If only IDs are provided, then `objects_type` must be
            specified.
        objects_type (ObjectTypes | int, optional): Object type. Required if
            `objects` is a list of IDs. Possible values can be found in
            EnumDSSXMLObjectTypes.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID.
        project_name (str, optional): Project name.
        force: If True, then no additional prompt will be shown before
            deleting objects.
        journal_comment (str, optional): Comment that will be added to the
            objects' change journal entries. If None, no comment will be added.
        success_msg (str, optional): Custom message to log if deletion is
            successful.
        fail_msg (str, optional): Custom message to log if deletion fails.

    Returns:
        bool: True if deletion of all items was successful, False otherwise.
    """
    if success_msg is None:
        success_msg = "Successfully deleted the batch of objects."
    if fail_msg is None:
        fail_msg = "Deleting some of the batch of objects failed."

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    def get_object_dict(obj_rep):
        NO_TYPE_ERR_MSG = (
            "When not providing type in object representation, "
            "`objects_type` must be specified."
        )
        if isinstance(obj_rep, str):
            if not objects_type:
                raise ValueError(NO_TYPE_ERR_MSG)
            return {'id': obj_rep, 'type': get_enum_val(objects_type, ObjectTypes)}
        elif isinstance(obj_rep, dict):
            if 'type' not in obj_rep and not objects_type:
                raise ValueError(NO_TYPE_ERR_MSG)
            if 'id' not in obj_rep:
                raise ValueError(
                    "When `objects` is a list of dicts, each dict must contain "
                    "the 'id' key and either a 'type' key or `objects_type` "
                    "must be specified."
                )
            return {
                'id': obj_rep['id'],
                'type': get_enum_val(obj_rep.get('type', objects_type), ObjectTypes),
            }
        elif isinstance(obj_rep, Entity):
            return {'id': obj_rep.id, 'type': obj_rep.type.value}
        else:
            raise ValueError(
                "Each item in `objects` must be either an Entity instance, "
                "a dict with 'id' and 'type', or an ID string."
            )

    body = [get_object_dict(obj_rep) for obj_rep in objects]

    user_input = 'N'
    if not force:
        object_str = "object" if len(objects) == 1 else f"{len(objects)} objects"
        user_input = input(
            f"Are you sure you want to delete the selected {object_str}? [Y/N]: "
        )
        if user_input != 'Y':
            return False
    try:
        res: Response = objects_api.bulk_delete_objects(
            connection,
            body,
            project_id=proj_id,
            error_msg=fail_msg,
            journal_comment=journal_comment,
        )

        if config.verbose and res.ok:
            logger.info(success_msg)

        return res.ok
    except Exception:
        logger.warning(fail_msg)
        return False


class Object(Entity, ACLMixin, CertifyMixin, CopyMixin, MoveMixin, DeleteMixin):
    """Class representing a general type object using attributes common for
     all available metadata objects.

    Attributes:
        name: name of the object
        id: object ID
        description: Description of the object
        abbreviation: Object abbreviation
        version: Object version ID
        ancestors: List of ancestor folders
        type: Object type. Enum
        subtype: Object subtype
        ext_type: Object extended type.
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd HH:mm:ss" in UTC
        owner: User object that is the owner
        icon_path: Object icon path
        view_media: View media settings
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        hidden: Specifies whether the object is hidden
        certified_info: Certification status, time of certification, and
            information about the certifier (currently only for document and
            report)
        project_id: project ID
        target_info: target information, only applicable to Shortcut objects
    """

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'certified_info': CertifiedInfo.from_dict,
        'owner': User.from_dict,
    }
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'date_created',
            'date_modified',
            'acg',
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acl',
            'comments',
            'project_id',
            'hidden',
            'target_info',
            'hidden',
            'comments',
        ): objects_processors.get_info
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
        ): (objects_processors.update, 'partial_put'),
    }

    def __init__(self, connection: "Connection", type: ObjectTypes, id: str):
        """Initialize object by ID.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            id (str): Identifier of an existing object.
            type (ObjectTypes): object type
        """

        super().__init__(connection=connection, object_id=id, type=type)

    def _init_variables(self, **kwargs) -> None:
        object_type = kwargs.get('type')
        self._OBJECT_TYPE = (
            ObjectTypes(object_type)
            if ObjectTypes.contains(object_type)
            else ObjectTypes.NOT_SUPPORTED
        )
        super()._init_variables(**kwargs)

    def __str__(self):
        return f"Object named: '{self.name}' with ID: '{self.id}'"

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
        owner_id: str | None = None,
        owner_username: str | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter the object properties.

        Args:
            name (str, optional): object name
            description (str, optional): object description
            abbreviation (str, optional): abbreviation
            hidden (str, optional): Specifies whether the metric is hidden
            comments (str, optional): long description of the object
            owner (str, User, optional): username, user ID, or User object
                representing the new owner of the object. If `owner` is
                provided, `owner_id` and `owner_username` are ignored
            owner_id (str, optional): ID of the new owner of the object. If only
                owner_id and owner_username are provided, then owner_username is
                omitted and the owner is set to the user with the given ID
            owner_username (str, optional): username of the new owner of the
                object
            journal_comment (optional, str): Comment that will be added to the
                object's change journal entry
        """
        if owner or owner_id or owner_username:
            owner = get_owner_id(self.connection, owner, owner_id, owner_username)
            owner_id = None
            owner_username = None
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_objects(
        cls,
        connection: "Connection",
        object_type: TypeOrSubtype | int,
        name: str | None = None,
        project_id: str | None = None,
        to_dictionary: bool = False,
        domain: int | SearchDomain = SearchDomain.CONFIGURATION,
        pattern: int | SearchPattern = SearchPattern.CONTAINS,
        folder: 'Folder | str | FolderPathType | None' = None,
        folder_id: str | None = None,
        folder_name: str | None = None,
        folder_path: FolderPathType | None = None,
        limit: int | None = None,
        **filters,
    ) -> list["Object"] | list[dict]:
        objects = full_search(
            connection,
            object_types=object_type,
            name=name,
            project=project_id,
            domain=domain,
            pattern=pattern,
            root=folder,
            root_id=folder_id,
            root_name=folder_name,
            root_path=folder_path,
            limit=limit,
            **filters,
        )
        if to_dictionary:
            return objects
        return [cls.from_dict(source=obj, connection=connection) for obj in objects]
