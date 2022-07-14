from functools import cached_property
import logging
from typing import Optional, Type

from mstrio.api import datasources
from mstrio.api import tables as tables_api
from mstrio.connection import Connection
from mstrio.datasources.datasource_instance import DatasourceInstance
from mstrio.modeling.schema import ObjectSubType, SchemaObjectReference
from mstrio.modeling.schema.helpers import TableColumn, TableColumnMergeOption
from mstrio.modeling.schema.table.logical_table import list_logical_tables, LogicalTable
from mstrio.utils.helper import Dictable, fetch_objects
from mstrio.utils.version_helper import method_version_handler

logging.getLogger().setLevel(logging.INFO)


@method_version_handler('11.3.0100')
def list_datasource_warehouse_tables(
    connection: Connection,
    datasource_id: str,
    namespace_id: str,
    name: str = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None
) -> list[Type["WarehouseTable"]] | list[dict]:
    """Lists available warehouse tables in a specified datasource within a
       specified namespace.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        datasource_id (str): ID of a datasource.
        namespace_id (str): ID of a namespace within a given datasource_id.
        name (str): string by which to filter the table name
        to_dictionary (bool, optional): If True, the function will return list
            of dictionaries. Otherwise, list of WarehouseTable objects.
            Defaults to False.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.

    Returns:
        Union[list["WarehouseTable"], list[dict]]: A list of WarehouseTable
            or dictionary objects representing warehouse tables in a specified
            namespace in a specified datasource.

    Examples:
        >>> datasource_id = "DAD6CAD6457DAF29E34463961688EA60"
        >>> namespace_id = "eyJucyI6InB1YmxpYyJ9"
        >>> available_wh_tables = list_datasource_warehouse_tables(
            connection, datasource_id, namespace_id)
    """

    tables = fetch_objects(
        connection=connection,
        api=tables_api.get_available_warehouse_tables,
        limit=limit,
        filters={'name': name} if name else None,
        dict_unpack_value="tables",
        datasource_id=datasource_id,
        namespace_id=namespace_id,
    )
    [
        table.update({
            "datasource": {
                "id": datasource_id
            }, "namespace_id": namespace_id
        }) for table in tables
    ]
    if to_dictionary:
        return tables
    return WarehouseTable.bulk_from_dict(source_list=tables, connection=connection)


class WarehouseTable(Dictable):
    """An object representation of a warehouse table. Depending on whether a
    warehouse table is included in a project, it may or may not have a
    persistent id and associated PhysicalTable object. When you add a warehouse
    table to a project, a MSTR server will create a PhysicalTable object that
    represents the added warehouse table and will assign it a persistent ID.
    You can then manipulate the table further using functionalities in
    mstrio.modeling.schema.table.physical_table.

    Attributes:
        connection (Connection): An object representation of MSTR Connection.
        datasource (DatasourceInstance): An object representation of datasource
            instance in which the table resides.
        name (str): A name of the table.
        namespace (str): A name of a namespace in which the table resides.
        namespace_id (str): An ID of a namespace in which the table resides.
        physical_table_id(str): An ID of an associated PhysicalTable object.
            This attribute is set automatically after `add_to_project()` method
            was called on the table.
        dependent_logical_tables (Union[list[dict], list[LogicalTable]]): A list
            of logical tables that are mapped to the warehouse table.
        columns (Union[list[dict], list[TableColumn]]): A list of table columns.

    """

    _FROM_DICT_MAP: dict = {"datasource": DatasourceInstance.from_dict}
    _DELETE_NONE_VALUES_RECURSION = False
    available_tables: list["WarehouseTable"] = []

    def __init__(
        self,
        id: str,
        connection: Connection,
        datasource: DatasourceInstance,
        namespace_id: str,
        name: str,
        namespace: str,
    ):
        self.__id = id  # Non-persistent. It will change if the table name or namespace changes.
        self.connection = connection
        self.datasource = datasource
        self.name = name
        self.namespace = namespace
        self.namespace_id = namespace_id
        # When table is added to a project, it will get a persistent ID
        self.physical_table_id = None
        self._dependent_logical_tables = None
        self._columns = None

    def add_to_project(
        self,
        logical_table_name: str,
        prefix: Optional[str] = None,
        col_merge_option: Optional[TableColumnMergeOption | str] = None,
    ) -> Type["LogicalTable"]:
        """Adds a table to a project. This function corresponds to 'ADD WHTABLE'
           statement from MSTR Command Manager.

        Args:
            logical_table_name (str): Name of the logical table which will be
                mapped to this warehouse table.
            prefix (Optional[str], optional): Table prefix. Defaults to None.
            col_merge_option (Optional[Union[TableColumnMergeOption, str]]:
                Defines a column merge option. Defaults to None.

        Returns:
            LogicalTable: A LogicalTable object representing a logical table
                mapped to this warehouse table.
        """
        lt = LogicalTable.create(
            connection=self.connection,
            table_name=logical_table_name,
            primary_data_source=SchemaObjectReference(
                object_id=self.datasource.id, sub_type=ObjectSubType.LOGICAL_TABLE
            ),
            column_merge_option=col_merge_option,
            physical_table_prefix=prefix,
            physical_table_name=self.name,
            physical_table_namespace=self.namespace,
        )
        self.physical_table_id = lt.physical_table.id
        self.list_dependent_logical_tables(refresh=True)
        return lt

    def list_dependent_logical_tables(self, to_dictionary: bool = False,
                                      refresh: bool = False) -> list["LogicalTable"] | list[dict]:
        """Get all dependent logical tables.

        Args:
            to_dictionary (bool, optional): If True, returns a list of
                dictionaries. Defaults to False.
            refresh(bool, optional): If True, refreshes the result stored in
                `self.dependent_logical_tables`.

        Returns:
            Union[list[LogicalTable], list[dict]]: A list of LogicalTable
                objects or dictionaries representing logical tables.
        """
        if self._dependent_logical_tables and not refresh:
            return self._dependent_logical_tables
        logical_tables = list_logical_tables(connection=self.connection)
        if self.physical_table_id:
            dependent_logical_tables = [
                table for table in logical_tables
                if table.physical_table.id == self.physical_table_id
            ]
        else:
            dependent_logical_tables = [
                table for table in logical_tables if table.physical_table.table_name == self.name
            ]
        if refresh:
            self._dependent_logical_tables = dependent_logical_tables
        if to_dictionary:
            return [table.to_dict() for table in dependent_logical_tables]
        return dependent_logical_tables

    def delete_from_project(self, force: bool = False) -> Optional[list[bool]]:
        """Remove the Warehouse Table from a project by removing all of its
        dependent logical tables. It will only delete dependent logical
        tables if they themselves have no dependent objects. This function
        corresponds to "REMOVE WHTABLE" statement from MSTR Command Manager.
        """
        dependent_logical_tables = self.list_dependent_logical_tables(refresh=True)
        if dependent_logical_tables:
            logging.warning("Following logical tables will be deleted: ")
            [logging.info(f"{str(table)}") for table in dependent_logical_tables]
            confirmed_delete = (force or input("Would you like to continue? Y/n").lower() == "y")
            if confirmed_delete:
                statuses = [table.delete(force=True) for table in dependent_logical_tables]
                self.physical_table_id = (None if all(statuses) else self.physical_table_id)
                return statuses
        else:
            logging.error("This table is not included in a project.")

    def list_columns(self, to_dictionary: bool = False,
                     refresh: bool = False) -> list[Type[TableColumn]] | list[dict]:
        """Get columns for a specific database table.

        Args:
            to_dictionary (bool, optional): If True, returns a list of
                dictionaries. Defaults to False.
            refresh (bool, optional): If True, refetches and overwrites the
                cached version of results stored in
                WarehouseTable.available_tables.

        Returns:
            Union[list[TableColumn], list[dict]]: A list of TableColumn objects
                or dictionaries representing table columns.
        """
        if self._columns and not refresh:
            return self._columns
        datasource_id = (
            self.datasource.id
            if isinstance(self.datasource, DatasourceInstance) else self.datasource.get("id")
        )
        columns = fetch_objects(
            connection=self.connection,
            api=datasources.get_table_columns,
            limit=None,
            filters={},
            dict_unpack_value="columns",
            datasource_id=datasource_id,
            namespace_id=self.namespace_id,
            table_id=self.__id,
        )

        if to_dictionary:
            return columns

        column_objects = TableColumn.bulk_from_dict(
            source_list=columns, connection=self.connection
        )
        if refresh:
            self._columns = column_objects
        return column_objects

    @property
    def dependent_logical_tables(self):
        if not self._dependent_logical_tables:
            self._dependent_logical_tables = self.list_dependent_logical_tables()
        return self._dependent_logical_tables

    @cached_property
    def columns(self):
        self._columns = self.list_columns()
        return self._columns
