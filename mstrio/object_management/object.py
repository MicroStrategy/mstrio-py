import logging
from typing import TYPE_CHECKING

from mstrio.object_management.search_operations import (
    SearchDomain,
    SearchPattern,
    full_search,
)
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.acl import ACLMixin
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.entity import CertifyMixin, CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum
from mstrio.utils.helper import (
    get_args_from_func,
    get_default_args_from_func,
    get_valid_project_id,
)
from mstrio.utils.response_processors import objects as objects_processors

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


def list_objects(
    connection: "Connection",
    object_type: ObjectTypes | int,
    name: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    domain: SearchDomain | int = SearchDomain.CONFIGURATION,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    to_dictionary: bool = False,
    limit: int = None,
    **filters,
) -> list["Object"] | list[dict]:
    """Get list of objects or dicts. Optionally filter the
    objects by specifying filters.

    Specify either `project_id` or `project_name`.
    When `project_id` is provided (not `None`), `project_name` is omitted.

    Args:
        connection: Strategy One connection object returned by
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
            ENUM mstrio.object_management.SearchPattern.
            Default value is CONTAINS (4).
        to_dictionary: If True returns dict, by default (False) returns Objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg', 'owner', 'ext_type']

    Examples:
        >>> list_objects(connection, object_type=ObjectTypes.USER)
    """

    project_id = get_valid_project_id(
        connection=connection,
        project_id=project_id,
        project_name=project_name,
        with_fallback=True,
    )

    result = Object._list_objects(
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

    if not result:
        logger.info(
            f"Search in the domain: {domain.name} returned empty result."
            " Try searching in different domain."
        )
    return result


class Object(Entity, ACLMixin, CertifyMixin, CopyMixin, MoveMixin, DeleteMixin):
    """Class representing a general type object using attributes common for
     all available metadata objects.

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
            'target_info',
            'hidden',
            'comments',
        ): objects_processors.get_info
    }
    _API_PATCH: dict = {
        (
            'name',
            'description',
            'abbreviation',
            'hidden',
            'folder_id',
            'comments',
        ): (objects_processors.update, 'partial_put'),
    }

    def __init__(self, connection: "Connection", type: ObjectTypes, id: str):
        """Initialize object by ID.

        Args:
            connection: Strategy One connection object returned by
                `connection.Connection()`.
            id (str): Identifier of an existing object.
            type (ObjectTypes): object type
        """

        super().__init__(connection=connection, object_id=id, type=type)

    def _init_variables(self, **kwargs) -> None:
        object_type = kwargs.get('type')
        self._OBJECT_TYPE = (
            ObjectTypes(object_type)
            if ObjectTypes.contains(object_type)
            else ObjectTypes.NOT_SUPPORTED
        )
        super()._init_variables(**kwargs)

    def __str__(self):
        return f"Object named: '{self.name}' with ID: '{self.id}'"

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        abbreviation: str | None = None,
        hidden: bool | None = None,
        comments: str | None = None,
    ) -> None:
        """Alter the object properties.

        Args:
            name: object name
            description: object description
            abbreviation: abbreviation
            hidden: Specifies whether the metric is hidden
            comments: long description of the object
        """
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        default_dict = dict(zip(args[-len(defaults) :], defaults)) if defaults else {}
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
        object_type: ObjectTypes | int,
        name: str | None = None,
        project_id: str | None = None,
        to_dictionary: bool = False,
        domain: int | SearchDomain = SearchDomain.CONFIGURATION,
        pattern: int | SearchPattern = SearchPattern.CONTAINS,
        limit: int | None = None,
        **filters,
    ) -> list["Object"] | list[dict]:
        objects = full_search(
            connection,
            object_types=get_enum(object_type, ObjectTypes),
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
