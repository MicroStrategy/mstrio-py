import pandas as pd
import datetime as dt
from collections import defaultdict


class Model:
    """Internal utility for generating the definition of multi-table and
    single-table datasets.

    Create the definition of a super cube containing one or more tables. The
    definition includes the name and description of the super cube and the name
    and description of each table, attribute, and metric within the super cube.

    Attributes:
    """

    # dictionary key names
    _KEY_TABLE_NAME = 'table_name'
    _KEY_DATA_FRAME = 'data_frame'
    _KEY_AS_ATTR = 'to_attribute'
    _KEY_AS_METR = 'to_metric'
    _KEY_UPDATE_POL = 'update_policy'
    _KEY_TABLES = [_KEY_TABLE_NAME, _KEY_DATA_FRAME, _KEY_AS_ATTR, _KEY_AS_METR]

    _MAX_DESC_LEN = 250

    _INVALID_CHARS = [
        '\\',
        '"',
        '[',
        ']',
    ]  # check for invalid characters in column names

    def __init__(
        self,
        tables,
        name,
        description=None,
        folder_id=None,
        ignore_special_chars=False,
        attr_forms_mapping=None,
    ):
        """Initializes Model with tables, a name, and an optional description.

        Args:
            tables (list of dicts): List of one or more dictionaries with keys
                `table_name`, `data_frame`, and optionally `as_attribute` and
                `as_metric`. Note that `as_attribute` and `as_metric` should be
                used when the default Python data type (e.g. `int`) should be
                converted to an attribute instead of a metric in MicroStrategy.
            name (str): Name of the data set.
            description (str, optional): Description of the data set. Must be
                less than or equal to 250 characters.
            folder_id (str, optional): ID of the shared folder that the super
                cube should be created within. If `None`, defaults to the user's
                My Reports folder.
        """

        self._ignore_special_chars = ignore_special_chars

        # check integrity of tables list
        self._check_table_list(tables=tables)

        # check super cube name params
        self._name = name
        self._check_param_str(self._name, msg="SuperCube name should be a string.")
        self._check_param_len(
            self._name,
            msg=f"SuperCube name should be <= {self._MAX_DESC_LEN} characters.",
            max_length=self._MAX_DESC_LEN,
        )
        self._check_param_inv_chars(
            self._name,
            msg="SuperCube name cannot contain '{}', '{}', '{}', '{}'.".format(
                *self._INVALID_CHARS
            ),
            invalid_chars=self._INVALID_CHARS,
        )

        # check super cube description params
        if description is None:
            self._description = ""
        else:
            self._description = description
            self._check_param_str(
                self._description, msg="SuperCube description should be a string."
            )
            self._check_param_len(
                self._description,
                msg=(
                    f"SuperCube description should be <= {self._MAX_DESC_LEN}"
                    " characters."
                ),
                max_length=self._MAX_DESC_LEN,
            )

        # check folder_id param
        self._folder_id = folder_id or ''

        # init lists to accumulate table, attr, metric definitions and model
        self._tables = []
        self._attributes = []
        self._metrics = []
        self._model = None

        forms_mapping = attr_forms_mapping or []
        # build the model
        self._build(tables=tables, forms_mapping=forms_mapping)

    def get_model(self):
        """Return the model object."""
        return self._model

    def _build(self, tables, forms_mapping):
        """Generates the data model by mapping attributes and metrics from list
        of tables."""

        table2columns_used = self._add_user_defined_attribute_forms(forms_mapping)

        # Map tables one by one
        for table in tables:
            mapped_columns = table2columns_used[table['table_name']]
            self._map_table(table, mapped_columns)

        # set model object
        self._model = {
            'name': self._name,
            'description': self._description,
            'folderId': self._folder_id,
            'tables': self._tables,
            'metrics': self._metrics,
            'attributes': self._attributes,
        }

    def _add_user_defined_attribute_forms(self, forms_mapping):
        table2columns_used = defaultdict(set)

        for attr in forms_mapping:
            self._attributes.append(attr.to_dict())
            for form in attr.forms:
                for expr in form.expressions:
                    table2columns_used[expr.table].add(expr.column)

        return table2columns_used

    def _map_table(self, table, skip_columns):
        df = table[self._KEY_DATA_FRAME]

        # map column names and column types
        col_names = self._get_col_names(df)
        col_types = self._get_col_types(df)
        table_name = table[self._KEY_TABLE_NAME]

        # map tables
        self._add_table(name=table_name, col_names=col_names, col_types=col_types)

        # map attributes and metrics
        for name, column_type in zip(col_names, col_types):
            if name in skip_columns:
                continue

            if name in table.get(self._KEY_AS_ATTR, []):
                self._add_attribute(name, table_name)
            elif name in table.get(self._KEY_AS_METR, []) or self._is_metric(
                column_type
            ):
                self._add_metric(name, table_name)
            else:
                self._add_attribute(name, table_name)

    def _get_col_types(self, table):
        """Map column types from each column in the list of table."""
        list_dtypes_values = list(table.dtypes.values)

        for i in range(len(table.columns)):
            if list_dtypes_values[i] == 'object' and isinstance(
                table.columns[i][0], dt.time
            ):
                list_dtypes_values[i] = 'time'

        return [self._map_data_type(datatype) for datatype in list_dtypes_values]

    def _add_metric(self, name, table_name):
        """Add a metric to a metric list instance."""
        self._metrics.append(
            {
                'name': name,
                'expressions': [{'tableName': table_name, 'columnName': name}],
            }
        )

    def _add_attribute(self, name, table_name):
        """Add an attribute to an attribute list instance."""
        self._attributes.append(
            {
                'name': name,
                'attributeForms': [
                    {
                        'category': 'ID',
                        'expressions': [{'tableName': table_name, 'columnName': name}],
                    }
                ],
            }
        )

    def _add_table(self, name, col_names, col_types):
        """Add a table to a table list instance."""
        self._tables.append(
            {
                'name': name,
                'columnHeaders': [
                    {'name': name, 'dataType': typ}
                    for name, typ in zip(col_names, col_types)
                ],
            }
        )

    def _check_table_list(self, tables):
        """Check integrity of table list parameter."""

        # tables must be a list
        if not isinstance(tables, list):
            raise TypeError("Elements of tables must be a list of dicts.")

        # tables cannot be length 0
        if len(tables) == 0:
            raise ValueError("No tables have been added to the super cube.")

        # check integrity of each table passed to tables
        for table in tables:
            self._check_table(table)

    def _check_table(self, table):
        """Check integrity of table parameter."""

        # force all list elements to be a dict with specific names
        table_keys_list = "', '".join(self._KEY_TABLES)
        msg = f"Each table must be a dictionary with keys: '{table_keys_list}'."

        if not isinstance(table, dict):
            raise TypeError(msg)

        if not all(k in table for k in (self._KEY_TABLE_NAME, self._KEY_DATA_FRAME)):
            raise ValueError(msg)

        # check that the value of the data frame key is a pandas data frame
        if not isinstance(table[self._KEY_DATA_FRAME], pd.DataFrame):
            msg = (
                "Pandas DataFrame must be passed as the value in the "
                f"'{self._KEY_DATA_FRAME}' key."
            )
            raise TypeError(msg)

        # check for presence of invalid characters in data frame column names
        if not self._ignore_special_chars and any(
            [
                col
                for col in table[self._KEY_DATA_FRAME].columns
                for inv in self._INVALID_CHARS
                if inv in col
            ]
        ):
            msg = "Column names cannot contain '{}', '{}', '{}', '{}'".format(
                *self._INVALID_CHARS
            )
            raise ValueError(msg)

    @staticmethod
    def _get_col_names(table):
        """Returns column names from a table as a list."""
        return list(table.columns)

    @staticmethod
    def _map_data_type(datatype):
        """Maps a Python data type to a MicroStrategy data type."""
        return {
            'object': 'STRING',
            'int32': 'INTEGER',
            'int64': 'BIGINTEGER',
            'float32': 'DOUBLE',
            'float64': 'DOUBLE',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'DATETIME',
            'time': 'TIME',
        }.get(str(datatype))

    @staticmethod
    def _check_param_len(param, msg, max_length):
        if len(param) > max_length:
            raise ValueError(msg)

        return True

    @staticmethod
    def _check_param_str(param, msg):
        if not isinstance(param, str):
            raise TypeError(msg)

        return True

    @staticmethod
    def _check_param_inv_chars(param, msg, invalid_chars):
        if any(inv for inv in invalid_chars if inv in param):
            raise ValueError(msg)

    @staticmethod
    def _is_metric(datatype):
        """Helper function for determining if the requested datatype is (by
        default) a metric or attribute."""
        return datatype in ['DOUBLE', 'INTEGER', 'BIGINTEGER', 'BIGDECIMAL']

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def folder_id(self):
        return self._folder_id

    @property
    def tables(self):
        return self._tables

    @property
    def attributes(self):
        return self._attributes

    @property
    def metrics(self):
        return self._metrics
