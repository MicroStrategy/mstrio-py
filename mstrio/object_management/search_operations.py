import itertools
import logging
from concurrent.futures import as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from mstrio.api import browsing, objects
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.object_management.search_enums import (
    CertifiedStatus,
    SearchDomain,
    SearchPattern,
    SearchResultsFormat,
)
from mstrio.server import Environment
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, EntityBase, MoveMixin
from mstrio.utils.helper import (
    Dictable,
    _prepare_objects,
    exception_handler,
    get_args_from_func,
    get_enum_val,
    get_objects_id,
    merge_id_and_type,
)
from mstrio.utils.response_processors import browsing as browsing_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.types import TypeOrSubtype

logger = logging.getLogger(__name__)


@class_version_handler('11.3.0100')
class SearchObject(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Search object describing criteria that specify a search for objects.

    Attributes:
        connection: A Strategy One connection object
        id: Object ID
        name: Object name
        description: Object description
        abbreviation: Object abbreviation
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        version: Version ID
        owner: Owner ID and name
        icon_path: Object icon path
        view_media: View media settings
        ancestors: List of ancestor folders
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.SEARCH
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'owner': User.from_dict}
    _API_PATCH: dict = {
        **Entity._API_PATCH,
        'folder_id': (objects_processors.update, 'partial_put'),
    }

    def __init__(self, connection: "Connection", id: str) -> None:
        """Initialize SearchObject object and synchronize with server.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            id: ID of SearchObject
        """
        super().__init__(connection=connection, object_id=id)


@method_version_handler('11.3.0000')
def quick_search(
    connection: Connection,
    project: Project | str | None = None,
    name: str | None = None,
    root: str | None = None,
    root_path: str | None = None,
    pattern: SearchPattern | int = SearchPattern.CONTAINS,
    object_types: Optional["TypeOrSubtype"] = None,
    get_ancestors: bool = False,
    cross_cluster: bool = False,
    hidden: bool | None = None,
    certified_status: CertifiedStatus = CertifiedStatus.ALL,
    limit: int | None = None,
    offset: int | None = None,
    to_dictionary: bool = True,
):
    """Use the stored results of the Quick Search engine to return
     search results and display them as a list. The Quick Search
     engine periodically indexes the metadata and stores the results in memory,
     making Quick Search very fast but with results that may not be the
     most recent.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with
            (pattern) B (name).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        root_path (str, optional): Path of the root folder in which the search
            will be performed. Can be provided as an alternative to
            `root` parameter. If both are provided, `root` is used.
                the path has to be provided in the following format:
                    if it's inside of a project, example:
                        /MicroStrategy Tutorial/Public Objects/Metrics
                    if it's a root folder, example:
                        /CASTOR_SERVER_CONFIGURATION/Users
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.types.ObjectTypes and
            mstrio.types.ObjectSubTypes
        get_ancestors(bool): Specifies whether to return the list of ancestors
            for each object
        certified_status(CertifiedStatus): Defines a search criteria based
            on the certified status of the object, possible values available in
            CertifiedStatus enum
        cross_cluster(bool): Perform search in all unique projects across the
            cluster,this parameter only takes affect for I-Server with
            cluster nodes.
        hidden(bool): Filter the result based on the 'hidden' field of objects.
            If not passed, no filtering is applied.
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        offset (int): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        to_dictionary (bool): If True returns dicts, by default
            (False) returns objects.

    Returns:
         list of objects or list of dictionaries
    """
    from mstrio.utils.object_mapping import map_objects_list

    if root_path and not root:
        from mstrio.object_management.folder import get_folder_id_from_path

        root = get_folder_id_from_path(connection=connection, path=root_path)

    project_id = get_objects_id(project, Project)
    if object_types and not isinstance(object_types, list):
        object_types = [get_enum_val(object_types, (ObjectTypes, ObjectSubTypes))]
    elif object_types:
        object_types = [
            get_enum_val(t, (ObjectTypes, ObjectSubTypes)) for t in object_types
        ]
    pattern = get_enum_val(pattern, SearchPattern)
    certified_status = get_enum_val(certified_status, CertifiedStatus)
    resp = browsing.get_quick_search_result(
        connection,
        project_id=project_id,
        name=name,
        pattern=pattern,
        object_types=object_types,
        root=root,
        get_ancestors=get_ancestors,
        hidden=hidden,
        cross_cluster=cross_cluster,
        limit=limit,
        certified_status=certified_status,
        offset=offset,
    )
    objects = resp.json()["result"]
    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


@method_version_handler('11.3.0100')
def quick_search_from_object(
    connection: Connection,
    project: Project | str,
    search_object: SearchObject | str,
    include_ancestors: bool = False,
    include_acl: bool = False,
    subtypes: ObjectSubTypes | list[ObjectSubTypes] | int | list[int] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    to_dictionary: bool = True,
):
    """Perform a quick search based on a predefined Search Object.
    Use an existing search object for Quick Search engine to return
    search results and display them as a list.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        search_object(SearchObject): Search object ID to retrieve result from
        include_ancestors(bool): Specifies whether to return the list of
            ancestors for each object
        include_acl(bool): Specifies whether to return the list of ACL for each
            object
        subtypes(list, int): This parameter is used to filter the objects in the
            result to include only the ones whose “subtype” is included in
            the values of this parameter
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        offset (int): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        to_dictionary (bool): If True returns dicts, by default
            (False) returns objects.

    Returns:
        list of objects or list of dictionaries
    """
    from mstrio.utils.object_mapping import map_objects_list

    project_id = get_objects_id(project, Project)
    search_object_id = get_objects_id(search_object, SearchObject)
    subtypes = get_enum_val(subtypes, ObjectSubTypes)
    resp = browsing.get_quick_search_result_from_object(
        connection,
        project_id,
        search_object_id,
        subtypes=subtypes,
        include_ancestors=include_ancestors,
        include_acl=include_acl,
        limit=limit,
        offset=offset,
    )
    objects = resp.json()["result"]
    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


@method_version_handler('11.3.0000')
def get_search_suggestions(
    connection: Connection,
    project: Project | str | None = None,
    key: str | None = None,
    max_results: int = 4,
    cross_cluster: bool | None = None,
) -> list[str]:
    """Request search suggestions from the server.

    Args:
        connection (object): Strategy One REST API connection object
        project (string, optional): `Project` object or ID
        key (string, optional): value the search pattern is set to, which will
            be applied to the names of suggestions being searched
        max_results (int, optional): maximum number of items returned
            for a single request. Used to control paging behavior.
            Default value is `-1` for no limit.
        cross_cluster (bool, optional): perform search in all unique projects
            across the cluster, this parameter only takes effect for I-Server
            with cluster nodes. Default value is `None`

    Returns:
        list of search suggestions
    """
    project_id = get_objects_id(project, Project)
    return (
        browsing.get_search_suggestions(
            connection=connection,
            project_id=project_id,
            key=key,
            count=max_results,
            is_cross_cluster=cross_cluster,
        )
        .json()
        .get('suggestions')
    )


@method_version_handler('11.3.0000')
def full_search(
    connection: Connection,
    project: Project | str | None = None,
    name: str | None = None,
    pattern: SearchPattern | int = SearchPattern.CONTAINS,
    domain: SearchDomain | int = SearchDomain.PROJECT,
    root: str | None = None,
    root_path: str | None = None,
    object_types: Optional['TypeOrSubtype'] = None,
    uses_object_id: EntityBase | str | None = None,
    uses_object_type: ObjectTypes | int | None = None,
    uses_recursive: bool = False,
    uses_one_of: bool = False,
    used_by_object_id: EntityBase | str | None = None,
    used_by_object_type: ObjectTypes | str | None = None,
    used_by_recursive: bool = False,
    used_by_one_of: bool = False,
    begin_modification_time: str | None = None,
    end_modification_time: str | None = None,
    results_format: SearchResultsFormat | str = SearchResultsFormat.LIST,
    limit: int | None = None,
    offset: int | None = None,
    to_dictionary: bool = True,
    **filters,
) -> list[dict] | list[Entity]:
    """Perform a full metadata search and return results.

    Note:
        If you have a large number of objects in your environment, try to use
        `limit` and `offset` parameters to retrieve the results in batches.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with
            pattern) B (name).
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        domain(integer or enum class object): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.object_management.SearchDomain.
            Default value is PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        root_path (str, optional): Path of the root folder in which the search
            will be performed. Can be provided as an alternative to
            `root` parameter. If both are provided, `root` is used.
                the path has to be provided in the following format:
                    if it's inside of a project, example:
                        /MicroStrategy Tutorial/Public Objects/Metrics
                    if it's a root folder, example:
                        /CASTOR_SERVER_CONFIGURATION/Users
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.types.ObjectTypes and
            mstrio.types.ObjectSubTypes
        uses_object_id(string): Constrain the search to only return
            objects which use the given object.
        uses_object_type(string): Constrain the search to only return
            objects which use the given object. Possible values
            available in ENUMs mstrio.types.ObjectTypes
        uses_recursive(boolean): Control the Intelligence server to
            also find objects that use the given objects indirectly. Default
            value is false.
        uses_one_of(boolean): Control the Intelligence server to also
            find objects that use one of or all of given objects indirectly.
            Default value is false.
        used_by_object_id(string): Constrain the search to only return
            objects which are used by the given object.
        used_by_object_type(string): Constrain the search to only return
            objects which are used by the given object. Possible values
            available in ENUM mstrio.types.ObjectTypes
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        used_by_one_of(boolean): Control the Intelligence server to also
            find objects that are used by one of or all of given objects
            indirectly. Default value is false.
        begin_modification_time(string, optional): Field to filter request
            to return records newer than a given date in
            format 'yyyy-MM-dd'T'HH:mm:ssZ', for example 2021-04-04T06:33:32Z.
        end_modification_time(string, optional): Field to filter request
            to return records older than a given date in
            format 'yyyy-MM-dd'T'HH:mm:ssZ', for example 2022-04-04T06:33:32Z.
        results_format(SearchResultsFormat): either a list or a tree format
        to_dictionary (bool): If False returns objects, by default
            (True) returns dictionaries.
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        offset (int): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Returns:
        list of objects or list of dictionaries
    """
    if root_path and not root:
        from mstrio.object_management.folder import get_folder_id_from_path

        # NOSONAR - `root` is referenced as field in `locals()`
        root = get_folder_id_from_path(connection=connection, path=root_path)  # NOSONAR
    passed_params = locals()
    passed_params.pop('root_path', None)
    start_search_args = get_args_from_func(start_full_search)
    search_result_args = get_args_from_func(get_search_results)
    start_search_params = {
        k: v for k, v in passed_params.items() if k in start_search_args
    }
    search_result_params = {
        k: v for k, v in passed_params.items() if k in search_result_args
    }
    resp = start_full_search(**start_search_params)
    search_result_params["search_id"] = resp["id"]
    del search_result_params["filters"]
    search_result_params.update(**filters)
    return get_search_results(**search_result_params)


@method_version_handler('11.3.0000')
def start_full_search(
    connection: Connection,
    project: Project | str | None = None,
    name: str | None = None,
    object_types: Optional["TypeOrSubtype"] = None,
    pattern: SearchPattern | int = SearchPattern.CONTAINS,
    domain: SearchDomain | int = SearchDomain.PROJECT,
    root: str | None = None,
    root_path: str | None = None,
    uses_object_id: EntityBase | str | None = None,
    uses_object_type: ObjectTypes | ObjectSubTypes | int | None = None,
    uses_recursive: bool = False,
    uses_one_of: bool = False,
    used_by_object_id: EntityBase | str | None = None,
    used_by_object_type: ObjectTypes | ObjectSubTypes | int | None = None,
    used_by_recursive: bool = False,
    used_by_one_of: bool = False,
    begin_modification_time: str | None = None,
    end_modification_time: str | None = None,
) -> dict:
    """Search the metadata for objects in a specific project that
    match specific search criteria, and save the results in IServer memory.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.types.ObjectTypes and
            mstrio.types.ObjectSubTypes
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with
            (pattern) B (name).
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        domain(integer or enum class object): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.object_management.SearchDomain.
            Default value is PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        root_path (str, optional): Path of the root folder in which the search
            will be performed. Can be provided as an alternative to
            `root` parameter. If both are provided, `root` is used.
                the path has to be provided in the following format:
                    if it's inside of a project, example:
                        /MicroStrategy Tutorial/Public Objects/Metrics
                    if it's a root folder, example:
                        /CASTOR_SERVER_CONFIGURATION/Users
        uses_object_id(string): Constrain the search to only return
            objects which use the given object.
        uses_object_type(int, ObjectTypes): Constrain the search to only return
            objects which use the given object. Possible values
            available in ENUMs mstrio.types.ObjectTypes
        uses_recursive(boolean): Control the Intelligence server to
            also find objects that use the given objects indirectly. Default
            value is false.
        uses_one_of(boolean): Control the Intelligence server to also find
             objects that use one of or all of given objects indirectly.
             Default value is false.
        used_by_object_id(string): Constrain the search to only return
            objects which are used by the given object.
        used_by_object_type(int, ObjectTypes): Constrain the search to only
            return objects which are used by the given object. Possible values
            available in ENUM mstrio.types.ObjectTypes
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        used_by_one_of(boolean): Control the Intelligence server to also
            find objects that are used by one or all given objects
            indirectly. Default value is false.
        begin_modification_time(string, optional): Field to filter request
            to return records newer than a given date in
            format 'yyyy-MM-dd'T'HH:mm:ssZ', for example 2021-04-04T06:33:32Z.
        end_modification_time(string, optional): Field to filter request
            to return records older than a given date in
            format 'yyyy-MM-dd'T'HH:mm:ssZ', for example 2022-04-04T06:33:32Z.

    Returns:
        dictionary consisting of id (Search ID) and total items number
    """
    if root_path and not root:
        from mstrio.object_management.folder import get_folder_id_from_path

        root = get_folder_id_from_path(connection=connection, path=root_path)

    if uses_object_id and used_by_object_id:
        exception_handler(
            msg="It is not allowed to use both ‘uses_object’ and ‘used_by_object’ in "
            "one request.",
            exception_type=AttributeError,
        )

    uses_object = (
        merge_id_and_type(
            uses_object_id,
            uses_object_type,
            "Please provide both `uses_object_id` and `uses_object_type`.",
        )
        if uses_object_id
        else None
    )
    used_by_object = (
        merge_id_and_type(
            used_by_object_id,
            used_by_object_type,
            "Please provide both `used_by_object_id` and `uses_object_type`.",
        )
        if used_by_object_id
        else None
    )

    project_id = get_objects_id(project, Project)
    if object_types and not isinstance(object_types, list):
        object_types = [get_enum_val(object_types, (ObjectTypes, ObjectSubTypes))]
    elif object_types:
        object_types = [
            get_enum_val(t, (ObjectTypes, ObjectSubTypes)) for t in object_types
        ]
    pattern = get_enum_val(pattern, SearchPattern)
    domain = get_enum_val(domain, SearchDomain)
    resp = browsing.store_search_instance(
        connection=connection,
        project_id=project_id,
        name=name,
        pattern=pattern,
        domain=domain,
        root=root,
        object_types=object_types,
        uses_object=uses_object,
        uses_recursive=uses_recursive,
        uses_one_of=uses_one_of,
        used_by_object=used_by_object,
        used_by_recursive=used_by_recursive,
        used_by_one_of=used_by_one_of,
        begin_modification_time=begin_modification_time,
        end_modification_time=end_modification_time,
    )
    return resp.json()


@method_version_handler('11.3.0000')
def get_search_results(
    connection: Connection,
    search_id: str,
    project: Project | str | None = None,
    results_format: SearchResultsFormat = SearchResultsFormat.LIST,
    limit: int | None = None,
    offset: int | None = None,
    to_dictionary: bool = False,
    **filters,
):
    """Retrieve the results of a full metadata search previously stored in
    an instance in IServer memory, may be obtained by `start_full_search`.

    Note:
        If you have a large number of objects in your environment, try to use
        `limit` and `offset` parameters to retrieve the results in batches.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        search_id (str): Search ID (identifies the results of a previous search
            stored in IServer memory)
        project (string): `Project` object or ID
        results_format(SearchResultsFormat): either a list or a tree format
        to_dictionary (bool): If True returns dicts, by default
            (False) returns objects.
        limit (int): limit the number of elements returned. If `None` (default),
            all objects are returned.
        offset (int): Starting point within the collection of returned
            results. Used to control paging behavior. Default is 0.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Returns:
        list of objects or list of dictionaries
    """
    passed_params = locals()
    get_result_args = get_args_from_func(_get_search_result_tree_format)
    get_result_params = {k: v for k, v in passed_params.items() if k in get_result_args}
    project_id = get_objects_id(project, Project)
    get_result_params['project_id'] = project_id
    if results_format == SearchResultsFormat.TREE:
        logger.info(
            'Notice. When results_format is equal to TREE, results are always returned'
            ' in a dictionary format.'
        )
        return _get_search_result_tree_format(**get_result_params)
    get_result_params.update({**filters, 'to_dictionary': to_dictionary})
    return _get_search_result_list_format(**get_result_params)


def _get_search_result_list_format(
    connection: Connection,
    search_id: str,
    project_id: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    to_dictionary: bool = True,
    **filters,
):
    from mstrio.utils.object_mapping import map_objects_list

    try:
        response = browsing.get_search_results(
            connection=connection,
            search_id=search_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
    except IServerError as e:
        if 'Java heap space' in str(e):
            logger.warning(
                "If you have a large number of objects in your environment, "
                "try to use `limit` and `offset` parameters "
                "to retrieve the results in batches."
            )
        raise e
    objects = _prepare_objects(response.json(), filters, project_id=project_id)

    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


def _get_search_result_tree_format(
    connection: Connection,
    search_id: str,
    project_id: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    try:
        resp = browsing.get_search_results_tree_format(
            connection=connection,
            search_id=search_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )
    except IServerError as e:
        if 'Java heap space' in str(e):
            logger.warning(
                "If you have a large number of objects in your environment, "
                "try to use `limit` and `offset` parameters "
                "to retrieve the results in batches."
            )
        raise e
    if resp.content:
        return resp.json()
    return {}


def find_objects_with_id(
    connection: Connection,
    object_id: str,
    projects: list[Project] | list[str] | None = None,
    to_dictionary=False,
) -> list[dict[str, dict | type[Entity]]]:
    """Find object by its ID only, without knowing project ID and object type.
    The search is performed by iterating over projects and trying to retrieve
    the objects with different type.

    Limitation:
        - Only object types supported by mstrio, i.g. present in
            `mstrio.types.ObjecTypes` enum, are used.
        - Configuration object are also not searched.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`.
        object_id (str): ID of an object.
        projects (list[Project] | list[str], optional): List of projects where
            to perform the search. By default, if no project are provides, the
            search is performed on all loaded projects.
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns objects.

    Returns:
        Returns list of dict with the following structure:
        {
            'project_id': <str>,
            'object_data': <dict or object>
        }
    """
    env = Environment(connection)
    projects = projects if projects else env.list_loaded_projects()

    with FuturesSessionWithRenewal(connection=connection) as session:
        futures = []

        for project, obj_type in itertools.product(projects, ObjectTypes):
            project_id = project.id if isinstance(project, Project) else project

            future = objects.get_object_info_async(
                future_session=session,
                id=object_id,
                object_type=obj_type.value,
                project_id=project_id,
            )
            future.project_id = project_id
            futures.append(future)

    from mstrio.utils.object_mapping import map_object

    return [
        {
            'project_id': future.project_id,
            'object_data': (
                result.json()
                if to_dictionary
                else map_object(connection, result.json())
            ),
        }
        for future in as_completed(futures)
        if (result := future.result()) and result.ok
    ]


@dataclass
class QuickSearchData(Dictable):
    """Object that specifies a search criteria for quick search.
    Attributes:
        project_id (str): Project ID
        object_ids (list[str]): List of object IDs
    """

    project_id: str
    object_ids: list[str]


@method_version_handler(version='11.3.1160')
def quick_search_by_id(
    connection: 'Connection',
    search_data: QuickSearchData | list[QuickSearchData],
    to_dictionary: bool = False,
    **filters,
) -> list[dict | type[Entity]]:
    """Perform a quick search based on a project IDs and object IDs.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        search_data (QuickSearchData | list[QuickSearchData]): search data
        to_dictionary (bool): If True returns dicts, by default
            (False) returns objects.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'project_id']

    """
    from mstrio.utils.object_mapping import map_objects_list

    search_data = search_data if isinstance(search_data, list) else [search_data]
    body = {"projectIdAndObjectIds": [obj.to_dict() for obj in search_data]}
    response = browsing_processors.get_search_objects(connection=connection, body=body)
    prepared_objects = _prepare_objects(response, filters)

    if to_dictionary:
        return prepared_objects
    return map_objects_list(connection, prepared_objects)
