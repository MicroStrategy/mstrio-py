import logging
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.modeling.data_model.data_model_component import DataModelComponent
from mstrio.modeling.data_model.helpers import unpack_information_dict
from mstrio.utils.helper import delete_none_values
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.modeling.data_model.data_model import DataModel

logger = logging.getLogger(__name__)


@method_version_handler('11.6.0100')
def list_data_model_tables(
    connection: Connection,
    data_model: 'DataModel | str',
    to_dictionary: bool = False,
    limit: int | None = None,
    offset: int | None = None,
    fields: str | None = None,
    show_expression_as: str | None = None,
    show_derived_columns: bool | None = None,
    show_derived_forms: bool | None = None,
    show_relationship_candidates: bool | None = None,
    changeset_id: str | None = None,
) -> list['DataModelTable'] | list[dict]:
    """Get a list of tables of a Mosaic data model.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        data_model (DataModel | str): data model object or its ID
        to_dictionary (bool, optional): if True, return tables as
            a list of dicts
        limit (int, optional): limit the number of elements returned
        offset (int, optional): starting point within the collection
        fields (str, optional): comma-separated top-level field whitelist
        show_expression_as (str, optional): specify how expressions are
            presented ('tree' or 'tokens')
        show_derived_columns (bool, optional): whether to show derived columns
        show_derived_forms (bool, optional): whether to show derived forms
        show_relationship_candidates (bool, optional): whether to show
            relationship candidates
        changeset_id (str, optional): ID of an existing changeset to read from

    Returns:
        A list of DataModelTable objects or dictionaries representing them.
    """
    data_model_id = data_model if isinstance(data_model, str) else data_model.id
    tables = (
        data_models.list_data_model_tables(
            connection,
            id=data_model_id,
            changeset_id=changeset_id,
            offset=offset,
            limit=limit,
            fields=fields,
            show_expression_as=show_expression_as,
            show_derived_columns=show_derived_columns,
            show_derived_forms=show_derived_forms,
            show_relationship_candidates=show_relationship_candidates,
        )
        .json()
        .get('tables', [])
    )
    if limit:
        tables = tables[:limit]
    if to_dictionary:
        return [unpack_information_dict(table) for table in tables]
    return [
        DataModelTable._from_api_source(connection, data_model_id, table)
        for table in tables
    ]


@class_version_handler('11.6.0100')
class DataModelTable(DataModelComponent):
    """Python representation of a logical table of a Mosaic data model."""

    _ACL_SUBTYPE = 'logical_table'
    _GET_FUNC = staticmethod(data_models.get_data_model_table)
    _DELETE_FUNC = staticmethod(data_models.delete_data_model_table)
    _ID_KWARG = 'table_id'

    @classmethod
    def create(
        cls,
        connection: Connection,
        data_model: 'DataModel | str',
        name: str,
        physical_table: dict,
        description: str | None = None,
        definition: dict | None = None,
        fields: str | None = None,
        show_derived_columns: bool | None = None,
        show_derived_forms: bool | None = None,
    ) -> 'DataModelTable':
        """Add a new logical table to a Mosaic data model.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            data_model (DataModel | str): data model object or its ID
            name (str): name of the table
            physical_table (dict): physical table definition. Three `type`
                variants are supported:
                - `warehouse_partition_table`: `{'type':
                  'warehouse_partition_table', 'namespace': ..., 'tableName':
                  ..., 'databaseInstance': {'objectId': ...}}`
                - `pipeline`: table backed by a data-server pipeline
                - `freeform_sql`: `{'type': 'freeform_sql', 'sqlStatement':
                  ..., 'columns': [...]}`
            description (str, optional): description of the table
            definition (dict, optional): additional top-level body keys of the
                `ms-DataModelTableAdd` schema, merged into the request body
                (e.g. `primaryDataSource`)
            fields (str, optional): comma-separated top-level field whitelist
            show_derived_columns (bool, optional): whether to show derived
                columns in the response
            show_derived_forms (bool, optional): whether to show derived forms
                in the response

        Note:
            Publish silently no-ops when physical-table columns carry
            warehouse-catalog sentinel dataTypes (e.g. `variable_length_string`
            with precision -1, or decimal with scale -MIN_INT). Replace such
            sentinel values with real precisions/scales before creating the
            table, otherwise `DataModel.publish` will report success without
            loading any data.

        Returns:
            DataModelTable object.
        """
        data_model_id = data_model if isinstance(data_model, str) else data_model.id
        body = {
            'name': name,
            'description': description,
            'physicalTable': physical_table,
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.create_data_model_table(
            connection,
            id=data_model_id,
            body=body,
            fields=fields,
            show_derived_columns=show_derived_columns,
            show_derived_forms=show_derived_forms,
        ).json()
        if config.verbose:
            logger.info(
                f"Successfully created table named: '{name}' with ID: '"
                f"{response.get('id')}' in data model '{data_model_id}'."
            )
        return cls._from_api_source(connection, data_model_id, response)

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        physical_table: dict | None = None,
        definition: dict | None = None,
    ) -> None:
        """Alter the table (partial update via PATCH).

        Args:
            name (str, optional): new name of the table
            description (str, optional): new description of the table
            physical_table (dict, optional): new physical table definition
            definition (dict, optional): additional top-level body keys merged
                into the request body
        """
        body = {
            'name': name,
            'description': description,
            'physicalTable': physical_table,
            **(definition or {}),
        }
        body = delete_none_values(body, recursion=False)
        response = data_models.update_data_model_table(
            self.connection, id=self.data_model_id, table_id=self.id, body=body
        )
        self._set_object_attributes(**unpack_information_dict(response.json()))
        if config.verbose:
            logger.info(
                f"Successfully altered table with ID: '{self.id}' in data "
                f"model '{self.data_model_id}'."
            )
