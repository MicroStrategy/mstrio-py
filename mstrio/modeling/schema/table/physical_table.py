import logging
from typing import Optional, TYPE_CHECKING, Union

from mstrio.api import datasources
from mstrio.api import tables as tables_api
from mstrio.connection import Connection
from mstrio.modeling.schema import ObjectSubType
from mstrio.modeling.schema.helpers import PhysicalTableType, TableColumn
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import Entity
from mstrio.utils.helper import fetch_objects, get_valid_project_id
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.schema.table.logical_table import LogicalTable

NO_PROJECT_ERR_MSG = "You must specify or select a project."

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0100')
def list_physical_tables(
    connection: Connection,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    filters: Optional[dict] = None,
    limit: Optional[int] = None,
    to_dictionary: bool = False,
    include_unassigned_tables: bool = False
) -> Union[list["PhysicalTable"], list[dict]]:
    """List all physical tables in a project.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        project_id (Optional[str], optional): ID of a project. Defaults to None.
        project_name (Optional[str], optional): Name of a project. Defaults to
            None.
        limit(int, optional) limit the number of elements returned.
            If `None` (default), all objects are returned.
        to_dictionary(bool, optional): If True returns a list of dictionaries.
            Defaults to False.
        filters (dict, optional): dict that specifies filter expressions by
            which objects will be filtered locally.
        include_unassigned_tables(bool, optional): if True also returns tables
            which are not assigned to any metadata object. Including those may
            significantly extend time required to gather data.
            Defaults to False.
    Returns:
        Union[list["PhysicalTable"], list[dict]]: A list of PhysicalTable
            objects or dictionaries representing physical tables.
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True
    )
    if include_unassigned_tables:
        tables = full_search(
            connection=connection,
            project=project_id,
            object_types=ObjectTypes.DBTABLE,
            limit=limit,
            **(filters or {})
        )
    else:
        tables = fetch_objects(
            connection=connection,
            api=tables_api.get_tables,
            limit=limit,
            project_id=project_id,
            filters=filters or {},
            dict_unpack_value="tables",
            fields="physicalTable",
        )

        tables = list({item['id']: item for item in tables}.values())

    return (
        tables if to_dictionary else
        PhysicalTable.bulk_from_dict(source_list=tables, connection=connection)
    )


@method_version_handler('11.3.0100')
def list_tables_prefixes(
        connection: Connection,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
):
    """Returns the prefixes for the physical tables

    Args:
        connection: Object representation of MSTR Connection
        project_id (Optional[str], optional): ID of a project. Defaults to None
        project_name (Optional[str], optional): Name of a project. Defaults to
            None.

    Returns:
        A dictionary of prefixes for all the physical tables
    """
    project_id = get_valid_project_id(connection=connection,
                                      project_id=project_id,
                                      project_name=project_name,
                                      with_fallback=False if project_name else True)

    physical_tables = list_physical_tables(connection, project_id=project_id, to_dictionary=True)
    return {table.get("table_prefix") for table in physical_tables}


@method_version_handler('11.3.0100')
def list_namespaces(
    connection: "Connection",
    id: str,
    refresh: Optional[bool] = None,
    limit: Optional[int] = None,
    **filters,
) -> list[dict]:
    """Get list of namespaces. Optionally filter them by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        id (str): Datasource ID
        refresh (bool, optional): Force refresh
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name']

    Examples:
        >>> list_namespaces(connection, id='A23BBC514D336D5B4FCE919FE19661A3')
    """
    namespaces = fetch_objects(
        connection=connection,
        api=datasources.get_datasource_namespaces,
        dict_unpack_value="namespaces",
        limit=limit,
        filters=filters,
        id=id,
        refresh=refresh,
    )

    return namespaces


@class_version_handler('11.3.0100')
class PhysicalTable(Entity):
    """An object representation of a metadata of physical table. A physical
        table describes the metadata of a warehouse table. It contains a set of
        columns with a schema definition. Currently, two types of physical
        tables are supported. One is called a normal table. It uses the table
        name and namespace to fetch schema definitions from the warehouse. The
        other table is a freeform SQL table. It uses a SQL statement to fetch
        schema definitions.

    Attributes:
        information: An object that contains all of the type-neutral information
            stored in the metadata about an object.
        columns: A list of objects representing a physical column that might
            appear in some data source. In addition to representing physical
            columns, we also use this object to represent columns that do not
            actually appear in any data source but which the engine should
            create if it needs to make a column to contain data for some higher
            level construct (e.g. a fact, an attribute form etc.).
        namespace: The namespace in which a table resides
        table_name: The name of a table
        table_prefix: A table prefix of this physical table
        type: A table type
        sql_statement: This field applies only to a free form sql physical table
    """

    _OBJECT_TYPE: ObjectTypes = ObjectTypes.DBTABLE
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "columns": [TableColumn.from_dict],
        "table_type": PhysicalTableType,
        "owner": User.from_dict,
    }
    _REST_ATTR_MAP = {"object_id": "id"}

    def __init__(
        self,
        connection: Connection,
        id: str,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None
    ):
        """Initializes a PhysicalTable object. You have to provide ID of a
            physical table object. You can get this ID e.g. using
            `mstrio.project_object.schema.tables.list_physical_tables()`. It
            will try to fetch as much information as possible. To start, it will
            fetch all information related to Entity class. If the physical table
            has at least one logical table associated with it (in a project
            mapped to a connection object), it will fetch additional information
            Info: It's necessary to provide an ID of the table. If you only
                provide the name of a table, it will not be initialized

        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.

        Note:
            When `project_id` is `None` and `project_name` is `None`, then
             its value is overwritten by `project_id` from `connection` object.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            id (str): ID of a physical table object.
            name (str, optional) read-only, Used to improve readability of
                the PhysicalTable class string representation
            project_id (str, optional): ID of a project. Defaults to None.
            project_name (str, optional): Name of a project. Defaults to
                None.

        Examples:
            >>> PhysicalTable(connection, id='5DE0F8934CBD82437D6FA1AFF75F6C58')
        """
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )

        super().__init__(connection=connection, object_id=id)
        try:
            # If the physical table is included in a project, more info can be
            # fetched.
            physical_tables: list[dict] = list_physical_tables(connection, project_id,
                                                               to_dictionary=True,
                                                               filters={'id': id})
            table = physical_tables[0]
            table.update({"table_type": table.pop("type", None)})
            self._set_object_attributes(**table)
        except LookupError:
            pass

    def _init_variables(self, **kwargs) -> None:
        if kwargs.get("id"):
            super()._init_variables(**kwargs)
        elif kwargs.get("information"):
            # available when fetched as a part of a logical table
            information = kwargs.pop("information")
            kwargs.update(
                {
                    "id": information.get("object_id"),
                    "table_type": kwargs.pop("type", None),
                    **information,
                }
            )
            super()._init_variables(**kwargs)

            columns = kwargs.get("columns")
            self.columns = (
                TableColumn.bulk_from_dict(source_list=columns, connection=self.connection)
                if columns else None
            )
            self.namespace = kwargs.get("namespace")
            self.primary_locale = kwargs.get("primary_locale")

            sub_type = kwargs.get("sub_type")
            self._sub_type = ObjectSubType(sub_type) if sub_type else None
            self.table_name = kwargs.get("table_name")
            self.table_prefix = kwargs.get("table_prefix")

            table_type = kwargs.get("table_type")
            self.table_type = PhysicalTableType(table_type) if table_type else None
            self._version = kwargs.get("version_id")

    def list_dependent_logical_tables(self) -> list["LogicalTable"]:
        """Searches and filters a list of logical tables based on provided
           physical `table_id`.

        Returns:
            list[LogicalTable]: A list of `LogicalTable` objects that are
                dependents of the specified physical table.
        """
        from mstrio.modeling.schema.table.logical_table import list_logical_tables

        logical_tables = list_logical_tables(connection=self.connection)

        return [table for table in logical_tables if table.physical_table.id == self.id]

    def delete(self, force: bool = False) -> None:
        """Searches for all logical table dependents based on provided physical
           `table_id`. If they are found (i.e. physical table is included in
           a project) then information about dependents will be shown and prompt
           will be displayed. If prompt is positive, it will delete all
           dependent logical tables which in turn automatically removes the
           physical table from the project. Note, that table will be deleted
           only if all dependent logical tables have no dependents themselves.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            table_id (str): ID of a physical table.
            force: (bool): If True then prompt will be skipped.
        """
        dependent_logical_tables = self.list_dependent_logical_tables()
        if dependent_logical_tables:
            logger.warning("Following dependent logical tables will be deleted: ")
            logger.warning(",".join(str(table) for table in dependent_logical_tables))
            confirmed_delete = (force or input("Do you want to continue? [Y/n]: ").lower() == "y")
            if confirmed_delete:
                [table.delete(force=True) for table in dependent_logical_tables]
                logger.info(f"Successfully removed Warehouse Table with id: {self.id}")
        else:
            logger.error("This table is not included in a project.")
