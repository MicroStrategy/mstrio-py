from concurrent.futures import as_completed, Future
from functools import cached_property
import logging
from typing import Optional, Type

from requests import HTTPError, ReadTimeout
from tqdm import tqdm

from mstrio.api import datasources
from mstrio.api import tables as tables_api
from mstrio.connection import Connection
from mstrio.datasources.datasource_instance import (
    DatasourceInstance,
    list_connected_datasource_instances
)
from mstrio.modeling.schema import ObjectSubType, SchemaObjectReference
from mstrio.modeling.schema.helpers import TableColumn, TableColumnMergeOption
from mstrio.modeling.schema.table.logical_table import list_logical_tables, LogicalTable
from mstrio.utils.helper import Dictable, fetch_objects
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


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


def list_warehouse_tables(
    connection: Connection,
    to_dictionary: bool = False,
    name: Optional[str] = None,
    datasource_id: Optional[str] = None
) -> list["WarehouseTable"] | list[dict]:
    """Fetches all available warehouse table. This operation is done
       asynchronously and is heavy: a lot of requests are performed to fetch
       all connected and available datasources, namespaces and finally
       warehouse tables for each combination. Additionally, the result could be
       filtered. Available filters are table name and datasource id. These
       filters can be combined.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        to_dictionary (bool, optional): If True, returns a list of dictionaries.
            If False, returns a list of WarehouseTable objects.
        name (str, optional): A name of a warehouse table.
        datasource_id (str, optional): ID of a datasource.

    Returns:
        list[WarehouseTable] | list[dict]: A list of dictionaries
            or WarehouseTable objects.

    """
    return WarehouseTable._list_warehouse_tables(
        connection, to_dictionary, name, datasource_id
    )


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

    def list_dependent_logical_tables(
        self,
        to_dictionary: bool = False,
        refresh: bool = False
    ) -> list["LogicalTable"] | list[dict]:
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
            logger.warning("Following logical tables will be deleted: ")
            [logger.info(f"{str(table)}") for table in dependent_logical_tables]
            confirmed_delete = (force or input("Would you like to continue? Y/n").lower() == "y")
            if confirmed_delete:
                statuses = [table.delete(force=True) for table in dependent_logical_tables]
                self.physical_table_id = (None if all(statuses) else self.physical_table_id)
                return statuses
        else:
            logger.error("This table is not included in a project.")

    def list_columns(
        self,
        to_dictionary: bool = False,
        refresh: bool = False
    ) -> list[Type[TableColumn]] | list[dict]:
        """Get columns for a specific database table.

        Args:
            to_dictionary (bool, optional): If True, returns a list of
                dictionaries. Defaults to False.
            refresh (bool, optional): If True, refetches and overwrites the
                cached version of results stored in
                WarehouseTable.columns.

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
        self._columns = column_objects
        return column_objects

    @classmethod
    def _list_warehouse_tables(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        name: Optional[str] = None,
        datasource_id: Optional[str] = None
    ) -> list["WarehouseTable"] | list[dict]:
        """Fetches all available warehouse table in a project mapped to the
           Connection object. This operation is done asynchronously and is
           heavy: a lot of requests are performed to fetch all connected and
           available datasources, namespaces and finally warehouse tables for
           each combination. Additionally, the result could be filtered.
           Available filters are table name and datasource id. These
           filters can be combined.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            to_dictionary (bool, optional): If True, returns a list of
                dictionaries. If False, returns a list of WarehouseTable
                objects.
            name (str, optional): A name of a warehouse table.
            datasource_id (str, optional): ID of a datasource.

        Returns:
            list[WarehouseTable] | list[dict]: A list of dictionaries
                or WarehouseTable objects.
        """
        if name or datasource_id:
            tables = cls._filter(connection=connection, name=name, datasource_id=datasource_id)
            if to_dictionary:
                return [table.to_dict() for table in tables]
            return tables

        return cls._list_available_warehouse_tables(
            connection=connection,
            to_dictionary=to_dictionary,
        )

    @classmethod
    def _filter(
        cls,
        connection: Connection,
        name: Optional[str] = None,
        datasource_id: Optional[str] = None
    ) -> list["WarehouseTable"]:
        """Fetches (if not yet fetched) and filters all available warehouse
           tables. Available filters are table name and datasource id. These
           filters can be combined.

           Args:
            connection (Connection): Object representation of MSTR Connection.
            name (str, optional): A name of a warehouse table.
            datasource_id (str, optional): ID of a datasource.

        Returns:
            list[WarehouseTable]: A list of filtered warehouse tables.
        """

        available_tables = cls._list_available_warehouse_tables(connection)

        if name and datasource_id:
            datasource_tables = [
                table
                for table in available_tables
                if table.datasource.id == datasource_id
            ]
            available_tables = [
                table
                for table in datasource_tables
                if table.name == name.lower()
            ]

        elif name:
            available_tables = [table for table in available_tables if table.name == name.lower()]
        elif datasource_id:
            available_tables = [
                table for table in available_tables if table.datasource.id == datasource_id
            ]
        return available_tables

    @classmethod
    def _list_available_warehouse_tables(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
    ) -> list["WarehouseTable"] | list[dict]:
        """Fetches all available warehouse table in a project mapped to the
           Connection object. This operation is done asynchronously and is
           heavy: a lot of requests are performed to fetch all connected and
           available datasources, namespaces and finally warehouse tables for
           each combination.

           connection (Connection): Object representation of MSTR Connection.
           to_dictionary (bool): If True, returns a list of dictionaries.

        Returns:
            Union[list[dict], list["WarehouseTable"]]: A list of dictionaries
                or WarehouseTable objects.
        """

        connected_datasource_instances: list[dict] = list_connected_datasource_instances(
            connection, to_dictionary=True)
        urls: dict[str, str] = cls._get_namespaces_urls(connection, connected_datasource_instances)

        with FuturesSessionWithRenewal(connection=connection) as session:
            namespaces: dict[str, list[dict]] = cls._get_namespaces(connection, urls, session)

            warehouse_tables_futures = cls._get_warehouse_tables_futures(
                connection, session, namespaces)

            warehouse_tables: list[dict] = cls._get_warehouse_tables(connection,
                                                                     warehouse_tables_futures)

            available_tables = cls.bulk_from_dict(source_list=warehouse_tables,
                                                  connection=connection)
        if to_dictionary:
            return warehouse_tables

        return available_tables

    @classmethod
    def _get_warehouse_tables(
        cls,
        connection: Connection,
        warehouse_tables_futures: list[Future]
    ) -> list[dict]:
        """Retrieves warehouse tables from a list of provided futures.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            warehouse_tables_futures (list[Future]): A list of futures that
            resolve to warehouse tables in a given datasource in a given
            namespace.

        Returns:
            list[dict]: A list of warehouse tables retrieved from all the
                futures.
        """

        warehouse_tables: list[dict] = []
        with tqdm(total=len(warehouse_tables_futures),
                  desc="Retrieving warehouse tables...") as pbar:
            for future in as_completed(warehouse_tables_futures):
                namespace_tables = cls._get_future_with_request_exceptions_handlers_and_pbar(
                    cls._get_tables_from_future, future, pbar, connection=connection)
                if namespace_tables:
                    warehouse_tables += namespace_tables

        return warehouse_tables

    @classmethod
    def _get_namespaces(
        cls,
        connection: Connection,
        urls: dict,
        session: FuturesSessionWithRenewal
    ) -> dict[str, list[dict]]:
        """Retrieves namespaces for every url using provided session object.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            urls (dict): A dictionary with datasource ID as a key and list of
                namespace urls as a value.
            session (FuturesSession): A FuturesSession object used to fetch
                urls asynchronously.

        Returns:
            dict[str, list[dict]]: A dictionary which keys are datasource ids
                and which values are lists of namespaces.
        """
        namespaces: dict[str, list[dict]] = {}
        namespaces_futures = cls._get_namespaces_futures(connection, session, urls)
        with tqdm(
                total=len(namespaces_futures),
                desc="Retrieving namespaces from available datasources...",
        ) as pbar:
            for future in as_completed(namespaces_futures):
                namespaces[
                    future
                    .datasource_id] = cls._get_future_with_request_exceptions_handlers_and_pbar(
                        cls._get_namespaces_from_future, future, pbar)
        return namespaces

    @classmethod
    def _get_future_with_request_exceptions_handlers_and_pbar(
        cls, func, future, pbar, **func_kwargs
    ):
        try:
            return func(future=future, **func_kwargs)
        except (ReadTimeout, HTTPError, ConnectionError) as e:
            logger.error(e)
        finally:
            pbar.update()

    @staticmethod
    def _get_namespaces_urls(
        connection: "Connection",
        connected_datasource_instances: list[dict]
    ) -> dict[str, str]:
        """Creates urls to api/datasources/{datasource_id}/catalog/namespaces
           that are later used to fetch all namespaces from a specified
           datasource

        Args:
            connection (Connection): Object representation of MSTR Connection.
            connected_datasource_instances (list[dict]): list of dictionaries
                representing connected datasource instances.

        Returns:
            dict[str, str]: a dictionary with datasource id as a key,
                and matching namespaces url as a value
        """
        return {
            connected_datasource_instance.get("id"):
            (f"{connection.base_url}/api/datasources/{connected_datasource_instance.get('id')}"
             f"/catalog/namespaces")
            for connected_datasource_instance in connected_datasource_instances
        }

    @staticmethod
    def _get_namespaces_futures(
        connection: "Connection",
        session: FuturesSessionWithRenewal,
        urls: dict[str, str]
    ) -> list[Future]:
        """Creates Future objects using specified FuturesSession object for each
           url.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            session (FuturesSession): A FuturesSession object used to fetch
                the url.
            urls (dict[str, str]): a dictionary with datasource id as a key,
                and matching namespaces url as a value.

        Returns:
            list[Future]: A list of Future objects that later resolve to
                namespaces within a specified datasource.
        """
        futures = []
        for datasource_id, url in urls.items():
            future = session.get(
                url,
                headers={
                    "X-MSTR-ProjectID": connection.project_id,
                },
            )
            future.datasource_id = datasource_id
            futures.append(future)
        return futures

    @staticmethod
    def _get_warehouse_tables_futures(
        connection: "Connection",
        session: FuturesSessionWithRenewal,
        namespaces: dict[str, list[dict]],
    ) -> list[Future]:
        """Creates Future objects using specified FuturesSession object for each
           namespace for each datasource.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            session (FuturesSession): A FuturesSession object used to fetch
                the tables.
            namespaces (dict[str, list[dict]]): a dictionary with datasource id
                as a key and list of available namespaces withing this
                datasource as a value.

        Returns:
            list[Future]: A list of Future objects that later resolve to
                warehouse tables for each namespace for each datasource.
        """
        futures = []
        for datasource_id, namespaces_list in namespaces.items():
            if namespaces_list:
                for namespace in namespaces_list:
                    namespace_id = namespace.get("id")
                    future = tables_api.get_available_warehouse_tables_async(
                        session,
                        connection,
                        datasource_id=datasource_id,
                        namespace_id=namespace_id,
                    )
                    future.datasource_id = datasource_id
                    future.namespace_id = namespace_id
                    future.namespace = namespace.get("name")
                    futures.append(future)
        return futures

    @staticmethod
    def _get_namespaces_from_future(future: Future) -> list[dict]:
        """Retrieves a list of namespaces from a given future.

        Args:
            future (Future): A future object that resolves to a dictionary that
                contains a list of namespaces.

        Returns:
            list[dict]: A list of namespaces retrieved from the future.
        """
        resp = future.result()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("namespaces")
        return []

    @staticmethod
    def _get_tables_from_future(connection: Connection, future: Future) -> list[dict]:
        """Retrieves a list of tables from a given future.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            future (Future): A future object that resolves to a dictionary that
                contains a list of tables.

        Returns:
            list[dict]: A list of tables retrieved from the future.
        """
        warehouse_tables = []
        resp = future.result()
        tables = resp.json().get("tables")
        if tables:
            for table in tables:
                table["connection"] = connection
                table["datasource"] = {"id": future.datasource_id}
                table["namespace_id"] = future.namespace_id
                warehouse_tables.append(table)
        return warehouse_tables

    @property
    def dependent_logical_tables(self):
        if not self._dependent_logical_tables:
            self._dependent_logical_tables = self.list_dependent_logical_tables()
        return self._dependent_logical_tables

    @cached_property
    def columns(self):
        self._columns = self.list_columns()
        return self._columns
