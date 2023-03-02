from typing import Optional, TYPE_CHECKING, Union

from mstrio.utils.exceptions import NotSupportedError
from mstrio.types import ObjectTypes

if TYPE_CHECKING:
    from mstrio.object_management.search_enums import (
        SearchDomain, SearchPattern, SearchResultsFormat
    )
    from mstrio.server import Project
    from mstrio.types import TypeOrSubtype
    from mstrio.utils.entity import Entity


class DependenceMixin:
    """DependenceMixin class adds functionality of listing dependents
    and dependencies. Must be mixedin with Entity or its subclasses.
    """

    def list_dependents(
        self: 'Entity',
        project: Optional[Union['Project', str]] = None,
        name: Optional[str] = None,
        pattern: Union['SearchPattern', int] = 4,
        domain: Union['SearchDomain', int] = 2,
        object_types: Optional['TypeOrSubtype'] = None,
        uses_recursive: bool = False,
        root: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        results_format: Union['SearchResultsFormat', str] = 'LIST',
        to_dictionary: bool = True,
        **filters,
    ):
        """List dependents of an object.

        Args:
            project (string): `Project` object or ID
            name(string): Value the search pattern is set to, which will
                be applied to the names of object types being searched.
                For example, search for all report objects (type) whose name
                begins with (patter) B (name).
            pattern(integer or enum class object): Pattern to search for,
                such as Begin With or Exactly. Possible values are available in
                ENUM mstrio.object_management.SearchPattern.
                Default value is CONTAINS (4).
            domain(integer or enum class object): Domain where the search
                will be performed, such as Local or Project. Possible values are
                available in ENUM mstrio.object_management.SearchDomain.
                Default value is PROJECT (2).
            root(string, optional): Folder ID of the root folder where the
                search will be performed.
            object_types(enum class object or integer or list of enum class
                objects or integers): Type(s) of object(s) to be searched,
                such as Folder, Attribute or User. Possible values available
                in ENUMs mstrio.types.ObjectTypes and
                mstrio.types.ObjectSubTypes
            uses_recursive(boolean): Control the Intelligence server to
                also find objects that use the given objects indirectly. Default
                value is false.
            results_format(SearchResultsFormat): either a list or a tree format
            to_dictionary (bool): If False returns objects, by default
                (True) returns dictionaries.
            limit (int): limit the number of elements returned.
                If `None` (default), all objects are returned.
            offset (int): Starting point within the collection of returned
                results. Used to control paging behavior. Default is 0.
            **filters: Available filter parameters: ['id', 'name', 'description'
                ,'date_created', 'date_modified', 'acg']

        Returns:
            list of objects or list of dictionaries
        """
        from mstrio.object_management.search_operations import full_search

        if self._OBJECT_TYPE == ObjectTypes.NONE:
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
            object_types=object_types,
            uses_recursive=uses_recursive,
            root=root,
            limit=limit,
            offset=offset,
            results_format=results_format,
            to_dictionary=to_dictionary,
            **filters
        )

    def list_dependencies(
        self: 'Entity',
        project: Optional[Union['Project', str]] = None,
        name: Optional[str] = None,
        pattern: Union['SearchPattern', int] = 4,
        domain: Union['SearchDomain', int] = 2,
        object_types: Optional['TypeOrSubtype'] = None,
        used_by_recursive: bool = False,
        root: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        results_format: Union['SearchResultsFormat', str] = 'LIST',
        to_dictionary: bool = True,
        **filters,
    ):
        """List list_dependencies of an object.

        Args:
            project (string): `Project` object or ID
            name(string): Value the search pattern is set to, which will
                be applied to the names of object types being searched.
                For example, search for all report objects (type) whose name
                begins with (patter) B (name).
            pattern(integer or enum class object): Pattern to search for,
                such as Begin With or Exactly. Possible values are available in
                ENUM mstrio.object_management.SearchPattern.
                Default value is CONTAINS (4).
            domain(integer or enum class object): Domain where the search
                will be performed, such as Local or Project. Possible values are
                available in ENUM mstrio.object_management.SearchDomain.
                Default value is PROJECT (2).
            root(string, optional): Folder ID of the root folder where the
                search will be performed.
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
            **filters: Available filter parameters: ['id', 'name', 'description'
                ,'date_created', 'date_modified', 'acg']

        Returns:
            list of objects or list of dictionaries
        """
        from mstrio.object_management.search_operations import full_search

        if self._OBJECT_TYPE == ObjectTypes.NONE:
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
            used_by_object_id=self.id,
            used_by_object_type=self._OBJECT_TYPE,
            results_format=results_format,
            used_by_recursive=used_by_recursive,
            name=name,
            object_types=object_types,
            root=root,
            limit=limit,
            offset=offset,
            to_dictionary=to_dictionary,
            **filters
        )
