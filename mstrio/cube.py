from operator import itemgetter

from tqdm.auto import tqdm
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
import requests

from mstrio.api import cubes
from mstrio.api import datasets
from mstrio.utils.parser import Parser
from mstrio.utils.filter import Filter
import mstrio.utils.helper as helper
from mstrio.dataset import Dataset


class Cube:
    """
    Access, filter, publish, and extract data from MicroStrategy in-memory cubes.

    Create a Cube object to load basic information on a cube dataset. Specify subset of cube
    to be fetched through Cube.apply_filters() and Cube.clear_filters(). Fetch dataset through
    Cube.to_dataframe() method.

    Attributes:
        connection: MicroStrategy connection object returned by `connection.Connection()`.
        cube_id: Identifier of a pre-existing cube containing the required data.
        instance_id (str): Identifier of an instance if cube instance has been already initialized,
                NULL by default.
        parallel (bool, optional): If True (default), utilize optimal number of threads to
            increase the download speed. If False, this feature will be disabled.
        progress_bar(bool, optional): If True (default), show the download progress bar.

    """

    def __init__(self, connection, cube_id, instance_id=None, parallel=True, progress_bar=True):
        """Initialize an instance of a cube.

        Args:
            connection: MicroStrategy connection object returned by `connection.Connection()`.
            cube_id (str): Identifier of a pre-existing cube containing the required data.
            instance_id (str): Identifier of an instance if cube instance has been already initialized,
                NULL by default.
            parallel (bool, optional): If True (default), utilize optimal number of threads to
                increase the download speed. If False, this feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download progress bar.

        """

        self._connection = connection
        self._cube_id = cube_id
        self.instance_id = instance_id
        self.parallel = parallel
        self.progress_bar = progress_bar

        self._size_limit = 10000000      # this sets desired chunk size in bytes
        self._initial_limit = 1000    # initial limit for the cube_instance request
        self._table_definition = {}
        self._dataframe = None
        self._dataframes = []
        self._attr_elements = None

        # load dataset information
        self.__info()
        self.__definition()
        self.__remove_row_count()

        self.__filter = Filter(attributes=self.attributes,
                               metrics=self.metrics,
                               row_count_metrics=self._row_counts)


    def to_dataframe(self, limit=None, multi_df=False):
        """Extract contents of a cube into a Pandas Data Frame.

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
        if limit:
            self._initial_limit = limit

        if self.instance_id is None:
            res = self.__initialize_cube(self._initial_limit)
        else:
            # try to get first chunk from already initialized instance of cube,
            # if not possible, initialize new instance
            try:
                res = self.__get_chunk(instance_id=self.instance_id, offset=0, limit=self._initial_limit)
            except requests.HTTPError:
                res = self.__initialize_cube(self._initial_limit)

        # Gets the pagination totals and instance_id from the response object
        _instance = res.json()
        _instance_id = _instance['instanceId']
        _pagination = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=res.json(), parse_cube=True)
        p.parse(response=_instance)

        # If there are more rows to fetch, fetch them
        if _pagination['current'] != _pagination['total']:
            if not limit:
                limit = max(1000, int((self._initial_limit * self._size_limit) / len(res.content)))
            # Count the number of additional iterations
            it_total = int((_pagination['total']-self._initial_limit)/limit) + \
                ((_pagination['total']-self._initial_limit) % limit != 0)

            if self.parallel and it_total > 1:
                threads = helper.get_parallel_number(it_total)
                with FuturesSession(executor=ThreadPoolExecutor(max_workers=threads),
                                    session=self._connection.session) as session:
                    fetch_pbar = tqdm(desc="Downloading", total=it_total+1, disable=(not self.progress_bar))
                    future = self.__fetch_chunks_future(session, _pagination, _instance_id, limit)
                    fetch_pbar.update()
                    for i, f in enumerate(future, start=1):
                        response = f.result()
                        if not response.ok:
                            helper.response_handler(response, "Error getting cube contents.")
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
            # split dataframe to dataframes matching tables in Cube
            self._dataframes = [self._dataframe[columns].copy() for _, columns \
                                in self.__multitable_definition().items()]
            return self._dataframes
        else:
            return self._dataframe

    def __fetch_chunks_future(self, future_session, pagination, instance_id, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [cubes.cube_instance_id_coroutine(future_session, connection=self._connection,
                                                 cube_id=self._cube_id,
                                                 instance_id=instance_id,
                                                 offset=_offset,
                                                 limit=limit,
                                                 verbose=helper.debug())
                for _offset in range(self._initial_limit, pagination['total'], limit)]

    def __fetch_chunks(self, parser, pagination, it_total, instance_id, limit):

        # Fetch add'l rows from this object instance from the intelligence server
        with tqdm(desc="Downloading", total=it_total+1, disable=(not self.progress_bar)) as fetch_pbar:
            fetch_pbar.update()
            for _offset in range(self._initial_limit, pagination['total'], limit):
                response = self.__get_chunk(instance_id=instance_id, offset=_offset, limit=limit)
                fetch_pbar.update()
                fetch_pbar.set_postfix(rows=str(min(_offset+limit, pagination['total'])))
                parser.parse(response=response.json())

    def __initialize_cube(self, limit):
        inst_pbar = tqdm(desc='Initializing an instance of a cube. Please wait...',
                         bar_format='{desc}', leave=False, ncols=280, disable=(not self.progress_bar))
        # Request a new instance, set instance id
        response = cubes.cube_instance(connection=self._connection,
                                       cube_id=self._cube_id,
                                       body=self.__filter._filter_body(),
                                       offset=0,
                                       limit=self._initial_limit,
                                       verbose=helper.debug())
        inst_pbar.close()
        return response

    def __get_chunk(self, instance_id, offset, limit):
        return cubes.cube_instance_id(connection=self._connection,
                                      cube_id=self._cube_id,
                                      instance_id=instance_id,
                                      offset=offset,
                                      limit=limit,
                                      verbose=helper.debug())

    def apply_filters(self, attributes=None, metrics=None, attr_elements=None, operator='In'):
        """Apply filters on the cube's objects, so only selected attributes, metrics and attributes' elements will be
        retrieved from Intelligence Server.

        Args:
            attributes (list or None, optional): ids of attributes to be included in the filter.
                If list is empty, no attributes will be selected and metric data will be aggregated.
            metrics (list or None, optional): ids of metrics to be included in the filter.
                If list is empty, no metrics will be selected.
            attr_elements (list or None, optional): attributes' elements to be included in the filter.
            operator (str, optional): a str flag used to specify if the attribute elements selected inside the
                filter should be included or excluded. Allowed values are: 'In', 'NotIn'
        """
        params = [attributes, metrics, attr_elements]
        filtering_is_requested = bool(not all(el is None for el in params))

        if filtering_is_requested:
            self.__filter._clear(attributes=attributes,
                                 metrics=metrics,
                                 attr_elements=attr_elements)
            self.__filter.operator = operator
            self._select_attribute_filter_conditionally(attributes)
            self._select_metric_filter_conditionally(metrics)
            self._select_attr_el_filter_conditionally(attr_elements)

    def _select_attribute_filter_conditionally(self, attributes_filtered):
        if attributes_filtered:
            self.__filter._select(object_id=attributes_filtered)
        elif attributes_filtered is not None:
            self.__filter.attr_selected = []

    def _select_metric_filter_conditionally(self, metrics_filtered):
        if metrics_filtered:
            self.__filter._select(object_id=metrics_filtered)
        elif metrics_filtered is not None:
            self.__filter.metr_selected = []

    def _select_attr_el_filter_conditionally(self, attr_el_filtered):
        if attr_el_filtered is not None:
            self.__filter._select_attr_el(element_id=attr_el_filtered)

    def clear_filters(self):
        """Clear previously set filters, allowing all attributes, metrics, and attribute elements to be retrieved."""

        self.__filter._clear()

        # once again remove Row Count metrics
        metrics_ids = [metric_id['id'] for metric_id in self.metrics]
        self.__filter._select(metrics_ids)

    def update(self, update_policy='upsert'):
        """Update single-table cube easily with the data frame stored in the Cube instance (cube.dataframe).
        Before the update, make sure that the data frame has been modified
        Args:
            update_policy(str): Update operation to perform. One of 'add' (inserts new, unique rows), 'update' (updates
                data in existing rows and columns), 'upsert' (updates existing data and inserts new rows), or 'replace'
                (replaces the existing data with new data).
        """
        if len(self._tables) > 1:
            helper.exception_handler(msg="""This feature works only for the single-table cubes.
                                            \rTo update multi-table cube use Dataset class.""")
        else:
            table_name = self._tables[0]["name"]
            dataset = Dataset(self._connection, dataset_id=self._cube_id)
            dataset.add_table(name=table_name, data_frame=self.dataframe, update_policy=update_policy)
            dataset.update()

    def save_as(self, name, description=None, folder_id=None, table_name=None, verbose=True):
        """Creates a new single-table cube with the data frame stored in the Cube instance (cube.dataframe).
        Before the update, make sure that the data exists.
        Args:
            name(str): Name of cube.
            description(str): Description of the cube.
            folder_id (str, optional): ID of the shared folder that the dataset should be created within. If `None`,
                defaults to the user's My Reports folder.
            table_name (str, optional): Name of the table. If None (default), the first table name of the original
                cube will be used.
        """
        if len(self._tables) > 1:
            helper.exception_handler(msg="""This feature works only for the single-table cubes.
                                            \rTo export multi-table cube use Dataset class.""")
        else:
            if table_name is None:
                table_name = self._tables[0]["name"]

            dataset = Dataset(self._connection, name=name, description=description)
            dataset.add_table(name=table_name, data_frame=self.dataframe, update_policy="add")
            dataset.create(folder_id=folder_id)

    def __multitable_definition(self):
        """Return all tables names and columns as a dictionary"""
        if not self._table_definition:
            try:
                res_tables = datasets.dataset_definition(connection=self._connection,
                                                        dataset_id=self._cube_id,
                                                        fields=['tables', 'columns'])
                _ds_definition = res_tables.json()

                for table in _ds_definition['result']['definition']['availableObjects']['tables']:
                    column_list = [column['columnName']
                        for column in _ds_definition['result']['definition']['availableObjects']['columns']
                        if table['name'] == column['tableName']]
                    self._table_definition[table['name']] = column_list
            except:
                helper.exception_handler("Some functionality is not available with this type of cube at the moment.", throw_error=False, exception_type=Warning, stack_lvl=3)
        return self._table_definition

    def __remove_row_count(self):
        """Remove all Row Count metrics from cube"""
        row_counts = list(map(itemgetter('name'), self._row_counts))
        self._metrics = list(filter(lambda x: x['name'] not in row_counts, self.metrics))

    def __info(self):
        """Get metadata for specific cubes. Implements GET /cubes to retrieve basic metadata."""

        res = cubes.cube_info(connection=self._connection, cube_id=self._cube_id, verbose=helper.debug())

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

        res = cubes.cube_definition(connection=self._connection, cube_id=self._cube_id, verbose=helper.debug())

        _definition = res.json()
        full_attributes = _definition["definition"]["availableObjects"]["attributes"]
        full_metrics = _definition["definition"]["availableObjects"]["metrics"]
        self._attributes = [{'name': attr['name'], 'id': attr['id']} for attr in full_attributes]
        self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

        self._tables = self.__multitable_definition().keys()
        row_counts = ['Row Count - {}'.format(table_name) for table_name in self._tables]
        self._row_counts = list(filter(lambda x: x['name'] in row_counts, self.metrics))

    def __get_attr_elements(self, limit=200000):
        """Get elements of report attributes synchronously.
        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements
        """

        attr_elements = []
        if self.attributes:
            pbar = tqdm(self.attributes, desc="Loading attribute elements",
                        leave=False, disable=(not self.progress_bar))
            # Fetch first chunk of attribute elements.
            for i, attr in enumerate(pbar):
                # Fetch first chunk of attribute elements.
                response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                cube_id=self._cube_id,
                                                                attribute_id=attr['id'],
                                                                offset=0,
                                                                limit=limit,
                                                                verbose=helper.debug())
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
                                                                    limit=limit,
                                                                    verbose=helper.debug())
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
        if self.attributes:
            threads = helper.get_parallel_number(len(self.attributes))
            with FuturesSession(executor=ThreadPoolExecutor(max_workers=threads),
                                session=self._connection.session) as session:
                # Fetch first chunk of attribute elements.
                futures = self.__fetch_attribute_elements_chunks(session, limit)
                pbar = tqdm(futures, desc="Loading attribute elements", leave=False, disable=(not self.progress_bar))
                for i, future in enumerate(pbar):
                    attr = self.attributes[i]
                    response = future.result()
                    if not response.ok:
                        helper.response_handler(response, "Error getting attribute " + attr["name"] + " elements")
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = cubes.cube_single_attribute_elements(connection=self._connection,
                                                                        cube_id=self._cube_id,
                                                                        attribute_id=attr["id"],
                                                                        offset=_offset,
                                                                        limit=limit,
                                                                        verbose=helper.debug())
                        elements.extend(response.json())
                    # Append attribute data to the list of attributes.
                    attr_elements.append({"attribute_name": attr['name'],
                                          "attribute_id": attr['id'],
                                          "elements": elements})
                pbar.close()

            return attr_elements

    def __fetch_attribute_elements_chunks(self, future_session, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [cubes.cube_single_attribute_elements_coroutine(future_session,
                                                               connection=self._connection,
                                                               cube_id=self._cube_id,
                                                               attribute_id=attribute['id'],
                                                               offset=0,
                                                               limit=limit,
                                                               verbose=helper.debug())
                for attribute in self.attributes]

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
            self.__filter.attr_elem_selected = self._attr_elements
        return self._attr_elements

    @property
    def selected_attributes(self):
        return self.__filter.attr_selected

    @property
    def selected_metrics(self):
        return self.__filter.metr_selected

    @property
    def selected_attr_elements(self):
        return self.__filter.attr_elem_selected

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
