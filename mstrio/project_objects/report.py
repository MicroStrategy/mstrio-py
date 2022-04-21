from typing import List, Optional, Union

from packaging import version
import pandas as pd
import requests
from tqdm.auto import tqdm

from mstrio import config
from mstrio.api import reports
from mstrio.connection import Connection
from mstrio.object_management.search_operations import full_search, SearchPattern
from mstrio.users_and_groups.user import User
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, DeleteMixin, Entity, ObjectTypes
from mstrio.utils.filter import Filter
from mstrio.utils.helper import fallback_on_timeout
import mstrio.utils.helper as helper
from mstrio.utils.parser import Parser
from mstrio.utils.sessions import FuturesSessionWithRenewal


def list_reports(connection: Connection, name_begins: Optional[str] = None,
                 to_dictionary: bool = False, limit: Optional[int] = None,
                 **filters) -> Union[List["Report"], List[dict]]:
    """Get list of Report objects or dicts with them.
    Optionally filter reports by specifying 'name_begins'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name_begins':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins (string, optional): characters that the report name must
            begin with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Report objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']

    Returns:
        list with Report objects or list of dictionaries
    """
    connection._validate_project_selected()
    objects_ = full_search(connection, object_types=ObjectTypes.REPORT_DEFINITION,
                           project=connection.project_id, name=name_begins,
                           pattern=SearchPattern.BEGIN_WITH, limit=limit, **filters)
    if to_dictionary:
        return objects_
    else:
        return [Report.from_dict(obj_, connection) for obj_ in objects_]


class Report(Entity, CertifyMixin, DeleteMixin):
    """Access, filter, publish, and extract data from in-memory reports.

    Create a Report object to load basic information on a report dataset.
    Specify subset of report to be fetched through `Report.apply_filters()` and
    `Report.clear_filters()`. Fetch dataset through `Report.to_dataframe()`
    method.

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id: Identifier of a pre-existing report containing the required
            data.
        name: Report name
        description: Report description
        abbreviation: Report abbreviation
        instance_id: Identifier of an instance if report instance has been
            already initialized, NULL by default.
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        version: Version ID
        owner: owner User object
        view_media: View media information
        ancestors: List of ancestor folders
        certified_info: Information whether report is certified or not,
            CertifiedInfo object
        attributes: List of attributes
        metrics: List of metrics
        attr_elements: All attributes elements of report
        selected_attributes: IDs of filtered attributes
        selected_metrics: IDs of filtered metrics
        selected_attr_elements: IDs of filtered attribute elements
        dataframe: content of a report extracted into a Pandas `DataFrame`
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """
    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict,
    }
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, id: str, instance_id: Optional[str] = None,
                 parallel: bool = True, progress_bar: bool = True):
        """Initialize an instance of a report.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing report containing
                the required data.
            instance_id (str): Identifier of an instance if report instance has
                been already initialized, NULL by default.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download
                progress bar.
        """
        connection._validate_project_selected()
        super().__init__(connection, id, instance_id=instance_id, parallel=parallel,
                         progress_bar=progress_bar)

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        self.instance_id = kwargs.get("instance_id")
        self._parallel = kwargs.get("parallel", True)
        self._initial_limit = 1000
        self._progress_bar = True if kwargs.get("progress_bar",
                                                True) and config.progress_bar else False
        self._cross_tab = False
        self._cross_tab_filter = {}
        self._subtotals = {}
        self._dataframe = None
        self._attr_elements = None

        self._attributes = []
        self._metrics = []
        self.__definition_retrieved = False
        self.__filter = None

    def alter(self, name: Optional[str] = None, description: Optional[str] = None,
              abbreviation: Optional[str] = None):
        """Alter Report properties.

        Args:
            name: new name of the Report
            description: new description of the Report
            abbreviation: new abbreviation of the Report
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def to_dataframe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Extract contents of a report instance into a Pandas `DataFrame`.

        Args:
            limit (None or int, optional): Used to control data extract
                behavior. By default (None) the limit is calculated
                automatically, based on an optimized physical size of one chunk.
                Setting limit manually will force the number of rows per chunk.
                Depending on system resources, a higher limit (e.g. 50,000) may
                reduce the total time required to extract the entire dataset.

        Returns:
            Pandas Data Frame containing the report contents.
        """
        if limit:
            self._initial_limit = limit

        if self.instance_id is None:
            res = self.__initialize_report(self._initial_limit)
        else:
            # try to get first chunk from already initialized instance of report
            # if not possible, initialize new instance
            try:
                res = self.__get_chunk(instance_id=self.instance_id, offset=0,
                                       limit=self._initial_limit)
            except requests.HTTPError:
                res = self.__initialize_report(self._initial_limit)

        # Gets the pagination totals from the response object
        _instance = res.json()
        self.instance_id = _instance['instanceId']
        paging = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=_instance, parse_cube=False)
        p.parse(response=_instance)

        # If there are more rows to fetch, fetch them
        if paging['current'] != paging['total']:
            if not limit:
                limit = max(1000, int((self._initial_limit * self._SIZE_LIMIT) / len(res.content)))
            # Count the number of additional iterations
            it_total = int((paging['total'] - self._initial_limit) / limit) + \
                ((paging['total'] - self._initial_limit) % limit != 0)

            if self._parallel and it_total > 1:
                threads = helper.get_parallel_number(it_total)
                with FuturesSessionWithRenewal(connection=self._connection,
                                               max_workers=threads) as session:
                    fetch_pbar = tqdm(desc="Downloading", total=it_total + 1,
                                      disable=(not self._progress_bar))
                    future = self.__fetch_chunks_future(session, paging, self.instance_id, limit)
                    fetch_pbar.update()
                    for i, f in enumerate(future, start=1):
                        response = f.result()
                        if not response.ok:
                            helper.response_handler(response, "Error getting report contents.")
                        fetch_pbar.update()
                        fetch_pbar.set_postfix(
                            rows=str(min(self._initial_limit + i * limit, paging['total'])))
                        p.parse(response.json())
                    fetch_pbar.close()
            else:
                self.__fetch_chunks(p, paging, it_total, self.instance_id, limit)

        # return parsed data as a data frame
        self._dataframe = p.dataframe

        # filter dataframe if report had crosstabs and filters were applied
        if self._cross_tab_filter != {}:
            if self._cross_tab_filter['metrics'] is not None:
                # drop metrics columns from dataframe
                metr_names = [
                    el['name'] for el in list(
                        filter(lambda x: x['id'] not in self._cross_tab_filter['metrics'],
                               self.metrics))
                ]
                self._dataframe = self._dataframe.drop(metr_names, axis=1)

            if self._cross_tab_filter['attr_elements'] is not None:
                # create dict of attributes and elements to iterate through
                attr_dict = {}
                for attribute in self._cross_tab_filter['attr_elements']:
                    key = attribute[:32]
                    attr_dict.setdefault(key, []).append(attribute[33:])
                # initialize indexes series for filter
                indexes = pd.Series([False] * len(self._dataframe))

                # logical OR for filtered attribute elements
                for attribute in attr_dict:
                    attr_name = list(filter(lambda x: x['id'] in attribute,
                                            self.attributes))[0]['name']
                    elements = attr_dict[attribute]
                    indexes = indexes | self._dataframe[attr_name].isin(elements)
                # select dataframe indexes with
                self._dataframe = self._dataframe[indexes]

            if self._cross_tab_filter['attributes'] is not None:
                attr_names = [
                    el['name'] for el in list(
                        filter(lambda x: x['id'] not in self._cross_tab_filter['attributes'],
                               self.attributes))
                ]
                # filtering out attribute forms columns
                to_be_removed = []
                to_be_added = []
                for attr in attr_names:
                    forms = [
                        column for column in self._dataframe.columns
                        if column.startswith(attr + '@')
                    ]
                    if forms:
                        to_be_removed.append(attr)
                        to_be_added.extend(forms)
                for elem in to_be_removed:
                    attr_names.remove(elem)
                attr_names.extend(to_be_added)
                # drop filtered out columns
                self._dataframe = self._dataframe.drop(attr_names, axis=1)
        return self._dataframe

    def __fetch_chunks_future(self, future_session, pagination, instance_id, limit):
        """Fetch add'l rows from this object instance from the Intelligence
        Server."""
        return [
            reports.report_instance_id_coroutine(
                future_session,
                connection=self._connection,
                report_id=self._id,
                instance_id=instance_id,
                offset=_offset,
                limit=limit,
            ) for _offset in range(self._initial_limit, pagination['total'], limit)
        ]

    def __fetch_chunks(self, parser, pagination, it_total, instance_id, limit):
        """Fetch add'l rows from this object instance from the Intelligence
        Server."""
        with tqdm(desc="Downloading", total=it_total + 1,
                  disable=(not self._progress_bar)) as fetch_pbar:
            fetch_pbar.update()
            for _offset in range(self._initial_limit, pagination['total'], limit):
                response = self.__get_chunk(instance_id=instance_id, offset=_offset, limit=limit)
                fetch_pbar.update()
                fetch_pbar.set_postfix(rows=str(min(_offset + limit, pagination['total'])))
                parser.parse(response=response.json())

    def __initialize_report(self, limit: int) -> requests.Response:
        inst_pbar = tqdm(desc='Initializing an instance of a report. Please wait...',
                         bar_format='{desc}', leave=False, ncols=285,
                         disable=(not self._progress_bar))

        # Switch off subtotals if I-Server version is higher than 11.2.1
        body = self._filter._filter_body()
        if version.parse(self._connection.iserver_version) >= version.parse("11.2.0100"):
            self._subtotals["visible"] = False
            body["subtotals"] = {"visible": self._subtotals["visible"]}

        # Request a new instance, set instance id
        response = reports.report_instance(
            connection=self._connection,
            report_id=self._id,
            body=body,
            offset=0,
            limit=self._initial_limit,
        )
        inst_pbar.close()
        return response

    def __get_chunk(self, instance_id: str, offset: int, limit: int) -> requests.Response:
        return reports.report_instance_id(
            connection=self._connection,
            report_id=self._id,
            instance_id=instance_id,
            offset=offset,
            limit=limit,
        )

    def apply_filters(self, attributes: Optional[list] = None, metrics: Optional[list] = None,
                      attr_elements: Optional[list] = None, operator: str = 'In') -> None:
        """Apply filters on the reports's objects.

        Filter by attributes, metrics and attribute elements.

        Args:
            attributes (list or None, optional): ids of attributes to be
                included in the filter. If list is empty, no attributes will be
                selected and metric data will be aggregated.
            metrics (list or None, optional): ids of metrics to be included in
                the filter. If list is empty, no metrics will be selected.
            attr_elements (list or None, optional): attribute elements to be
                included in the filter.
            operator (str, optional): a str flag used to specify if the
                attribute elements selected inside the filter should be included
                or excluded. Allowed values are: 'In', 'NotIn'.
        """
        filtering_is_requested = bool(not all(
            element is None for element in [attributes, metrics, attr_elements]))

        if self._cross_tab:
            self._cross_tab_filter = {
                'attributes': attributes,
                'metrics': metrics,
                'attr_elements': attr_elements
            }
        elif filtering_is_requested:
            self._filter._clear(attributes=attributes, metrics=metrics,
                                attr_elements=attr_elements)
            self._filter.operator = operator
            self._select_attribute_filter_conditionally(attributes)
            self._select_metric_filter_conditionally(metrics)
            self._select_attr_el_filter_conditionally(attr_elements)
            # Clear instance, to generate new with new filters
            self.instance_id = None

    def _select_attribute_filter_conditionally(self, attributes_filtered) -> None:
        if attributes_filtered:
            self._filter._select(object_id=attributes_filtered)
        elif attributes_filtered is not None:
            self._filter.attr_selected = []

    def _select_metric_filter_conditionally(self, metrics_filtered) -> None:
        if metrics_filtered:
            self._filter._select(object_id=metrics_filtered)
        elif metrics_filtered is not None:
            self._filter.metr_selected = []

    def _select_attr_el_filter_conditionally(self, attr_el_filtered) -> None:
        if attr_el_filtered is not None:
            self._filter._select_attr_el(element_id=attr_el_filtered)

    def clear_filters(self) -> None:
        """Clear previously set filters, allowing all attributes, metrics, and
        attribute elements to be retrieved."""

        self._filter._clear()
        if self._cross_tab:
            self._filter._select(object_id=[el['id'] for el in self.attributes])
            self._filter._select(object_id=[el['id'] for el in self.metrics])
        # Clear instance, to generate new with new filters
        self.instance_id = None

    def _get_definition(self) -> None:
        """Get the definition of a report, including attributes and metrics.

        Implements GET /v2/reports/<report_id>.
        """
        response = reports.report_definition(connection=self._connection,
                                             report_id=self._id).json()

        grid = response["definition"]["grid"]
        available_objects = response['definition']['availableObjects']

        if version.parse(self._connection.iserver_version) >= version.parse("11.2.0100"):
            self._subtotals = grid["subtotals"]
        self.name = response["name"]
        self._cross_tab = grid["crossTab"]

        # Check if report have custom groups or consolidations
        if available_objects['customGroups']:
            helper.exception_handler(msg="Reports with custom groups are not supported.",
                                     exception_type=ImportError)
        if available_objects['consolidations']:
            helper.exception_handler(msg="Reports with consolidations are not supported.",
                                     exception_type=ImportError)

        full_attributes = []
        for row in grid["rows"]:
            if row["type"] == "attribute":
                full_attributes.append(row)
        for column in grid["columns"]:
            if column["type"] == "attribute":
                full_attributes.append(column)
        self._attributes = [{'name': attr['name'], 'id': attr['id']} for attr in full_attributes]

        # Retrieve metrics from the report grid (only selected metrics)
        metrics_position = grid.get("metricsPosition")
        if metrics_position is None:
            self._metrics = []
        else:
            full_metrics = grid[metrics_position["axis"]][metrics_position["index"]]["elements"]
            self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

        self.__definition_retrieved = True

    def __get_attr_elements(self, limit: int = 50000) -> list:
        """Get elements of report attributes synchronously.

        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements.
        """

        def fetch_for_attribute(attribute):

            @fallback_on_timeout()
            def fetch_for_attribute_given_limit(limit):
                response = reports.report_single_attribute_elements(
                    connection=self._connection,
                    report_id=self._id,
                    attribute_id=attribute['id'],
                    offset=0,
                    limit=limit,
                )
                # Get total number of rows from headers.
                total = int(response.headers['x-mstr-total-count'])
                # Get attribute elements from the response.
                elements = response.json()

                # If total number of elements is bigger than the chunk size
                # (limit), fetch them incrementally.
                for _offset in range(limit, total, limit):
                    response = reports.report_single_attribute_elements(
                        connection=self._connection,
                        report_id=self._id,
                        attribute_id=attribute['id'],
                        offset=_offset,
                        limit=limit,
                    )
                    elements.extend(response.json())

                # Return attribute data.
                return {
                    "attribute_name": attribute['name'],
                    "attribute_id": attribute['id'],
                    "elements": elements
                }

            return fetch_for_attribute_given_limit(limit)[0]

        attr_elements = []
        if self.attributes:
            pbar = tqdm(self.attributes, desc="Loading attribute elements", leave=False,
                        disable=(not self._progress_bar))
            attr_elements = [fetch_for_attribute(attribute) for attribute in pbar]
            pbar.close()

        return attr_elements

    def __get_attr_elements_async(self, limit: int = 50000) -> list:
        """Get elements of report attributes asynchronously.

        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements.
        """

        attr_elements = []
        if self.attributes:
            threads = helper.get_parallel_number(len(self.attributes))
            with FuturesSessionWithRenewal(connection=self._connection,
                                           max_workers=threads) as session:
                # Fetch first chunk of attribute elements.
                futures = self.__fetch_attribute_elements_chunks(session, limit)
                pbar = tqdm(futures, desc="Loading attribute elements", leave=False,
                            disable=(not self._progress_bar))
                for i, future in enumerate(pbar):
                    attr = self.attributes[i]
                    response = future.result()
                    if not response.ok:
                        helper.response_handler(
                            response, "Error getting attribute " + attr['name'] + " elements")
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = reports.report_single_attribute_elements(
                            connection=self._connection,
                            report_id=self._id,
                            attribute_id=attr["id"],
                            offset=_offset,
                            limit=limit,
                        )
                        elements.extend(response.json())
                    # Append attribute data to the list of attributes.
                    attr_elements.append({
                        "attribute_name": attr['name'],
                        "attribute_id": attr['id'],
                        "elements": elements
                    })
                pbar.close()

            return attr_elements

    def __fetch_attribute_elements_chunks(self, future_session, limit: int) -> list:
        # Fetch add'l rows from this object instance
        return [
            reports.report_single_attribute_elements_coroutine(
                future_session,
                connection=self._connection,
                report_id=self._id,
                attribute_id=attribute['id'],
                offset=0,
                limit=limit,
            ) for attribute in self.attributes
        ]

    def list_properties(self):
        """List all properties of the object."""

        attributes = {key: self.__dict__[key] for key in self.__dict__ if not key.startswith('_')}
        attributes = {
            **attributes, "id": self.id,
            "instance_id": self.instance_id,
            "type": self.type,
            "subtype": self.subtype,
            "ext_type": self.ext_type,
            "date_created": self.date_created,
            "date_modified": self.date_modified,
            "version": self.version,
            "owner": self.owner,
            "view_media": self.view_media,
            "ancestors": self.ancestors,
            "certified_info": self.certified_info,
            "acg": self.acg,
            "acl": self.acl,
            "attributes": self.attributes,
            "metrics": self.metrics
        }
        return {
            key: attributes[key] for key in sorted(attributes, key=helper.sort_object_properties)
        }

    @property
    def attributes(self):
        if not self.__definition_retrieved:
            self._get_definition()
        return self._attributes

    @property
    def metrics(self):
        if not self.__definition_retrieved:
            self._get_definition()
        return self._metrics

    @property
    def attr_elements(self):
        if not self.__definition_retrieved:
            self._get_definition()
        if not self._attr_elements and self._id:
            if self._parallel is True:
                # TODO: move the fallback inside the function to apply
                # per-attribute, like with non-async version.
                self._attr_elements = fallback_on_timeout()(
                    self.__get_attr_elements_async)(50000)[0]
            else:
                self._attr_elements = self.__get_attr_elements()
            self._filter._populate_attr_elements(self._attr_elements)
        return self._attr_elements

    @property
    def _filter(self):
        if not self.__definition_retrieved:
            self._get_definition()
        if self.__filter is None:
            self.__filter = Filter(attributes=self._attributes, metrics=self._metrics,
                                   attr_elements=self._attr_elements)
        return self.__filter

    @property
    def selected_attributes(self):
        """Selected attributes for filtering."""
        return self._filter.attr_selected

    @property
    def selected_metrics(self):
        """Selected metrics for filtering."""
        return self._filter.metr_selected

    @property
    def selected_attr_elements(self):
        """Selected attribute elements for filtering."""
        return self._filter.attr_elem_selected

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._dataframe is None:
            helper.exception_handler(
                msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                exception_type=Warning)
        return self._dataframe
