import logging
from typing import TYPE_CHECKING, Any

from mstrio import config
from mstrio.api import datasources
from mstrio.datasources.datasource_login import DatasourceLogin
from mstrio.datasources.embedded_connection import EmbeddedConnection
from mstrio.datasources.helpers import (
    CharEncoding,
    DriverType,
    ExecutionMode,
    OAuthGrantType,
)
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    get_args_from_func,
    get_default_args_from_func,
    get_objects_id,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0000')
def list_datasource_connections(
    connection: "Connection",
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list["DatasourceConnection"] | list[dict]:
    """Get list of DatasourceConnection objects or dicts. Optionally filter the
    connections by specifying filters.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'description',
            'acg', 'execution_mode', 'max_cancel_attempt_time',
            'max_query_exe_time', 'max_connection_attempt_time',
            'connection_lifetime', 'connection_idle_timeout',
            'char_encoding_windows', 'char_encoding_unix',
            'table_prefix', 'connection_string', 'parameterized_queries',
            'extended_fetch', 'driver_type', 'oauth_parameter', 'iam',
            'resource', 'scope', 'enable_sso', 'datasource_login',
            'database_type', 'database_version']

    Examples:
        >>> list_datasource_connections(connection, name='db_conn_name')
    """
    return DatasourceConnection._list_datasource_connections(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


@class_version_handler('11.3.0000')
class DatasourceConnection(Entity, CopyMixin, DeleteMixin):
    """Datasource connection configuration object that represents a connection
    to the datasource.

    Attributes:
        connection: A Strategy One connection object.
        id: Unique datasource connection ID.
        name: Unique datasource connection name.
        description: Datasource connection description.
        execution_mode: ExecutionMode Enum specifying how SQL statements will be
            executed on a physical database connection made.
        max_cancel_attempt_time: Number of seconds before being timed out when
            attempting to make a connection.
        max_query_exe_time: Number of seconds during which a query must be
            executed before being timed out.
        max_connection_attempt_time: Number of seconds connection attempts to be
            made before timing out.
        connection_lifetime: Number of seconds of the connection lifetime.
        connection_idle_timeout: Number of seconds before being timed out when
            the connection is idle.
        char_encoding_windows: CharEncoding Enum specifying the encoding
            across connection for Windows drivers.
        char_encoding_unix: CharEncoding Enum specifying the encoding across
            connection for Unix drivers.
        table_prefix: String prefixed to the names of all temporary tables
            created by the Query Engine for this connection during report
            execution with this string.
        connection_string: Database connection string.
        parameterized_queries: Specifies whether parameterized queries are
            enabled.
        extended_fetch: Specifies whether or not to use the extended fetch ODBC
            call to retrieve data from the database connection.
        datasource_login: `DatasourceLogin` object or ID
        database_type: Database type
        database_version: Database version
        driver_type: DriverType Enum specifying Driver used for database
            connection.
        oauth_parameter: Used for authentication with OAuth.
        oauth_grant_type: Specifies the grant type for OAuth.
        type: Object type
        subtype: Object subtype
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        owner: User object that is the owner
        acg: Object access rights. It a bit vector where bits are defined at
            [EnumDSSXMLAccessRightFlags].
        acl: Object access control list
        iam: List of projects to which the fence is applied.
        resource: The url of configured Web API for OAuth authentication usage.
        scope: List of delegated permissions that the app is requesting.
        enable_sso: Specifies whether to use Single Sign-On.
    """

    _OBJECT_TYPE = ObjectTypes.DBCONNECTION
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'execution_mode': ExecutionMode,
        'datasource_login': DatasourceLogin.from_dict,
        'driver_type': DriverType,
        'char_encoding_unix': CharEncoding,
        'char_encoding_windows': CharEncoding,
        'oauth_grant_type': OAuthGrantType,
    }
    _API_GETTERS = {
        (
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
            'acl',
            'comments',
        ): objects_processors.get_info,
        (
            'id',
            'name',
            'description',
            'execution_mode',
            'max_cancel_attempt_time',
            'max_query_exe_time',
            'max_connection_attempt_time',
            'connection_lifetime',
            'connection_idle_timeout',
            'char_encoding_windows',
            'char_encoding_unix',
            'table_prefix',
            'connection_string',
            'parameterized_queries',
            'extended_fetch',
            'driver_type',
            'datasource_login',
            'database_type',
            'database_version',
            'oauth_parameter',
            'oauth_grant_type',
            'acg',
            'iam',
            'resource',
            'scope',
            'enable_sso',
        ): datasources.get_datasource_connection,
    }
    _API_PATCH: dict = {
        (
            'abbreviation',
            'comments',
            'owner',
        ): (objects_processors.update, 'partial_put'),
        (
            "name",
            "description",
            "execution_mode",
            "max_cancel_attempt_time",
            "max_query_exe_time",
            "max_connection_attempt_time",
            "connection_lifetime",
            "connection_idle_timeout",
            "char_encoding_windows",
            "char_encoding_unix",
            "table_prefix",
            "connection_string",
            "parameterized_queries",
            "extended_fetch",
            "driver_type",
            "database_type",
            "database_version",
            "datasource_login",
            'iam',
            'resource',
            'scope',
            'enable_sso',
        ): (
            datasources.update_datasource_connection,
            'patch',
        ),
    }
    _PATCH_PATH_TYPES = {
        **Entity._PATCH_PATH_TYPES,
        "execution_mode": str,
        "max_cancel_attempt_time": int,
        "max_query_exe_time": int,
        "max_connection_attempt_time": int,
        "connection_lifetime": int,
        "connection_idle_timeout": int,
        "char_encoding_windows": str,
        "char_encoding_unix": str,
        "table_prefix": str,
        "connection_string": str,
        "parameterized_queries": bool,
        "extended_fetch": bool,
        "driver_type": str,
        "database_type": str,
        "database_version": str,
        "datasource_login": dict,
        "iam": dict,
        "resource": str,
        "scope": str,
        "enable_sso": bool,
    }

    def __init__(
        self,
        connection: "Connection",
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """Initialize DatasourceConnection object and synchronize with server.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            name: exact name of Datasource Connection
            id: ID of Datasource Connection
        """

        if id is None and name is None:
            raise ValueError(
                "Please specify either 'id' or 'name' parameter in the constructor."
            )

        if id is None:
            objects_info = DatasourceConnection._list_datasource_connections(
                connection=connection, name=name, to_dictionary=True
            )
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no Datasource Connection: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.execution_mode = (
            ExecutionMode(kwargs["execution_mode"])
            if kwargs.get("execution_mode")
            else None
        )
        self.max_cancel_attempt_time = kwargs.get("max_cancel_attempt_time")
        self.max_query_exe_time = kwargs.get("max_query_exe_time")
        self.max_connection_attempt_time = kwargs.get("max_connection_attempt_time")
        self.connection_lifetime = kwargs.get("connection_lifetime")
        self.connection_idle_timeout = kwargs.get("connection_idle_timeout")
        self.char_encoding_windows = (
            CharEncoding(kwargs["char_encoding_windows"])
            if kwargs.get("char_encoding_windows")
            else None
        )
        self.char_encoding_unix = (
            CharEncoding(kwargs["char_encoding_unix"])
            if kwargs.get("char_encoding_unix")
            else None
        )
        self.table_prefix = kwargs.get("table_prefix")
        self.connection_string = kwargs.get("connection_string")
        self.parameterized_queries = kwargs.get("parameterized_queries")
        self.extended_fetch = kwargs.get("extended_fetch")
        self.driver_type = (
            DriverType(kwargs["driver_type"]) if kwargs.get("driver_type") else None
        )
        self.datasource_login = (
            DatasourceLogin.from_dict(kwargs.get("datasource_login"), self.connection)
            if kwargs.get("datasource_login")
            else None
        )
        self.database_type = kwargs.get("database_type")
        self.database_version = kwargs.get("database_version")
        self._oauth_parameter = kwargs.get("oauth_parameter")
        self._oauth_grant_type = (
            OAuthGrantType(kwargs["_oauth_grant_type"])
            if kwargs.get("_oauth_grant_type")
            else None
        )
        self.iam = kwargs.get("iam")
        self.resource = kwargs.get("resource")
        self.scope = kwargs.get("scope")
        self.enable_sso = kwargs.get("enable_sso")

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        execution_mode: str | ExecutionMode = None,
        max_cancel_attempt_time: int | None = None,
        max_query_exe_time: int | None = None,
        max_connection_attempt_time: int | None = None,
        connection_lifetime: int | None = None,
        connection_idle_timeout: int | None = None,
        char_encoding_windows: str | CharEncoding = None,
        char_encoding_unix: str | CharEncoding = None,
        table_prefix: str | None = None,
        connection_string: str | None = None,
        parameterized_queries: bool | None = None,
        extended_fetch: bool | None = None,
        driver_type: str | DriverType = None,
        database_type: str | None = None,
        database_version: str | None = None,
        datasource_login: str | DatasourceLogin | None = None,
        iam: dict | None = None,
        resource: str | None = None,
        scope: str | None = None,
        enable_sso: bool | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the datasource connection properties.

        Args:
            name: Unique datasource connection name.
            description: Datasource connection description.
            execution_mode: ExecutionMode Enum specifying how SQL statements
                will be executed on a physical database connection made.
            max_cancel_attempt_time: Number of seconds before being timed out
                when attempting to make a connection.
            max_query_exe_time: Number of seconds during which a query must be
                executed before being timed out.
            max_connection_attempt_time: Number of seconds connection attempts
                to be made before timing out.
            connection_lifetime: Number of seconds of the connection lifetime.
            connection_idle_timeout: Number of seconds before being timed out
                when the connection is idle.
            char_encoding_windows: CharEncoding Enum specifying the encoding
                across connection for Windows drivers.
            char_encoding_unix: CharEncoding Enum specifying the encoding across
                connection for Unix drivers.
            table_prefix: String prefixed to the names of all temporary tables
                created by the Query Engine for this connection during report
                execution with this string.
            connection_string: Database connection string.
            parameterized_queries: Specifies whether parameterized queries are
                enabled.
            extended_fetch: Specifies whether or not to use the extended fetch
                ODBC call to retrieve data from the database connection.
            driver_type: DriverType Enum specifying Driver used for database
                connection.
            datasource_login: `DatasourceLogin` object or ID
            driver_type: ENUM Drivers used for database connection.
            database_type: Database type
            database_version: Database version
            iam: List of projects to which the fence is applied.
            resource: The url of configured Web API for OAuth authentication
                usage.
            scope: List of delegated permissions that the app is requesting.
            enable_sso: Specifies whether to use Single Sign-On.
            comments: Long description of the object
            owner: New owner of the object
        """
        datasource_login = (
            {'id': get_objects_id(datasource_login, DatasourceLogin)}
            if datasource_login
            else None
        )
        if isinstance(owner, User):
            owner = owner.id
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
    def create(
        cls,
        connection: "Connection",
        name: str,
        description: str | None = None,
        acg: int | None = None,
        execution_mode: str | ExecutionMode = None,
        max_cancel_attempt_time: int | None = None,
        max_query_exe_time: int | None = None,
        max_connection_attempt_time: int | None = None,
        connection_lifetime: int | None = None,
        connection_idle_timeout: int | None = None,
        char_encoding_windows: str | CharEncoding = None,
        char_encoding_unix: str | CharEncoding = None,
        table_prefix: str | None = None,
        connection_string: str | None = None,
        parameterized_queries: bool = False,
        extended_fetch: bool = False,
        datasource_login: DatasourceLogin | str | None = None,
        database_type: str | None = None,
        database_version: str | None = None,
        driver_type: str | DriverType = None,
        oauth_parameter: str | None = None,
        iam: dict | None = None,
        resource: str | None = None,
        scope: str | None = None,
        enable_sso: bool = False,
    ) -> "DatasourceConnection":
        """Create a new datasource connection on the I-Server.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            name: Unique datasource connection name.
            description: Datasource connection description.
            acg: Object access rights. It's a bit vector where bits are defined
                at [EnumDSSXMLAccessRightFlags].
            execution_mode: ExecutionMode Enum specifying how SQL statements
                will be executed on a physical database connection made.
            max_cancel_attempt_time: Number of seconds before being timed out
                when attempting to make a connection.
            max_query_exe_time: Number of seconds during which a query must be
                executed before being timed out.
            max_connection_attempt_time: Number of seconds connection attempts
                to be made before timing out.
            connection_lifetime: Number of seconds of the connection lifetime.
            connection_idle_timeout: Number of seconds before being timed out
                when the connection is idle.
            char_encoding_windows: CharEncoding Enum specifying the encoding
                across connection for Windows drivers.
            char_encoding_unix: CharEncoding Enum specifying the encoding across
                connection for Unix drivers.
            table_prefix: String prefixed to the names of all temporary tables
                created by the Query Engine for this connection during report
                execution with this string.
            connection_string: Database connection string.
            parameterized_queries: Specifies whether parameterized queries are
                enabled.
            extended_fetch: Specifies whether or not to use the extended fetch
                ODBC call to retrieve data from the database connection.
            driver_type: DriverType Enum specifying Driver used for database
                connection.
            oauth_parameter: Used for authentication with oAuth.
            datasource_login: `DatasourceLogin` object or ID
            database_type: Database type
            database_version: Database version
            iam: List of projects to which the fence is applied.
            resource: The url of configured Web API for OAuth authentication
                usage.
            scope: List of delegated permissions that the app is requesting.
            enable_sso: Specifies whether to use Single Sign-On.

        Returns:
            DatasourceConnection object.
        """
        login_id = get_objects_id(datasource_login, DatasourceLogin)

        body = {
            "name": name,
            "description": description,
            "acg": acg,
            "executionMode": get_enum_val(execution_mode, ExecutionMode),
            "maxCancelAttemptTime": max_cancel_attempt_time,
            "maxQueryExeTime": max_query_exe_time,
            "maxConnectionAttemptTime": max_connection_attempt_time,
            "connectionLifetime": connection_lifetime,
            "connectionIdleTimeout": connection_idle_timeout,
            "charEncodingWindows": get_enum_val(char_encoding_windows, CharEncoding),
            "charEncodingUnix": get_enum_val(char_encoding_unix, CharEncoding),
            "tablePrefix": table_prefix,
            "connectionString": connection_string,
            "parameterizedQueries": parameterized_queries,
            "extendedFetch": extended_fetch,
            "database": {
                "login": {"id": login_id},
                "type": database_type,
                "version": database_version,
            },
            "driverType": get_enum_val(driver_type, DriverType),
            "oauthParameter": oauth_parameter,
            "iam": iam,
            "resource": resource,
            "scope": scope,
            "enable_sso": enable_sso,
        }
        body = helper.delete_none_values(body, recursion=True)
        response = datasources.create_datasource_connection(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created datasource connection named: '"
                f"{response.get('name')}' "
                f"with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    @classmethod
    def from_dict(
        cls,
        source: dict[str, Any],
        connection: 'Connection',
        to_snake_case: bool = True,
    ) -> 'DatasourceConnection | EmbeddedConnection':
        """Create a DatasourceConnection object from a dictionary.

        Args:
            source: Dictionary with DatasourceConnection properties
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            to_snake_case: If True, keys in the source dictionary are converted
                to snake_case.

        Returns:
            DatasourceConnection object.
        """
        if source.get("is_embedded"):
            return EmbeddedConnection.from_dict(source, connection, to_snake_case)
        return super().from_dict(source, connection, to_snake_case)

    @method_version_handler('11.3.0100')
    def test_connection(self) -> bool:
        """Test datasource connection object.

        Returns:
            True if connection can be established, else False.
        """
        body = {"id": self.id}
        return datasources.test_datasource_connection(self.connection, body).ok

    @method_version_handler('11.3.0900')
    def convert_to_dsn_less(self):
        """Convert datasource connection from DSN to DSN-less format and update
        the object to metadata.
        """
        response = datasources.convert_connection_dsn(
            connection=self.connection, ds_connection_id=self.id
        )
        if response.ok:
            response = response.json()
            self._set_object_attributes(**response)

    @classmethod
    def _list_datasource_connections(
        cls,
        connection: "Connection",
        to_dictionary: bool = False,
        limit: int | None = None,
        **filters,
    ) -> list["DatasourceConnection"] | list[dict]:
        objects = helper.fetch_objects(
            connection=connection,
            api=datasources.get_datasource_connections,
            dict_unpack_value="connections",
            limit=limit,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @property
    def oauth_parameter(self):
        return self._oauth_parameter

    @property
    def oauth_grant_type(self):
        return self._oauth_grant_type
