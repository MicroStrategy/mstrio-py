from typing import List, Optional, TYPE_CHECKING, Union

from mstrio.api import objects
from mstrio.object_management.search_operations import full_search, SearchDomain
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.acl import ACLMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_objects(connection: "Connection", object_type: ObjectTypes,
                 project_id: Optional[str] = None, domain: Union[SearchDomain,
                                                                 int] = SearchDomain.CONFIGURATION,
                 to_dictionary: bool = False, limit: int = None,
                 **filters) -> Union[List["Object"], List[dict]]:
    """Get list of objects or dicts. Optionally filter the
    objects by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        object_type: Object type. Possible values can
            be found in EnumDSSXMLObjectTypes
        project_id: ID of the project for which the objects are to be listed
        domain: domain where the search will be performed,
            such as Local or Project, possible values
            are defined in EnumDSSXMLSearchDomain
        to_dictionary: If True returns dict, by default (False) returns Objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Examples:
        >>> list_objects(connection, object_type=ObjectTypes.USER)
    """
    return Object._list_objects(
        connection=connection,
        object_type=object_type,
        project_id=project_id,
        domain=domain,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class Object(Entity, ACLMixin, CertifyMixin, CopyMixin, DeleteMixin):
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
    _DELETE_NONE_VALUES_RECURSION = True
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'certified_info': CertifiedInfo.from_dict,
        'owner': User.from_dict,
    }
    _API_GETTERS = {
        ('id', 'name', 'description', 'date_created', 'date_modified', 'acg', 'abbreviation',
         'type', 'subtype', 'ext_type', 'version', 'owner', 'icon_path', 'view_media', 'ancestors',
         'certified_info', 'acl', 'comments', 'project_id', 'hidden',
         'target_info'): objects.get_object_info
    }

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
            kwargs.get("type")) else ObjectTypes.NONE
        super()._init_variables(**kwargs)

    def __str__(self):
        return f"Object named: '{self.name}' with ID: '{self.id}'"

    def alter(self, name: Optional[str] = None, description: Optional[str] = None,
              abbreviation: Optional[str] = None) -> None:
        """Alter the object properties.

        Args:
            name: object name
            description: object description
            abbreviation: abbreviation
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

    @classmethod
    def _list_objects(cls, connection: "Connection", object_type: ObjectTypes,
                      project_id: Optional[str] = None, to_dictionary: bool = False,
                      domain: Union[int, SearchDomain] = SearchDomain.CONFIGURATION,
                      limit: Optional[int] = None, **filters) -> Union[List["Object"], List[dict]]:
        objects = full_search(
            connection,
            object_types=object_type,
            project=project_id,
            domain=domain,
            limit=limit,
            **filters,
        )
        if to_dictionary:
            return objects
        return [cls.from_dict(source=obj, connection=connection) for obj in objects]
