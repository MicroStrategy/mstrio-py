import logging
from typing import List, Optional, TYPE_CHECKING, Union

from mstrio.api import browsing
from mstrio.connection import Connection
from mstrio.object_management.search_enums import (
    CertifiedStatus, SearchDomain, SearchPattern, SearchResultsFormat
)
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import Entity, EntityBase
from mstrio.utils.helper import (
    exception_handler, fetch_objects_async, get_args_from_func, get_enum_val, get_objects_id,
    merge_id_and_type
)

if TYPE_CHECKING:
    from mstrio.types import TypeOrSubtype

logger = logging.getLogger(__name__)


class SearchObject(Entity):
    """Search object describing criteria that specify a search for objects.

    Attributes:
        connection: A MicroStrategy connection object
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
    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.SEARCH
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'owner': User.from_dict}

    def __init__(self, connection: "Connection", id: str) -> None:
        """Initialize SearchObject object and synchronize with server.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id: ID of SearchObject
        """
        super().__init__(connection=connection, object_id=id)


def quick_search(connection: Connection, project: Optional[Union[Project, str]] = None,
                 name: Optional[str] = None, root: Optional[str] = None,
                 pattern: Union[SearchPattern, int] = SearchPattern.CONTAINS,
                 object_types: Optional["TypeOrSubtype"] = None, get_ancestors: bool = False,
                 cross_cluster: bool = False, hidden: Optional[bool] = None,
                 certified_status: CertifiedStatus = CertifiedStatus.ALL,
                 limit: Optional[int] = None, offset: Optional[int] = None,
                 to_dictionary: bool = True):
    """Use the stored results of the Quick Search engine to return
     search results and display them as a list. The Quick Search
     engine periodically indexes the metadata and stores the results in memory,
     making Quick Search very fast but with results that may not be the
     most recent.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with (patter)
            B (name).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchPattern. Default value is CONTAINS (4).
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.utils.entity.ObjectTypes and
            mstrio.utils.entity.ObjectSubTypes
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
    project_id = get_objects_id(project, Project)
    if object_types and not isinstance(object_types, list):
        object_types = [get_enum_val(object_types, (ObjectTypes, ObjectSubTypes))]
    elif object_types:
        object_types = [get_enum_val(t, (ObjectTypes, ObjectSubTypes)) for t in object_types]
    pattern = get_enum_val(pattern, SearchPattern)
    certified_status = get_enum_val(certified_status, CertifiedStatus)
    resp = browsing.get_quick_search_result(connection, project_id=project_id, name=name,
                                            pattern=pattern, object_types=object_types, root=root,
                                            get_ancestors=get_ancestors, hidden=hidden,
                                            cross_cluster=cross_cluster, limit=limit,
                                            certified_status=certified_status, offset=offset)
    objects = resp.json()["result"]
    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


def quick_search_from_object(connection: Connection, project: Union[Project, str],
                             search_object: Union[SearchObject, str],
                             include_ancestors: bool = False, include_acl: bool = False,
                             subtypes: Optional[Union[ObjectSubTypes, List[ObjectSubTypes], int,
                                                      List[int]]] = None,
                             limit: Optional[int] = None, offset: Optional[int] = None,
                             to_dictionary: bool = True):
    """Perform a quick search based on a predefined Search Object.
    Use an existing search object for Quick Search engine to return
    search results and display them as a list.

    Args:
        connection (object): MicroStrategy connection object returned by
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
    resp = browsing.get_quick_search_result_from_object(connection, project_id, search_object_id,
                                                        subtypes=subtypes,
                                                        include_ancestors=include_ancestors,
                                                        include_acl=include_acl, limit=limit,
                                                        offset=offset)
    objects = resp.json()["result"]
    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


def get_search_suggestions(connection: Connection, project: Optional[Union[Project, str]] = None,
                           key: Optional[str] = None, max_results: int = 4,
                           cross_cluster: Optional[bool] = None) -> List[str]:
    """Request search suggestions from the server.

    Args:
        connection (object): MicroStrategy REST API connection object
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
    return browsing.get_search_suggestions(
        connection=connection, project_id=project_id, key=key, count=max_results,
        is_cross_cluster=cross_cluster).json().get('suggestions')


def full_search(connection: Connection, project: Optional[Union[Project, str]] = None,
                name: Optional[str] = None, pattern: Union[SearchPattern,
                                                           int] = SearchPattern.CONTAINS,
                domain: Union[SearchDomain,
                              int] = SearchDomain.PROJECT, root: Optional[str] = None,
                object_types: Optional["TypeOrSubtype"] = None,
                uses_object_id: Optional[Union[EntityBase, str]] = None,
                uses_object_type: Optional[Union[ObjectTypes, int]] = None,
                uses_recursive: bool = False, uses_one_of: bool = False,
                used_by_object_id: Optional[Union[EntityBase, str]] = None,
                used_by_object_type: Optional[Union[ObjectTypes, str]] = None,
                used_by_recursive: bool = False, used_by_one_of: bool = False,
                results_format: Union[SearchResultsFormat, str] = SearchResultsFormat.LIST,
                limit: Optional[int] = None, offset: Optional[int] = None,
                to_dictionary: bool = True,
                **filters) -> Union[List[dict], List[Entity]]:
    """Perform a full metadata search and return results.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with (patter)
            B (name).
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchPattern. Default value is CONTAINS (4).
        domain(integer or enum class object): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.browsing.SearchDomain. Default value is
            PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.utils.entity.ObjectTypes and
            mstrio.utils.entity.ObjectSubTypes
        uses_object_id(string): Constrain the search to only return
            objects which use the given object.
        uses_object_type(string): Constrain the search to only return
            objects which use the given object. Possible values
            available in ENUMs mstrio.utils.entity.ObjectTypes
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
            available in ENUM mstrio.utils.entity.ObjectTypes
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        used_by_one_of(boolean): Control the Intelligence server to also
            find objects that are used by one of or all of given objects
            indirectly. Default value is false.
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
    passed_params = locals()
    start_search_args = get_args_from_func(start_full_search)
    search_result_args = get_args_from_func(get_search_results)
    start_search_params = {k: v for k, v in passed_params.items() if k in start_search_args}
    search_result_params = {k: v for k, v in passed_params.items() if k in search_result_args}
    resp = start_full_search(**start_search_params)
    search_result_params["search_id"] = resp["id"]
    del search_result_params["filters"]
    search_result_params.update(**filters)
    return get_search_results(**search_result_params)


def start_full_search(connection: Connection, project: Optional[Union[Project, str]] = None,
                      name: Optional[str] = None, object_types: Optional["TypeOrSubtype"] = None,
                      pattern: Union[SearchPattern, int] = SearchPattern.CONTAINS,
                      domain: Union[SearchDomain,
                                    int] = SearchDomain.PROJECT, root: Optional[str] = None,
                      uses_object_id: Optional[Union[EntityBase, str]] = None,
                      uses_object_type: Optional[Union[ObjectTypes, ObjectSubTypes, int]] = None,
                      uses_recursive: bool = False, uses_one_of: bool = False,
                      used_by_object_id: Optional[Union[EntityBase, str]] = None,
                      used_by_object_type: Optional[Union[ObjectTypes, ObjectSubTypes,
                                                          int]] = None,
                      used_by_recursive: bool = False, used_by_one_of: bool = False) -> dict:
    """Search the metadata for objects in a specific project that
    match specific search criteria, and save the results in IServer memory.

    Args:
        connection (object): MicroStrategy connection object returned by
            `connection.Connection()`
        project (string): `Project` object or ID
        object_types(enum class object or integer or list of enum class objects
            or integers): Type(s) of object(s) to be searched, such as
            Folder, Attribute or User. Possible values available in ENUMs
            mstrio.utils.entity.ObjectTypes and
            mstrio.utils.entity.ObjectSubTypes
        name(string): Value the search pattern is set to, which will
            be applied to the names of object types being searched. For example,
            search for all report objects (type) whose name begins with (patter)
            B (name).
        pattern(integer or enum class object): Pattern to search for,
            such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchPattern. Default value is CONTAINS (4).
        domain(integer or enum class object): Domain where the search
            will be performed, such as Local or Project. Possible values are
            available in ENUM mstrio.browsing.SearchDomain. Default value is
            PROJECT (2).
        root(string, optional): Folder ID of the root folder where the search
            will be performed.
        uses_object_id(string): Constrain the search to only return
            objects which use the given object.
        uses_object_type(int, ObjectTypes): Constrain the search to only return
            objects which use the given object. Possible values
            available in ENUMs mstrio.utils.entity.ObjectTypes
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
            available in ENUM mstrio.utils.entity.ObjectTypes
        used_by_recursive(boolean, optional): Control the Intelligence server
            to also find objects that are used by the given objects indirectly.
            Default value is false.
        used_by_one_of(boolean): Control the Intelligence server to also
            find objects that are used by one of or all of given objects
            indirectly. Default value is false.

    Returns:
        dictionary consisting of id (Search ID) and total items number
    """

    if uses_object_id and used_by_object_id:
        exception_handler(
            msg="It is not allowed to use both ‘uses_object’ and ‘used_by_object’ in one request.",
            exception_type=AttributeError)

    uses_object = merge_id_and_type(
        uses_object_id, uses_object_type,
        "Please provide both `uses_object_id` and `uses_object_type`.") if uses_object_id else None
    used_by_object = merge_id_and_type(
        used_by_object_id, used_by_object_type,
        "Please provide both `used_by_object_id` and `uses_object_type`."
    ) if used_by_object_id else None

    project_id = get_objects_id(project, Project)
    if object_types and not isinstance(object_types, list):
        object_types = [get_enum_val(object_types, (ObjectTypes, ObjectSubTypes))]
    elif object_types:
        object_types = [get_enum_val(t, (ObjectTypes, ObjectSubTypes)) for t in object_types]
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
    )
    return resp.json()


def get_search_results(connection: Connection, search_id: str,
                       project: Optional[Union[Project, str]] = None,
                       results_format: SearchResultsFormat = SearchResultsFormat.LIST,
                       limit: Optional[int] = None, offset: Optional[int] = None,
                       to_dictionary: bool = False, **filters):
    """Retrieve the results of a full metadata search previously stored in
    an instance in IServer memory, may be obtained by `start_full_search`.

    Args:
        connection (object): MicroStrategy connection object returned by
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


def _get_search_result_list_format(connection: Connection, search_id: str,
                                   project_id: Optional[str] = None, limit: Optional[int] = None,
                                   offset: Optional[int] = None,
                                   to_dictionary: bool = True, **filters):
    from mstrio.utils.object_mapping import map_objects_list
    objects = fetch_objects_async(
        connection=connection,
        api=browsing.get_search_results,
        async_api=browsing.get_search_results_async,
        search_id=search_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
        chunk_size=1000,
        dict_unpack_value=None,
        filters=filters,
    )
    if to_dictionary:
        return objects
    return map_objects_list(connection, objects)


def _get_search_result_tree_format(connection: Connection, search_id: str,
                                   project_id: Optional[str] = None, limit: Optional[int] = None,
                                   offset: Optional[int] = None):
    resp = browsing.get_search_results_tree_format(
        connection=connection,
        search_id=search_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    if resp.content:
        return resp.json()
    return {}
