from tqdm.auto import tqdm
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor

from mstrio.api import reports
from mstrio.utils.parser import Parser
from mstrio.utils.filter import Filter
from packaging import version
import pandas as pd
import mstrio.utils.helper as helper


class Report:
    """
    Access, filter, publish, and extract data from in-memory reports.

    Create a Report object to load basic information on a report dataset. Specify subset of report
    to be fetched through Report.apply_filters() and Report.clear_filters(). Fetch dataset through
    Report.to_dataframe() method.

    Attributes:
        connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
        report_id: Identifier of a pre-existing report containing the required data.
        parallel (bool, optional): If True (default), utilize optimal number of threads to
            increase the download speed. If False, this feature will be disabled.
        progress_bar(bool, optional): If True (default), show the download progress bar.

    """

    def __init__(self, connection, report_id, parallel=True, progress_bar=True):
        """Initialize an instance of a report

        Args:
            connection: MicroStrategy connection object returned by `microstrategy.Connection()`.
            report_id (str): Identifier of a pre-existing report containing the required data.
            parallel (bool, optional): If True (default), utilize optimal number of threads to
                increase the download speed. If False, this feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download progress bar.

        """

        self._connection = connection
        self._report_id = report_id
        self._subtotals = None
        self.cross_tab = False
        self.cross_tab_filter = {}

        self.parallel = parallel
        self.progress_bar = progress_bar
        self._size_limit = 10000000      # this sets desired chunk size in bytes
        self._initial_limit = 1000     # initial limit for the report_instance request

        # load report information
        self.__definition()

        # load attribute elements
        self.__OFFSET = 0
        self._attr_elements = []

        self._filter = Filter(attributes=self._attributes, metrics=self._metrics, attr_elements=self._attr_elements)

        if self.cross_tab:
            self._filter.select(object_id=[el['id'] for el in self._attributes])
            self._filter.select(object_id=[el['id'] for el in self._metrics])
        self._dataframe = None

    def to_dataframe(self, limit=None):
        """Extract contents of a report instance into a Pandas Data Frame. Formerly `microstrategy.Connection.get_report()`.

        Args:
            limit (None or int, optional): Used to control data extract behavior. By default (None)
                the limit is calculated automatically, based on an optimized physical size of one
                chunk. Setting limit manually will force the number of rows per chunk. Depending on
                system resources, a higher limit (e.g. 50,000) may reduce the total time required
                to extract the entire dataset.

        Returns:
            Pandas Data Frame containing the report contents
        """
        inst_pbar = tqdm(desc='Initializing an instance of a report. Please wait...',
                         bar_format='{desc}', leave=False, ncols=285, disable=(not self.progress_bar))

        # Switch off subtotals if I-Server version is higher than 11.2.1
        body = self._filter.filter_body()
        if version.parse(self._connection.iserver_version) >= version.parse("11.2.0100"):
            self._subtotals["visible"] = False
            body["subtotals"] = {"visible": self._subtotals["visible"]}

        if limit:
            self._initial_limit = limit
        # Request a new instance, set instance id
        res = reports.report_instance(connection=self._connection,
                                      report_id=self._report_id,
                                      body=body,
                                      offset=self.__OFFSET,
                                      limit=self._initial_limit)
        inst_pbar.close()

        # Gets the pagination totals from the response object
        _instance = res.json()
        _instance_id = _instance['instanceId']
        _pagination = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=_instance, parse_cube=False)
        p.parse(response=_instance)

        # If there are more rows to fetch, fetch them
        if _pagination['current'] != _pagination['total']:
            if not limit:
                limit = max(1000, int((self._initial_limit * self._size_limit) / len(res.content)))
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
                            response = reports.report_instance_id(connection=self._connection,
                                                                  report_id=self._report_id, instance_id=_instance_id,
                                                                  offset=current_offset, limit=limit)
                        fetch_pbar.update()
                        fetch_pbar.set_postfix(rows=str(min(self._initial_limit+i*limit, _pagination['total'])))
                        p.parse(response.json())
                    fetch_pbar.close()
            else:
                self.__fetch_chunks(p, _pagination, it_total, _instance_id, limit)

        # return parsed data as a data frame
        self._dataframe = p.dataframe

        # filter received dataframe if report had crosstabs and filters were applied
        if self.cross_tab_filter != {}:
            if self.cross_tab_filter['metrics'] is not None:
                # drop metrics columns from dataframe
                metr_names = [el['name'] for el in list(filter(lambda x: x['id'] not in self.cross_tab_filter['metrics'],
                              self._metrics))]
                self._dataframe = self._dataframe.drop(metr_names, axis=1)

            if self.cross_tab_filter['attr_elements'] is not None:
                # create dict of attributes and elements to iterate through
                attr_dict = {}
                for attribute in self.cross_tab_filter['attr_elements']:
                    key = attribute[:32]
                    attr_dict.setdefault(key, []).append(attribute[33:])
                # initialize indexes series for filter
                indexes = pd.Series([False] * len(self._dataframe))

                # logical OR for filtered attribute elements
                for attribute in attr_dict:
                    attr_name = list(filter(lambda x: x['id'] in attribute, self._attributes))[0]['name']
                    elements = attr_dict[attribute]
                    indexes = indexes | self._dataframe[attr_name].isin(elements)
                # select datframe indexes with 
                self._dataframe = self._dataframe[indexes]

            if self.cross_tab_filter['attributes'] is not None:
                attr_names = [el['name'] for el in list(filter(lambda x: x['id'] not in self.cross_tab_filter['attributes'],
                              self._attributes))]
                self._dataframe = self._dataframe.drop(attr_names, axis=1)

        return self._dataframe

    def __fetch_chunks_future(self, session, pagination, instance_id, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [reports.report_instance_id_coroutine(session, connection=self._connection,
                                                     report_id=self._report_id,
                                                     instance_id=instance_id,
                                                     offset=_offset,
                                                     limit=limit)
                for _offset in range(self._initial_limit, pagination['total'], limit)]

    def __fetch_chunks(self, parser, pagination, it_total, instance_id, limit):

        # Fetch add'l rows from this object instance from the intelligence server
        with tqdm(desc="Downloading", total=it_total+1, disable=(not self.progress_bar)) as fetch_pbar:
            fetch_pbar.update()
            for _offset in range(self._initial_limit, pagination['total'], limit):
                response = reports.report_instance_id(connection=self._connection,
                                                      report_id=self._report_id,
                                                      instance_id=instance_id,
                                                      offset=_offset,
                                                      limit=limit)
                fetch_pbar.update()
                fetch_pbar.set_postfix(rows=str(min(_offset+limit, pagination['total'])))
                parser.parse(response=response.json())

    def apply_filters(self, attributes=None, metrics=None, attr_elements=None):
        """Apply filters on the report's objects, so only selected attributes, metrics and attributes' elements
        will be retrieved from Intelligence Server.

        Args:
            attributes (list or None, optional): ids of attributes to be included in the filter.
                If list is empty, no attributes will be selected and metric data will be aggregated.
            metrics (list or None, optional): ids of metrics to be included in the filter.
                If list is empty, no metrics will be selected.
            attr_elements (list or None, optional): attributes' elements to be included in the filter.
        """
        if self.cross_tab:
            self.cross_tab_filter = {'attributes': attributes, 'metrics': metrics, 'attr_elements': attr_elements}
        elif not all(element is None for element in [attributes, metrics, attr_elements]):
            if attr_elements:           # If parameter attr_elements is applied then fetch all attribute elements
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
        if self.cross_tab:
            self._filter.select(object_id=[el['id'] for el in self._attributes])
            self._filter.select(object_id=[el['id'] for el in self._metrics])

    def __definition(self):
        """Get the definition of a report, including attributes and metrics. Implements GET /v2/reports/<report_id>"""

        res = reports.report_definition(connection=self._connection, report_id=self._report_id)

        definition = res.json()
        grid = definition["definition"]["grid"]
        if version.parse(self._connection.iserver_version) >= version.parse("11.2.0100"):
            self._subtotals = grid["subtotals"]

        self._name = definition["name"]
        self.cross_tab = grid["crossTab"]
        available_objects = definition['definition']['availableObjects']

        # Check if report have custom groups or consolidations
        if available_objects['customGroups']:
            helper.exception_handler(msg="Reports with custom groups are not supported.", exception_type=ImportError)
        if available_objects['consolidations']:
            helper.exception_handler(msg="Reports with consolidations are not supported.", exception_type=ImportError)

        metrics_position = grid["metricsPosition"]
        full_metrics = grid[metrics_position["axis"]][metrics_position["index"]]["elements"]

        full_attributes = []
        for elem in grid["rows"]:
            if elem["type"] == "attribute":
                full_attributes.append(elem)
        for elem in grid["columns"]:
            if elem["type"] == "attribute":
                full_attributes.append(elem)

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
                response = reports.report_single_attribute_elements(connection=self._connection,
                                                                    report_id=self._report_id,
                                                                    attribute_id=attr['id'],
                                                                    offset=self.__OFFSET,
                                                                    limit=limit)
                # Get total number of rows from headers.
                total = int(response.headers['x-mstr-total-count'])
                # Get attribute elements from the response.
                elements = response.json()

                # If total number of elements is bigger than the chunk size (limit), fetch them incrementally.
                for _offset in range(limit, total, limit):
                    response = reports.report_single_attribute_elements(connection=self._connection,
                                                                        report_id=self._report_id,
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
        """Get elements of report attributes asynchronously. Implements GET /reports/<report_id>/attributes/<attribute_id>/elements"""

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
                        response = reports.report_single_attribute_elements(connection=self._connection,
                                                                            report_id=self._report_id,
                                                                            attribute_id=attr["id"],
                                                                            offset=0,
                                                                            limit=limit)
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = reports.report_single_attribute_elements(connection=self._connection,
                                                                            report_id=self._report_id,
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
        return [reports.report_single_attribute_elements_coroutine(session,
                                                                   connection=self._connection,
                                                                   report_id=self._report_id,
                                                                   attribute_id=attribute['id'],
                                                                   offset=0,
                                                                   limit=limit)
                for attribute in self._attributes]

    @property
    def name(self):
        return self._name

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
