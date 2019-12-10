import json
import warnings
import pandas as pd
from tqdm.auto import tqdm

from mstrio.api import cubes
from mstrio.api import datasets
from mstrio.utils.parsejson import parsejson
from mstrio.utils.filter import Filter


class Cube:
    """
    Access, filter, publish, and extract data from MicroStrategy in-memory cubes.

    Create a Cube object to load basic information on a cube dataset. Specify subset of cube
    to be fetched through Cube.apply_filters() and Cube.clear_filters(). Fetch dataset through
    Cube.to_dataframe() method.

    Attributes:
        connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
        cube_id: Identifier of a pre-existing cube containing the required data.
    """

    def __init__(self, connection, cube_id):
        """
        Initialize an instance of a cube.

        Args:
            connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
            cube_id (str): Identifier of a pre-existing cube containing the required data.
        """
        init_pbar = tqdm(desc='Initializing an instance of a cube. Please wait...', bar_format='{desc}', leave=False, ncols=280)

        self._connection = connection
        self._cube_id = cube_id

        # load dataset information
        self.__info()
        self.__definition()

        # load attribute elements
        self.__OFFSET = 0
        self._attr_elements = []

        self._filter = Filter(attributes=self._attributes, metrics=self._metrics, attr_elements=self._attr_elements)

        self._dataframe = None
        self._dataframes = []
        self._table_definition = {}
        init_pbar.close()

    def to_dataframe(self, limit=25000, progress_bar=True, multi_df=False):
        """
        Extract contents of a cube into a Pandas Data Frame. Previously `microstrategy.Connection.get_cube()`.

        Args:
            limit (int, optional): Used to control data extract behavior on datasets with a large number of rows.
                The default is 25000. As an example, if the dataset has 50,000 rows, get_cube() will incrementally
                extract all 50,000 rows in 1,000 row chunks. Depending on system resources, a higher limit (e.g. 10,000)
                may reduce the total time required to extract the entire dataset.
            progress_bar(bool, optional): If True (default), show the upload progress bar.
            multi_df (bool, optional): If True (default), return a list of df resembling the table structure of the cube. If False, returns one df.

        Returns:
            Pandas Data Frame containing the cube contents
        """
        inst_pbar = tqdm(desc='Connecting to MicroStrategy I-Server. Please wait...',
                         bar_format='{desc}', leave=False, ncols=310)

        # Request a new instance, set instance id
        res = cubes.cube_instance(connection=self._connection,
                                  cube_id=self._cube_id,
                                  body=self._filter.filter_body(),
                                  offset=self.__OFFSET,
                                  limit=limit)
        inst_pbar.close()
        if not res.ok:
            msg = "Error getting cube contents."
            self.__response_handler(response=res, msg=msg)
        else:
            _instance = res.json()
            _instance_id = _instance['instanceId']

            # Gets the pagination totals from the response object
            _pagination = _instance['result']['data']['paging']

            # If there are more rows to fetch, fetch them
            if _pagination['current'] != _pagination['total']:

                # initialize a list to capture slices from each query, and append the first request's result to the list
                table_data = [parsejson(response=_instance)]

                # Count the number of iterations
                it_total = int(_pagination['total']/limit)+(_pagination['total'] % limit != 0)

                # Fetch add'l rows from this object instance from the intelligence server
                with tqdm(total=it_total, disable=(not progress_bar)) as fetch_pbar:
                    if progress_bar:
                        fetch_pbar.update()
                        fetch_pbar.set_description("Downloading")
                        fetch_pbar.set_postfix(rows=limit)
                    for _offset in range(limit, _pagination['total'], limit):
                        if progress_bar:
                            fetch_pbar.update()
                            fetch_pbar.set_description("Downloading")
                            fetch_pbar.set_postfix(rows=min(_offset+limit, _pagination['total']))
                        response = cubes.cube_instance_id(connection=self._connection,
                                                          cube_id=self._cube_id,
                                                          instance_id=_instance_id,
                                                          offset=_offset,
                                                          limit=limit)
                        table_data.append(parsejson(response=response.json()))

                # concatenate and return the list of result data as a data frame
                self._dataframe = pd.concat(table_data).reset_index(drop=True)
            else:
                # otherwise parse the first result and return it as a dataframe
                self._dataframe = parsejson(response=_instance)
            
            if multi_df:
                # save the multitable_definition response to the instance
                self.__multitable_definition()

                # split dataframe to dataframes matching tables in Cube
                self._dataframes = [self._dataframe[columns].copy() for _, columns in self._table_definition.items()]

                return self._dataframes
            else:
                return self._dataframe

    def apply_filters(self, attributes=None, metrics=None, attr_elements=None):
        """
        Apply filters on the cube data so only the chosen attributes, metrics, and attribute elements are retrieved
        from the Intelligence Server.

        Args:
            attributes (list, optional): ids of attributes to be included in the filter.
            metrics (list, optional): ids of metrics to be included in the filter.
            attr_elements (list, optional): attributes' elements to be included in the filter.
        """
        if any([attributes, metrics, attr_elements]):
            if not self._attr_elements and attr_elements:
                self.__attr_elements()

            if self._attr_elements and not self._filter.attr_elems:
                self._filter = Filter(attributes=self._attributes, metrics=self._metrics,
                                      attr_elements=self._attr_elements)

            if attributes:
                self._filter.select(object_id=attributes)

            if attributes == []:
                self._filter.attr_selected = []

            if metrics:
                self._filter.select(object_id=metrics)

            if metrics == []:
                self._filter.metr_selected = []

            if attr_elements is not None:
                self._filter.select(object_id=attr_elements)

    def clear_filters(self):
        """Clear previously set filters, allowing all attributes, metrics, and attribute elements to be retrieved."""

        self._filter.clear()

    def __multitable_definition(self):
        """
        Return all tables names and collumns as a dictionary
        """
        res_tables = datasets.dataset_definition(connection=self._connection,
                                                 dataset_id=self._cube_id,
                                                 fields=['tables', 'columns'])
        _ds_definition = res_tables.json()

        for table in _ds_definition['result']['definition']['availableObjects']['tables']:
            _column_list = []
            for column in _ds_definition['result']['definition']['availableObjects']['columns']:
                if(table['name'] == column['tableName']):
                    _column_list.append(column['columnName'])
            self._table_definition[table['name']] = _column_list

    def __info(self):
        """Get metadata for specific cubes. Implements GET /cubes to retrieve basic metadata."""

        res = cubes.cube_info(connection=self._connection, cube_id=self._cube_id)

        if not res.ok:
            self.__response_handler(response=res, msg="Error getting cube metadata information. Check Cube ID.")
            return None
        else:
            _info = res.json()["cubesInfos"][0]
            self._name = _info["cubeName"]
            self._owner_id = _info["ownerId"]
            self._path = _info["path"]
            self._last_modified = _info["modificationTime"]
            self._server_mode = _info["serverMode"]
            self._size = _info["size"]
            self._status = _info["status"]

    def __definition(self):
        """Get the definition of a cube, including attributes and metrics. Implements GET /cubes/<cube_id>."""

        res = cubes.cube(connection=self._connection, cube_id=self._cube_id)

        if not res.ok:
            self.__response_handler(response=res, msg="Error getting cube definition. Check Cube ID.")
            return None
        else:
            _definition = res.json()
            full_attributes = _definition["result"]["definition"]["availableObjects"]["attributes"]
            full_metrics = _definition["result"]["definition"]["availableObjects"]["metrics"]
            self._attributes = [{'name': attr['name'], 'id': attr['id']} for attr in full_attributes]
            self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

    def __attr_elements(self, limit=25000, progress_bar=True):
        """Get attribute elements. Implements GET /cubes/<cube_id>/attributes/<attribute_id>/elements"""

        attr_elements = []
        if self._attributes is not None:
            with tqdm(total=len(self._attributes), disable=(not progress_bar)) as fetch_pbar:
                if progress_bar:
                    fetch_pbar.update()
                    fetch_pbar.set_description("Loading attribute elements")
                    fetch_pbar.set_postfix(rows=0)

                for i_attr, attr in enumerate(self._attributes):
                    if progress_bar:
                        fetch_pbar.update()
                        fetch_pbar.set_description("Loading attribute elements")
                        fetch_pbar.set_postfix(rows=i_attr)
                    # Fetch first chunk of attribute elements.
                    res = cubes.cube_single_attribute_elements(connection=self._connection,
                                                               cube_id=self._cube_id,
                                                               attribute_id=attr['id'],
                                                               offset=self.__OFFSET,
                                                               limit=limit)
                    if not res.ok:
                        msg = "Error retrieving attribute '" + attr['name'] + "' elements."
                        self.__response_handler(response=res, msg=msg)
                    else:
                        # Get total number of rows from headers.
                        total = int(res.headers['x-mstr-total-count'])
                        # Get attribute elements from the response.
                        elements = res.json()

                        # If total number of elements is bigger than the chunk size (limit), fetch them incrementally.
                        for _offset in range(limit, total, limit):
                            res = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                       cube_id=self._cube_id,
                                                                       attribute_id=attr['id'],
                                                                       offset=_offset,
                                                                       limit=limit)
                            elements.extend(res.json())

                        # Append attribute data to the list of attributes.
                        attr_elements.append({"attribute_name": attr['name'],
                                              "attribute_id": attr['id'],
                                              "elements": elements})

            self._attr_elements = attr_elements

    @staticmethod
    def __response_handler(response, msg):
        """Generic error message handler for transactions against datasets.

        Args:
            response: Response object returned by HTTP request.
            msg (str): Message to print in addition to any server-generated error message(s).

        """
        res = json.loads(response.content)
        print(msg)
        print("HTTP %i %s" % (response.status_code, response.reason))
        print("I-Server Error %s, %s" % (res['code'], res['message']))

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def status(self):
        return self._status

    @property
    def path(self):
        return self._path

    @property
    def last_modified(self):
        return self._last_modified

    @property
    def owner_id(self):
        return self._owner_id

    @property
    def attributes(self):
        return self._attributes

    @property
    def metrics(self):
        return self._metrics

    @property
    def attr_elements(self):
        return self._attr_elements

    @property
    def selected_attributes(self):
        return self._filter.attr_selected

    @property
    def selected_metrics(self):
        return self._filter.metr_selected

    @property
    def selected_attr_elements(self):
        return self._filter.attr_elem_selected

    @property
    def dataframe(self):
        if self._dataframe is None:
            warnings.warn("Dataframe looks empty. Make sure the data is valid (default join on i-Server is inner) and then retrieve with Cube.to_dataframe().", Warning, stacklevel=2)
        return self._dataframe

    @property
    def dataframes(self):
        if len(self._dataframes) == 0:
            warnings.warn("Dataframes look empty. Make sure the data is valid (default join on i-Server is inner) and then retrieve with Cube.to_dataframe().", Warning, stacklevel=2)
        return self._dataframes

    @property
    def table_definition(self):
        return self._table_definition
