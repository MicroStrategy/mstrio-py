from enum import auto
import logging
from typing import List, Optional, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api import objects, user_hierarchies
from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import delete_none_values, Dictable, fetch_objects, get_enum_val

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


class ElementDisplayOption(AutoName):
    LIMITED_ELEMENTS = auto()
    ALL_ELEMENTS = auto()
    NO_ELEMENTS = auto()


class UserHierarchySubType(AutoName):
    DIMENSION_USER = auto()
    DIMENSION_USER_HIERARCHY = auto()


def list_user_hierarchies(connection: "Connection", to_dictionary: bool = False, limit: int = None,
                          **filters) -> Union[List["UserHierarchy"], List[dict]]:
    """Get list of UserHierarchy objects or dicts. Optionally filter the
    user hierarchies by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            User Hierarchy objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Examples:
        >>> list_user_hierarchies(connection, name='hierarchy_name')
    """
    return UserHierarchy._list_user_hierarchies(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class HierarchyAttribute(Dictable):
    """Object that specifies the hierarchy attribute.

    Attributes:
        object_id: hierarchy attribute ID
        name: name of the attribute
        entry_point: whether this hierarchy attribute is an entry point
        element_display_option: used to control element display for
            each hierarchy attribute, ElementDisplayOption enum
        filters: the list of filters defined on this hierarchy attribute
        limit: the element display limit when element_display_option
            is limited_elements
    """
    _DELETE_NONE_VALUES_RECURSION = True

    _FROM_DICT_MAP = {
        'element_display_option': ElementDisplayOption,
        'filters': [SchemaObjectReference.from_dict]
    }

    def __init__(self, object_id: str, entry_point: bool, name: str,
                 element_display_option: Union[ElementDisplayOption, str],
                 filters: Union[List[SchemaObjectReference],
                                List[dict]] = None, limit: Optional[int] = None):
        self.object_id = object_id
        self.entry_point = entry_point
        self.name = name
        self.element_display_option = element_display_option if isinstance(
            element_display_option,
            ElementDisplayOption) else ElementDisplayOption(element_display_option)
        self.filters = [
            SchemaObjectReference.from_dict(obj_ref)
            if not isinstance(obj_ref, SchemaObjectReference) else object_id for obj_ref in filters
        ] if filters else None
        self.limit = limit

    def __eq__(self, other):
        if isinstance(self, dict):
            self = HierarchyAttribute.from_dict(self)
        if isinstance(other, dict):
            other = HierarchyAttribute.from_dict(other)
        return self.name == other.name and self.object_id == other.object_id


class HierarchyRelationship(Dictable):
    """Object that specifies the hierarchy relationship between
    hierarchy attributes.

    Attributes:
        parent: an information about an object representing a
            parent in a current hierarchy relationship,
            SchemaObjectReference object
        child: an information about an object representing a
            child in a current hierarchy relationship,
            SchemaObjectReference object
    """
    _DELETE_NONE_VALUES_RECURSION = True

    _FROM_DICT_MAP = {
        'parent': SchemaObjectReference.from_dict,
        'child': SchemaObjectReference.from_dict
    }

    def __init__(self, parent: Union[SchemaObjectReference, dict],
                 child: Union[SchemaObjectReference, dict]):
        self.parent = parent if isinstance(
            parent, SchemaObjectReference) else SchemaObjectReference.from_dict(parent)
        self.child = child if isinstance(
            child, SchemaObjectReference) else SchemaObjectReference.from_dict(child)

    def __eq__(self, other):
        if isinstance(self, dict):
            self = HierarchyRelationship.from_dict(self)
        if isinstance(other, dict):
            other = HierarchyRelationship.from_dict(other)
        return self.parent == other.parent and self.child == other.child


class UserHierarchy(Entity, DeleteMixin):
    """A unique abstraction of hierarchies above the System Hierarchy,
    which can contain an arbitrary number of attributes and paths between
    them. These User Hierarchies allow users to browse through the data
    and drill as required by business needs, as opposed to how the data
    is physically stored in the data source.

    Attributes:
        name: name of the user hierarchy
        id: user hierarchy ID
        description: description of the user hierarchy
        sub_type: string literal used to identify the type of a metadata object,
            UserHierarchySubType enum
        version: object version ID
        ancestors: list of ancestor folders
        type: object type, ObjectTypes enum
        ext_type: object extended type, ExtendedType enum
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        owner: User object that is the owner
        acg: access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: object access control list
        version_id: the version number this object is currently carrying
        use_as_drill_hierarchy: whether this user hierarchy is used as
            drill hierarchy, default True
        is_embedded: if true indicates that the target object of this reference
            is embedded within this object, if this field is omitted
            (as is usual) then the target is not embedded.
        path: the path of the object, read only
        primary_locale: the primary locale of the object, in the IETF BCP 47
            language tag format, such as "en-US", read only
        attributes: the list of user hierarchy attributes
        relationships: the list of attribute relationships stored in
            the user hierarchy
        destination_folder_id: a globally unique identifier used to distinguish
            between metadata objects within the same project
    """
    _DELETE_NONE_VALUES_RECURSION = True

    _OBJECT_TYPE = ObjectTypes.DIMENSION
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP, 'owner': User.from_dict,
        'sub_type': UserHierarchySubType,
        'attributes': [HierarchyAttribute.from_dict],
        'relationships': [HierarchyRelationship.from_dict]
    }
    _API_GETTERS = {
        ('type', 'subtype', 'ext_type', 'date_created', 'date_modified', 'version', 'owner',
         'ancestors', 'acg', 'acl'): objects.get_object_info,
        ('id', 'name', 'description', 'sub_type', 'date_created', 'date_modified', 'path',
         'version_id', 'use_as_drill_hierarchy', 'is_embedded', 'primary_locale', 'attributes',
         'relationships', 'destination_folder_id'): user_hierarchies.get_user_hierarchy
    }
    _API_PATCH: dict = {
        ('name', 'description', 'relationships', 'use_as_drill_hierarchy', 'destination_folder_id',
         'sub_type', 'is_embedded', 'attributes'): (user_hierarchies.update_user_hierarchy, "put")
    }
    _API_DELETE = staticmethod(user_hierarchies.delete_user_hierarchy)
    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'sub_type': str,
        'use_as_drill_hierarchy': bool,
        'destination_folder_id': str,
        'is_embedded': bool,
        'attributes': list,
        'relationships': list,
    }
    _REST_ATTR_MAP = {
        "object_id": "id",
    }

    def __init__(self, connection: "Connection", id: Optional[str] = None,
                 name: Optional[str] = None):
        """Initialize user hierarchy object by its identifier.

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Args:

        """
        if id is None and name is None:
            raise ValueError("Please specify either 'name' or 'id' parameter in the constructor.")

        if id is None:
            objects_info = self._list_user_hierarchies(connection=connection, name=name,
                                                       to_dictionary=True)

            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no User Hierarchy: '{name}'")
        else:
            super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.sub_type = UserHierarchySubType(
            kwargs.get('subType')) if kwargs.get('subType') else None
        self.primary_locale = kwargs.get('primaryLocale')
        self.is_embedded = kwargs.get('isEmbedded')
        self.destination_folder_id = kwargs.get('destinationFolderId')
        self.use_as_drill_hierarchy = kwargs.get('useAsDrillHierarchy')
        self.attributes = [
            HierarchyAttribute.from_dict(source=attr) for attr in kwargs.get("attributes")
        ] if kwargs.get('attributes') else None
        self.relationships = [
            HierarchyRelationship.from_dict(source=rel) for rel in kwargs.get("relationships")
        ] if kwargs.get('attributes') else None
        self._path = kwargs.get('path')
        self._version_id = kwargs.get('versionId')

    @classmethod
    def create(cls, connection: "Connection", name: str, sub_type: Union[str,
                                                                         UserHierarchySubType],
               destination_folder_id: str, attributes: Union[List[HierarchyAttribute], List[dict]],
               use_as_drill_hierarchy: bool = True, description: str = None,
               is_embedded: bool = False, primary_locale: str = None,
               relationships: Union[List[HierarchyRelationship], List[dict]] = None):
        """Create a new user hierarchy in a specific project.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name (str): name of a new user hierarchy.
            sub_type (str, enum): string literal used to identify the type of
                a metadata object, UserHierarchySubType enum
            attributes (list): the list of attributes that
                do have any relationships currently
            destination_folder_id (str): a globally unique identifier used
                to distinguish between metadata objects within the same project
            use_as_drill_hierarchy (bool, optional): whether this user hierarchy
                is used as drill hierarchy
            description (str, optional): optional description of a new
                user hierarchy
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            primary_locale (str, optional): the primary locale of the object,
                in the IETF BCP 47 language tag format, such as "en-US"
            relationships (list, optional): the list of attribute
                relationships stored in the system hierarchy
        Returns:
            UserHierarchy object
        """
        attributes = [
            attr.to_dict() if isinstance(attr, HierarchyAttribute) else attr for attr in attributes
        ]
        relationships = [
            rel.to_dict() if isinstance(rel, HierarchyRelationship) else rel
            for rel in relationships
        ] if relationships else None
        body = {
            "information": {
                "name": name,
                "description": description,
                "subType": get_enum_val(sub_type, UserHierarchySubType),
                "destinationFolderId": destination_folder_id,
                "isEmbedded": is_embedded,
                "primaryLocale": primary_locale
            },
            "useAsDrillHierarchy": use_as_drill_hierarchy,
            "primaryLocale": primary_locale,
            "attributes": attributes,
            "relationships": relationships
        }
        body = delete_none_values(body, recursion=True)
        response = user_hierarchies.create_user_hierarchy(connection, body).json()
        if config.verbose:
            logger.info(f"Successfully created user hierarchy named: '{response['name']}' "
                        f"with ID: '{response['id']}'")
        return cls.from_dict(source=response, connection=connection)

    def alter(self, name: str = None, sub_type: Union[str, UserHierarchySubType] = None,
              attributes: Union[List[HierarchyAttribute], List[dict], None] = None,
              use_as_drill_hierarchy: Optional[bool] = None, description: Optional[str] = None,
              is_embedded: bool = False, destination_folder_id: Optional[str] = None,
              relationships: Union[List[HierarchyRelationship], List[dict], None] = None):
        """Alter the user hierarchies properties.

        Args:
            name (str, optional): name of a user hierarchy
            sub_type (str, enum, optional):  string literal used to identify
                the type of a metadata object, UserHierarchySubType enum
            description(str, optional): description of a user hierarchy
            use_as_drill_hierarchy (bool, optional): whether this user hierarchy
                is used as drill hierarchy
            attributes (list, optional): the list of attributes that
                do have any relationships currently
            is_embedded (bool, optional): if true indicates that the target
                object of this reference is embedded within this object
            destination_folder_id (str, optional): a globally unique identifier
                used to distinguish between objects within the same project
            relationships (list, optional): the list of attribute
                relationships stored in the system hierarchy
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

    def add_attribute(self, attribute: Union[HierarchyAttribute, dict]):
        """Add an attribute to an existing hierarchy.

        Args:
            attribute: (HierarchyAttribute, dict): an attribute
                to be added to the hierarchy
        """
        return self.alter(attributes=self.attributes + [attribute])

    def remove_attribute(self, attribute: Union[HierarchyAttribute, dict]):
        """Remove attribute from an existing user hierarchy.

        Args:
            attribute: (HierarchyAttribute, dict): an attribute
                to be removed from the hierarchy
        """
        attributes = [attr for attr in self.attributes if attr != attribute]
        return self.alter(attributes=attributes)

    def add_relationship(self, relationship: Union[HierarchyRelationship, dict]):
        """Add a relationship to an existing hierarchy.

        Args:
            relationship: (HierarchyRelationship, dict): a relationship
                to be added to the hierarchy
        """
        return self.alter(relationships=self.relationships + [relationship])

    def remove_relationship(self, relationship: Union[HierarchyRelationship, dict]):
        """Remove relationship from an existing user hierarchy.

        Args:
            relationship: (HierarchyRelationship, dict): a relationship
                to be removed from the hierarchy
        """
        relationships = [rel.to_dict() for rel in self.relationships if rel != relationship]
        body = self.to_dict()
        body['relationships'] = relationships
        response = user_hierarchies.update_user_hierarchy(connection=self.connection, id=self.id,
                                                          changeset_id=None, body=body)
        if response.ok:
            response = response.json()
            self._set_object_attributes(**response)

    @classmethod
    def _list_user_hierarchies(cls, connection: "Connection", to_dictionary: bool = False,
                               limit: int = None,
                               **filters) -> Union[List["UserHierarchy"], List[dict]]:
        objects = fetch_objects(
            connection=connection,
            api=user_hierarchies.get_user_hierarchies,
            dict_unpack_value="hierarchies",
            limit=limit,
            filters=filters,
        )
        if to_dictionary:
            return objects
        return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @property
    def path(self):
        return self._path

    @property
    def version_id(self):
        return self._version_id
