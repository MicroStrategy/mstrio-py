import logging

from mstrio import config
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import Entity
from mstrio.utils.helper import _prepare_objects as filter_objects
from mstrio.utils.helper import delete_none_values
from mstrio.utils.response_processors import drivers
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


def list_drivers(
    connection: Connection, to_dictionary: bool = False, **filters
) -> list['Driver'] | list[dict]:
    """Get all drivers as list of Driver objects or dictionaries.

    Optionally filter the drivers by specifying filters.

    Args:
        connection: Strategy One connection object
        to_dictionary: If True returns a list of Driver dicts,
           otherwise returns a list of Driver objects
       **filters: Available filter parameters:
           ['id', 'name', 'is_enabled', 'is_odbc']
    """
    return Driver.list(connection, to_dictionary, **filters)


@class_version_handler('11.3.0960')
class Driver(Entity):
    """Object representation of Strategy One Driver

    Attributes:
        connection: A Strategy One connection object
        id: Driver's ID
        name: Driver's name
        is_enabled: specifies if a Driver is enabled
        is_odbc: specifies if a Driver is of ODBC type
        description: Object description
        abbreviation: Object abbreviation
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        version: Version ID
        owner: User object that is the owner
        icon_path: Object icon path
        view_media: View media settings
        ancestors: List of ancestor folders
        certified_info: Certification status, time of certification, and
            information about the certifier (currently only for document and
            report)
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.DRIVER
    _API_GETTERS = {
        (
            'name',
            'description',
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
            'comments',
            'owner',
        ): objects_processors.get_info,
        ('id', 'name', 'is_enabled', 'is_odbc'): drivers.get,
    }
    _API_PATCH: dict = {
        'enabled': (drivers.update, 'patch'),
        (
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
    }

    def __init__(
        self, connection: Connection, id: str | None = None, name: str | None = None
    ):
        """Initialize Driver object by passing ID or name.
        When `id` is provided, `name` is omitted.

        Args:
            connection (Connection): Strategy One connection object
            id (str): ID of Driver
            name (str): name of Driver
        """

        if id is None and name is None:
            raise ValueError(
                "Please specify either 'id' or 'name' parameter in the constructor."
            )

        if id is None:
            result: list[dict] = self.list(connection, name=name, to_dictionary=True)

            if result:
                object_data = result[0]
                self._init_variables(**object_data, connection=connection)
            else:
                raise ValueError(f"There is no Driver named: '{name}'.")
        elif id == '':
            raise ValueError("Driver's ID cannot be an empty string.")
        else:
            super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self.is_enabled = kwargs.get('is_enabled')
        self.is_odbc = kwargs.get('is_odbc')

    def alter(
        self,
        is_enabled: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Update properties of a Driver

        Args:
            is_enabled (bool, optional): specifies if a Driver is enabled
            comments (str, optional): long description of the Driver
            owner: (str, User, optional): owner of the Driver
        """
        if isinstance(owner, User):
            owner = owner.id
        properties = {
            'enabled': is_enabled,
            'comments': comments,
            'owner': owner,
        }
        not_none_properties = delete_none_values(properties, recursion=False)
        self._alter_properties(**not_none_properties)

        if config.verbose:
            logger.info(f"Updated driver: '{self.name}' with ID: {self.id}.")

    @classmethod
    def list(
        cls, connection: Connection, to_dictionary: bool = False, **filters
    ) -> list[type['Driver']] | list[dict]:
        """Get all driver as list of Driver objects or dictionaries.

        Optionally filter the drivers by specifying filters.

        Args:
            connection (Connection): Strategy One connection object
            to_dictionary (bool): If True returns a list of Driver dicts,
               otherwise returns a list of Driver objects
           **filters: Available filter parameters:
               ['id', 'name', 'is_enabled', 'is_odbc']
        """

        objects = filter_objects(drivers.get_all(connection), filters)

        if to_dictionary:
            return objects

        return cls.bulk_from_dict(source_list=objects, connection=connection)

    def enable(self):
        """Enable driver."""
        if not self.is_enabled:
            self.alter(is_enabled=True)

    def disable(self):
        """Disable driver."""
        if self.is_enabled:
            self.alter(is_enabled=False)
