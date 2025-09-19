from datetime import datetime
import itertools
import logging
from concurrent.futures import as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from requests import Response

from mstrio import config
from mstrio.api import browsing, objects
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.object_management.search_enums import (
    CertifiedStatus,
    SearchDomain,
    SearchPattern,
    SearchResultsFormat,
    SearchScope,
)
from mstrio.server import Environment
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, EntityBase, MoveMixin
from mstrio.utils.helper import (
    Dictable,
    _prepare_objects,
    camel_to_snake,
    exception_handler,
    filter_params_for_func,
    get_args_from_func,
    get_enum_val,
    get_objects_id,
    get_owner_id,
    get_project_id_or_none,
    merge_id_and_type,
)
from mstrio.utils.response_processors import browsing as browsing_processors
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.time_helper import DatetimeFormats, str_to_datetime
from mstrio.utils.version_helper import (
    class_version_handler,
    meets_minimal_version,
    method_version_handler,
)
from mstrio.utils.wip import WipLevels, wip

if TYPE_CHECKING:
    from mstrio.types import TypeOrSubtype
    from mstrio.object_management.folder import Folder

logger = logging.getLogger(__name__)


class DateQuery(Dictable):
    """Object that specifies a date query for searches: either a date range or
    number of days or months before the current date.

    Attributes:
        begin_time (datetime | None): Start date of the range.
        end_time (datetime | None): End date of the range. `begin_time` and
            `end_time` must be provided together. They must be the only
            parameters provided if used.
        since_days (int | None): Number of days before the current date.
            Must be the only parameter provided if used.
        since_months (int | None): Number of months before the current date.
            Must be the only parameter provided if used.
    """

    def __init__(
        self,
        begin_time: datetime | str | None = None,
        end_time: datetime | str | None = None,
        since_days: int | None = None,
        since_months: int | None = None,
    ) -> None:
        """Initialize DateQuery object.

        Args:
            begin_time (datetime, optional): Start date of the range.
            end_time (datetime, optional): End date of the range.
            since_days (int, optional): Number of days before the current date.
            since_months (int, optional): Number of months before the current
                date.
        """

        if not any([begin_time, end_time, since_days, since_months]):
            exception_handler(
                msg="At least one of the following parameters must be provided: "
                "'begin_time', 'end_time', 'since_days', 'since_months'.",
                exception_type=ValueError,
            )
        if begin_time and not end_time:
            exception_handler(
                msg="If 'begin_time' is provided, 'end_time' must also be provided.",
                exception_type=ValueError,
            )
        if end_time and not begin_time:
            exception_handler(
                msg="If 'end_time' is provided, 'begin_time' must also be provided.",
                exception_type=ValueError,
            )
        is_range = begin_time is not None
        is_since_days = since_days is not None
        is_since_months = since_months is not None

        if is_range + is_since_days + is_since_months > 1:
            exception_handler(
                msg="Only one kind of the date query can be provided: "
                "'begin_time' and 'end_time' (date range), 'since_days', "
                "'since_months'.",
                exception_type=ValueError,
            )

        self.begin_time = (
            str_to_datetime(begin_time, DatetimeFormats.FULLDATETIME.value)
            if isinstance(begin_time, str)
            else begin_time
        )
        self.end_time = (
            str_to_datetime(end_time, DatetimeFormats.FULLDATETIME.value)
            if isinstance(end_time, str)
            else end_time
        )
        self.since_days = since_days
        self.since_months = since_months

    def to_dict(self, camel_case=True) -> dict:
        """Convert DateQuery object to a dictionary.

        Args:
            camel_case (bool): If True, returns keys in camelCase format,
                otherwise returns keys in snake_case format.

        Returns:
            dict: Dictionary representation of the DateQuery object.
        """

        result = {
            'beginTime': self.begin_time.isoformat() if self.begin_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'sinceDays': self.since_days,
            'sinceMonths': self.since_months,
        }

        return result if camel_case else camel_to_snake(result)


@class_version_handler('11.3.0100')
class SearchObject(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Search object describing criteria that specify a search for objects.

    Attributes:
        connection (Connection): A Strategy One connection object
        id (str): Object ID
        name (str): Object name
        description (str): Object description
        abbreviation (str): Object abbreviation
        type (int): Object type
        subtype (int): Object subtype
        ext_type (int, optional): Object extended type
        date_created (datetime): Creation time, DateTime object
        date_modified (datetime): Last modification time, DateTime object
        version (str): Version ID
        owner (dict): Owner ID and name
        icon_path (str, optional): Object icon path
        view_media (str, optional): View media settings
        ancestors (list[Folder]): List of ancestor folders
        acg (int): Access rights (See EnumDSSXMLAccessRightFlags for
            possible values)
        acl (list[dict]): Object access control list
        name_query (str, optional): Object name to search for
        description_query (str, optional): Object description to search for
        root_folder_query (str, optional): Root folder to search in
        object_types_query (list[ObjectTypes], optional): Object types to
            search for in the query
        object_subtypes_query (list[ObjectSubTypes], optional): Object subtypes
            to search for in the query
        date_created_query (DateQuery, optional): Date created query
        date_modified_query (DateQuery, optional): Date modified query
        owner_query (str, optional): Owner query
        lcid_query (int, optional): Locale query
        include_hidden (bool, optional): Whether to include hidden objects
        include_subfolders (bool, optional): Whether to include subfolders
        exclude_folders (list[str], optional): Folder IDs to exclude
            from the search
        scope (SearchScope, optional): Scope of the search with regard to
            System Managed Objects.
    """

    @staticmethod
    def _date_query_or_none(source, *args, **kwargs) -> DateQuery | None:
        """Create a DateQuery object from a dictionary or return None."""
        if source is None:
            return None
        return DateQuery.from_dict(source, *args, **kwargs)

    _OBJECT_TYPE = ObjectTypes.SEARCH
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'object_types_query': [ObjectTypes.from_rest_value],
        'object_subtypes_query': [ObjectSubTypes.from_rest_value],
        'date_created_query': _date_query_or_none,
        'date_modified_query': _date_query_or_none,
        'scope': SearchScope,
    }
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
        if meets_minimal_version(connection.iserver_version, '11.4.1200'):
            self._API_GETTERS.update(
                {
                    (
                        "name_query",
                        "description_query",
                        "root_folder_query",
                        "object_types_query",
                        "object_subtypes_query",
                        "date_created_query",
                        "date_modified_query",
                        "owner_query",
                        "lcid_query",
                        "include_hidden",
                        "include_subfolders",
                        "exclude_folders",
                        "scope",
                    ): browsing_processors.get_search_object,
                }
            )
        super().__init__(connection=connection, object_id=id)

    def _init_variables(self, default_value, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.name_query = kwargs.get('name_query', None)
        self.description_query = kwargs.get('description_query', None)
        self.root_folder_query = kwargs.get('root_folder_query', None)
        self.object_types_query = kwargs.get('object_types_query', None)
        self.object_subtypes_query = kwargs.get('object_subtypes_query', None)
        self.date_created_query = kwargs.get('date_created_query', None)
        self.date_modified_query = kwargs.get('date_modified_query', None)
        self.owner_query = kwargs.get('owner_query', None)
        self.lcid_query = kwargs.get('lcid_query', None)
        self.include_hidden = kwargs.get('include_hidden', None)
        self.include_subfolders = kwargs.get('include_subfolders', None)
        self.exclude_folders = kwargs.get('exclude_folders', None)
        self.scope = kwargs.get('scope', None)

    @staticmethod
    def _get_date_query_fields(
        date_created_query: DateQuery | None,
        date_modified_query: DateQuery | None,
    ) -> tuple[str | None, dict | None]:
        """Convert a pair of date query field values to REST schema of shape
        (date_query_type, date_query).

        Args:
            date_created_query: The date created query field.
            date_modified_query: The date modified query field.

        Returns:
            tuple[str | None, dict | None]: A tuple containing the date query
                type (str) and the date query. Both set to None if no date
                query is provided.
        """
        if date_created_query and date_modified_query:
            exception_handler(
                msg="Only one of 'date_created_query' or 'date_modified_query' "
                "should be provided.",
                exception_type=ValueError,
            )

        if date_created_query:
            date_query_type = 'created'
        elif date_modified_query:
            date_query_type = 'modified'
        else:
            date_query_type = None
        if (date_query := date_created_query or date_modified_query) is not None:
            if isinstance(date_query, DateQuery):
                date_query = date_query.to_dict(camel_case=False)

        return date_query_type, date_query

    @staticmethod
    def _type_to_rest(t: ObjectTypes | ObjectSubTypes | int, cls) -> str:
        """Convert a type or subtype specification to a string accepted by REST.

        Args:
            t (ObjectTypes | ObjectSubTypes | int): The type or subtype
                to convert.
            cls: The class to use for the conversion, `ObjectTypes` or
                `ObjectSubTypes`.

        Returns:
            str: The converted type as a string.
        """
        if cls not in (ObjectTypes, ObjectSubTypes):
            raise ValueError(f"Invalid class: {cls}")
        if isinstance(t, int):
            t = cls(t)
        return t.to_rest_value()

    @classmethod
    @wip(level=WipLevels.PREVIEW)
    def create(
        cls,
        connection: Connection,
        name: str | None,
        destination_folder: 'str | Folder',
        project: Project | None = None,
        project_id: str | None = None,
        project_name: str | None = None,
        name_query: str | None = None,
        description_query: str | None = None,
        root_folder_query: 'str | Folder | None' = None,
        object_types_query: ObjectTypes | int | list[ObjectTypes | int] | None = None,
        object_subtypes_query: (
            ObjectSubTypes | int | list[ObjectSubTypes | int] | None
        ) = None,
        date_created_query: DateQuery | None = None,
        date_modified_query: DateQuery | None = None,
        owner_query: str | User | None = None,
        owner_query_id: str | None = None,
        owner_query_username: str | None = None,
        lcid_query: int | None = None,
        include_hidden: bool | None = None,
        include_subfolders: bool | None = None,
        exclude_folders: 'list[str | Folder] | None' = None,
        scope: SearchScope | None = None,
        to_dictionary: bool = False,
    ) -> 'SearchObject | dict':
        """Create a new SearchObject.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`.
            name (str or None): Name of the SearchObject. If None, a default
                name will be generated.
            destination_folder (str or Folder): Folder (ID or Folder object)
                where the SearchObject will be created.
            project (Project, optional): Project object where the SearchObject
                will be created. If not provided, the connection's project
                will be used.
            project_id (str, optional): Project ID where the SearchObject
                will be created. May be used instead of `project`.
            project_name (str, optional): Project name where the SearchObject
                will be created. May be used instead of `project`.
            name_query (str, optional): Object name to search for.
            description_query (str, optional): Object description to search for.
            root_folder_query (str, optional): Root folder ID to search in.
            object_types_query (list[ObjectTypes | int], int, optional):
                Object types to search for in the query.
            object_subtypes_query (list[ObjectSubTypes | int], int, optional):
                Object subtypes to search for in the query.
            date_created_query (DateQuery, optional): Date created query.
            date_modified_query (DateQuery, optional): Date modified query.
                Only one of `date_created_query` or `date_modified_query`
                should be provided.
            owner_query (str, User, optional): username, user ID, or User object
                representing the object owner specified in the query. If
                `owner_query` is provided, `owner_query_id` and
                `owner_query_username` are ignored
            owner_query_id (str, optional): ID of the object owner specified in
                the query. If only owner_query_id and owner_query_username are
                provided, then owner_query_username is omitted and the owner is
                set to the user with the given ID
            owner_query_username (str, optional): username of the the object
                owner specified in the query
            lcid_query (int, optional): Locale query.
            include_hidden (bool, optional): Whether to include hidden objects.
            include_subfolders (bool, optional): Whether to include subfolders.
            exclude_folders (list[str], optional): Folder IDs to exclude
                from the search
            scope (SearchScope, str, optional): Scope of the search with regard
                to System Managed Objects. Possible values are
                "not_managed_only", "managed_only", "all". Defaults to
                "not_managed_only".
            to_dictionary (bool): If True, returns a dictionary with the new
                object's details instead of a SearchObject. Defaults to False.

        Returns:
            The new Search Object.
        """
        from mstrio.object_management import Folder

        project_id = get_project_id_or_none(
            connection=connection,
            project=project,
            project_id=project_id,
            project_name=project_name,
        )

        if isinstance(destination_folder, Folder):
            destination_folder = destination_folder.id
        if isinstance(root_folder_query, Folder):
            root_folder_query = root_folder_query.id

        date_query_type, date_query = SearchObject._get_date_query_fields(
            date_created_query=date_created_query,
            date_modified_query=date_modified_query,
        )

        if isinstance(object_types_query, ObjectTypes):
            object_types_query = [object_types_query]
        if object_types_query is not None:
            object_types_query = [
                SearchObject._type_to_rest(t, ObjectTypes) for t in object_types_query
            ]
        if isinstance(object_subtypes_query, ObjectSubTypes):
            object_subtypes_query = [object_subtypes_query]
        if object_subtypes_query is not None:
            object_subtypes_query = [
                SearchObject._type_to_rest(t, ObjectSubTypes)
                for t in object_subtypes_query
            ]

        owner_query = get_owner_id(
            connection, owner_query, owner_query_id, owner_query_username
        )

        visibility = 'ALL' if include_hidden else 'VISIBLE'

        if exclude_folders is not None:
            exclude_folders = [
                folder.id if isinstance(folder, Folder) else folder
                for folder in exclude_folders
            ]

        if isinstance(scope, SearchScope):
            scope = scope.value

        body = {
            "name": name,
            "location": destination_folder,
            "nameQuery": name_query,
            "descriptionQuery": description_query,
            "root": root_folder_query,
            "types": object_types_query,
            "subtypes": object_subtypes_query,
            "dateFilterType": date_query_type,
            "timeRange": date_query,
            "visibility": visibility,
            "includeSubfolders": include_subfolders,
            "excludedFolders": exclude_folders,
            "ownerId": owner_query,
            "localeId": lcid_query,
            "scope": scope,
        }
        body = helper.delete_none_values(source=body, recursion=True)
        res: Response = browsing.create_search_object(
            connection=connection,
            project_id=project_id,
            body=body,
        )
        new_id = res.json().get('id')
        new_search = cls(
            connection=connection,
            id=new_id,
        )
        if config.verbose:
            logger.info(
                f"Successfully created Search Object named: '{new_search}' "
                f"with ID: '{new_id}'"
            )
        return new_search.to_dict() if to_dictionary else new_search

    @wip(level=WipLevels.PREVIEW)
    def run(
        self,
        pattern: SearchPattern | None = None,
        results_format: SearchResultsFormat = SearchResultsFormat.LIST,
        limit: int | None = None,
        offset: int | None = None,
        to_dictionary: bool = False,
    ) -> list[EntityBase] | list[dict]:
        """Execute the search operation with the stored parameters.

        Args:
            pattern (SearchPattern, optional): Search pattern to apply to the
                search query, e.g. CONTAINS or EXACTLY.
            results_format (SearchResultsFormat, optional): Format for the
                search results. Defaults to LIST.
            limit (int, optional): Maximum number of results to return.
            offset (int, optional): Offset for pagination.
            to_dictionary (bool): If True, returns a dictionary with the new
                object's details instead of an object. Defaults to False.

        Returns:
            List of matching objects.
        """

        search_result_params = filter_params_for_func(get_search_results, locals())

        date_query_type, date_query = SearchObject._get_date_query_fields(
            date_created_query=self.date_created_query,
            date_modified_query=self.date_modified_query,
        )
        if date_query_type is not None:
            date_query_type = date_query_type.upper()
        visibility = 'ALL' if self.include_hidden else 'VISIBLE'
        if self.object_types_query is None and self.object_subtypes_query is None:
            type_query = None
        else:
            type_query = (self.object_types_query or []) + (
                self.object_subtypes_query or []
            )
            type_query = [t.value for t in type_query]

        body = {
            "includeSubfolders": self.include_subfolders,
            "dateFilterType": date_query_type,
            "timeRange": date_query,
            "descriptionQuery": self.description_query,
            "ownerId": self.owner_query,
            "localeId": self.lcid_query,
            "excludedFolders": self.exclude_folders,
        }
        instance_res = browsing.store_search_instance_v2(
            self.connection,
            body=body,
            project_id=self.connection.project_id,
            name=self.name_query,
            pattern=pattern.value if pattern else None,
            scope=self.scope.value if self.scope else None,
            root=self.root_folder_query,
            type=type_query,
            visibility=visibility,
        ).json()

        search_result_params["project"] = self.connection.project_id
        search_result_params["search_id"] = instance_res["id"]
        search_result_params["connection"] = self.connection
        return get_search_results(**search_result_params)


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
    response = browsing_processors.get_objects_from_quick_search(
        connection=connection, body=body
    )
    prepared_objects = _prepare_objects(response, filters)

    if to_dictionary:
        return prepared_objects
    return map_objects_list(connection, prepared_objects)
