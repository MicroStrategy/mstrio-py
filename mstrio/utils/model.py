import pandas as pd


class Model(object):
    """Internal utility for generating the definition of multi-table and single-table datasets.

    Create the definition of a dataset containing one or more tables. The definition includes the name and description
    of the dataset and the name and description of each table, attribute, and metric within the dataset.

    Attributes:

    """

    # dictionary key names
    _KEY_TABLE_NAME = 'table_name'
    _KEY_DATA_FRAME = 'data_frame'
    _KEY_AS_ATTR = 'to_attribute'
    _KEY_AS_METR = 'to_metric'
    _KEY_UPDATE_POL = 'update_policy'
    _KEY_TABLES = [_KEY_TABLE_NAME, _KEY_DATA_FRAME, _KEY_AS_ATTR, _KEY_AS_METR]

    __MAX_DESC_LEN = 250

    _INVALID_CHARS = ['\\', '"', '[', ']']  # check for invalid characters in column names

    def __init__(self, tables, name, description=None, folder_id=None, ignore_special_chars=False):
        """Initializes Model with tables, a name, and an optional description.

        Args:
            tables (:obj:`list` of :obj:`dict`): List of one or more dictionaries with keys `table_name`, `data_frame`,
                and optionally `as_attribute` and `as_metric`. Note that `as_attribute` and `as_metric` should be used
                when the default Python data type (e.g. `int`) should be converted to an attribute instead of a metric
                in MicroStrategy.
            name (str): Name of the data set.
            description (str, optional): Description of the data set. Must be less than or equal to 250 characters.
            folder_id (str, optional): ID of the shared folder that the dataset should be created within. If `None`,
                defaults to the user's My Reports folder.

        """

        self.__ignore_special_chars = ignore_special_chars

        # check integrity of tables list
        self.__check_table_list(tables=tables)

        # check dataset name params
        self.__name = name
        self.__check_param_str(self.__name, msg="Dataset name should be a string.")
        self.__check_param_len(self.__name,
                               msg="Dataset name should be <= {} characters.".format(self.__MAX_DESC_LEN),
                               max_length=self.__MAX_DESC_LEN)
        self.__check_param_inv_chars(self.__name,
                                     msg="Dataset name cannot contain '{}', '{}', '{}', '{}'."
                                     .format(*self._INVALID_CHARS),
                                     invalid_chars=self._INVALID_CHARS)

        # check dataset description params
        if description is None:
            self.__description = ""
        else:
            self.__description = description
            self.__check_param_str(self.__description, msg="Dataset description should be a string.")
            self.__check_param_len(self.__description,
                                   msg="Dataset description should be <= {} characters.".format(self.__MAX_DESC_LEN),
                                   max_length=self.__MAX_DESC_LEN)

        # check folder_id param
        if folder_id is None:
            self._folder_id = ""
        else:
            self._folder_id = folder_id

        # init lists to accumulate table, attr, metric definitions and model object
        self.__tables = []
        self.__attributes = []
        self.__metrics = []
        self.__model = None

        # build the model
        self.__build(tables=tables)

    def get_model(self):
        """Return the model object."""
        return self.__model

    def __build(self, tables):
        """Generates the data model by mapping attributes and metrics from list of tables."""

        for table in tables:

            # map column names and column types
            _col_names = self.__get_col_names(table[self._KEY_DATA_FRAME])
            _col_types = self.__get_col_types(table[self._KEY_DATA_FRAME])

            # map tables
            self.__add_table(name=table[self._KEY_TABLE_NAME], col_names=_col_names, col_types=_col_types)

            # map attributes and metrics
            for _name, _type in zip(_col_names, _col_types):

                if self.__is_metric(_type):
                    if self._KEY_AS_ATTR in table.keys() and _name in table[self._KEY_AS_ATTR]:
                        self.__add_attribute(_name, table[self._KEY_TABLE_NAME])
                    else:
                        self.__add_metric(_name, table[self._KEY_TABLE_NAME])

                else:
                    if self._KEY_AS_METR in table.keys() and _name in table[self._KEY_AS_METR]:
                        self.__add_metric(_name, table[self._KEY_TABLE_NAME])
                    else:
                        self.__add_attribute(_name, table[self._KEY_TABLE_NAME])

        # set model object
        self.__model = {"name": self.__name,
                        "description": self.__description,
                        "folderId": self._folder_id,
                        "tables": self.__tables,
                        "metrics": self.__metrics,
                        "attributes": self.__attributes}

    def __get_col_types(self, table):
        """Map column types from each column in the list of table."""
        return list(map(self.__map_data_type, list(table.dtypes.values)))

    def __add_metric(self, name, table_name):
        """Add a metric to a metric list instance."""
        self.__metrics.append({'name': name, 'expressions': [{'tableName': table_name, 'columnName': name}]})

    def __add_attribute(self, name, table_name):
        """Add an attribute to an attribute list instance."""
        self.__attributes.append({'name': name,
                                  'attributeForms': [{'category': 'ID',
                                                      'expressions': [{'tableName': table_name,
                                                                       'columnName': name}]}]})

    def __add_table(self, name, col_names, col_types):
        """Add a table to a table list instance."""
        self.__tables.append({'name': name,
                              'columnHeaders': [{'name': name, 'dataType': typ} for name, typ in
                                                zip(col_names, col_types)]})

    def __check_table_list(self, tables):
        """Check integrity of table list parameter."""

        # tables must be a list
        if not isinstance(tables, list):
            raise TypeError("Elements of tables must be a list of dicts.")

        # tables cannot be length 0
        if len(tables) == 0:
            raise ValueError("No tables have been added to the dataset.")

        # check integrity of each table passed to tables
        for table in tables:
            self.__check_table(table)

    def __check_table(self, table):
        """Check integrity of table parameter."""

        # force all list elements to be a dict with specific names
        msg = "Each table must be a dictionary with keys: '{}', '{}', '{},' and '{}'.".format(*self._KEY_TABLES)
        if not isinstance(table, dict):
            raise TypeError(msg)

        if not all(k in table.keys() for k in (self._KEY_TABLE_NAME, self._KEY_DATA_FRAME)):
            raise ValueError(msg)

        # check that the value of the data frame key is a pandas data frame
        if not isinstance(table[self._KEY_DATA_FRAME], pd.DataFrame):
            msg = "Pandas DataFrame must be passed as the value in the '{}' key.".format(self._KEY_DATA_FRAME)
            raise TypeError(msg)

        # check for presence of invalid characters in data frame column names
        if not self.__ignore_special_chars:
            if any([col for col in table[self._KEY_DATA_FRAME].columns for inv in self._INVALID_CHARS if inv in col]):
                msg = "Column names cannot contain '{}', '{}', '{}', '{}'".format(*self._INVALID_CHARS)
                raise ValueError(msg)

    @staticmethod
    def __get_col_names(table):
        """Returns column names from a table as a list."""
        return list(table.columns)

    @staticmethod
    def __map_data_type(datatype):
        """Maps a Python data type to a MicroStrategy data type."""
        if datatype == 'object':
            return "STRING"
        elif datatype in ['int64', 'int32']:
            return "INTEGER"
        elif datatype in ['float64', 'float32']:
            return "DOUBLE"
        elif datatype == 'bool':
            return "BOOLEAN"
        elif datatype == 'datetime64[ns]':
            return 'DATETIME'

    @staticmethod
    def __check_param_len(param, msg, max_length):
        if len(param) > max_length:
            raise ValueError(msg)
        else:
            return True

    @staticmethod
    def __check_param_str(param, msg):
        if not isinstance(param, str):
            raise TypeError(msg)
        else:
            return True

    @staticmethod
    def __check_param_inv_chars(param, msg, invalid_chars):
        if any([inv for inv in invalid_chars if inv in param]):
            raise ValueError(msg)

    @staticmethod
    def __is_metric(datatype):
        """Helper function for determining if the requested datatype is (by default) a metric or attribute."""
        if datatype in ["DOUBLE", "INTEGER"]:
            return True
        else:
            return False

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def folder_id(self):
        return self._folder_id

    @property
    def tables(self):
        return self.__tables

    @property
    def attributes(self):
        return self.__attributes

    @property
    def metrics(self):
        return self.__metrics
