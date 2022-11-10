import logging
from typing import List, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api import datasources, objects
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.helper import get_args_from_func, get_default_args_from_func
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@method_version_handler('11.2.0500')
def list_datasource_logins(
    connection: "Connection", to_dictionary: bool = False, limit: int = None, **filters
) -> Union[List["DatasourceLogin"], List[dict]]:
    """Get list of DatasourceLogin objects or dicts. Optionally filter the
    logins by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Examples:
        >>> list_db_logins(connection, name='db_login_name')
    """
    return DatasourceLogin._list_datasource_logins(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


@class_version_handler('11.2.0500')
class DatasourceLogin(Entity, CopyMixin, DeleteMixin):
    """A user login configuration object to access a particular datasource. Also
    formerly known as database login.

    Attributes:
        name: name of the database login
        id: database login ID
        description: Description of the database login
        username: database user to be used by the database login
        version: Object version ID
        ancestors: List of ancestor folders
        type: Object type. Enum
        subtype: Object subtype
        ext_type: Object extended type.
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        owner: User object that is the owner
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.DBLOGIN
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'owner': User.from_dict}
    _API_GETTERS = {
        (
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
            'acl'
        ): objects.get_object_info,
        ('id', 'name', 'description', 'username', 'date_created', 'date_modified',
         'acg'): datasources.get_datasource_login
    }
    _API_PATCH: dict = {
        ("abbreviation"): (objects.update_object, "partial_put"),
        ("name", "username", "description",
         "password"): (datasources.update_datasource_login, "patch")
    }
    _PATCH_PATH_TYPES = {"name": str, "username": str, "description": str, "password": str}

    def __init__(self, connection: "Connection", name: str = None, id: str = None):
        """Initialize DatasourceLogin object."""

        if id is None and name is None:
            raise ValueError("Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            objects_info = DatasourceLogin._list_datasource_logins(
                connection=connection, name=name, to_dictionary=True
            )
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no Datasource Login: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.username = kwargs.get("username")

    def alter(
        self,
        name: str = None,
        username: str = None,
        description: str = None,
        password: str = None
    ) -> None:
        """Alter the datasource login properties.

        Args:
            name: login object name
            username: username
            description: login object description
            password: database password to be used by the database login
        """
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        username: str,
        password: str,
        description: str = None
    ) -> "DatasourceLogin":
        """Create a new datasource login.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name: login object name
            username: username
            description: login object description
            password: database password to be used by the database login
        Returns:
            DatasourceConnection object.
        """
        body = {
            "name": name, "description": description, "username": username, "password": password
        }
        body = helper.delete_none_values(body, recursion=True)
        response = datasources.create_datasource_login(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created datasource login named: '{response.get('name')}' "
                f"with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    @classmethod
    def _list_datasource_logins(
        cls, connection: "Connection", to_dictionary: bool = False, limit: int = None, **filters
    ) -> Union[List["DatasourceLogin"], List[dict]]:
        objects = helper.fetch_objects(
            connection=connection,
            api=datasources.get_datasource_logins,
            dict_unpack_value="logins",
            limit=limit,
            filters=filters
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]
