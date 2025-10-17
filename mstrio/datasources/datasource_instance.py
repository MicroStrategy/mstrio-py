import logging
import time
from enum import auto
from typing import TYPE_CHECKING, Optional

from pypika import Query

from mstrio import config
from mstrio.api import datasources
from mstrio.datasources import DatasourceConnection, Dbms, list_datasource_connections
from mstrio.server.project import Project
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    encode_as_b64,
    get_args_from_func,
    get_default_args_from_func,
    get_objects_id,
)
from mstrio.utils.resolvers import validate_owner_key_in_filters
from mstrio.utils.response_processors import datasources as datasources_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler
from mstrio.utils.vldb_mixin import ModelVldbMixin

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0000')
def list_datasource_instances(
    connection: "Connection",
    to_dictionary: bool = False,
    limit: int | None = None,
    ids: list[str] | None = None,
    database_types: list[str] | None = None,
    project: Optional['Project | str'] = None,
    **filters,
) -> list["DatasourceInstance"] | list[dict]:
    """Get list of DatasourceInstance objects or dicts. Optionally filter the
    datasource instances by specifying filters.

    Args:
        connection: Strategy One connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        ids: list of datasources ids as strings. By default `None`.
        database_types: list of strings representing database types.
            By default `None`. Available values: ['reserved', 'access',
            'altibase', 'amazon_athena', 'amazon_aurora', 'amazon_redshift',
            'arcadia_platform', 'aster', 'big_data_engine', 'cassandra',
            'cirro', 'cloud_element', 'cloud_gateway', 'cloud_gateway_aws_s3',
            'cloud_gateway_azure_adls_2', 'cloud_gateway_google_cloud_storage',
            'composite', 'concur', 'connection_cloud', 'data_direct_cloud',
            'datallegro', 'db2', 'denodo', 'drill', 'dropbox', 'eloqua',
            'enterprise_db', 'ess_base', 'exa_solution', 'excel', 'facebook',
            'gbase_8a', 'generic', 'generic_data_connector', 'google_analytics',
            'google_big_query', 'google_big_query_ff_sql', 'google_drive',
            'hive', 'hive_thrift', 'hubspot', 'impala', 'informatica',
            'informix', 'kognitiowx2', 'kyvos_mdx', 'mapd', 'marketo',
            'mark_logic', 'mem_sql', 'metamatrix', 'microsoft_as', 'mongo_db',
            'my_sql', 'neoview', 'netezza', 'open_access', 'oracle',
            'par_accel', 'par_stream', 'paypal', 'phoenix', 'pig',
            'pivotal_hawq', 'postgre_sql', 'presto', 'red_brick', 'salesforce',
            'sand', 'sap', 'sap_hana', 'sap_hana_mdx', 'search_engine',
            'servicenow', 'shopify', 'snow_flake', 'spark_config', 'spark_sql',
            'splunk', 'sql_server', 'square', 'sybase', 'sybase_iq',
            'sybase_sql_any', 'tandem', 'teradata', 'tm1', 'twitter', 'unknown',
            'url_auth', 'vectorwise', 'vertica', 'xquery']
        project: id (str) of a project or instance of an Project class
            to search for the datasource instances in. When provided, both
            `ids` and `database_types` are ignored. By default `None`.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg', 'datasource_type',
            'table_prefix', 'odbc_version', 'intermediate_store_db_name',
            'intermediate_store_table_space_name', 'dbms', 'owner', 'hidden',
            'datasource_connection', 'database_type', 'database_version',
            'primary_datasource', 'data_mart_datasource']

    Examples:
        >>> list_datasource_instances(connection, name='ds_instance_name')
    """
    return DatasourceInstance._list_datasource_instances(
        connection=connection,
        ids=ids,
        database_types=database_types,
        to_dictionary=to_dictionary,
        limit=limit,
        project=project,
        **filters,
    )


def list_connected_datasource_instances(
    connection: "Connection", to_dictionary: bool = False
) -> list["DatasourceInstance"] | list[dict]:
    """List all datasource instances for which there is an associated
    Database Login and are connected to a project mapped to a Connection object.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        to_dictionary (bool, optional): If True returns a list of dictionaries
            representing datasource instances

    Returns:
        list["DatasourceInstance"] | list[dict]: A list of connected
            datasource instances.
    """
    all_datasource_instances = list_datasource_instances(connection, to_dictionary=True)
    datasource_connections_ids = [
        ds_connection.get('id')
        for ds_connection in list_datasource_connections(connection, to_dictionary=True)
    ]
    connected_datasource_instances = [
        ds_instance
        for ds_instance in all_datasource_instances
        if ds_instance.get('datasource_connection').get('id')
        in datasource_connections_ids
        # remove xquery datasources because they are not available
        # in Workstation and listing namespaces for them can cause
        # old IServer to become unresponsive.
        and ds_instance.get('database_type') != 'xquery'
    ]

    if to_dictionary:
        return connected_datasource_instances
    return [
        DatasourceInstance.from_dict(source=ds_instance, connection=connection)
        for ds_instance in connected_datasource_instances
    ]


class DatasourceType(AutoName):
    RESERVED = auto()
    NORMAL = auto()
    DATA_IMPORT = auto()
    DATA_IMPORT_PRIMARY = auto()


@class_version_handler('11.3.0000')
class DatasourceInstance(Entity, CopyMixin, DeleteMixin, ModelVldbMixin):
    """Object representation of Strategy One DataSource Instance object.

    Attributes:
        connection: A Strategy One connection object
        id: Datasource Instance ID
        name: Datasource Instance name
        description: Datasource Instance description
        dbms: The database management system (DBMS) object
        database: `Database` object
        datasource_type: DatasourceType Enum (reserved, normal, data_import,
            data_import_primary)
        table_prefix: Table prefix
        odbc_version: Odbc version ENUM
        intermediate_store_db_name: Intermediate store DBName
        intermediate_store_table_space_name: intermediate store table space
            name
        type: Object type
        subtype: Object subtype
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        owner: User object that is the owner
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.DBROLE
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'dbms': Dbms.from_dict,
        'owner': User.from_dict,
        'datasource_type': DatasourceType,
        'datasource_connection': DatasourceConnection.from_dict,
    }
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
            'acl',
        ): objects_processors.get_info,
        (
            'id',
            'name',
            'description',
            'date_created',
            'date_modified',
            'datasource_type',
            'table_prefix',
            'odbc_version',
            'intermediate_store_db_name',
            'datasource_connection',
            'database_type',
            'database_version',
            'primary_datasource',
            'data_mart_datasource',
            'intermediate_store_table_space_name',
            'dbms',
            'acg',
        ): datasources.get_datasource_instance,
    }
    _API_PATCH: dict = {
        (
            'abbreviation',
            'owner',
        ): (objects_processors.update, 'partial_put'),
        (
            "name",
            "description",
            "datasource_type",
            "table_prefix",
            "intermediate_store_db_name",
            "intermediate_store_table_space_name",
            "odbc_version",
            "datasource_connection",
            "primary_datasource",
            "data_mart_datasource",
            "dbms",
        ): (
            datasources.update_datasource_instance,
            'patch',
        ),
    }
    _PATCH_PATH_TYPES = {
        **Entity._PATCH_PATH_TYPES,
        "datasource_type": str,
        "table_prefix": str,
        "intermediate_store_db_name": str,
        "intermediate_store_table_space_name": str,
        "odbc_version": str,
        "datasource_connection": dict,
        "primary_datasource": dict,
        "data_mart_datasource": dict,
        "dbms": dict,
    }
    _MODEL_VLDB_API = {
        'GET_ADVANCED': datasources.get_vldb_settings,
        'PUT_ADVANCED': datasources.update_vldb_settings,
        'GET_APPLICABLE': datasources.get_applicable_vldb_settings,
    }

    def __init__(
        self,
        connection: "Connection",
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """Initialize DatasourceInstance object by passing name or id.

        To explore all available DatasourceInstance objects use the
        `list_datasource_instance()` method.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            name: exact name of Datasource Instance
            id: ID of Datasource Instance
        """
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'id' or 'name' parameter in the constructor."
            )

        if id is None:
            objects_info = DatasourceInstance._list_datasource_instances(
                connection=connection, name=name, to_dictionary=True
            )
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                helper.exception_handler(
                    f"There is no Datasource Instance: '{name}'",
                    exception_type=ValueError,
                )
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.datasource_type = (
            DatasourceType(kwargs["datasource_type"])
            if kwargs.get("datasource_type")
            else None
        )
        self.table_prefix = kwargs.get("table_prefix")
        self.intermediate_store_db_name = kwargs.get("intermediate_store_db_name")
        self.intermediate_store_table_space_name = kwargs.get(
            "intermediate_store_table_space_name"
        )
        self.odbc_version = kwargs.get("odbc_version")
        self.datasource_connection = (
            DatasourceConnection.from_dict(
                kwargs.get("datasource_connection"), self.connection
            )
            if kwargs.get("datasource_connection")
            else None
        )
        self.database_type = kwargs.get("database_type")
        self.database_version = kwargs.get("database_version")
        self.primary_datasource = (
            DatasourceInstance.from_dict(
                kwargs.get("primary_datasource"), self.connection
            )
            if kwargs.get("primary_datasource")
            else None
        )
        self.data_mart_datasource = (
            DatasourceInstance.from_dict(
                kwargs.get("data_mart_datasource"), self.connection
            )
            if kwargs.get("data_mart_datasource")
            else None
        )
        self.dbms = (
            Dbms.from_dict(kwargs.get("dbms"), self.connection)
            if kwargs.get("dbms")
            else None
        )

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        dbms: Dbms | str,
        description: str | None = None,
        datasource_type: str | DatasourceType | None = None,
        table_prefix: str | None = None,
        odbc_version: str | None = None,
        intermediate_store_db_name: str | None = None,
        intermediate_store_table_space_name: str | None = None,
        datasource_connection: str | DatasourceConnection | None = None,
        database_type: str = None,
        database_version: str = None,
        primary_datasource: Optional["str | DatasourceInstance"] = None,
        data_mart_datasource: Optional["str | DatasourceInstance"] = None,
    ) -> Optional["DatasourceInstance"]:
        """Create a new DatasourceInstance object on I-Server.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            name: Datasource name
            dbms: The database management system (DBMS) object or id
            description: Datasource description
            datasource_type: DatasourceType Enum (reserved, normal, data_import,
                data_import_primary)
            table_prefix: Table prefix
            odbc_version: Odbc version ENUM (version3x, version2x)
            intermediate_store_db_name: Intermediate store DBName
            intermediate_store_table_space_name: intermediate store table space
                name
            datasource_connection: `DatasourceConnection` object or ID
            database_type: Database type
            database_version: Database version
            primary_datasource: `DatasourceInstance` object or ID
            data_mart_datasource: `DatasourceInstance` object or ID

        Returns:
            DatasourceInstance object.
        """
        dbms_id = get_objects_id(dbms, Dbms)
        connection_id = get_objects_id(datasource_connection, DatasourceConnection)
        primary_datasource_id = get_objects_id(primary_datasource, cls)
        data_mart_datasource_id = get_objects_id(data_mart_datasource, cls)
        database = {
            "type": database_type,
            "version": database_version,
            "connection": {"id": connection_id},
        }
        if primary_datasource_id:
            database["primaryDatasource"] = {"id": primary_datasource_id}
        if data_mart_datasource_id:
            database["dataMartDatasource"] = {"id": data_mart_datasource_id}

        body = {
            "name": name,
            "database": database,
            "description": description,
            "datasourceType": get_enum_val(datasource_type, DatasourceType),
            "tablePrefix": table_prefix,
            "odbcVersion": odbc_version,
            "intermediateStoreDbName": intermediate_store_db_name,
            "intermediateStoreTableSpaceName": intermediate_store_table_space_name,
            "dbms": {"id": dbms_id},
        }
        body = helper.delete_none_values(body, recursion=True)
        response = datasources.create_datasource_instance(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created datasource instance named: "
                f"'{response.get('name')}' with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        datasource_type: str | DatasourceType | None = None,
        table_prefix: str | None = None,
        odbc_version: str | None = None,
        intermediate_store_db_name: str | None = None,
        intermediate_store_table_space_name: str | None = None,
        dbms: str | Dbms | None = None,
        datasource_connection: str | DatasourceConnection | None = None,
        primary_datasource: Optional["str | DatasourceInstance"] = None,
        data_mart_datasource: Optional["str | DatasourceInstance"] = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter DatasourceInstance properties.

        Args:
            name: Datasource name
            description: Datasource description
            datasource_type: DatasourceType Enum (reserved, normal, data_import,
                data_import_primary)
            table_prefix: Table prefix
            odbc_version: Odbc version ENUM (version3x, version2x)
            intermediate_store_db_name: Intermediate store DBName
            intermediate_store_table_space_name: intermediate store table space
                name
            dbms: The database management system (DBMS) object or ID
            datasource_connection: `DatasourceConnection` object or ID
            primary_datasource: `DatasourceInstance` object or ID
            data_mart_datasource: `DatasourceInstance` object or ID
            owner: `User` object or ID

        """
        dbms = {'id': get_objects_id(dbms, Dbms)} if dbms else None
        datasource_connection = (
            {'id': get_objects_id(datasource_connection, DatasourceConnection)}
            if datasource_connection
            else None
        )
        primary_datasource = (
            {'id': get_objects_id(primary_datasource, self)}
            if primary_datasource
            else None
        )
        data_mart_datasource = (
            {'id': get_objects_id(data_mart_datasource, self)}
            if data_mart_datasource
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
    def _list_datasource_instances(
        cls,
        connection: "Connection",
        to_dictionary: bool | None = False,
        limit: int | None = None,
        ids: list | None = None,
        database_types: list | None = None,
        project: Project | str | None = None,
        **filters,
    ) -> list["DatasourceInstance"] | list[dict]:
        validate_owner_key_in_filters(filters)

        project_id = project.id if isinstance(project, Project) else project
        objects = helper.fetch_objects(
            connection=connection,
            api=datasources.get_datasource_instances,
            dict_unpack_value="datasources",
            limit=limit,
            filters=filters,
            ids=ids,
            database_types=database_types,
            project=project_id,
        )

        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    def _set_object_attributes(self, **kwargs) -> None:
        super()._set_object_attributes(**kwargs)
        if kwargs.get("primary_datasource"):
            self.primary_datasource = DatasourceInstance(
                id=kwargs.get("primary_datasource").get("id"),
                name=kwargs.get("primary_datasource").get("name"),
                connection=self.connection,
            )
        if kwargs.get("data_mart_datasource"):
            self.data_mart_datasource = DatasourceInstance(
                id=kwargs.get("data_mart_datasource").get("id"),
                name=kwargs.get("data_mart_datasource").get("name"),
                connection=self.connection,
            )

    @method_version_handler('11.3.0900')
    def convert_ds_connection_to_dsn_less(self):
        """Convert datasource embedded connection from DSN to DSN-less format
        connection string and update the object to metadata.
        """
        response = datasources.convert_ds_dsn(
            connection=self.connection, datasource_id=self.id
        )
        if response.ok:
            self.fetch()

    @method_version_handler('11.3.1060')
    def execute_query(
        self,
        project_id: str | Project,
        query: str,
        max_retries: int = 10,
        retry_delay: int = 5,
    ) -> dict:
        """Execute an SQL query on the given datasource.

        Args:
            project_id (str | Project): project ID or Project class instance
            query (str): query to be executed
            max_retries (int, optional): maximum number of retries in case
                the query execution fails. Default is 10.
            retry_delay (int, optional): time to wait
                between retries in seconds. Default is 5.

        Returns:
            Dictionary containing execution results data for the query.
        """
        project_id = project_id.id if isinstance(project_id, Project) else project_id
        return DatasourceInstance._execute_query(
            connection=self.connection,
            query=query,
            datasource_id=self.id,
            project_id=project_id,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    @staticmethod
    def _execute_query(
        connection: 'Connection',
        query: str | Query,
        datasource_id: str,
        project_id: str,
        max_retries: int = 10,
        retry_delay: int = 5,
    ) -> dict:
        """Execute an SQL query on the given datasource.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`
            query (str): query to be executed
            datasource_id (str): ID of the DatasourceInstance to execute the
                query on
            project_id (str): ID of the project
            max_retries (int): maximum number of retries
                in case the query execution fails. Default is 10.
            retry_delay (int): time to wait between retries in seconds.
                Default is 5.

        Returns:
            Dictionary containing execution results data for the query.
        """
        execution_id = datasources_processors.execute_query(
            connection=connection,
            body={'query': encode_as_b64(query)},
            id=datasource_id,
            project_id=project_id,
        ).get('id')
        for _ in range(max_retries):
            execution = datasources_processors.get_query_results(
                connection=connection, id=execution_id
            )
            if execution.get('status') == 3:
                return execution
            elif execution.get('status') == 4:
                if 'Error type: Odbc success with info.' in execution.get('message'):
                    return execution
                else:
                    raise ValueError(
                        f"Query execution failed with the following error: "
                        f"{execution.get('message')}"
                    )
            if config.verbose:
                logger.info(
                    f"The query is still running. Retrying in {retry_delay} seconds."
                )
            time.sleep(retry_delay)
        logger.error("The query did not finish within the maximum number of retries.")
