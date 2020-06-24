from tqdm.auto import tqdm
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor
from packaging.version import parse as parse_version
import requests
import pandas as pd

from mstrio.api import reports
from mstrio.utils.parser import Parser
from mstrio.utils.filter import Filter
import mstrio.utils.helper as helper


class Report:
    """
    Access, filter, publish, and extract data from in-memory reports.

    Create a Report object to load basic information on a report dataset.
    Specify subset of report to be fetched through Report.apply_filters() and
    Report.clear_filters(). Fetch dataset through Report.to_dataframe() method.

    Attributes:
        connection: MicroStrategy connection object returned by `connection.Connection()`.
        report_id: Identifier of a pre-existing report containing the required data.
        instance_id (str): Identifier of an instance if report instance has been already initialized,
                NULL by default.
        parallel (bool, optional): If True (default), utilize optimal number of threads to
            increase the download speed. If False, this feature will be disabled.
        progress_bar(bool, optional): If True (default), show the download progress bar.

    """

    def __init__(self, connection, report_id, instance_id=None, parallel=True, progress_bar=True):
        """Initialize an instance of a report

        Args:
            connection: MicroStrategy connection object returned by `connection.Connection()`.
            report_id (str): Identifier of a pre-existing report containing the required data.
            instance_id (str): Identifier of an instance if report instance has been already initialized,
                NULL by default.
            parallel (bool, optional): If True (default), utilize optimal number of threads to
                increase the download speed. If False, this feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download progress bar.
        """

        self._connection = connection
        self._report_id = report_id
        self.instance_id = instance_id
        self.parallel = parallel
        self.progress_bar = progress_bar

        self._subtotals = None
        self.cross_tab = False
        self.cross_tab_filter = {}
        self._size_limit = 10000000    # this sets desired chunk size in bytes
        self._initial_limit = 1000     # initial limit for the report_instance request
        self._dataframe = None
        self._attr_elements = None

        # load report information
        self.__definition()
        self.__filter = Filter(attributes=self.attributes,
                               metrics=self.metrics)


    def to_dataframe(self, limit=None):
        """Extract contents of a report instance into a Pandas Data Frame.

        Args:
            limit (None or int, optional): Used to control data extract behavior. By default (None)
                the limit is calculated automatically, based on an optimized physical size of one
                chunk. Setting limit manually will force the number of rows per chunk. Depending on
                system resources, a higher limit (e.g. 50,000) may reduce the total time required
                to extract the entire dataset.

        Returns:
            Pandas Data Frame containing the report contents
        """
        if limit:
            self._initial_limit = limit

        if self.instance_id is None:
            res = self.__initialize_report(self._initial_limit)
        else:
            # try to get first chunk from already initialized instance of report,
            # if not possible, initialize new instance
            try:
                res = self.__get_chunk(instance_id=self.instance_id, offset=0, limit=self._initial_limit)
            except requests.HTTPError:
                res = self.__initialize_report(self._initial_limit)

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
                            helper.response_handler(response, "Error getting report contents.")
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
                metr_names = [el['name'] for el in list(
                    filter(lambda x: x['id'] not in self.cross_tab_filter['metrics'], self.metrics))]
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
                    attr_name = list(filter(lambda x: x['id'] in attribute, self.attributes))[0]['name']
                    elements = attr_dict[attribute]
                    indexes = indexes | self._dataframe[attr_name].isin(elements)
                # select datframe indexes with
                self._dataframe = self._dataframe[indexes]

            if self.cross_tab_filter['attributes'] is not None:
                attr_names = [el['name'] for el in list(
                    filter(lambda x: x['id'] not in self.cross_tab_filter['attributes'], self.attributes))]
                self._dataframe = self._dataframe.drop(attr_names, axis=1)

        return self._dataframe

    def __fetch_chunks_future(self, future_session, pagination, instance_id, limit):
        # Fetch add'l rows from this object instance from the intelligence server
        return [reports.report_instance_id_coroutine(future_session, connection=self._connection,
                                                     report_id=self._report_id,
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

    def __initialize_report(self, limit):
        inst_pbar = tqdm(desc='Initializing an instance of a report. Please wait...',
                         bar_format='{desc}', leave=False, ncols=285, disable=(not self.progress_bar))

        # Switch off subtotals if I-Server version is higher than 11.2.1
        body = self.__filter._filter_body()
        if parse_version(self._connection.iserver_version) >= parse_version("11.2.0100"):
            self._subtotals["visible"] = False
            body["subtotals"] = {"visible": self._subtotals["visible"]}

        # Request a new instance, set instance id
        response = reports.report_instance(connection=self._connection,
                                           report_id=self._report_id,
                                           body=body,
                                           offset=0,
                                           limit=self._initial_limit,
                                           verbose=helper.debug())
        inst_pbar.close()
        return response

    def __get_chunk(self, instance_id, offset, limit):
        return reports.report_instance_id(connection=self._connection,
                                          report_id=self._report_id,
                                          instance_id=instance_id,
                                          offset=offset,
                                          limit=limit,
                                          verbose=helper.debug())

    def apply_filters(self, attributes=None, metrics=None, attr_elements=None, operator='In'):
        """Apply filters on the reports's objects, so only selected attributes, metrics and attributes' elements will be retrieved from Intelligence Server.

        Args:
            attributes (list or None, optional): ids of attributes to be included in the filter.
                If list is empty, no attributes will be selected and metric data will be aggregated.
            metrics (list or None, optional): ids of metrics to be included in the filter.
                If list is empty, no metrics will be selected.
            attr_elements (list or None, optional): attributes' elements to be included in the filter.
            operator (str, optional): a str flag used to specify if the attribute elements selected inside the
                filter should be included or excluded. Allowed values are: 'In', 'NotIn'
        """
        filtering_is_requested = bool(not all(element is None for element in [attributes, metrics, attr_elements]))

        if self.cross_tab:
            self.cross_tab_filter = {'attributes': attributes, 'metrics': metrics, 'attr_elements': attr_elements}
        elif filtering_is_requested:
            self.__filter._clear(attributes=attributes, metrics=metrics, attr_elements=attr_elements)
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
        if self.cross_tab:
            self.__filter._select(object_id=[el['id'] for el in self.attributes])
            self.__filter._select(object_id=[el['id'] for el in self.metrics])

    def __definition(self):
        """Get the definition of a report, including attributes and metrics. Implements GET /v2/reports/<report_id>"""

        response = reports.report_definition(connection=self._connection,
                                             report_id=self._report_id,
                                             verbose=helper.debug()).json()

        grid = response["definition"]["grid"]
        available_objects = response['definition']['availableObjects']

        if parse_version(self._connection.iserver_version) >= parse_version("11.2.0100"):
            self._subtotals = grid["subtotals"]
        self._name = response["name"]
        self.cross_tab = grid["crossTab"]

        # Check if report have custom groups or consolidations
        if available_objects['customGroups']:
            helper.exception_handler(msg="Reports with custom groups are not supported.", exception_type=ImportError)
        if available_objects['consolidations']:
            helper.exception_handler(msg="Reports with consolidations are not supported.", exception_type=ImportError)

        full_attributes = []
        for row in grid["rows"]:
            if row["type"] == "attribute":
                full_attributes.append(row)
        for column in grid["columns"]:
            if column["type"] == "attribute":
                full_attributes.append(column)
        self._attributes = [{'name': attr['name'], 'id': attr['id']} for attr in full_attributes]

        # Retrieve metrics from the report grid (metrics selected only in the report)
        metrics_position = grid.get("metricsPosition")
        if metrics_position is None:
            self._metrics = []
        else:
            full_metrics = grid[metrics_position["axis"]][metrics_position["index"]]["elements"]
            self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

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
                response = reports.report_single_attribute_elements(connection=self._connection,
                                                                    report_id=self._report_id,
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
                    response = reports.report_single_attribute_elements(connection=self._connection,
                                                                        report_id=self._report_id,
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
        """Get elements of report attributes asynchronously.
        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements
        """

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
                        helper.response_handler(response, "Error getting attribute " + attr['name'] + " elements")
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = reports.report_single_attribute_elements(connection=self._connection,
                                                                            report_id=self._report_id,
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
        return [reports.report_single_attribute_elements_coroutine(future_session,
                                                                   connection=self._connection,
                                                                   report_id=self._report_id,
                                                                   attribute_id=attribute['id'],
                                                                   offset=0,
                                                                   limit=limit,
                                                                   verbose=helper.debug())
                for attribute in self.attributes]

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
