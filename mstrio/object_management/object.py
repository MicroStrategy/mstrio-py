from typing import List, Optional, TYPE_CHECKING, Union

from mstrio.api import objects
from mstrio.object_management.search_operations import full_search, SearchDomain, SearchPattern
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.acl import ACLMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.helper import (
    get_args_from_func, get_default_args_from_func, get_valid_project_id
)

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_objects(
    connection: "Connection",
    object_type: ObjectTypes,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    domain: Union[SearchDomain, int] = SearchDomain.CONFIGURATION,
    search_pattern: Union[SearchPattern, int] = SearchPattern.CONTAINS,
    to_dictionary: bool = False,
    limit: int = None,
    **filters,
) -> Union[List["Object"], List[dict]]:
    """Get list of objects or dicts. Optionally filter the
    objects by specifying filters.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        object_type: Object type. Possible values can
            be found in EnumDSSXMLObjectTypes
        name (string, optional): value the search pattern is set to, which
            will be applied to the names of objects being searched
        project_id: ID of the project for which the objects are to be listed
        project_name: project name
        domain: domain where the search will be performed,
            such as Local or Project, possible values
            are defined in EnumDSSXMLSearchDomain
        search_pattern (SearchPattern enum or int, optional): pattern to search
            for, such as Begin With or Exactly. Possible values are available in
            ENUM mstrio.browsing.SearchPattern. Default value is CONTAINS (4).
        to_dictionary: If True returns dict, by default (False) returns Objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Examples:
        >>> list_objects(connection, object_type=ObjectTypes.USER)
    """
    # Project is validated only if project was specified in arguments -
    # otherwise fetch is performed from a non-project area.
    if project_id or project_name:
        project_id = get_valid_project_id(
            connection=connection,
            project_id=project_id,
            project_name=project_name,
        )

    return Object._list_objects(
        connection=connection,
        object_type=object_type,
        name=name,
        project_id=project_id,
        domain=domain,
        pattern=search_pattern,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class Object(Entity, ACLMixin, CertifyMixin, CopyMixin, MoveMixin, DeleteMixin):
    """Class representing a general type object using attributes common for
     all available objects.

    Attributes:
        name: name of the object
        id: object ID
        description: Description of the object
        abbreviation: Object abbreviation
        version: Object version ID
        ancestors: List of ancestor folders
        type: Object type. Enum
        subtype: Object subtype
        ext_type: Object extended type.
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd HH:mm:ss" in UTC
        owner: User object that is the owner
        icon_path: Object icon path
        view_media: View media settings
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        hidden: Specifies whether the object is hidden
        certified_info: Certification status, time of certification, and
            information about the certifier (currently only for document and
            report)
        project_id: project ID
        target_info: target information, only applicable to Shortcut objects
    """
    _DELETE_NONE_VALUES_RECURSION = False
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'certified_info': CertifiedInfo.from_dict,
        'owner': User.from_dict,
    }
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'date_created',
            'date_modified',
            'acg',
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acl',
            'comments',
            'project_id',
            'hidden',
            'target_info'
        ): objects.get_object_info
    }
    _API_PATCH: dict = {**Entity._API_PATCH, ('folder_id'): (objects.update_object, 'partial_put')}

    def __init__(self, connection: "Connection", type: ObjectTypes, id: str):
        """Initialize object by ID.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of an existing object.
            type (ObjectTypes): object type
        """

        super().__init__(connection=connection, object_id=id, type=type)

    def _init_variables(self, **kwargs) -> None:
        self._OBJECT_TYPE = ObjectTypes(kwargs.get("type")) if ObjectTypes.contains(
            kwargs.get("type")
        ) else ObjectTypes.NONE
        super()._init_variables(**kwargs)

    def __str__(self):
        return f"Object named: '{self.name}' with ID: '{self.id}'"

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        abbreviation: Optional[str] = None
    ) -> None:
        """Alter the object properties.

        Args:
            name: object name
            description: object description
            abbreviation: abbreviation
        """
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_objects(
        cls,
        connection: "Connection",
        object_type: ObjectTypes,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        to_dictionary: bool = False,
        domain: Union[int, SearchDomain] = SearchDomain.CONFIGURATION,
        pattern: Union[int, SearchPattern] = SearchPattern.CONTAINS,
        limit: Optional[int] = None,
        **filters,
    ) -> Union[List["Object"], List[dict]]:
        objects = full_search(
            connection,
            object_types=object_type,
            name=name,
            project=project_id,
            domain=domain,
            pattern=pattern,
            limit=limit,
            **filters,
        )
        if to_dictionary:
            return objects
        return [cls.from_dict(source=obj, connection=connection) for obj in objects]
