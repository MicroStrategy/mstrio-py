import pandas as pd
import requests
from packaging import version
from tqdm.auto import tqdm

from mstrio import config
from mstrio.api import attributes as attributes_api
from mstrio.api import reports as reports_api
from mstrio.api.schedules import get_contents_schedule
from mstrio.connection import Connection
from mstrio.distribution_services.schedule import Schedule
from mstrio.object_management.search_operations import SearchPattern, full_search
from mstrio.project_objects.prompt import Prompt
from mstrio.users_and_groups.user import User
from mstrio.utils.cache import CacheSource, ContentCacheMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import (
    CertifyMixin,
    CopyMixin,
    DeleteMixin,
    Entity,
    MoveMixin,
    ObjectSubTypes,
    ObjectTypes,
    VldbMixin,
)
from mstrio.utils.filter import Filter
from mstrio.utils.helper import (
    exception_handler,
    fallback_on_timeout,
    get_parallel_number,
    get_valid_project_id,
    response_handler,
    sort_object_properties,
)
from mstrio.utils.parser import Parser
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.translation_mixin import TranslationMixin


def list_reports(
    connection: Connection,
    name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    folder_id: str | None = None,
    folder_path: str | None = None,
    **filters,
) -> list[type['Report']] | list[dict]:
    """Get list of Report objects or dicts with them.
    Optionally filter reports by specifying 'name'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name':
        ? - any character
        * - 0 or more of any characters
        e.g. name = ?onny will return Sonny and Tonny

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Note:
        When `project_id` is `None` and `project_name` is `None`,
        then its value is overwritten by `project_id` from `connection` object.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name (string, optional): value the search pattern is set to, which
            will be applied to the names of reports being searched
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Report objects
        search_pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Contains. Possible values are available
            in ENUM mstrio.object_management.SearchPattern.
            Default value is BEGIN WITH (4).
        project_id (string, optional): Project ID
        project_name (string, optional): Project name
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        folder_id (string, optional): ID of a folder where the search
            will be performed. Defaults to None.
        folder_path (str, optional): Path of the folder in which the search
            will be performed. Can be provided as an alternative to `folder_id`
            parameter. If both are provided, `folder_id` is used.
                    the path has to be provided in the following format:
                        if it's inside of a project, example:
                            /MicroStrategy Tutorial/Public Objects/Metrics
                        if it's a root folder, example:
                            /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']

    Returns:
        list with Report objects or list of dictionaries
    """
    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=not project_name,
    )

    objects_ = full_search(
        connection,
        object_types=ObjectTypes.REPORT_DEFINITION,
        project=project_id,
        name=name,
        pattern=search_pattern,
        limit=limit,
        root=folder_id,
        root_path=folder_path,
        **filters,
    )
    reports = [
        item for item in objects_ if Report._is_subtype_supported(item['subtype'])
    ]
    if to_dictionary:
        return reports
    return [
        Report.from_dict(
            source=report_dict, connection=connection, with_missing_value=True
        )
        for report_dict in reports
    ]


class Report(
    Entity,
    CertifyMixin,
    CopyMixin,
    MoveMixin,
    DeleteMixin,
    ContentCacheMixin,
    TranslationMixin,
    VldbMixin,
):
    """Access, filter, publish, and extract data from in-memory reports.

    Create a Report object to load basic information on a report dataset.
    Specify subset of report to be fetched through `Report.apply_filters()` and
    `Report.clear_filters()`. Fetch dataset through `Report.to_dataframe()`
    method.

    _CACHE_TYPE is a variable used by ContentCache class for cache filtering
    purposes.

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
        sql: SQL View of the Report
        attributes: List of attributes
        metrics: List of metrics
        page_by_attributes: List of attributes selected for Page By
        attr_elements: All attributes elements of report
        page_by_elements: Elements of attributes selected for Page By in the
            report. The IDs are in the terse format used for page selection,
            which is different than the one used in the attr_elements field.
        current_page_by: Attribute elements selected for Page By in the report
        selected_attributes: IDs of filtered attributes
        selected_metrics: IDs of filtered metrics
        selected_attr_elements: IDs of filtered attribute elements
        dataframe: content of a report extracted into a Pandas `DataFrame`
        prompts: List of report prompts
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION
    _OBJECT_SUBTYPES = [
        ObjectSubTypes.REPORT_GRID,
        ObjectSubTypes.REPORT_GRAPH,
        ObjectSubTypes.REPORT_ENGINE,
        ObjectSubTypes.REPORT_GRID_AND_GRAPH,
        ObjectSubTypes.REPORT_TRANSACTION,
        ObjectSubTypes.REPORT_HYPER_CARD,
    ]
    _CACHE_TYPE = CacheSource.Type.REPORT
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict,
    }
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes

    _API_PATCH: dict = {
        ('name', 'description', 'abbreviation', 'hidden', 'folder_id'): (
            objects_processors.update,
            'partial_put',
        )
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
        instance_id: str | None = None,
        parallel: bool = True,
        progress_bar: bool = True,
    ):
        """Initialize an instance of a report.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing report containing
                the required data.
            name (str): Name of the report to be looked up if ID is not provided
            instance_id (str): Identifier of an instance if report instance has
                been already initialized, NULL by default.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download
                progress bar.
        """

        connection._validate_project_selected()

        if id is None and name is None:
            raise ValueError(
                "Please specify either 'id' or 'name' parameter in the constructor."
            )

        if id is None:
            result: list[dict] = list_reports(connection, name=name, to_dictionary=True)

            if result:
                object_data = result[0]
                self._init_variables(**object_data, connection=connection)
            else:
                raise ValueError(f"There is no Report named: '{name}'.")
        elif id == '':
            raise ValueError("Report ID cannot be an empty string.")
        else:
            super().__init__(
                connection,
                id,
                instance_id=instance_id,
                parallel=parallel,
                progress_bar=progress_bar,
            )

    def _init_variables(self, default_value, **kwargs):
        super()._init_variables(default_value=default_value, **kwargs)
        self.instance_id = kwargs.get("instance_id")
        self._parallel = kwargs.get("parallel", True)
        self._initial_limit = 1000
        self._progress_bar = kwargs.get("progress_bar", True) and config.progress_bar
        self._cross_tab = False
        self._cross_tab_filter = {}
        self._subtotals = {}
        self._dataframe = None
        self._attr_elements = None
        self._page_by_elements = {}
        self._sql = None
        self._current_page_by = []
        self._prompts = None

        self._attributes = []
        self._metrics = []
        self._page_by_attributes = []
        self.__definition_retrieved = False
        self.__filter = None

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        hidden: bool | None = None,
    ):
        """Alter Report properties.

        Args:
            name: new name of the Report
            description: new description of the Report
            abbreviation: new abbreviation of the Report
            hidden: Specifies whether the metric is hidden
        """
        func = self.alter
        args = func.__code__.co_varnames[: func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def to_dataframe(
        self,
        limit: int | None = None,
        page_element_id: str | list[str] | dict[str, str] | None = None,
        prompt_answers: list[Prompt] | None = None,
    ) -> pd.DataFrame:
        """Extract contents of a report instance into a Pandas `DataFrame`.

        Args:
            limit (None or int, optional): Used to control data extract
                behavior. By default (None) the limit is calculated
                automatically, based on an optimized physical size of one chunk.
                Setting limit manually will force the number of rows per chunk.
                Depending on system resources, a higher limit (e.g. 50,000) may
                reduce the total time required to extract the entire dataset.
            page_element_id (str, list[str] or dict[str, str], optional): ID of
                the attribute elements chosen for Page By, for example,
                `'h4;8D679D3511D3E4981000E787EC6DE8A4'`.
                If passed as a list, the attribute elements should be listed in
                the same order as the attributes in the `page_by_attributes`
                field. If passed as a dictionary, the keys should be the
                attribute IDs and the values should be the attribute
                element IDs.
            prompt_answers (None or list of Prompts, optional): List of Prompt
                class objects answering the prompts of the report. Only needed
                if the report has prompts.

        Returns:
            Pandas Data Frame containing the report contents.
        """
        if limit:
            self._initial_limit = limit

        attr_ids = [a['id'] for a in self.page_by_attributes]
        if isinstance(page_element_id, str):
            page_element_id = [page_element_id]
        if isinstance(page_element_id, dict):
            page_element_id = [page_element_id.get(attr_id, "") for attr_id in attr_ids]

        if page_element_id:
            page_element_id = [
                str(el_id).partition(';')[0] + ';' + attr
                for el_id, attr in zip(page_element_id, attr_ids)
            ]

        if self.instance_id is None or page_element_id != self._current_page_by:
            self._current_page_by = page_element_id
            res = self.__initialize_report(self._initial_limit)
        else:
            # try to get first chunk from already initialized instance of report
            # if not possible, initialize new instance
            try:
                res = self.__get_chunk(
                    instance_id=self.instance_id, offset=0, limit=self._initial_limit
                )
            except requests.HTTPError:
                res = self.__initialize_report(self._initial_limit)

        _instance = res.json()
        self.instance_id = _instance['instanceId']

        # Answer prompts if provided
        if prompt_answers:
            json = {"prompts": [prompt.to_dict() for prompt in prompt_answers]}
            reports_api.answer_report_prompts(
                connection=self._connection,
                report_id=self.id,
                instance_id=self.instance_id,
                body=json,
            )
            # Get the instance results again, as they weren't generated
            # properly until the prompts were answered
            _instance = reports_api.report_instance_id(
                connection=self.connection,
                report_id=self.id,
                instance_id=self.instance_id,
                offset=0,
                limit=self._initial_limit,
            ).json()

        # Gets the pagination totals from the response object
        paging = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=_instance, parse_cube=False)
        p.parse(response=_instance)

        # If there are more rows to fetch, fetch them
        if paging['current'] != paging['total']:
            if not limit:
                limit = max(
                    1000,
                    int((self._initial_limit * self._SIZE_LIMIT) / len(res.content)),
                )
            # Count the number of additional iterations
            it_total = int((paging['total'] - self._initial_limit) / limit) + (
                (paging['total'] - self._initial_limit) % limit != 0
            )

            if self._parallel and it_total > 1:
                threads = get_parallel_number(it_total)
                with FuturesSessionWithRenewal(
                    connection=self._connection, max_workers=threads
                ) as session:
                    fetch_pbar = tqdm(
                        desc="Downloading",
                        total=it_total + 1,
                        disable=(not self._progress_bar),
                    )
                    future = self.__fetch_chunks_future(
                        session, paging, self.instance_id, limit
                    )
                    fetch_pbar.update()
                    for i, f in enumerate(future, start=1):
                        response = f.result()
                        if not response.ok:
                            response_handler(response, "Error getting report contents.")
                        fetch_pbar.update()
                        fetch_pbar.set_postfix(
                            rows=str(
                                min(self._initial_limit + i * limit, paging['total'])
                            )
                        )
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
                    el['name']
                    for el in list(
                        filter(
                            lambda x: x['id'] not in self._cross_tab_filter['metrics'],
                            self.metrics,
                        )
                    )
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
                    attr_name = list(
                        filter(
                            lambda x, attr=attribute: x['id'] in attr, self.attributes
                        )
                    )[0]['name']
                    elements = attr_dict[attribute]
                    indexes = indexes | self._dataframe[attr_name].isin(elements)
                # select dataframe indexes with
                self._dataframe = self._dataframe[indexes]

            if self._cross_tab_filter['attributes'] is not None:
                attr_names = [
                    el['name']
                    for el in list(
                        filter(
                            lambda x: x['id']
                            not in self._cross_tab_filter['attributes'],
                            self.attributes,
                        )
                    )
                ]
                # filtering out attribute forms columns
                to_be_removed = []
                to_be_added = []
                for attr in attr_names:
                    forms = [
                        column
                        for column in self._dataframe.columns
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
        """Fetch added rows from this object instance from the Intelligence
        Server."""
        return [
            reports_api.report_instance_id_coroutine(
                future_session,
                report_id=self._id,
                instance_id=instance_id,
                offset=_offset,
                limit=limit,
            )
            for _offset in range(self._initial_limit, pagination['total'], limit)
        ]

    def __fetch_chunks(self, parser, pagination, it_total, instance_id, limit):
        """Fetch added rows from this object instance from the Intelligence
        Server."""
        with tqdm(
            desc="Downloading", total=it_total + 1, disable=(not self._progress_bar)
        ) as fetch_pbar:
            fetch_pbar.update()
            for _offset in range(self._initial_limit, pagination['total'], limit):
                response = self.__get_chunk(
                    instance_id=instance_id, offset=_offset, limit=limit
                )
                fetch_pbar.update()
                fetch_pbar.set_postfix(
                    rows=str(min(_offset + limit, pagination['total']))
                )
                parser.parse(response=response.json())

    def __initialize_report(self, limit: int) -> requests.Response:
        inst_pbar = tqdm(
            desc='Initializing an instance of a report. Please wait...',
            bar_format='{desc}',
            leave=False,
            ncols=285,
            disable=(not self._progress_bar),
        )

        # Switch off subtotals if I-Server version is higher than 11.2.1
        body = self._filter._request_body()
        if version.parse(self._connection.iserver_version) >= version.parse(
            "11.2.0100"
        ):
            self._subtotals["visible"] = False
            body["subtotals"] = {"visible": self._subtotals["visible"]}

        if self._current_page_by:
            body["currentPageBy"] = [{"id": el} for el in self._current_page_by]

        # Request a new instance, set instance id
        response = reports_api.report_instance(
            connection=self._connection,
            report_id=self._id,
            body=body,
            offset=0,
            limit=limit or self._initial_limit,
        )
        inst_pbar.close()
        return response

    def __get_chunk(
        self, instance_id: str, offset: int, limit: int
    ) -> requests.Response:
        return reports_api.report_instance_id(
            connection=self._connection,
            report_id=self._id,
            instance_id=instance_id,
            offset=offset,
            limit=limit,
        )

    def apply_filters(
        self,
        attributes: list | None = None,
        metrics: list | None = None,
        attr_elements: list | None = None,
        operator: str = 'In',
    ) -> None:
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
        filtering_is_requested = bool(
            not all(element is None for element in [attributes, metrics, attr_elements])
        )

        if self._cross_tab:
            self._cross_tab_filter = {
                'attributes': attributes,
                'metrics': metrics,
                'attr_elements': attr_elements,
            }
        elif filtering_is_requested:
            self._filter._clear(
                attributes=attributes, metrics=metrics, attr_elements=attr_elements
            )
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
        response = reports_api.report_definition(
            connection=self._connection, report_id=self._id
        ).json()

        grid = response["definition"]["grid"]
        available_objects = response['definition']['availableObjects']

        if version.parse(self._connection.iserver_version) >= version.parse(
            "11.2.0100"
        ):
            self._subtotals = grid["subtotals"]
        self.name = response["name"]
        self._cross_tab = grid["crossTab"]

        # Check if report have custom groups or consolidations
        if available_objects['customGroups']:
            exception_handler(
                msg="Reports with custom groups are not supported.",
                exception_type=ImportError,
            )
        if available_objects['consolidations']:
            exception_handler(
                msg="Reports with consolidations are not supported.",
                exception_type=ImportError,
            )

        full_attributes = []
        full_page_by_attributes = []
        for row in grid["rows"]:
            if row["type"] == "attribute":
                full_attributes.append(row)
        for column in grid["columns"]:
            if column["type"] == "attribute":
                full_attributes.append(column)
        for paging in grid["pageBy"]:
            if paging["type"] == "attribute":
                full_page_by_attributes.append(paging)
        self._attributes = [
            {'name': attr['name'], 'id': attr['id']} for attr in full_attributes
        ]
        self._page_by_attributes = [
            {'name': attr['name'], 'id': attr['id']} for attr in full_page_by_attributes
        ]

        # Retrieve metrics from the report grid (only selected metrics)
        metrics_position = grid.get("metricsPosition")
        if metrics_position is None:
            self._metrics = []
        else:
            full_metrics = grid[metrics_position["axis"]][metrics_position["index"]][
                "elements"
            ]
            self._metrics = [
                {'name': metr['name'], 'id': metr['id']} for metr in full_metrics
            ]

        self.__definition_retrieved = True

    def __get_attr_elements(self, limit: int = 50000) -> list:
        """Get elements of report attributes synchronously.

        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements.
        """

        def fetch_for_attribute(attribute):
            @fallback_on_timeout()
            def fetch_for_attribute_given_limit(limit):
                response = reports_api.report_single_attribute_elements(
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
                    response = reports_api.report_single_attribute_elements(
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
                    "elements": elements,
                }

            return fetch_for_attribute_given_limit(limit)[0]

        attrs = []
        attr_elements = []
        if self.attributes:
            attrs += self.attributes
        if self.page_by_attributes:
            attrs += self.page_by_attributes
        pbar = tqdm(
            attrs,
            desc="Loading attribute elements",
            leave=False,
            disable=(not self._progress_bar),
        )
        attr_elements = [fetch_for_attribute(attribute) for attribute in pbar]

        return attr_elements

    def __get_attr_elements_async(self, limit: int = 50000) -> list:
        """Get elements of report attributes asynchronously.

        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements.
        """

        attrs = []
        attr_elements = []
        if self.attributes:
            attrs += self.attributes
        if self.page_by_attributes:
            attrs += self.page_by_attributes

        if attrs:
            threads = get_parallel_number(len(attrs))
            with FuturesSessionWithRenewal(
                connection=self._connection, max_workers=threads
            ) as session:
                # Fetch first chunk of attribute elements.
                futures = self.__fetch_attribute_elements_chunks(session, limit)
                pbar = tqdm(
                    futures,
                    desc="Loading attribute elements",
                    leave=False,
                    disable=(not self._progress_bar),
                )
                for i, future in enumerate(pbar):
                    attr = attrs[i]
                    response = future.result()
                    if not response.ok:
                        response_handler(
                            response, f"Error getting attribute {attr['name']} elements"
                        )
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = reports_api.report_single_attribute_elements(
                            connection=self._connection,
                            report_id=self._id,
                            attribute_id=attr["id"],
                            offset=_offset,
                            limit=limit,
                        )
                        elements.extend(response.json())
                    # Append attribute data to the list of attributes.
                    attr_elements.append(
                        {
                            "attribute_name": attr['name'],
                            "attribute_id": attr['id'],
                            "elements": elements,
                        }
                    )
                pbar.close()

            return attr_elements

    def __fetch_attribute_elements_chunks(self, future_session, limit: int) -> list:
        # Fetch add'l rows from this object instance
        return [
            reports_api.report_single_attribute_elements_coroutine(
                future_session,
                report_id=self._id,
                attribute_id=attribute['id'],
                offset=0,
                limit=limit,
            )
            for attribute in self.attributes + self.page_by_attributes
        ]

    def list_properties(self):
        """List all properties of the object."""

        attributes = {
            key: self.__dict__[key] for key in self.__dict__ if not key.startswith('_')
        }
        attributes = {
            **attributes,
            "id": self.id,
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
            "metrics": self.metrics,
        }
        return {
            key: attributes[key]
            for key in sorted(attributes, key=sort_object_properties)
        }

    def list_available_schedules(
        self, to_dictionary: bool = False
    ) -> list["Schedule"] | list[dict]:
        """Get a list of schedules available for the report.

        Args:
            to_dictionary (bool, optional): If True returns a list of
                dictionaries, otherwise returns a list of Schedules.
                False by default.

        Returns:
            List of Schedule objects or list of dictionaries.
        """
        schedules_list_response = (
            get_contents_schedule(
                connection=self.connection,
                project_id=self.connection.project_id,
                body={'id': self.id, 'type': 'report'},
            )
            .json()
            .get('schedules')
        )
        if to_dictionary:
            return schedules_list_response
        return [
            Schedule.from_dict(connection=self.connection, source=schedule_id)
            for schedule_id in schedules_list_response
        ]

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
    def page_by_attributes(self):
        if not self.__definition_retrieved:
            self._get_definition()
        return self._page_by_attributes

    @property
    def attr_elements(self):
        if not self.__definition_retrieved:
            self._get_definition()
        if not self._attr_elements and self._id:
            if self._parallel is True:
                # TODO: move the fallback inside the function to apply
                # per-attribute, like with non-async version.
                self._attr_elements = fallback_on_timeout()(
                    self.__get_attr_elements_async
                )(50000)[0]
            else:
                self._attr_elements = self.__get_attr_elements()
            self._filter._populate_attr_elements(self._attr_elements)
        return self._attr_elements

    @property
    def page_by_elements(self):
        """Elements of attributes selected for Page By in the report.
        The IDs are in the terse format used for page selection.
        """
        for attr in self.page_by_attributes:
            attr_id = attr['id']
            if attr_id not in self._page_by_elements:
                response = attributes_api.get_attribute_elements(
                    connection=self._connection, id=attr['id']
                )
                element_ids = [el['id'] for el in response.json()]
                self._page_by_elements[attr_id] = element_ids
        return self._page_by_elements

    @property
    def current_page_by(self):
        """Selected page of the report broken down by selected attributes."""
        return self._current_page_by

    @property
    def _filter(self):
        if not self.__definition_retrieved:
            self._get_definition()
        if self.__filter is None:
            self.__filter = Filter(
                attributes=self._attributes,
                metrics=self._metrics,
                attr_elements=self._attr_elements,
            )
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
            exception_handler(
                msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                exception_type=Warning,
            )
        return self._dataframe

    @property
    def sql(self) -> str:
        """SQL View of the Report."""
        if self._sql is None:
            temp_instance_id = (
                self.instance_id
                if self.instance_id
                else reports_api.report_instance(
                    connection=self.connection,
                    report_id=self.id,
                    execution_stage='resolve_prompts',
                )
                .json()
                .get('instanceId')
            )
            self._sql = (
                reports_api.report_sql(
                    connection=self._connection,
                    report_id=self.id,
                    instance_id=temp_instance_id,
                )
                .json()
                .get('sqlStatement')
            )
        return self._sql

    @property
    def prompts(self) -> dict:
        """Prompts of the report."""
        if self._prompts is None:
            prompts = reports_api.get_report_prompts(
                connection=self.connection, report_id=self.id
            ).json()
            self._prompts = [Prompt.from_dict(prompt) for prompt in prompts]
        return self._prompts
