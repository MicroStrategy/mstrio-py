from typing import TYPE_CHECKING

from mstrio.api import datasources
from mstrio.datasources.datasource_login import DatasourceLogin
from mstrio.datasources.helpers import CharEncoding, DriverType, ExecutionMode
from mstrio.utils.entity import EntityBase
from mstrio.utils.helper import get_args_from_func, get_default_args_from_func
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection


@class_version_handler('11.3.0000')
class EmbeddedConnection(EntityBase):
    """Datasource connection configuration object that represents an embedded
    connection template for the datasource.

    Attributes:
        connection: A Strategy One connection object.
        id: Unique datasource connection ID.
        name: Unique datasource connection name.
        datasource_id: ID of the corresponding datasource instance.
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
        oauth_parameter: Used for authentication with oAuth.
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

    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'execution_mode': ExecutionMode,
        'datasource_login': DatasourceLogin.from_dict,
        'driver_type': DriverType,
        'char_encoding_unix': CharEncoding,
        'char_encoding_windows': CharEncoding,
    }
    _API_GETTERS = {
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
            'acg',
            'iam',
            'resource',
            'scope',
            'enable_sso',
        ): datasources.get_embedded_connection,
    }
    _API_PATCH: dict = {
        (
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
            "oauth_parameter",
            'resource',
            'scope',
            'enable_sso',
        ): (
            datasources.update_embedded_connection,
            'patch',
        ),
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "execution_mode": str,
        "max_cancel_attempt_time": int,
        "max_query_exe_time": int,
        "max_connection_attempt_time": int,
        "connection_lifetime": int,
        "connection_idle_timeout": int,
        "char_encoding_windows": str,
        "char_encoding_unix": str,
        "table_prefix": str,
        "parameterized_queries": bool,
        "extended_fetch": bool,
        "driver_type": str,
        "oauth_parameter": str,
        "iam": dict,
        "resource": str,
        "scope": str,
        "enable_sso": bool,
    }

    def __init__(
        self,
        connection: "Connection",
        datasource_id: str,
    ) -> None:
        """Initialize EmbeddedConnection object and synchronize with server.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            datasource_id: ID of the corresponding Datasource Connection.
                The embedded connection object has an ID, but it cannot be used
                in a meaningful way in REST API. The corresponding datasource
                instance ID is used instead.
        """

        super().__init__(connection=connection, object_id=datasource_id)
        self.datasource_id = datasource_id

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
        self.execution_mode = (
            ExecutionMode(kwargs["execution_mode"])
            if kwargs.get("execution_mode")
            else None
        )
        self.datasource_id = kwargs.get("datasource_id")
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
            DatasourceLogin.from_dict(datasource_login, self.connection)
            if (datasource_login := kwargs.get("datasource_login"))
            else None
        )
        self.database_type = kwargs.get("database_type")
        self.database_version = kwargs.get("database_version")
        self._oauth_parameter = kwargs.get("oauth_parameter")
        self.iam = kwargs.get("iam")
        self.resource = kwargs.get("resource")
        self.scope = kwargs.get("scope")
        self.enable_sso = kwargs.get("enable_sso")

    def alter(
        self,
        description: str | None = None,
        execution_mode: str | ExecutionMode | None = None,
        max_cancel_attempt_time: int | None = None,
        max_query_exe_time: int | None = None,
        max_connection_attempt_time: int | None = None,
        connection_lifetime: int | None = None,
        connection_idle_timeout: int | None = None,
        char_encoding_windows: str | CharEncoding | None = None,
        char_encoding_unix: str | CharEncoding | None = None,
        table_prefix: str | None = None,
        connection_string: str | None = None,
        parameterized_queries: bool | None = None,
        extended_fetch: bool | None = None,
        driver_type: str | DriverType | None = None,
        oauth_parameter: str | None = None,
        resource: str | None = None,
        scope: str | None = None,
        enable_sso: bool | None = None,
        comments: str | None = None,
    ) -> None:
        """Alter the datasource connection properties.

        Args:
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
            resource: The url of configured Web API for OAuth authentication
                usage.
            scope: List of delegated permissions that the app is requesting.
            enable_sso: Specifies whether to use Single Sign-On.
        """
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
        local = locals()
        properties = {'datasource_id': self.datasource_id}
        for property_key in default_dict.keys():
            if local[property_key] is not None and property_key != 'datasource_id':
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @property
    def oauth_parameter(self):
        return self._oauth_parameter
