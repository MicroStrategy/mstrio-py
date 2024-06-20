import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import folders
from mstrio.object_management import PredefinedFolders
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.helper import (
    fetch_objects_async,
    get_default_args_from_func,
    get_valid_project_id,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.translation_mixin import TranslationMixin

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


def list_folders(
    connection: "Connection",
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
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
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
             'owner', 'hidden',
          'ext_type']

    Returns:
        list of `Folder` objects or list of dictionaries
    """
    # Project is validated only if project was specified in arguments -
    # otherwise fetch is performed from a non-project area.
    if project_id or project_name:
        project_id = get_valid_project_id(
            connection=connection, project_id=project_id, project_name=project_name
        )
    objects = fetch_objects_async(
        connection,
        folders.list_folders,
        folders.list_folders_async,
        limit=limit,
        chunk_size=1000,
        project_id=project_id,
        filters=filters,
    )

    if to_dictionary:
        return objects
    else:
        from mstrio.utils.object_mapping import map_objects_list

        return map_objects_list(connection, objects)


def get_my_personal_objects_contents(
    connection: "Connection",
    project_id: str | None = None,
    project_name: str | None = None,
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
        with_fallback=not project_name,
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
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
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
        with_fallback=not project_name,
    )

    objects = fetch_objects_async(
        connection,
        folders.get_predefined_folder_contents,
        folders.get_predefined_folder_contents_async,
        limit=limit,
        chunk_size=1000,
        folder_type=folder_type.value,
        project_id=project_id,
        filters=filters,
    )

    if to_dictionary:
        return objects
    else:
        from mstrio.utils.object_mapping import map_objects_list

        return map_objects_list(connection, objects)


def get_folder_id_from_path(connection: "Connection", path: str) -> str:
    """Get folder id from folder path.

    Args:
        connection (Connection): MicroStrategy connection object returned by
            `connection.Connection()`
        path (str): path of the Folder
            the path has to be provided in the following format:
                if it's inside of a project, example:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, example:
                    /CASTOR_SERVER_CONFIGURATION/Users

    Returns:
        Folder id.
    """
    if path[0] == '/':
        path = path[1:]
    if path[-1] == '/':
        path = path[:-1]
    folders_in_path = path.split('/')
    project_id = (
        get_valid_project_id(project_name=folders_in_path[0], connection=connection)
        if folders_in_path[0] != 'CASTOR_SERVER_CONFIGURATION'
        else None
    )
    try:
        if project_id:
            original_project_id = connection.project_id
            connection.project_id = project_id
            # This root Project folder is hardcoded in every Environment
            folder = Folder(
                connection=connection, id='D43364C684E34A5F9B2F9AD7108F7828'
            )
        else:
            castor_id = (
                folders.get_predefined_folder_id(connection=connection, folder_type=39)
                .json()
                .get('id')
            )
            folder = Folder(connection=connection, id=castor_id)
        for i in range(1, len(folders_in_path)):
            temp_ids = [
                item.get('id')
                for item in folder.get_contents(to_dictionary=True)
                if item.get('type') == 8 and item.get('name') == folders_in_path[i]
            ]
            if not temp_ids:
                error_message = (
                    f"Couldn't find folder with given name {folders_in_path[i]} "
                    f"while exploring the path. Check if provided path is correct."
                )
                raise ValueError(error_message)
            folder = Folder(
                connection=connection,
                id=temp_ids[0],
            )
        return folder.id
    finally:
        if project_id:
            connection.project_id = (
                original_project_id if original_project_id else connection.project_id
            )


class Folder(Entity, CopyMixin, MoveMixin, DeleteMixin, TranslationMixin):
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

    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'owner': User.from_dict}

    _API_PATCH: dict = {
        (
            'name',
            'description',
            'abbreviation',
            'hidden',
            'folder_id',
            'comments',
        ): (objects_processors.update, 'partial_put')
    }

    _OBJECT_TYPE = ObjectTypes.FOLDER
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        path: str | None = None,
        name: str | None = None,
    ):
        """Initialize folder object by its identifier.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify folder.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str, optional): Identifier of a pre-existing folder containing
                the required data.
            path (str, optional): path of a a pre-existing folder containing
                the required data. Can be provided as an alternative to
                `id` parameter. If both are provided, `id` is used.
                    the path has to be provided in the following format:
                        if it's inside of a project, example:
                            /MicroStrategy Tutorial/Public Objects/Metrics
                        if it's a root folder, example:
                            /CASTOR_SERVER_CONFIGURATION/Users
            name (str): name of folder.
        """
        if not id:
            if path:
                id = get_folder_id_from_path(connection, path)
            else:
                raise ValueError("Either 'id' or 'path' has to be provided.")

        super().__init__(connection, id, name=name)

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        parent: str | None = None,
        parent_path: str | None = None,
        description: str | None = None,
    ) -> "Folder":
        """Create a new folder in a folder selected within connection object
        by providing its name, id of parent folder and optionally description.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name (str): name of a new folder.
            parent (str): id of a parent folder in which new folder will be
                created.
            parent_path (str, optional): path of a parent folder in which new
                folder will be created. Can be provided as an alternative to
                `parent` parameter. If both are provided, `parent` is used.
                    the path has to be provided in the following format:
                        if it's inside of a project, example:
                            /MicroStrategy Tutorial/Public Objects/Metrics
                        if it's a root folder, example:
                            /CASTOR_SERVER_CONFIGURATION/Users
            description (str, optional): optional description of a new folder.

        Returns:
            newly created folder
        """
        connection._validate_project_selected()

        if not parent:
            if parent_path:
                parent = get_folder_id_from_path(connection, parent_path)
            else:
                raise ValueError("Either 'parent' or 'parent_path' has to be provided.")

        response = folders.create_folder(connection, name, parent, description).json()
        if config.verbose:
            logger.info(
                f"Successfully created folder named: '{response.get('name')}' "
                f"with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
    ) -> None:
        """Alter the folder properties.

        Args:
            name: folder name
            description: folder description
            hidden: Specifies whether the metric is hidden
            comments: long description of the folder
        """
        func = self.alter
        default_dict = get_default_args_from_func(func)
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def get_contents(
        self, to_dictionary: bool = False, include_subfolders=False, **filters
    ) -> list:
        """Get contents of a folder. It can contain other folders or different
        kinds of objects.

        Args:
            to_dictionary (bool, optional): If True returns dicts, by default
                (False) returns objects.
            include_subfolders (bool, optional): If True returns contents of all
                subfolders as well. False by default.
                Note that using this option may result in a large number of
                objects being fetched, especially if coupled with filters.
            **filters: Available filter parameters: ['name', 'id', 'type',
                'subtype', 'date_created', 'date_modified', 'version',
                'acg', 'owner', 'ext_type']

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
            filters=filters,
        )

        if include_subfolders:
            if filters:
                child_folders = fetch_objects_async(
                    self.connection,
                    folders.get_folder_contents,
                    folders.get_folder_contents_async,
                    limit=None,
                    chunk_size=1000,
                    id=self.id,
                    filters={'type': 8},
                )
            else:
                child_folders = [child for child in objects if child.get('type') == 8]
            for child_folder in child_folders:
                folder = Folder(connection=self.connection, id=child_folder.get('id'))
                objects += folder.get_contents(
                    to_dictionary=True, include_subfolders=True, **filters
                )

        if to_dictionary:
            return objects
        else:
            from mstrio.utils.object_mapping import map_objects_list

            return map_objects_list(self.connection, objects)
