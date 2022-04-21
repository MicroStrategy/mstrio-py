from enum import Enum
import logging
from operator import itemgetter
from typing import List, Optional, TYPE_CHECKING, Union

from pandas.core.frame import DataFrame
import requests
from tqdm.auto import tqdm

from mstrio import config
from mstrio.api import cubes, datasets
from mstrio.connection import Connection
from mstrio.object_management.search_operations import full_search, SearchPattern
from mstrio.project_objects.datasets import cube_cache
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import DeleteMixin, Entity, VldbMixin
from mstrio.utils.filter import Filter
from mstrio.utils.helper import choose_cube, exception_handler, fallback_on_timeout
import mstrio.utils.helper as helper
from mstrio.utils.parser import Parser
from mstrio.utils.sessions import FuturesSessionWithRenewal

if TYPE_CHECKING:
    from .cube_cache import CubeCache
    from .olap_cube import OlapCube
    from .super_cube import SuperCube

logger = logging.getLogger(__name__)


class CubeStates(Enum):
    ACTIVE = 2
    DIRTY = 16
    DIRTY_INFO = 8
    FOREIGN = 2048
    IMPORTED = 1024
    LOAD_PENDING = 128
    LOADED = 32
    PENDING_FOR_ENGINE = 512
    PERSISTED = 4
    PROCESSING = 1
    READY = 64
    RESERVED = 0
    UNLOAD_PENDING = 256
    UNKNOWN1 = 4096
    UNKNOWN2 = 8192
    UNKNOWN3 = 16384

    @classmethod
    def show_status(cls, status: int) -> List[str]:
        """Show states of a cube calculated from numerical value of its state.
        Additionally list of those states' names is returned.

        Args:
            status (integer): numerical value of cube's status

        Returns:
            List with names of cube's states.
        """

        def parse_cube_status_bin_to_list(status_bin: int) -> List[str]:
            output = []
            # sort states from enum based on its value and return as a table of
            # tuples (value, name)
            states = sorted(((s.value, s.name) for s in cls), key=lambda x: -x[0])
            for state in states:
                if status_bin >= state[0]:
                    status_bin -= state[0]
                    output.append(state[1])
            return output

        states = parse_cube_status_bin_to_list(status)
        output = []
        for state in states:
            if 'UNKNOWN' in state:
                continue
            output.append(' '.join(s.capitalize() for s in state.split('_')))
        print(', '.join(output))
        return output


def list_all_cubes(connection: Connection, name_begins: Optional[str] = None,
                   to_dictionary: bool = False, limit: Optional[int] = None,
                   **filters) -> Union[List[Union["OlapCube", "SuperCube"]], List[dict]]:
    """Get list of Cube objects (OlapCube or SuperCube) or dicts with them.
    Optionally filter cubes by specifying 'name_begins'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name_begins':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins (string, optional): characters that the cube name must begin
            with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns SuperCube/OlapCube objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']

    Returns:
        list with OlapCubes and SuperCubes or list of dictionaries
    """
    connection._validate_project_selected()
    objects_ = full_search(connection, project=connection.project_id, name=name_begins,
                           object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE],
                           pattern=SearchPattern.BEGIN_WITH, limit=limit, **filters)
    if to_dictionary:
        return objects_
    else:
        all_cubes = []
        for object_ in objects_:
            cube_subtype = object_['subtype']
            if cube_subtype == int(ObjectSubTypes.OLAP_CUBE):
                from .olap_cube import OlapCube
                all_cubes.append(OlapCube.from_dict(object_, connection))
            elif cube_subtype == int(ObjectSubTypes.SUPER_CUBE):
                from .super_cube import SuperCube
                all_cubes.append(SuperCube.from_dict(object_, connection))
        return all_cubes


def load_cube(
    connection: Connection, cube_id: Optional[str] = None, cube_name: Optional[str] = None,
    folder_id: Optional[str] = None, instance_id: Optional[str] = None
) -> Union["OlapCube", "SuperCube", List[Union["OlapCube", "SuperCube"]]]:
    """Load single cube specified by either 'cube_id' or both 'cube_name' and
    'folder_id'.

    It is also possible to load cube by providing only `cube_name`, but in that
    case we may retrieve more than one cube as cube's name is unique only within
    a folder.

    `instance_id` is used only when a single cube is retrieved.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        cube_id(string, optional): ID of cube
        cube_name(string, optional): name of cube
        folder_id(string, optional): ID of folder in which the cube is stored
        instance_id (str, optional): Identifier of an instance if cube instance
            has been already initialized. Will be used if only one cube is
            found. `None` by default.

    Returns:
         object of type OlapCube or SuperCube based on the subtype of a cube
         returned from metadata.

    Raises:
        ValueError when neither `cube_id` nor `cube_name` are provided.
    """
    connection._validate_project_selected()

    if cube_id:
        if cube_name:
            msg = "Both `cube_id` and `cube_name` provided. Loading cube based on `cube_id`."
            exception_handler(msg, Warning, False)
        elif folder_id:
            msg = ("Both `cube_id` and `folder_id` provided. "
                   "Loading cube based on `cube_id` from all folders.")
            exception_handler(msg, Warning, False)
        objects_ = full_search(connection, project=connection.project_id,
                               object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE],
                               pattern=SearchPattern.EXACTLY, id=cube_id)
    elif not cube_name:
        msg = "Specify either `cube_id` or `cube_name`."
        raise ValueError(msg)
    else:  # getting cube by `cube_name` and optionally `folder_id`
        objects_ = full_search(connection, project=connection.project_id, name=cube_name,
                               object_types=[ObjectSubTypes.OLAP_CUBE, ObjectSubTypes.SUPER_CUBE],
                               pattern=SearchPattern.EXACTLY, root=folder_id)

    ret_cubes = []
    for object_ in objects_:
        object_ = object_ if len(objects_) > 1 else {**object_, "instance_id": instance_id}

        ret_cubes.append(choose_cube(connection, object_))
        ret_cubes = [tmp for tmp in ret_cubes if tmp]  # remove `None` values

    if len(ret_cubes) == 0:
        exception_handler("Cube was not found.", Warning, False)
        return None
    elif len(ret_cubes) == 1:
        return ret_cubes[0]
    else:
        exception_handler(f"More than one cube with name {cube_name} was loaded.", Warning, False)
        return ret_cubes


class _Cube(Entity, VldbMixin, DeleteMixin):
    """Access, filter, publish, and extract data from MicroStrategy in-memory
    cubes.

    Create a Cube object to load basic information on a cube dataset. Specify
    subset of cube to be fetched through `Cube.apply_filters()` and
    `Cube.clear_filters()`. Fetch dataset through `Cube.to_dataframe()` method.

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id: Identifier of a pre-existing cube containing the required data.
        instance_id (str): Identifier of an instance if cube instance has been
            already initialized, NULL by default.
    """
    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION
    _OBJECT_SUBTYPE = ObjectSubTypes.NONE.value
    # TODO maybe add cube_info call and attribute to
    # TODO API_GETTERS **{('TODO'): cubes.cube_info}
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP, 'owner': User.from_dict,
        'certified_info': CertifiedInfo.from_dict
    }
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, id: str, name: Optional[str] = None,
                 instance_id: Optional[str] = None, parallel: bool = True,
                 progress_bar: bool = True):
        """Initialize an instance of a cube by its id.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing cube containing
                the required data.
            name (str): Name of a cube.
            instance_id (str): Identifier of an instance if cube instance has
                been already initialized, None by default.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download
                progress bar.
        """
        super().__init__(connection, id, name=name, instance_id=instance_id, parallel=parallel,
                         progress_bar=progress_bar, subtype=self._OBJECT_SUBTYPE)
        connection._validate_project_selected()
        self._get_definition()

    def _init_variables(self, **kwargs):
        super()._init_variables(**kwargs)
        self.instance_id = kwargs.get("instance_id")
        self._parallel = kwargs.get("parallel", True)
        self._initial_limit = 1000
        self._progress_bar = True if kwargs.get("progress_bar",
                                                True) and config.progress_bar else False
        self._table_definition = {}
        self._dataframe = None
        self._dataframes = []
        self._attr_elements = None
        # these properties were not fetched from self.__definition() and will be
        # lazily fetched when calling properties `attributes` or `metrics`
        self._attributes = []
        self._metrics = []
        self._row_counts = []
        self._table_names = []
        self.__definition_retrieved = False
        # these properties were not fetched from self.__info() and all will be
        # lazily fetched when calling any of properties: `owner_id`, `path`,
        # `size`, `status`
        self._owner_id = None
        self._path = None
        self._server_mode = None
        self._size = None
        self._status = None
        self.__info_retrieved = False
        self.__filter = None

        # caches will be lazily retrieved from I-Server when calling  for cube's
        # property `caches`
        self._caches = None

    def alter(self, name: Optional[str] = None, description: Optional[str] = None,
              abbreviation: Optional[str] = None):
        """Alter Cube properties.

        Args:
            name: new name of the Dataset
            description: new description of the Dataset
            abbreviation: new abbreviation of the Dataset
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

    def get_caches(self) -> List["CubeCache"]:
        """Get list of caches of the cube.

        Returns:
            list of caches of the cube
        """
        self._caches = cube_cache.list_cube_caches(self._connection, cube_id=self._id)
        return self._caches

    def to_dataframe(self, limit: Optional[int] = None, multi_df: bool = False):
        """Extract contents of a cube into a Pandas `DataFrame`.

        Args:
            limit (None or int, optional): Used to control data extract
                behavior. By default (None) the limit is calculated
                automatically, based on an optimized physical size of one chunk.
                Setting limit manually will force the number of rows per chunk.
                Depending on system resources, a higher limit (e.g. 50,000) may
                reduce the total time required to extract the entire dataset.
            multi_df (bool, optional): If True, return a list of data frames
                resembling the table structure of the cube. If False (default),
                returns one data frame.

        Returns:
            Pandas Data Frame containing the cube contents
        """
        if limit:
            self._initial_limit = limit

        if self.instance_id is None:
            res = self.__create_cube_instance(self._initial_limit)
        else:

            # try to get first chunk from already initialized instance of cube,
            # if not possible, initialize new instance
            try:
                res = cubes.cube_instance_id(connection=self.connection, cube_id=self._id,
                                             instance_id=self.instance_id, offset=0,
                                             limit=self._initial_limit)
            except requests.HTTPError:
                res = self.__create_cube_instance(self._initial_limit)

        # Gets the pagination totals and instance_id from the response object
        _instance = res.json()
        self.instance_id = _instance['instanceId']
        paging = _instance['data']['paging']

        # initialize parser and process first response
        p = Parser(response=_instance, parse_cube=True)
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
                            helper.response_handler(response, "Error getting cube contents.")
                        fetch_pbar.update()
                        fetch_pbar.set_postfix(
                            rows=str(min(self._initial_limit + i * limit, paging['total'])))
                        p.parse(response.json())
                    fetch_pbar.close()
            else:
                self.__fetch_chunks(p, paging, it_total, self.instance_id, limit)

        # return parsed data as a data frame
        self._dataframe = p.dataframe
        # split dataframe to dataframes matching tables in Cube
        if multi_df:
            # split dataframe to dataframes matching tables in Cube
            self._dataframes = [
                self._dataframe[columns].copy()
                for _, columns in self.__multitable_definition().items()
            ]
            return self._dataframes
        else:
            return self._dataframe

    def __fetch_chunks_future(self, future_session, pagination, instance_id, limit):
        """Fetch add'l rows from this object instance from the Intelligence
        Server."""
        return [
            cubes.cube_instance_id_coroutine(
                future_session,
                connection=self._connection,
                cube_id=self._id,
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
                response = cubes.cube_instance_id(connection=self.connection, cube_id=self._id,
                                                  instance_id=instance_id, offset=_offset,
                                                  limit=limit)
                fetch_pbar.update()
                fetch_pbar.set_postfix(rows=str(min(_offset + limit, pagination['total'])))
                parser.parse(response=response.json())

    def __create_cube_instance(self, limit):
        inst_pbar = tqdm(desc='Initializing an instance of a cube. Please wait...',
                         bar_format='{desc}', leave=False, ncols=280,
                         disable=(not self._progress_bar))
        # Request a new instance, set instance id
        response = cubes.cube_instance(
            connection=self._connection,
            cube_id=self._id,
            body=self._filter._filter_body(),
            offset=0,
            limit=self._initial_limit,
        )
        inst_pbar.close()
        return response

    def apply_filters(self, attributes: Optional[list] = None, metrics: Optional[list] = None,
                      attr_elements: Optional[list] = None, operator: str = 'In') -> None:
        """Apply filters on the cube's objects.

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
        params = [attributes, metrics, attr_elements]
        filtering_is_requested = bool(not all(el is None for el in params))

        if filtering_is_requested:
            self._filter._clear(attributes=attributes, metrics=metrics,
                                attr_elements=attr_elements)
            self._filter.operator = operator
            self._select_attribute_filter_conditionally(attributes)
            self._select_metric_filter_conditionally(metrics)
            self._select_attr_el_filter_conditionally(attr_elements)
            # Clear instance, to generate new with new filters
            self.instance_id = None

    def _select_attribute_filter_conditionally(self, attributes_filtered):
        if attributes_filtered:
            self._filter._select(object_id=attributes_filtered)
        elif attributes_filtered is not None:
            self._filter.attr_selected = []

    def _select_metric_filter_conditionally(self, metrics_filtered):
        if metrics_filtered:
            self._filter._select(object_id=metrics_filtered)
        elif metrics_filtered is not None:
            self._filter.metr_selected = []

    def _select_attr_el_filter_conditionally(self, attr_el_filtered):
        if attr_el_filtered is not None:
            self._filter._select_attr_el(element_id=attr_el_filtered)

    def clear_filters(self) -> None:
        """Clear previously set filters, allowing all attributes, metrics, and
        attribute elements to be retrieved."""

        self._filter._clear()

        # once again remove Row Count metrics
        metrics_ids = [metric_id['id'] for metric_id in self.metrics]
        self._filter._select(metrics_ids)
        # Clear instance, to generate new with new filters
        self.instance_id = None

    def refresh_status(self) -> None:
        """Refresh cube's status and show which states it represents."""
        res = cubes.status(self._connection, self._id)
        if res.ok:
            self._status = int(res.headers['X-MSTR-CubeStatus'])

    def show_status(self) -> List[str]:
        """Show which states are represented by cube's status."""
        return CubeStates.show_status(self.status)

    def list_properties(self) -> dict:
        """List all properties of the object."""

        attributes = {key: self.__dict__[key] for key in self.__dict__ if not key.startswith('_')}
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
            "size": self.size,
            "status": self.status,
            "path": self.path,
            "attributes": self.attributes,
            "metrics": self.metrics,
        }
        return {
            key: attributes[key] for key in sorted(attributes, key=helper.sort_object_properties)
        }

    def _get_info(self) -> None:
        """Get metadata for specific cubes.

        Implements GET /cubes to retrieve basic metadata.
        """
        if self._id is not None:
            res = cubes.cube_info(connection=self._connection, id=self._id)

            _info = res.json()["cubesInfos"][0]
            self.name = _info["cubeName"]  # duplicated
            self._owner_id = _info["ownerId"]
            self._path = _info["path"]
            self._server_mode = _info["serverMode"]
            self._size = _info["size"]
            self._status = _info["status"]

            # for lazy fetch properties
            self.__info_retrieved = True

    def _get_definition(self) -> None:
        """Get the definition of a cube, including attributes and metrics.

        Implements GET /v2/cubes/<cube_id>.
        """
        if self._id is not None:
            _definition = cubes.cube_definition(connection=self._connection, id=self._id).json()
            full_attributes = _definition["definition"]["availableObjects"]["attributes"]
            full_metrics = _definition["definition"]["availableObjects"]["metrics"]
            self._attributes = [{
                'name': attr['name'],
                'id': attr['id']
            } for attr in full_attributes]
            self._metrics = [{'name': metr['name'], 'id': metr['id']} for metr in full_metrics]

            self._table_names = self.__multitable_definition().keys()
            row_counts = [f'Row Count - {table_name}' for table_name in self._table_names]
            self._row_counts = list(filter(lambda x: x['name'] in row_counts, self._metrics))
            self.__remove_row_count()
            # for lazy fetch properties
            self.__definition_retrieved = True

    def __multitable_definition(self):
        """Return all tables names and columns as a dictionary."""
        if not self._table_definition:
            res_tables = datasets.dataset_definition(connection=self._connection, id=self._id,
                                                     fields=['tables', 'columns'],
                                                     whitelist=[('ERR001', 500)])
            if res_tables.ok:
                ds_definition = res_tables.json()
                for table in ds_definition['result']['definition']['availableObjects']['tables']:
                    column_list = [
                        column['columnName'] for column in ds_definition['result']['definition']
                        ['availableObjects']['columns'] if table['name'] == column['tableName']
                    ]
                    self._table_definition[table['name']] = column_list
        return self._table_definition

    def __remove_row_count(self):
        """Remove all Row Count metrics from cube."""
        row_counts = list(map(itemgetter('name'), self._row_counts))
        self._metrics = list(filter(lambda x: x['name'] not in row_counts, self._metrics))

    def __get_attr_elements(self, limit=50000):
        """Get elements of report attributes synchronously.

        Implements GET /reports/<report_id>/attributes/<attribute_id>/elements.
        """

        def fetch_for_attribute(attribute):

            @fallback_on_timeout()
            def fetch_for_attribute_given_limit(limit):
                response = cubes.cube_single_attribute_elements(
                    connection=self._connection,
                    cube_id=self._id,
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
                    response = cubes.cube_single_attribute_elements(
                        connection=self._connection,
                        cube_id=self._id,
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

    def __get_attr_elements_async(self, limit=50000):
        """Get attribute elements.

        Implements GET /cubes/<cube_id>/attributes/<attribute_id>/elements.
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
                            response, "Error getting attribute " + attr["name"] + " elements")
                    elements = response.json()
                    # Get total number of rows from headers.
                    total = int(response.headers['x-mstr-total-count'])
                    for _offset in range(limit, total, limit):
                        response = cubes.cube_single_attribute_elements(
                            connection=self._connection,
                            cube_id=self._id,
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

    def __fetch_attribute_elements_chunks(self, future_session, limit):
        """Fetch add'l rows from this object instance from the Intelligence
        Server"""
        return [
            cubes.cube_single_attribute_elements_coroutine(
                future_session,
                connection=self._connection,
                cube_id=self._id,
                attribute_id=attribute['id'],
                offset=0,
                limit=limit,
            ) for attribute in self.attributes
        ]

    def unpublish(self, force: bool = False) -> bool:
        """Unpublish Cube by removing all of its caches.

        Args:
            force: If True, then no additional prompt will be shown before
                deleting Cube.

        Returns:
            True when all of cube's caches were deleted and it was successfully
            unpublished. False otherwise.
        """
        user_input = 'N'
        if not force:
            user_input = input(f"Are you sure you want to unpublish cube '{self.name}' with ID: "
                               f"{self._id}? This operation will delete all of its caches. "
                               f"[Y/N]: ") or 'N'
        if force or user_input == 'Y':
            all_caches_num = len(self.caches)
            deleted_caches_num = 0
            for cache in self.caches:
                if cache.delete(True):
                    deleted_caches_num += 1
            if all_caches_num == deleted_caches_num:
                logger.info(
                    f"Cube '{self.name}' with ID: '{self._id}' was successfully unpublished."
                )
                self._caches = []
                return True
            else:
                logger.warning(
                    f"Cube '{self.name}' with ID: '{self._id}' was not successfully unpublished"
                    f", because not all of its caches were deleted."
                )
                return False
        else:
            return False

    @property
    def size(self) -> int:
        if not self.__info_retrieved:
            self._get_info()
        return self._size

    @property
    def status(self):
        if not self.__info_retrieved:
            self._get_info()
        return self._status

    @property
    def path(self) -> str:
        if not self.__info_retrieved:
            self._get_info()
        return self._path

    @property
    def owner_id(self) -> str:
        if not self.__info_retrieved:
            self._get_info()
        return self._owner_id

    @property
    def attributes(self) -> List[dict]:
        if not self.__definition_retrieved:
            self._get_definition()
        return self._attributes

    @property
    def metrics(self) -> List[dict]:
        if not self.__definition_retrieved:
            self._get_definition()
        return self._metrics

    @property
    def attr_elements(self) -> list:
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
    def dataframe(self) -> DataFrame:
        if self._dataframe is None:
            helper.exception_handler(
                msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                exception_type=Warning)
        return self._dataframe

    @property
    def dataframes(self):
        if len(self._dataframes) == 0:
            helper.exception_handler(
                msg="Dataframe not loaded. Retrieve with Report.to_dataframe().",
                exception_type=Warning)
        return self._dataframes

    @property
    def table_definition(self):
        return self._table_definition

    @property
    def caches(self):
        if not self._caches:
            self.get_caches()
        return self._caches
