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
    get_valid_project_id,
)
from mstrio.utils.library import LibraryMixin
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler


@method_version_handler('11.4.0300')
def list_bots(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    **filters,
) -> list['Bot'] | list[dict]:
    """Get a list of bots.

    Args:
        connection (Connection): Strategy One connection object returned
            by 'connection.Connection()'
        name (str, optional): characters that the dashboard name must contain
        to_dictionary (bool, optional): if True, return Bots as a
            list of dicts
        limit (int, optional): limit the number of elements returned.
            If `None` (default), all objects are returned.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version',
            'owner', 'ext_type', 'view_media', 'certified_info']

    Returns:
        A list of bot objects or dictionaries.
    """

    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=True,
    )

    objects = search_operations.full_search(
        connection=connection,
        object_types=[
            ObjectSubTypes.DOCUMENT_BOT,
            ObjectSubTypes.DOCUMENT_BOT_2_0,
            ObjectSubTypes.DOCUMENT_BOT_UNIVERSAL,
        ],
        project=project_id,
        name=name,
        limit=limit,
        **filters,
    )

    if to_dictionary:
        return objects
    else:
        return [Bot.from_dict(source=obj, connection=connection) for obj in objects]


@class_version_handler('11.4.0300')
class Bot(Entity, CertifyMixin, CopyMixin, DeleteMixin, MoveMixin, LibraryMixin):
    """Python representation of a Strategy One Bot object"""

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION

    # May also initialize to DOCUMENT_BOT_2_0 or DOCUMENT_BOT_UNIVERSAL
    _OBJECT_SUBTYPE = ObjectSubTypes.DOCUMENT_BOT

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
        """Initialize Bot object by passing name or id.

        Args:
            connection (object): Strategy One connection object returned
                by `connection.Connection()`
            name (string, optional): name of Bot
            id (string, optional): ID of Bot
        """
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")
            bot = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_bots,
            )
            id = bot['id']
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
        """Alter the Bot.

        Args:
            name (str, optional): New name for the bot
            description (str, optional): New description for the bot
            abbreviation (str, optional): New abbreviation for the bot
            folder_id (str, optional): ID of the folder where the bot
                should be moved to
            folder_path (str, optional): Path to the folder where the bot
                should be moved to, optional instead of folder ID
            hidden (bool, optional): Hidden status of the bot
            status (str, optional): Status of the bot
                Can be either enabled or disabled
            comments (str, optional): New long description for the bot
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
        """Enable the bot."""
        self.alter(status='enabled')

    def disable(self) -> None:
        """Disable the bot."""
        self.alter(status='disabled')

    @property
    def status(self) -> str:
        """Status of the bot."""
        if self._status is None:
            self.fetch('status')
        return self._status
