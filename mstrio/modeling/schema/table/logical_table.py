import logging
from typing import Optional

from tqdm import tqdm

from mstrio import config
from mstrio.api import objects
from mstrio.api import tables as tables_api
from mstrio.connection import Connection
from mstrio.modeling.schema import ObjectSubType, SchemaObjectReference
from mstrio.modeling.schema.attribute import Attribute
from mstrio.modeling.schema.fact import Fact
from mstrio.modeling.schema.helpers import (
    PhysicalTableType,
    TableColumn,
    TableColumnMergeOption,
    TablePrefixOption
)
from mstrio.modeling.schema.table.physical_table import PhysicalTable
from mstrio.object_management import Folder
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum, get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    exception_handler,
    fetch_objects,
    get_args_from_func,
    get_default_args_from_func,
    get_valid_project_id
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

NO_PROJECT_ERR_MSG = "You must specify or select a project."

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0100')
def list_logical_tables(
    connection: Connection,
    to_dictionary: bool = False,
    table_type: Optional[PhysicalTableType] = None,
    name: Optional[str] = None,
    folder_id: Optional[str] = None,
    folder_name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    filters: Optional[dict] = None,
    limit: Optional[int] = None
) -> list["LogicalTable"] | list[dict]:
    """List all logical tables in a project mapped to a specified connection.
       Optionally, you can filter by physical table type.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        name (Optional[str], optional): Name of a table.
        project_id (Optional[str], optional): ID of a project. Defaults to None.
        project_name (Optional[str], optional): Name of a project. Defaults to
            None.
        folder_id (Optional[str], optional): ID of a folder in which to look for
            logical tables. Defaults to None.
        folder_name (Optional[str], optional): Name of a folder in which to look
            for logical tables. Defaults to None.
        to_dictionary (bool, optional): If True returns a list of dictionaries.
            Defaults to False.
        table_type(PhysicalTableType, optional): If specified, returns a list
            of logical tables with physical table with this type.
        filters: dict that specifies filter expressions. Available filters are
            `name`, `folder_id`, `folder_name`, `project_id` and `project_name`
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.

    Returns:
        list["LogicalTable"] | list[dict]: A list of LogicalTable objects
            or dictionaries representing logical tables.
    """
    if any([name, folder_id, folder_name, project_id, project_name]):
        return _full_search_logical_tables(
            connection=connection,
            to_dictionary=to_dictionary,
            name=name,
            folder_id=folder_id,
            folder_name=folder_name,
            project_id=project_id,
            project_name=project_name,
            limit=limit
        )
    else:
        if table_type:
            logical_tables = fetch_objects(
                connection,
                tables_api.get_tables,
                limit=None,
                filters=filters or {},
                dict_unpack_value="tables",
                fields="information,physicalTable",
            )
            table_type = get_enum_val(table_type, PhysicalTableType)

            def remove_physical_table(data):
                data.pop('physical_table')
                return data

            logical_tables = [
                remove_physical_table(table)
                for table in logical_tables
                if table.get("physical_table").get("type") == table_type
            ]
            logical_tables = logical_tables[:limit] if limit else logical_tables
        else:
            logical_tables = fetch_objects(
                connection,
                tables_api.get_tables,
                limit=limit,
                filters=filters or {},
                dict_unpack_value="tables",
                fields="information",
            )

        return logical_tables if to_dictionary else LogicalTable.bulk_from_dict(
            source_list=logical_tables, connection=connection
        )


def _full_search_logical_tables(
    connection: Connection,
    name: Optional[str] = None,
    folder_id: Optional[str] = None,
    folder_name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    limit: Optional[int] = None,
    to_dictionary: bool = False
) -> list[type["LogicalTable"]] | list[dict]:
    """Searches for a logical table in a specified project. You can narrow the
       search result by folder's id or name.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection (Connection): Object representation of MSTR Connection.
        name (Optional[str], optional): Name of a table.
        project_id (Optional[str], optional): ID of a project. Defaults to None.
        project_name (Optional[str], optional): Name of a project. Defaults to
            None.
        folder_id (Optional[str], optional): ID of a folder in which to look for
            logical tables. Defaults to None.
        folder_name (Optional[str], optional): Name of a folder in which to look
            for logical tables. Defaults to None.
        to_dictionary (bool, optional): If True, the function will return list
            of dictionaries. Otherwise, list of LogicalTable objects.
            Defaults to False.

    Throws:
        ValueError if:
            - Project could not be determined
            - `folder_name` was specified but folder could not be found.

    Returns:
        list[dict] | list["LogicalTable"]: A list of logical tables
            in a given project represented either as objects or dictionaries.

    Examples:
        >>> full_search_logical_tables(connection)
        >>> full_search_tables(connection,
                               project_name='MicroStrategy Tutorial',
                               folder_id='24BAE4BF704E8E269333BEAF7195AF88')
        >>> full_search_logical_tables(connection,
                                       project_name='MicroStrategy Tutorial',
                                       folder_name='My Answers')
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True,
    )

    if folder_name and not folder_id:
        folders = full_search(
            connection=connection,
            project=project_id,
            object_types=ObjectTypes.FOLDER,
            limit=limit
        )
        folder = next(filter(lambda _folder: _folder.get("name") == folder_name, folders), None)
        folder_id = folder["id"] if folder else exception_handler(
            'Folder with a given name was not found.', exception_type=ValueError
        )

    logical_tables = full_search(
        connection=connection,
        name=name,
        project=project_id,
        object_types=ObjectTypes.TABLE,
        root=folder_id,
    )
    return (
        logical_tables if to_dictionary else
        LogicalTable.bulk_from_dict(source_list=logical_tables, connection=connection)
    )


@method_version_handler('11.3.0100')
def list_changeset_tables(
    connection: Connection,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    limit: Optional[int] = None,
    changeset_id: Optional[str] = None,
    **filters,
) -> list[type["LogicalTable"]]:
    # Changeset must be specified
    if not changeset_id:
        exception_handler(msg="You must specify changeset ID.", exception_type=ValueError)

    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=False if project_name else True
    )

    tables_list = fetch_objects(
        connection=connection,
        api=tables_api.get_tables,
        limit=limit,
        project_id=project_id,
        changeset_id=changeset_id,
        dict_unpack_value="tables",
        filters=filters,
    )

    return LogicalTable.bulk_from_dict(source_list=tables_list, connection=connection)


@class_version_handler('11.3.0100')
class LogicalTable(Entity, DeleteMixin, MoveMixin):
    """An object representation of a logical table, referred to as Table in
    Command Manager. A logical table describes the higher-level data model
    objects (facts, attributes, etc.) that the architect wishes to use to model
    the contents of the physical table.

    A logical table cannot exist without a physical table. Each logical table
    is mapped to exactly one physical table. However, a physical table may be
    mapped to many logical tables (each additional one is called logical table
    alias). This class exposes interface to create both logical and logical
    table alias.

    After performing a write operation on a LogicalTable object, you may want to
    reload the schema using mstrio.modeling.schema.schema_management module.

    Attributes:
        name: name of the logical table
        id: id of the logical table
        description: description of the logical table
        sub_type: string literal used to identify the type of a metadata object,
            ObjectSubType enum
        version: object version ID
        ancestors: list of ancestor folders
        type: object type, ObjectTypes enum
        ext_type: object extended type, ExtendedType enum
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        owner: User object that is the owner
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
        version_id: the version number this object is currently carrying
        is_embedded: if true indicates that the target object of this reference
            is embedded within this object, if this field is omitted
            (as is usual) then the target is not embedded.
        path: the path of the object, read only
        primary_locale: the primary locale of the object, in the IETF BCP 47
            language tag format, such as "en-US", read only
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
        logical_size: a size based on the columns in the tables and the
            attributes to which those columns correspond. Uses the conceptual or
            logical attribute definitions to assign a size to each table in the
            project.
        is_logical_size_locked: An indication if the logical table size of a
            table is locked or not. When a table’s logical size is locked, the
            table is excluded from the logical table size calculation when a
            schema update is performed.
        is_part_of_partition: An indication whether this table is part of
            a partition table.
        is_true_key: An indication whether a specified primary key is the true
            key.
        table_key: A list of objects representing table keys defined on physical
            table
        partition_level: List of objects representing partition attributes
        attributes: list of objects representing business concepts reflected in
            data. Attributes provide a context in which to report on and analyze
            business facts or calculations.
        facts: list of objects representing essential elements within the
            business data model and basis for almost all metrics. They relate
            numeric data values from the data warehouse to the MicroStrategy
            reporting environment. E.g. sales dollars, units sold, profit etc.
        primary_data_source: Table's data can be from different data sources.
            Primary data source is the first option for table's data source.
        enclose_sql_in_parentheses: This property is only applied if a logical
            table is based upon a free form sql table. By default, this property
            value is set to true. This encloses the entire SQL that you typed in
            the sqlStatement field in parentheses when the SQL statement is
            executed.
        physical_table: Metadata of a physical table based on warehouse's
            physical table or free form sql.
        partition_tables: A list of objects representing partition's tables
            metadata
        secondary_data_sources: MicroStrategy support mapping the table to more
            than one data source. This attribute is a list of object
            representations of a reference to a datasource.
    """

    _OBJECT_TYPE: ObjectTypes = ObjectTypes.TABLE
    _FROM_DICT_MAP: dict = {
        **Entity._FROM_DICT_MAP,
        "owner": User.from_dict,
        "attributes": [Attribute.from_dict],
        "sub_type": ObjectSubType,
        "primary_data_source": SchemaObjectReference.from_dict,
        "secondary_data_sources": [SchemaObjectReference.from_dict],
        "physical_table": PhysicalTable.from_dict,
        "table_key": [SchemaObjectReference.from_dict],
        "facts": [Fact.from_dict],
    }
    _API_GETTERS = {
        (
            "name",
            "description",
            "abbreviation",
            "type",
            "subtype",
            "ext_type",
            "date_created",
            "date_modified",
            "version",
            "owner",
            "icon_path",
            "view_media",
            "ancestors",
            "certified_info",
            "acg",
            "acl",
            "comments",
            "project_id",
            "hidden",
            "target_info",
        ): objects.get_object_info,
        (
            "id",
            "is_embedded",
            "primary_locale",
            "destination_folder_id",
            "logical_size",
            "is_logical_size_locked",
            "is_part_of_partition",
            "is_true_key",
            "table_key",
            "partition_level",
            "attributes",
            "facts",
            "primary_data_source",
            "enclose_sql_in_parentheses",
            "physical_table",
            "partition_tables",
            "secondary_data_sources",
        ): tables_api.get_table,
    }
    _API_PATCH: dict = {
        (
            "name",
            "description",
            "logical_size",
            "is_true_key",
            "primary_data_source",
            "enclose_sql_in_parentheses",
            "physical_table",
            "secondary_data_sources",
        ): (tables_api.patch_table, "partial_put"),
        "folder_id": (objects.update_object, "partial_put"),
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "logical_size": int,
        "is_logical_size_locked": str,
        "is_true_key": bool,
        "primary_data_source": dict,
        "enclose_sql_in_parentheses": bool,
        "physical_table": dict,
        "secondary_data_sources": list,
        "folder_id": str,
    }

    def __init__(
        self,
        connection: Connection,
        id: Optional[str] = None,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """Initializes a LogicalTable object. You can specify either `id`
            or `name` where `id` has a priority. You must specify
            either `project_id` or `project_name` if Connection object provided
            as `connection` is not mapped to a project.

        Specify either `project_id` or `project_name`.
        When `project_id` is provided (not `None`), `project_name` is omitted.

        Note:
            When `project_id` is `None` and `project_name` is `None`, then
            its value is overwritten by `project_id` from `connection` object.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            id (Optional[str], optional): ID of a table. Defaults to None.
            name (Optional[str], optional): Name of a table. Defaults to
                None.
            project_id (Optional[str], optional): ID of a project. Defaults to
                None.
            project_name (Optional[str], optional): Name of a project. Defaults
                to None.

        Throws:
            ValueError if:
                - neither `id` nor `name` were specified
                - a specified project could not be found.
                - a specified table could not be found.

        Examples:
            >>> LogicalTable(connection,
                             id='FF529E1446BE3DF75ECD4B8E18618747')
            >>> LogicalTable(connection, name='lu_day_of_week')
        """

        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=False if project_name else True
        )

        if not id and not name:
            exception_handler(
                msg="You must specify table's id or table's name.",
                exception_type=ValueError,
            )
        elif not id:
            try:
                id = full_search(
                    connection=connection,
                    project=project_id,
                    object_types=ObjectTypes.TABLE,
                    name=name,
                )[0].get("id")
            except IndexError:
                exception_handler(
                    msg="Table with a given name was not found.",
                    exception_type=ValueError,
                )
        super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        attributes = kwargs.get("attributes")
        self.attributes = (
            Attribute.bulk_from_dict(source_list=attributes, connection=self.connection)
            if attributes else None
        )

        ancestors = kwargs.get("ancestors")
        self.folder_id = ancestors[-1].get("id") if ancestors else None
        self.destination_folder_id = kwargs.get("destination_folder_id")

        facts = kwargs.get("facts")
        if facts:
            [f.update(f.pop("information")) for f in facts]
        self.facts = (
            Fact.bulk_from_dict(source_list=facts, connection=self.connection) if facts else None
        )
        self.is_logical_size_locked = kwargs.get("is_logical_size_locked")
        self.is_part_of_partition = kwargs.get("is_part_of_partition")
        self.is_true_key = kwargs.get("is_true_key")
        self.logical_size = kwargs.get("logical_size")

        physical_table = kwargs.get("physical_table")
        self.physical_table = (
            PhysicalTable.from_dict(source=physical_table, connection=self.connection)
            if physical_table else None
        )

        primary_data_source = kwargs.get("primary_data_source")
        self.primary_data_source = (
            SchemaObjectReference.from_dict(source=primary_data_source)
            if primary_data_source else None
        )
        self.primary_locale = kwargs.get("primary_locale")

        secondary_data_sources = kwargs.get("secondary_data_sources")
        self.secondary_data_sources = (
            SchemaObjectReference.bulk_from_dict(
                source_list=secondary_data_sources, connection=self.connection
            ) if secondary_data_sources else None
        )

        sub_type = kwargs.get("sub_type")
        self._sub_type = ObjectSubType(sub_type) if sub_type else None

        table_key = kwargs.get("table_key")
        self.table_key = (
            SchemaObjectReference.bulk_from_dict(
                source_list=table_key, connection=self.connection
            ) if table_key else None
        )
        self._version = kwargs.get("version_id")

    @classmethod
    def create(
        cls,
        connection: "Connection",
        primary_data_source: SchemaObjectReference | dict,
        table_name: Optional[str] = None,
        table_description: Optional[str] = None,
        sub_type: Optional[ObjectSubType | str] = ObjectSubType.LOGICAL_TABLE,
        destination_folder: Optional[Folder | str] = None,
        is_embedded: Optional[bool] = None,
        physical_table: Optional[PhysicalTable | dict] = None,
        physical_table_name: Optional[str] = None,
        physical_table_namespace: Optional[str] = None,
        physical_table_type: Optional[PhysicalTableType] = PhysicalTableType.NORMAL,
        physical_table_prefix: Optional[str] = None,
        columns: Optional[list[TableColumn] | list[dict]] = None,
        sql_statement: Optional[str] = None,
        logical_size: Optional[int] = None,
        is_part_of_partition: Optional[bool] = None,
        is_true_key: Optional[bool] = None,
        enclose_sql_in_parentheses: Optional[bool] = None,
        check_secondary_data_source_table: Optional[bool] = None,
        column_merge_option: Optional[TableColumnMergeOption] = TableColumnMergeOption.REUSE_ANY,
        table_prefix_option: Optional[TablePrefixOption] = None,
    ) -> type["LogicalTable"]:
        """Create a new table in a specific project.

        Args:
            connection (object): MicroStrategy connection object returned by
                `connection.Connection()`.
            primary_data_source (object): Information about an object referenced
                within the  specification of another object. An object reference
                typically contains only enough fields to uniquely identify
                the referenced objects.
            table_name (str, optional): Logical table name
            table_description (str, optional): Logical table description
            sub_type (enum, str, optional): String literal used to identify the
                type of a metadata object.
            destination_folder (object, str, optional): Globally unique
                identifier used to distinguish between metadata objects within
                the same project
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            physical_table (object, dict, optional): Physical table
            physical_table_name (str, optional): Table name
            physical_table_namespace (str, optional): Datasource namespace
            physical_table_type (enum, optional): Table type
            physical_table_prefix (str, optional): Table prefix of the table
            columns (object, optional): Columns
            sql_statement (str, optional): SQL statement that will be executed
                against the warehouse to get column data of the physical table.
            logical_size (int, optional): Size of a table
            is_part_of_partition (bool, optional): whether current table is part
                of partition table.
            is_true_key (bool, optional): MicroStrategy requires each table to
                have a primary key, which is a unique value identifying each
                distinct data record or row. A primary key can be defined by one
                or more columns in the table. MicroStrategy determines the
                primary key for a table based on the attribute's mapped to the
                columns of the table. The key is made up of the lowest level
                attributes. If these columns are mapped to attributes in
                MicroStrategy, then the primary key is represented correctly.
                In this case, if isTrueKey is returned as true, it indicates
                specified primary key is the true key.
            enclose_sql_in_parentheses (bool, optional): This property is only
                applied to free form sql table. This encloses the entire SQL
                that you typed in the sqlStatement field in parentheses when
                the SQL statement is executed.
            check_secondary_data_source_table (bool, optional): API finds
                compatible tables in the project. If a compatible table is
                found, the compatible table object information is returned.
                If no table is found, a new table is created.
                Available values: 'true', 'false'
                    If 'true', finds compatible tables in the project.
                        If a compatible table is found, the compatible table
                        object information is returned. If no table is found,
                        a new table is created.
                    If 'false', a new table is created.
            column_merge_option (enum, optional): Defines a column merge option
                Available values: 'reuse_any', 'reuse_compatible_data_type',
                'reuse_matched_data_type'.
                If 'TableColumnMergeOption.REUSE_ANY', updates the column
                    data type to use the most recent column definition.
                If 'TableColumnMergeOption.REUSE_COMPATIBLE_DATA_TYPE', updates
                    the column data type to use the data type with the largest
                    precision or scale.
                If 'TableColumnMergeOption.REUSE_MATCHED_DATA_TYPE', renames
                    the column in newly added table to allow it to have
                    different data types.
            table_prefix_option (enum, optional): Define the table prefix
                Available values: 'ADD_DEFAULT_PREFIX', 'ADD_NAMESPACE'.
                If 'TablePrefixOption.ADD_DEFAULT_PREFIX', applies the default
                    prefix setting on warehouse catalog.
                If 'TablePrefixOption.ADD_NAMESPACE', create a prefix same
                    with namespace.
        Returns:
            LogicalTable object

        Examples:
            >>> LogicalTable.create(connection,
                                    physical_table=PhysicalTable(
                                        connection=connection,
                                        id="8D67911E11D3E4981000E787EC6DE8A4",
                                    ),
                                    primary_data_source=SchemaObjectReference(
                                        object_id="A23BBC514D336D5B4FCE919FA3",
                                        sub_type=ObjectSubType.DB_ROLE
                                    ),
                                    )
            >>> LogicalTable.create(connection,
                    physical_table_name="lu_prescriber",
                    physical_table_namespace="public",
                    primary_data_source=SchemaObjectReference(
                            object_id="DAD6CAD6457DAF29E34463961688EA60",
                            sub_type=ObjectSubType.DB_ROLE),
                    table_name="New Table", table_description="New Description",
                    sub_type=ObjectSubType.LOGICAL_TABLE))
        """
        if physical_table and any([
                physical_table_name,
                physical_table_namespace,
                physical_table_prefix,
                sql_statement,
                columns,
        ]):
            msg = (
                "You can either pass the `physical table` object or specify parameters related "
                "to the physical table, not both."
            )
            exception_handler(msg, exception_type=ValueError)

        physical_table = (
            PhysicalTable(connection=connection, id=physical_table.get("id"))
            if isinstance(physical_table, dict) else physical_table
        )

        if get_enum_val(getattr(physical_table, "table_type", physical_table_type)
                        ) == get_enum_val(PhysicalTableType.WAREHOUSE_PARTITION):
            exception_handler(
                msg="Warehouse Partition tables are not supported.",
                exception_type=TypeError,
            )

        if (physical_table_name and physical_table_namespace) and sql_statement:
            msg = (
                "Specify either a `physical_table_name` and `physical_table_namespace`"
                " or `sql_statement`"
            )
            exception_handler(msg, exception_type=ValueError)

        primary_data_source = (
            primary_data_source.to_dict()
            if isinstance(primary_data_source, SchemaObjectReference) else primary_data_source
        )

        physical_table = {
            "type": get_enum_val(
                getattr(physical_table, "table_type", physical_table_type),
                PhysicalTableType,
            ),
            "tableName": getattr(physical_table, "table_name", physical_table_name),
            "namespace": getattr(physical_table, "namespace", physical_table_namespace),
            "tablePrefix": getattr(physical_table, "table_prefix", physical_table_prefix),
            "columns": [col.to_dict() if isinstance(col, TableColumn) else col for col in cols] if
            (cols := getattr(physical_table, "columns", columns)) else None,
            "sqlStatement": getattr(physical_table, "sql_statement", sql_statement),
        }

        body = {
            "information": {
                "name": table_name,
                "description": table_description,
                "subType": get_enum_val(sub_type, ObjectSubType),
                "destinationFolderId": destination_folder.id
                if isinstance(destination_folder, Folder) else destination_folder,
                "isEmbedded": is_embedded,
            },
            "logicalSize": logical_size,
            "isPartOfPartition": is_part_of_partition,
            "isTrueKey": is_true_key,
            "primaryDataSource": primary_data_source,
            "encloseSqlInParentheses": enclose_sql_in_parentheses,
            "physicalTable": physical_table,
        }
        body = delete_none_values(body, recursion=True)

        response = tables_api.post_table(
            connection=connection,
            data=body,
            check_secondary_data_source_table=check_secondary_data_source_table,
            column_merge_option=get_enum_val(column_merge_option, TableColumnMergeOption),
            table_prefix_option=get_enum_val(table_prefix_option, TablePrefixOption),
        ).json()

        if config.verbose:
            logger.info(
                f"Successfully created table named: '{response['name']}' "
                f"with ID: '{response['id']}'"
            )

        # TODO remove when new proper endpoint will be implemented
        table = cls.from_dict(source=response, connection=connection)
        if destination_folder:
            table.move(destination_folder)

        return table

    @classmethod
    def create_alias(cls, connection: "Connection", id: str) -> type["LogicalTable"]:
        """Create a new table alias in a specific project.

        Args:
            connection (object): MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Physical table id
        Returns:
            LogicalTable object

        Examples:
            >>> LogicalTable.create_alias(connection,
                                          id="E278D17342991E49710D6F90E2A7BF2C"
                                          )
        """
        body = {"physicalTable": {"information": {"objectId": id}}}

        response = tables_api.post_table(connection=connection, data=body).json()
        if config.verbose:
            logger.info(
                f"Successfully created table alias named: '{response['name']}' "
                f"with ID: '{response['id']}'"
            )

        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: Optional[str] = None,
        is_true_key: Optional[bool] = None,
        logical_size: Optional[int] = None,
        description: Optional[str] = None,
        is_logical_size_locked: Optional[bool] = None,
        primary_data_source: Optional[SchemaObjectReference] = None,
        secondary_data_sources: Optional[list[SchemaObjectReference] | list[dict]] = None,
        physical_table_object_name: Optional[str] = None,
        physical_table_name: Optional[str] = None,
        physical_table_prefix: Optional[str] = None,
        sql_statement: Optional[str] = None,
        enclose_sql_in_parentheses: Optional[bool] = None,
        columns: Optional[list[TableColumn] | list[dict]] = None,
        folder_id: Optional[str] = None,
    ) -> None:  # NOSONAR
        """Alters properties specified by keyword arguments.

        Args:
            name (Optional[str], optional): Name of a logical table. Defaults to
                None.
            is_true_key (Optional[bool]): MicroStrategy requires each table to
                have a primary key, which is a unique value identifying each
                distinct data record or row. A primary key can be defined by one
                or more columns in the table. MicroStrategy determines the
                primary key for a table based on the attribute's mapped to the
                columns of the table. The key is made up of the lowest level
                attributes. If these columns are mapped to attributes in
                MicroStrategy, then the primary key is represented correctly.
                In this case, if isTrueKey is returned as true, it indicates
                specified primary key is the true key. Defaults to None.
            logical_size (Optional[int], optional): Size of a logical table.
                Defaults to None.
            description (str, optional): Logical table description
            is_logical_size_locked (Optional[bool], optional): An indication if
                the logical table size of a table is locked or not. When a
                table’s logical size is locked, the table is excluded from the
                logical table size calculation when a schema update is
                performed. Defaults to None.
            primary_data_source (Optional[SchemaObjectReference], optional):
                Table's data can be from different data sources. Primary data
                source is the first option for table's data source. Defaults to
                None.
            secondary_data_sources (Optional[List[SchemaObjectReference] |
                List[dict]], optional): MicroStrategy support mapping the table
                to more than one data source. This attribute is a list of object
                representations of a reference to a datasource. Defaults to None
            physical_table_object_name (Optional[str], optional): A new name of
                an object (on MSTR server) that represents a physical table
                mapped to the logical table. Defaults to None.
            physical_table_name (Optional[str], optional): A new name of a
                physical table mapped to the logical table. Defaults to None.
            physical_table_prefix (Optional[str], optional): A new prefix for a
                physical table mapped to the logical table. Defaults to None.
            sql_statement (Optional[str], optional): A new SQL statement for
                physical table mapped to the logical table. Defaults to None.
            enclose_sql_in_parentheses(Optional[bool], optional): This encloses
                the entire SQL that you typed in the sqlStatement field
                in parentheses when the SQL statement is executed.
            columns (Optional[List[TableColumn] | List[dict]], optional):
                A list of new columns of a physical table mapped to the logical
                table. Defaults to None.
            folder_id (Optional[str], optional): The ID of a folder to which a
                logical  table should be moved. Defaults to None.

            Throws:
                TypeError if:
                    - Attempting to alter a logical table when it depends upon a
                        physical table which type is "Warehouse Partition Table"
                    - Attempting to alter `physical_table_name` or
                        `physical_table_prefix` when the logical table depends
                        upon a freeform sql physical table.
                    - Attempting to alter `sql_statement` or columns when the
                        logical table depends upon a normal physical table.

            Examples:
                >>> LogicalTable(connection,
                                 id='FF529E1446BE3DF75ECD4B8E18618747').alter(
                                     name="Altered Name"
                                 )
        """
        self.__validate_physical_table_type()
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        physical_table_type = self.physical_table.table_type
        if physical_table_type == PhysicalTableType.NORMAL and (sql_statement or columns):
            exception_handler(
                msg=(
                    "You cannot change `sql_statement` nor `columns` attributes when a logical"
                    " table depends upon a normal physical table."
                ),
                exception_type=TypeError,
            )
        elif physical_table_type == PhysicalTableType.SQL and (physical_table_prefix
                                                               or physical_table_name):
            exception_handler(
                msg=(
                    "You cannot change `physical_table_name` nor `physical_table_prefix` when"
                    "a logical table depends upon a freeform sql physical table."
                ),
                exception_type=TypeError,
            )

        physical_table = (
            {
                "information": {
                    "name": properties.pop("physical_table_object_name")
                }
            } if properties.get("physical_table_object_name") else {}
        )
        physical_table.update(
            {
                "table_prefix": properties.pop("physical_table_prefix", None),
                "table_name": properties.pop("physical_table_name", None),
                "sql_statement": properties.pop("sql_statement", None),
                "columns": properties.pop("columns", None),
            }
        )
        properties["physical_table"] = delete_none_values(physical_table, recursion=True)

        self._alter_properties(**properties)

    def update_physical_table_structure(
        self, col_merge_option: TableColumnMergeOption | str
    ) -> None:
        """Updates a structure of a physical table upon which the logical table
           depends.

        Args:
            col_merge_option (TableColumnMergeOption | str): A new
                structure for a physical table upon which the logical table
                depends.

        Throws:
            TypeError: Attempting to update a structure of a physical table
                which type is "Warehouse Partition Table"

        Examples:
            >>> LogicalTable(connection,
                             id='FF529E1446BE3DF75ECD4B8E18618747')
                             .update_physical_table_structure(
                                 TableColumnMergeOption.REUSE_ANY
                             )
        """
        self.__validate_physical_table_type()
        col_merge_option = get_enum_val(col_merge_option, TableColumnMergeOption)

        res = tables_api.patch_table(
            connection=self.connection,
            id=self.id,
            body=None,
            column_merge_option=col_merge_option,
        )
        if res.ok:
            data = res.json().get("physicalTable")
            logger.info(
                f"Successfully modified a structure of a physical table '{data.get('tableName')}' "
                f"with ID: '{data.get('information').get('objectId')}' "
                f"in a '{data.get('namespace')}' namespace "
                f"with a '{data.get('tablePrefix')}' table prefix."
            )

    @classmethod
    def update_physical_table_structure_for_all_tables(
        cls,
        connection: "Connection",
        col_merge_option: TableColumnMergeOption | str,
    ):
        """Updates structure for every table in a project mapped to a
           connection.

        Args:
            connection (Connection): Object representation of MSTR Connection.
            col_merge_option (TableColumnMergeOption | str): A new
                structure for a physical table upon which the logical table
                depends.
        """
        col_merge_option = get_enum(col_merge_option, TableColumnMergeOption)
        logical_tables = list_logical_tables(connection)
        with tqdm(total=len(logical_tables), desc="Updating structures...") as progress_bar:
            for table in logical_tables:
                if (table.physical_table.table_type != PhysicalTableType.WAREHOUSE_PARTITION):
                    table.update_physical_table_structure(col_merge_option=col_merge_option)
                progress_bar.update()

    def __validate_physical_table_type(self) -> bool:
        """Validates whether a table can be modified by checking if a physical
            table type upon which the logical table depends is
            "Warehouse Partition Table"

        Returns:
            bool: True if the type of a physical table is not
                "Warehouse Partition Table", else False
        """
        if self.physical_table.table_type == PhysicalTableType.WAREHOUSE_PARTITION:
            exception_handler(
                msg="Warehouse Partition tables cannot be edited.",
                exception_type=TypeError,
            )
        return True

    def list_columns(self, to_dictionary: bool = False):
        """Lists columns of the table in a dictionary or objects form

        Args:
        to_dictionary (bool): specifies whether to list the columns as
            dictionaries or objects. Defaults to False

        Returns:
            A list of columns as dictionaries or objects, depending on input"""
        if to_dictionary:
            return [column.to_dict() for column in self.physical_table.columns]
        return self.physical_table.columns
