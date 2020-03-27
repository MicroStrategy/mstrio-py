from tqdm.auto import tqdm
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

from mstrio.api import cubes
from mstrio.api import datasets
from mstrio.utils.parser import Parser
from mstrio.utils.filter import Filter
import mstrio.utils.helper as helper


class Cube:
    """
    Access, filter, publish, and extract data from MicroStrategy in-memory cubes.

    Create a Cube object to load basic information on a cube dataset. Specify subset of cube
    to be fetched through Cube.apply_filters() and Cube.clear_filters(). Fetch dataset through
    Cube.to_dataframe() method.

    Attributes:
        connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
        cube_id: Identifier of a pre-existing cube containing the required data.
        parallel (bool, optional): If True (default), utilize optimal number of threads to
            increase the download speed. If False, this feature will be disabled.
        progress_bar(bool, optional): If True (default), show the download progress bar.

    """

    def __init__(self, connection, cube_id, parallel=True, progress_bar=True):
        """Initialize an instance of a cube.

        Args:
            connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
            cube_id (str): Identifier of a pre-existing cube containing the required data.
            parallel (bool, optional): If True (default), utilize optimal number of threads to
                increase the download speed. If False, this feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download progress bar.

        """

        self._connection = connection
        self._cube_id = cube_id
        self.parallel = parallel
        self.progress_bar = progress_bar
        self._size_limit = 10000000      # this sets desired chunk size in bytes
        self._initial_limit = 1000     # initial limit for the cube_instance request


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

    def to_dataframe(self, limit=None, multi_df=False):
        """Extract contents of a cube into a Pandas Data Frame. Previously `microstrategy.Connection.get_cube()`.

        Args:
            limit (None or int, optional): Used to control data extract behavior. By default (None)
                the limit is calculated automatically, based on an optimized physical size of one
                chunk. Setting limit manually will force the number of rows per chunk. Depending on
                system resources, a higher limit (e.g. 50,000) may reduce the total time required
                to extract the entire dataset.
            multi_df (bool, optional): If True, return a list of data frames resembling the table
                structure of the cube. If False (default), returns one data frame.

        Returns:
            Pandas Data Frame containing the cube contents
        """
        inst_pbar = tqdm(desc='Initializing an instance of a cube. Please wait...',
                         bar_format='{desc}', leave=False, ncols=280, disable=(not self.progress_bar))
        if limit:
            self._initial_limit = limit

        # Request a new instance, set instance id
        res = cubes.cube_instance(connection=self._connection,
                                  cube_id=self._cube_id,
                                  body=self._filter.filter_body(),
                                  offset=self.__OFFSET,
                                  limit=self._initial_limit)
        inst_pbar.close()

        # Gets the pagination totals and instance_id from the response object
        _instance = res.json()
        _instance_id = _instance['instanceId']
        _pagination = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=_instance, parse_cube=True)
        p.parse(response=_instance)

        # If there are more rows to fetch, fetch them
        if _pagination['current'] != _pagination['total']:
            if not limit:
                limit = max(1000, int((self._initial_limit * self._size_limit) / len(res.content)))
            # Count the number of additional iterations
            it_total = int((_pagination['total']-self._initial_limit)/limit) + ((_pagination['total']-self._initial_limit) % limit != 0)

            if self.parallel and it_total > 1:
                threads = helper.get_parallel_number(it_total)
                with FuturesSession(executor=ThreadPoolExecutor(max_workers=threads)) as session:
                    fetch_pbar = tqdm(desc="Downloading", total=it_total+1, disable=(not self.progress_bar))
                    future = self.__fetch_chunks_future(session, _pagination, _instance_id, limit)
                    fetch_pbar.update()
                    for i, f in enumerate(future, start=1):
                        response = f.result()
                        if not response.ok:
                            current_offset = self._initial_limit+(i-1)*limit
                            response = cubes.cube_instance_id(connection=self._connection, cube_id=self._cube_id,
                                                              instance_id=_instance_id, offset=current_offset,
                                                              limit=limit)
                        fetch_pbar.update()
                        fetch_pbar.set_postfix(rows=str(min(self._initial_limit+i*limit, _pagination['total'])))
                        p.parse(response.json())
                    fetch_pbar.close()
            else:
                self.__fetch_chunks(p, _pagination, it_total, _instance_id, limit)

        # return parsed data as a data frame
        self._dataframe = p.dataframe
        # split dataframe to dataframes matching tables in Cube
        if multi_df:
            # save the multitable_definition response to the instance
            self.__multitable_definition()
            # split dataframe to dataframes matching tables in Cube
            self._dataframes = [self._dataframe[columns].copy() for _, columns in self._table_definition.items()]
            return self._dataframes
        else:
            return self._dataframe

    def __fetch_chunks_future(self, session, pagination, instance_id, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [cubes.cube_instance_id_coroutine(session, connection=self._connection,
                                                 cube_id=self._cube_id,
                                                 instance_id=instance_id,
                                                 offset=_offset,
                                                 limit=limit)
                for _offset in range(self._initial_limit, pagination['total'], limit)]

    def __fetch_chunks(self, parser, pagination, it_total, instance_id, limit):

        # Fetch add'l rows from this object instance from the intelligence server
        with tqdm(desc="Downloading", total=it_total+1, disable=(not self.progress_bar)) as fetch_pbar:
            fetch_pbar.update()
            for _offset in range(self._initial_limit, pagination['total'], limit):
                response = cubes.cube_instance_id(connection=self._connection,
                                                  cube_id=self._cube_id,
                                                  instance_id=instance_id,
                                                  offset=_offset,
                                                  limit=limit)
                fetch_pbar.update()
                fetch_pbar.set_postfix(rows=str(min(_offset+limit, pagination['total'])))
                parser.parse(response=response.json())

    def apply_filters(self, attributes=None, metrics=None, attr_elements=None):
        """Apply filters on the cube data so only the chosen attributes, metrics, and attribute elements are retrieved
        from the Intelligence Server.

        Args:
            attributes (list or None, optional): ids of attributes to be included in the filter.
                If list is empty, no attributes will be selected and metric data will be aggregated.
            metrics (list or None, optional): ids of metrics to be included in the filter.
                If list is empty, no metrics will be selected.
            attr_elements (list or None, optional): attributes' elements to be included in the filter.
        """
        if not all(element is None for element in [attributes, metrics, attr_elements]):
            if attr_elements:
                self.attr_elements

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
        """Return all tables names and columns as a dictionary"""

        res_tables = datasets.dataset_definition(connection=self._connection,
                                                 dataset_id=self._cube_id,
                                                 fields=['tables', 'columns'])
        _ds_definition = res_tables.json()

        for table in _ds_definition['result']['definition']['availableObjects']['tables']:
            column_list = [column['columnName']
                           for column in _ds_definition['result']['definition']['availableObjects']['columns']
                           if table['name'] == column['tableName']]
            self._table_definition[table['name']] = column_list

    def __info(self):
        """Get metadata for specific cubes. Implements GET /cubes to retrieve basic metadata."""

        res = cubes.cube_info(connection=self._connection, cube_id=self._cube_id)

        _info = res.json()["cubesInfos"][0]
        self._name = _info["cubeName"]
        self._owner_id = _info["ownerId"]
        self._path = _info["path"]
        self._last_modified = _info["modificationTime"]
        self._server_mode = _info["serverMode"]
        self._size = _info["size"]
        self._status = _info["status"]

    def __definition(self):
        """Get the definition of a cube, including attributes and metrics. Implements GET /v2/cubes/<cube_id>."""

        res = cubes.cube_definition(connection=self._connection, cube_id=self._cube_id)

        _definition = res.json()
        full_attributes = _definition["definition"]["availableObjects"]["attributes"]
        full_metrics = _definition["definition"]["availableObjects"]["metrics"]
        self._attributes = [{'name': attr['name'], 'id': attr['id']} for attr in full_attributes]
        self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

    def __get_attr_elements(self, limit=200000):
        """Get elements of report attributes synchronously. Implements GET /reports/<report_id>/attributes/<attribute_id>/elements"""

        attr_elements = []
        if self._attributes is not None:
            pbar = tqdm(self._attributes, desc="Loading attribute elements", leave=False, disable=(not self.progress_bar))
            # Fetch first chunk of attribute elements.
            for i, attr in enumerate(pbar):
                # Fetch first chunk of attribute elements.
                response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                cube_id=self._cube_id,
                                                                attribute_id=attr['id'],
                                                                offset=self.__OFFSET,
                                                                limit=limit)
                # Get total number of rows from headers.
                total = int(response.headers['x-mstr-total-count'])
                # Get attribute elements from the response.
                elements = response.json()

                # If total number of elements is bigger than the chunk size (limit), fetch them incrementally.
                for _offset in range(limit, total, limit):
                    response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                    cube_id=self._cube_id,
                                                                    attribute_id=attr['id'],
                                                                    offset=_offset,
                                                                    limit=limit)
                    elements.extend(response.json())

                # Append attribute data to the list of attributes.
                attr_elements.append({"attribute_name": attr['name'],
                                      "attribute_id": attr['id'],
                                      "elements": elements})
            pbar.close()

        return attr_elements

    def __get_attr_elements_async(self, limit=200000):
        """Get attribute elements. Implements GET /cubes/<cube_id>/attributes/<attribute_id>/elements"""

        attr_elements = []
        if self._attributes is not None:
            threads = helper.get_parallel_number(len(self._attributes))
            with FuturesSession(executor=ThreadPoolExecutor(max_workers=threads)) as session:
                # Fetch first chunk of attribute elements.
                futures = self.__fetch_attribute_elements_chunks(session, limit)
                pbar = tqdm(futures, desc="Loading attribute elements", leave=False, disable=(not self.progress_bar))
                for i, future in enumerate(pbar):
                    attr = self.attributes[i]
                    response = future.result()
                    if not response.ok:
                        response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                        cube_id=self._cube_id,
                                                                        attribute_id=attr["id"],
                                                                        offset=0,
                                                                        limit=limit)
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                        cube_id=self._cube_id,
                                                                        attribute_id=attr["id"],
                                                                        offset=_offset,
                                                                        limit=limit)
                        elements.extend(response.json())
                    # Append attribute data to the list of attributes.
                    attr_elements.append({"attribute_name": attr['name'],
                                          "attribute_id": attr['id'],
                                          "elements": elements})
                pbar.close()

            return attr_elements

    def __fetch_attribute_elements_chunks(self, session, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [cubes.cube_single_attribute_elements_coroutine(session,
                                                               connection=self._connection,
                                                               cube_id=self._cube_id,
                                                               attribute_id=attribute['id'],
                                                               offset=0,
                                                               limit=limit)
                for attribute in self._attributes]

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
        if not self._attr_elements:
            if self.parallel is True:
                self._attr_elements = self.__get_attr_elements_async()
            else:
                self._attr_elements = self.__get_attr_elements()
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
            helper.exception_handler(msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                                     exception_type=Warning, throw_error=False)
        return self._dataframe

    @property
    def dataframes(self):
        if len(self._dataframes) == 0:
            helper.exception_handler(msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                                     exception_type=Warning, throw_error=False)
        return self._dataframes

    @property
    def table_definition(self):
        return self._table_definition
