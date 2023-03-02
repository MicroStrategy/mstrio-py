import logging
from typing import Optional, TYPE_CHECKING

from mstrio import config
from mstrio.api import folders, objects
from mstrio.object_management import PredefinedFolders
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.helper import (
    fetch_objects_async,
    get_default_args_from_func,
    get_valid_project_id
)

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


def list_folders(
    connection: "Connection",
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters
) -> list["Folder"] | list[dict]:
    """Get a list of folders - either all folders in a specific project or all
    folders that are outside of projects, called configuration-level folders.
    The list of configuration-level folders includes folders such as users, user
    groups, databases, etc. which are not project-specific. If you pass
    a `project_id` or `project_name`, you get folders in that project;
    if not, then you get configuration-level folders.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        Id of project is not taken directly from `Connection` object, so you
        have to specify it explicitly.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (string, optional): project ID
        project_name (string, optional): project name
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns objects.
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Returns:
        list of `Folder` objects or list of dictionaries
    """
    # Project is validated only if project was specified in arguments -
    # otherwise fetch is performed from a non-project area.
    if project_id or project_name:
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
        )
    objects = fetch_objects_async(
        connection,
        folders.list_folders,
        folders.list_folders_async,
        limit=limit,
        chunk_size=1000,
        project_id=project_id,
        filters=filters
    )

    if to_dictionary:
        return objects
    else:
        from mstrio.utils.object_mapping import map_objects_list
        return map_objects_list(connection, objects)


def get_my_personal_objects_contents(
    connection: "Connection",
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
) -> list:
    """Get contents of `My Personal Objects` folder in a specific project.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        project_id (string, optional): project ID
        project_name (string, optional): project name
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns objects.

    Returns:
        list of objects or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects = folders.get_my_personal_objects_contents(connection, project_id).json()
    if to_dictionary:
        return objects
    else:
        from mstrio.utils.object_mapping import map_objects_list
        return map_objects_list(connection, objects)


def get_predefined_folder_contents(
    connection: "Connection",
    folder_type: PredefinedFolders,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters
) -> list:
    """Get contents of a pre-defined MicroStrategy folder in a specific project.
    Available values for `folder_type` are stored in enum `PredefinedFolders`.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Note:
        When `project_id` is `None`, then its value is overwritten by
        `project_id` from `connection` object.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        folder_type (enum): pre-defined folder type. Available values are
            stored in enum `PredefinedFolders`.
        project_id (string, optional): project ID
        project_name (string, optional): project name
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns objects.
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Returns:
        list of objects or list of dictionaries
    """

    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    objects = fetch_objects_async(
        connection,
        folders.get_predefined_folder_contents,
        folders.get_predefined_folder_contents_async,
        limit=limit,
        chunk_size=1000,
        folder_type=folder_type.value,
        project_id=project_id,
        filters=filters
    )

    if to_dictionary:
        return objects
    else:
        from mstrio.utils.object_mapping import map_objects_list
        return map_objects_list(connection, objects)


class Folder(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Object representation of MicroStrategy Folder object.

    Attributes:
        connection: MSTR Connection object
        id: ID of the folder
        name: name of the folder
        description: description of the folder
        type: the type of the folder (based on EnumDSSXMLObjectTypes)
        subtype: the subtype of the folder (based on EnumDSSXMLObjectSubTypes)
        date_created: the date/time at which the folder was first saved into the
            metadata
        date_modified: the date/time at which the folder was last saved into the
            metadata
        version: the version number this folder is currently carrying
        acl: an array of access control entry objects
        owner: User object, the owner of the object
        acg: access rights, EnumDSSXMLAccessRightFlags
        ext_type: object extended type, EnumDSSExtendedType
        ancestors: list of ancestor folders
        abbreviation: folder's abbreviation
        hidden: specifies whether the folder is hidden
        icon_path: folder icon path
        view_media: view media settings
        certified_info: CertifiedInfo object, certification status, time of
            certification, and information about the certifier (currently only
            for document and report)
        contents: contents of folder
    """

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict
    }

    _API_PATCH: dict = {**Entity._API_PATCH, ('folder_id'): (objects.update_object, 'partial_put')}

    _OBJECT_TYPE = ObjectTypes.FOLDER
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes

    def __init__(self, connection: "Connection", id: str, name: Optional[str] = None):
        """Initialize folder object by its identifier.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify folder.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing folder containing
                the required data.
            name (str): name of folder.
        """
        super().__init__(connection, id, name=name)

    @classmethod
    def create(
        cls, connection: "Connection", name: str, parent: str, description: Optional[str] = None
    ) -> "Folder":
        """Create a new folder in a folder selected within connection object
        by providing its name, id of parent folder and optionally description.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name (str): name of a new folder.
            parent (str): id of a parent folder in which new folder will be
                created.
            description (str, optional): optional description of a new folder.

        Returns:
            newly created folder
        """
        connection._validate_project_selected()
        response = folders.create_folder(connection, name, parent, description).json()
        if config.verbose:
            logger.info(
                f"Successfully created folder named: '{response.get('name')}' "
                f"with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Alter the folder properties.

        Args:
            name: folder name
            description: folder description
        """
        func = self.alter
        default_dict = get_default_args_from_func(func)
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def get_contents(self, to_dictionary: bool = False, **filters) -> list:
        """Get contents of folder. It can contains other folders or different
        kinds of objects.

        Args:
            to_dictionary (bool, optional): If True returns dicts, by default
                (False) returns objects.
            **filters: Available filter parameters: ['id', 'name',
                'description', 'date_created', 'date_modified', 'acg']

        Returns:
            Contents as Python objects (when `to_dictionary` is `False` (default
            value)) or contents as dictionaries otherwise.
        """
        objects = fetch_objects_async(
            self.connection,
            folders.get_folder_contents,
            folders.get_folder_contents_async,
            limit=None,
            chunk_size=1000,
            id=self.id,
            filters=filters
        )

        if to_dictionary:
            return objects
        else:
            from mstrio.utils.object_mapping import map_objects_list
            return map_objects_list(self.connection, objects)
