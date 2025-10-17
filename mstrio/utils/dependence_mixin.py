from typing import TYPE_CHECKING, Optional

from mstrio.helpers import NotSupportedError
from mstrio.types import ObjectTypes

if TYPE_CHECKING:
    from mstrio.object_management.search_enums import (
        SearchDomain,
        SearchPattern,
        SearchResultsFormat,
        SearchScope,
    )
    from mstrio.server.project import Project
    from mstrio.types import TypeOrSubtype
    from mstrio.utils.entity import Entity


class DependenceMixin:
    """DependenceMixin class adds functionality of listing dependents
    and dependencies. Must be mixedin with Entity or its subclasses.
    """

    def list_dependents(
        self: 'Entity',
        project: 'Project | str | None' = None,
        name: str | None = None,
        pattern: 'SearchPattern | int' = 4,
        domain: 'SearchDomain | int' = 2,
        scope: 'SearchScope | str' = None,
        object_types: Optional['TypeOrSubtype'] = None,
        uses_recursive: bool = False,
        root: str | None = None,
        root_path: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        results_format: 'SearchResultsFormat | str' = 'LIST',
        to_dictionary: bool = True,
        **filters,
    ) -> list[dict] | list['Entity']:
        """List dependents of an object.

        Args:
            project (string): `Project` object or ID
            name (string): Value the search pattern is set to, which will
                be applied to the names of object types being searched.
                For example, search for all report objects (type) whose name
                begins with (pattern) B (name).
            pattern (integer or enum class object): Pattern to search for,
                such as Begin With or Exactly. Possible values are available in
                ENUM mstrio.object_management.SearchPattern.
                Default value is CONTAINS (4).
            domain (integer or enum class object): Domain where the search
                will be performed, such as Local or Project. Possible values are
                available in ENUM mstrio.object_management.SearchDomain.
                Default value is PROJECT (2).
            scope (SearchScope, str, optional): Scope of the search with regard
                to System Managed Objects. Possible values are available in
                ENUM mstrio.object_management.SearchScope.
            root (string, optional): Folder ID of the root folder where the
                search will be performed.
            root_path (str, optional): Path of the root folder in which the
                search will be performed. Can be provided as an alternative to
                `root` parameter. If both are provided, `root` is used.
                the path has to be provided in the following format:
                >>> # if it's inside of a project, example:
                >>>     /MicroStrategy Tutorial/Public Objects/Metrics
                >>> # if it's a root folder, example:
                >>>     /CASTOR_SERVER_CONFIGURATION/Users
            object_types (enum class object or integer or list of enum class
                objects or integers): Type(s) of object(s) to be searched,
                such as Folder, Attribute or User. Possible values available
                in ENUMs mstrio.types.ObjectTypes and
                mstrio.types.ObjectSubTypes
            uses_recursive (boolean): Control the Intelligence server to
                also find objects that use the given objects indirectly. Default
                value is false.
            results_format (SearchResultsFormat): either a list or a tree format
            to_dictionary (bool): If False returns objects, by default
                (True) returns dictionaries.
            limit (int): limit the number of elements returned.
                If `None` (default), all objects are returned.
            offset (int): Starting point within the collection of returned
                results. Used to control paging behavior. Default is 0.
            **filters: Available filter parameters: ['id', 'name',
                'description', 'date_created', 'date_modified', 'acg']

        Returns:
            list of objects or list of dictionaries
        """
        from mstrio.object_management.search_enums import (
            SearchDomain,
            SearchPattern,
            SearchScope,
        )
        from mstrio.object_management.search_operations import full_search

        pattern = pattern if pattern is not None else SearchPattern.CONTAINS
        domain = domain if domain is not None else SearchDomain.PROJECT
        scope = scope if scope is not None else SearchScope.NOT_MANAGED_ONLY

        if isinstance(scope, str):
            scope = SearchScope(scope)

        if self._OBJECT_TYPE == ObjectTypes.NOT_SUPPORTED:
            raise NotSupportedError(
                f"Listing dependents is not supported for unsupported object"
                f" with ID {self.id}."
            )

        project = project or self.connection.project_id
        if project is None:
            raise AttributeError(
                "Project not selected. Select project using `project` parameter."
            )

        return full_search(
            connection=self.connection,
            project=project,
            uses_object_id=self.id,
            uses_object_type=self._OBJECT_TYPE,
            name=name,
            pattern=pattern,
            domain=domain,
            scope=scope,
            object_types=object_types,
            uses_recursive=uses_recursive,
            root=root,
            root_path=root_path,
            limit=limit,
            offset=offset,
            results_format=results_format,
            to_dictionary=to_dictionary,
            **filters,
        )

    def has_dependents(self: 'Entity') -> bool:
        """Check if the object has any dependents.

        Returns:
            True if the object has dependents, False otherwise.
        """
        from mstrio.object_management.search_enums import SearchDomain, SearchScope

        return bool(
            self.list_dependents(
                limit=1,
                domain=SearchDomain.PROJECT,
                scope=SearchScope.ALL,
                uses_recursive=False,
                to_dictionary=True,
            )
        )

    def list_dependencies(
        self: 'Entity',
        project: 'Project | str | None' = None,
        name: str | None = None,
        pattern: 'SearchPattern | int' = 4,
        domain: 'SearchDomain | int' = 2,
        scope: 'SearchScope | str' = None,
        object_types: Optional['TypeOrSubtype'] = None,
        used_by_recursive: bool = False,
        root: str | None = None,
        root_path: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        results_format: 'SearchResultsFormat | str' = 'LIST',
        to_dictionary: bool = True,
        **filters,
    ):
        """List list_dependencies of an object.

        Args:
            project (string): `Project` object or ID
            name(string): Value the search pattern is set to, which will
                be applied to the names of object types being searched.
                For example, search for all report objects (type) whose name
                begins with (pattern) B (name).
            pattern(integer or enum class object): Pattern to search for,
                such as Begin With or Exactly. Possible values are available in
                ENUM mstrio.object_management.SearchPattern.
                Default value is CONTAINS (4).
            domain(integer or enum class object): Domain where the search
                will be performed, such as Local or Project. Possible values are
                available in ENUM mstrio.object_management.SearchDomain.
                Default value is PROJECT (2).
            scope (SearchScope, str, optional): Scope of the search with regard
                to System Managed Objects. Possible values are available in
                ENUM mstrio.object_management.SearchScope.
            root(string, optional): Folder ID of the root folder where the
                search will be performed.
            root_path (str, optional): Path of the root folder in which the
                search will be performed. Can be provided as an alternative to
                `root` parameter. If both are provided, `root` is used.
                    the path has to be provided in the following format:
                        if it's inside of a project, example:
                            /MicroStrategy Tutorial/Public Objects/Metrics
                        if it's a root folder, example:
                            /CASTOR_SERVER_CONFIGURATION/Users
            object_types(enum class object or integer or list of enum class
                objects or integers): Type(s) of object(s) to be searched,
                such as Folder, Attribute or User. Possible values available
                in ENUMs mstrio.types.ObjectTypes and
                mstrio.types.ObjectSubTypes
            used_by_recursive(boolean, optional): Control the Intelligence
                server to also find objects that are used by the given objects
                indirectly. Default value is false.
            results_format(SearchResultsFormat): either a list or a tree format
            to_dictionary (bool): If False returns objects, by default
                (True) returns dictionaries.
            limit (int): limit the number of elements returned.
                If `None` (default), all objects are returned.
            offset (int): Starting point within the collection of returned
                results. Used to control paging behavior. Default is 0.
            **filters: Available filter parameters: ['id', 'name',
                'description', 'date_created', 'date_modified', 'acg']

        Returns:
            list of objects or list of dictionaries
        """
        from mstrio.object_management.search_enums import (
            SearchDomain,
            SearchPattern,
            SearchScope,
        )
        from mstrio.object_management.search_operations import full_search

        pattern = pattern if pattern is not None else SearchPattern.CONTAINS
        domain = domain if domain is not None else SearchDomain.PROJECT
        scope = scope if scope is not None else SearchScope.NOT_MANAGED_ONLY

        if isinstance(scope, str):
            scope = SearchScope(scope)

        if self._OBJECT_TYPE == ObjectTypes.NOT_SUPPORTED:
            raise NotSupportedError(
                f"Listing dependencies is not supported for unsupported object"
                f" with ID {self.id}."
            )

        project = project or self.connection.project_id
        if project is None:
            raise AttributeError(
                "Project not selected. Select project using `project` parameter."
            )

        return full_search(
            connection=self.connection,
            project=project,
            pattern=pattern,
            domain=domain,
            scope=scope,
            used_by_object_id=self.id,
            used_by_object_type=self._OBJECT_TYPE,
            results_format=results_format,
            used_by_recursive=used_by_recursive,
            name=name,
            object_types=object_types,
            root=root,
            root_path=root_path,
            limit=limit,
            offset=offset,
            to_dictionary=to_dictionary,
            **filters,
        )
