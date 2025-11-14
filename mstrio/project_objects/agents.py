from typing import TYPE_CHECKING

from mstrio.api import library
from mstrio.connection import Connection
from mstrio.object_management import search_operations
from mstrio.object_management.folder import get_folder_id_from_path
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.helper import (
    filter_params_for_func,
    find_object_with_name,
)
from mstrio.utils.library import LibraryMixin
from mstrio.utils.resolvers import (
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.object_management.folder import Folder
    from mstrio.server.project import Project


@method_version_handler('11.4.0300')
def _list_implementation(
    factory_class: 'type[Entity]',
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
):
    from mstrio.object_management.search_enums import SearchPattern

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    objects = search_operations.full_search(
        connection=connection,
        object_types=factory_class._OBJECT_SUBTYPES,
        pattern=SearchPattern.EXACTLY,
        project=proj_id,
        name=name,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        limit=limit,
        **filters,
    )

    if to_dictionary:
        return objects
    else:
        return [
            factory_class.from_dict(source=obj, connection=connection)
            for obj in objects
        ]


def list_agents(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> list['Agent'] | list[dict]:
    """Get a list of Agents.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        name (str, optional): characters that the dashboard name must contain
        to_dictionary (bool, optional): if True, return Agents as a
            list of dicts
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version',
            'owner', 'ext_type', 'view_media', 'certified_info']

    Returns:
        A list of Agent objects or dictionaries.
    """
    return _list_implementation(
        Agent,
        connection=connection,
        name=name,
        to_dictionary=to_dictionary,
        limit=limit,
        project=project,
        project_id=project_id,
        project_name=project_name,
        folder=folder,
        folder_id=folder_id,
        folder_name=folder_name,
        folder_path=folder_path,
        **filters,
    )


@class_version_handler('11.4.0300')
class Agent(Entity, CertifyMixin, CopyMixin, DeleteMixin, MoveMixin, LibraryMixin):
    """Python representation of a Strategy One Agent object"""

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION

    _OBJECT_SUBTYPES = [
        ObjectSubTypes.DOCUMENT_AGENT,
        ObjectSubTypes.DOCUMENT_AGENT_UNIVERSAL,
    ]

    _API_GETTERS = {
        **Entity._API_GETTERS,
        'status': objects_processors.get_info,
        'recipients': library.get_document,
    }
    _API_PATCH: dict = {
        **Entity._API_PATCH,
        ('status', 'folder_id', 'owner'): (objects_processors.update, 'partial_put'),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'certified_info': CertifiedInfo.from_dict,
        'recipients': [User.from_dict],
    }

    def __init__(
        self, connection: Connection, name: str | None = None, id: str | None = None
    ) -> None:
        """Initialize Agent object by passing name or id.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Agent
            id (string, optional): ID of Agent
        """
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")

            agent = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_agents,
            )
            id = agent['id']
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
        )

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._status = kwargs.get('status')

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        folder_id: str | None = None,
        folder_path: str | None = None,
        hidden: bool | None = None,
        status: str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the Agent.

        Args:
            name (str, optional): New name for the Agent
            description (str, optional): New description for the Agent
            abbreviation (str, optional): New abbreviation for the Agent
            folder_id (str, optional): ID of the folder where the Agent
                should be moved to
            folder_path (str, optional): Path to the folder where the Agent
                should be moved to, optional instead of folder ID
            hidden (bool, optional): Hidden status of the Agent
            status (str, optional): Status of the Agent
                Can be either enabled or disabled
            comments (str, optional): New long description for the Agent
            owner: (str, User, optional): owner of the Driver
        """
        if isinstance(owner, User):
            owner = owner.id
        description = description or self.description
        if folder_path and not folder_id:
            folder_id = get_folder_id_from_path(
                connection=self.connection, path=folder_path
            )
        properties = filter_params_for_func(
            self.alter, locals(), exclude=['self', 'folder_path']
        )
        self._alter_properties(**properties)

    def enable(self) -> None:
        """Enable the Agent."""
        self.alter(status='enabled')

    def disable(self) -> None:
        """Disable the Agent."""
        self.alter(status='disabled')

    @property
    def status(self) -> str:
        """Status of the Agent."""
        if self._status is None:
            self.fetch('status')
        return self._status
