from enum import auto
import logging
from typing import List, Optional, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api import datasources, objects
from mstrio.datasources import DatasourceConnection, Dbms
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import get_objects_id

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


def list_datasource_instances(connection: "Connection", to_dictionary: bool = False,
                              limit: Optional[int] = None, ids: Optional[List[str]] = None,
                              database_types: Optional[List[str]] = None,
                              project: Optional[Union["Project", str]] = None,
                              **filters) -> Union[List["DatasourceInstance"], List[dict]]:
    """Get list of DatasourceInstance objects or dicts. Optionally filter the
    datasource instances by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
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
            'date_created', 'date_modified', 'datasource_type', table_prefix,
            'odbc_version', 'intermediate_store_db_name',
            'intermediate_store_table_space_name', 'dbms', 'owner', 'acg']

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


class DatasourceType(AutoName):
    RESERVED = auto()
    NORMAL = auto()
    DATA_IMPORT = auto()
    DATA_IMPORT_PRIMARY = auto()


class DatasourceInstance(Entity, CopyMixin, DeleteMixin):
    """Object representation of MicroStrategy DataSource Instance object.

    Attributes:
        connection: A MicroStrategy connection object
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

    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.DBROLE
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP, 'dbms': Dbms.from_dict,
        'owner': User.from_dict,
        'datasource_type': DatasourceType,
        'datasource_connection': DatasourceConnection.from_dict
    }
    _API_GETTERS = {
        ('abbreviation', 'type', 'subtype', 'ext_type', 'version', 'owner', 'icon_path',
         'view_media', 'ancestors', 'certified_info', 'acl'): objects.get_object_info,
        ('id', 'name', 'description', 'date_created', 'date_modified', 'datasource_type',
         'table_prefix', 'odbc_version', 'intermediate_store_db_name', 'datasource_connection',
         'database_type', 'database_version', 'primary_datasource', 'data_mart_datasource',
         'intermediate_store_table_space_name', 'dbms', 'acg'): datasources.get_datasource_instance
    }
    _API_PATCH: dict = {
        ('abbreviation'): (objects.update_object, 'partial_put'),
        ("name", "description", "datasource_type", "table_prefix", "intermediate_store_db_name",
         "intermediate_store_table_space_name", "odbc_version", "datasource_connection",
         "primary_datasource", "data_mart_datasource", "dbms"): (
            datasources.update_datasource_instance,
            'patch',
        )
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "datasource_type": str,
        "table_prefix": int,
        "intermediate_store_db_name": str,
        "intermediate_store_table_space_name": str,
        "odbc_version": str,
        "datasource_connection": dict,
        "primary_datasource": dict,
        "data_mart_datasource": dict,
        "dbms": dict,
    }

    def __init__(self, connection: "Connection", name: Optional[str] = None,
                 id: Optional[str] = None) -> None:
        """Initialize DatasourceInstance object by passing name or id.

        To explore all available DatasourceInstance objects use the
        `list_datasource_instance()` method.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name: exact name of Datasource Instance
            id: ID of Datasource Instance
        """
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            objects_info = DatasourceInstance._list_datasource_instances(
                connection=connection, name=name, to_dictionary=True)
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                helper.exception_handler(f"There is no Datasource Instance: '{name}'",
                                         exception_type=ValueError)
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.datasource_type = DatasourceType(
            kwargs["datasource_type"]) if kwargs.get("datasource_type") else None
        self.table_prefix = kwargs.get("table_prefix")
        self.intermediate_store_db_name = kwargs.get("intermediate_store_db_name")
        self.intermediate_store_table_space_name = kwargs.get(
            "intermediate_store_table_space_name")
        self.odbc_version = kwargs.get("odbc_version")
        self.datasource_connection = DatasourceConnection.from_dict(
            kwargs.get("datasource_connection"),
            self.connection) if kwargs.get("datasource_connection") else None
        self.database_type = kwargs.get("database_type")
        self.database_version = kwargs.get("database_version")
        self.primary_datasource = DatasourceInstance.from_dict(
            kwargs.get("primary_datasource"),
            self.connection) if kwargs.get("primary_datasource") else None
        self.data_mart_datasource = DatasourceInstance.from_dict(
            kwargs.get("data_mart_datasource"),
            self.connection) if kwargs.get("data_mart_datasource") else None
        self.dbms = Dbms.from_dict(kwargs.get("dbms"), self.connection)\
            if kwargs.get("dbms") else None

    @classmethod
    def create(
        cls, connection: "Connection", name: str, dbms: Union[Dbms, str],
        description: Optional[str] = None, datasource_type: Optional[Union[str,
                                                                           DatasourceType]] = None,
        table_prefix: Optional[str] = None, odbc_version: Optional[str] = None,
        intermediate_store_db_name: Optional[str] = None,
        intermediate_store_table_space_name: Optional[str] = None,
        datasource_connection: Union[str, DatasourceConnection,
                                     None] = None, database_type: str = None,
        database_version: str = None, primary_datasource: Union[str, "DatasourceInstance",
                                                                None] = None,
        data_mart_datasource: Union[str, "DatasourceInstance", None] = None
    ) -> Optional["DatasourceInstance"]:
        """Create a new DatasourceInstance object on I-Server.

        Args:
            connection: MicroStrategy connection object returned by
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
            "connection": {
                "id": connection_id
            }
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
            "dbms": {
                "id": dbms_id
            }
        }
        body = helper.delete_none_values(body, recursion=True)
        response = datasources.create_datasource_instance(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created datasource instance named: '{response.get('name')}' "
                f"with ID: '{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(self, name: Optional[str] = None, description: Optional[str] = None,
              datasource_type: Optional[Union[str, DatasourceType]] = None,
              table_prefix: Optional[str] = None, odbc_version: Optional[str] = None,
              intermediate_store_db_name: Optional[str] = None,
              intermediate_store_table_space_name: Optional[str] = None, dbms: Union[str, Dbms,
                                                                                     None] = None,
              datasource_connection: Union[str, DatasourceConnection, None] = None,
              primary_datasource: Union[str, "DatasourceInstance", None] = None,
              data_mart_datasource: Union[str, "DatasourceInstance", None] = None) -> None:
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

        """
        dbms = {'id': get_objects_id(dbms, Dbms)} if dbms else None
        datasource_connection = {
            'id': get_objects_id(datasource_connection, DatasourceConnection)
        } if datasource_connection else None
        primary_datasource = {
            'id': get_objects_id(primary_datasource, self)
        } if primary_datasource else None
        data_mart_datasource = {
            'id': get_objects_id(data_mart_datasource, self)
        } if data_mart_datasource else None
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_datasource_instances(cls, connection: "Connection",
                                   to_dictionary: Optional[bool] = False,
                                   limit: Optional[int] = None, ids: Optional[list] = None,
                                   database_types: Optional[list] = None,
                                   project: Optional[Union["Project", str]] = None,
                                   **filters) -> Union[List["DatasourceInstance"], List[dict]]:
        objects = helper.fetch_objects(connection=connection,
                                       api=datasources.get_datasource_instances,
                                       dict_unpack_value="datasources", limit=limit,
                                       filters=filters, ids=ids, database_types=database_types,
                                       project=project)
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    def _set_object_attributes(self, **kwargs) -> None:
        super()._set_object_attributes(**kwargs)
        if kwargs.get("primary_datasource"):
            setattr(
                self, 'primary_datasource',
                DatasourceInstance(id=kwargs.get("primary_datasource").get("id"),
                                   name=kwargs.get("primary_datasource").get("name"),
                                   connection=self.connection))
        if kwargs.get("data_mart_datasource"):
            setattr(
                self, 'data_mart_datasource',
                DatasourceInstance(id=kwargs.get("data_mart_datasource").get("id"),
                                   name=kwargs.get("data_mart_datasource").get("name"),
                                   connection=self.connection))
