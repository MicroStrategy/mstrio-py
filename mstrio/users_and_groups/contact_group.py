# NOSONAR
from collections import defaultdict
from enum import auto
import logging
from typing import Iterable, Optional, Union, List, TYPE_CHECKING

from mstrio import config
from mstrio.api import contact_groups
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import auto_match_args_entity, DeleteMixin, EntityBase
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import (
    Dictable, fetch_objects_async, get_args_from_func, get_default_args_from_func, get_objects_id
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.users_and_groups.contact import Contact

logger = logging.getLogger(__name__)


class ContactGroupMemberType(AutoName):
    CONTACT = auto()
    CONTACT_GROUP = auto()
    USER = auto()


class ContactGroupMember(Dictable):
    """ContactGroupMember class, representing either Contact or ContactGroup

    Attributes:
        name: member's name
        type: type of a member, instance of ContactGroupMemberType
        id: id of member, optional
        description: member's description, optional
        enabled: specifies if a member is enabled
    """
    _FROM_DICT_MAP = {"type": ContactGroupMemberType}

    def __init__(
        self,
        name: str,
        type: Union[str, ContactGroupMemberType],
        id: Optional[str] = None,
        description: Optional[str] = None,
        enabled: bool = True
    ):
        self.name = name
        self.type = ContactGroupMemberType(type) if isinstance(type, str) else type
        self.id = id
        self.description = description
        self.enabled = enabled

    def __repr__(self) -> str:
        param_dict = auto_match_args_entity(
            self.__init__, self, exclude=['self'], include_defaults=False
        )

        params = [
            f"{param}={self.type}" if param == 'type' else f'{param}={repr(value)}' for param,
            value in param_dict.items()
        ]
        formatted_params = ', '.join(params)

        return f'ContactGroupMember({formatted_params})'

    @classmethod
    def from_contact_or_contact_group(
        cls, obj: Union['Contact', 'ContactGroup']
    ) -> 'ContactGroupMember':
        """Initialize instance of class ContactGroupMember

        Args:
            obj: object to used as base for initializing instance of
            ContactGroupMember

        Returns:
            ContactGroupMember object
        """
        from mstrio.users_and_groups.contact import Contact

        if isinstance(obj, Contact):
            return cls(id=obj.id, name=obj.name, type=ContactGroupMemberType.CONTACT)

        if isinstance(obj, ContactGroup):
            return cls(id=obj.id, name=obj.name, type=ContactGroupMemberType.CONTACT_GROUP)


@method_version_handler('11.3.0200')
def list_contact_groups(
    connection: "Connection", to_dictionary: bool = False, limit: Optional[int] = None, **filters
) -> Union[List["ContactGroup"], List[dict]]:
    """Get all contact groups as list of ContactGroup objects or
    dictionaries.

    Optionally filter the contact groups by specifying filters.

    Args:
        connection(object): MicroStrategy connection object
        to_dictionary: If True returns a list of contact group dicts,
            otherwise returns a list of contact group objects
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            enabled]
    """
    return ContactGroup._list_contact_groups(
        connection=connection, to_dictionary=to_dictionary, limit=limit, **filters
    )


@class_version_handler('11.3.0200')
class ContactGroup(EntityBase, DeleteMixin):
    """Object representation of Microstrategy Contact Group object

    Attributes:
        name: contact group's name
        id: contact group's id
        description: contact group's description
        enabled: specifies if a contact group is enabled
        linked_user: user linked to contact group, instance of User
        members: list of contact group's members, instances of
            ContactGroupMember
        memberships: list of Contact Groups that the Contact Group belongs to
        connection: instance of Connection class, represents connection
                    to MicroStrategy Intelligence Server
    """
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'linked_user': User.from_dict,
        'members': [ContactGroupMember.from_dict],
    }
    _API_GETTERS = {
        ('id', 'name', 'description', 'enabled', 'linked_user', 'members',
         'memberships'): contact_groups.get_contact_group
    }
    _API_DELETE = staticmethod(contact_groups.delete_contact_group)
    _API_PATCH = {
        ('name', 'description', 'enabled', 'linked_user',
         'members'): (contact_groups.update_contact_group, 'put')
    }
    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'enabled': bool,
        'linked_user': dict,
        'members': list,
        'memberships': list
    }

    def __init__(
        self, connection: 'Connection', id: Optional[str] = None, name: Optional[str] = None
    ):
        """Initialize Contact Group object by passing id or name.
        When `id` is provided, name is omitted.

        Args:
            connection: MicroStrategy connection object
            id: ID of Contact
            name: name of Contact Group
        """

        if id is None and name is None:
            raise ValueError("Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            result = ContactGroup._list_contact_groups(
                connection=connection,
                name=name,
                to_dictionary=True,
            )
            if result:
                object_data, object_data['connection'] = result[0], connection
                self._init_variables(**object_data)
            else:
                raise ValueError(f"There is no Contact Group named: '{name}'")
        else:
            super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self.description = kwargs.get('description')
        self.enabled = kwargs.get('enabled')

        linked_user = kwargs.get("linked_user")
        self.linked_user = User.from_dict(linked_user, self.connection) if linked_user else None

        members = kwargs.get('members')
        self.members = [
            ContactGroupMember.from_dict(member) for member in members
        ] if members else None

        memberships = kwargs.get('memberships')
        self._memberships = [
            self.from_dict(m, self.connection) for m in memberships
        ] if memberships else None

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        linked_user: Union[str, User],
        members: List[Union[dict, ContactGroupMember]],
        description: Optional[str] = None,
        enabled: bool = True
    ) -> 'ContactGroup':
        """Create a new contact group.

        Args:
            connection: MicroStrategy connection object
                returned by `connection.Connection()`
            name: contact group name
            linked_user: user linked to contact
            members: list of members
            description: description of contact
            enabled: specifies if contact should be enabled

        Returns:
            `ContactGroup` object
        """
        members = [m.to_dict() if isinstance(m, ContactGroupMember) else m for m in members]
        linked_user = get_objects_id(linked_user, User)
        body = {
            'name': name,
            'description': description,
            'enabled': enabled,
            'linkedUser': {
                'id': linked_user
            },
            'members': members
        }
        res = contact_groups.create_contact_group(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created contact group named: '{res.get('name')}' "
                f"with ID: '{res.get('id')}'"
            )
        return cls.from_dict(res, connection)

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        linked_user: Optional[Union['User', str]] = None,
        members: Optional[Iterable[Union['ContactGroupMember', dict]]] = None
    ):
        """Update properties of a contact group

        Args:
            name: name of a contact
            description: description of a contact
            enabled: specifies if a contact is enabled
            linked_user: an object of class User linked to the contact
            members: list of contact group members, instances of
               `ContactGroupMember`
        """

        linked_user = {'id': get_objects_id(linked_user, User)} if linked_user else None

        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        defaults_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()

        properties = defaultdict(dict)

        for property_key in defaults_dict:
            if local[property_key] is not None:
                properties[property_key] = local[property_key]

        self._alter_properties(**properties)

    @classmethod
    def _list_contact_groups(
        cls,
        connection: "Connection",
        to_dictionary: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **filters
    ) -> Union[List["ContactGroup"], List[dict]]:
        objects = fetch_objects_async(
            connection=connection,
            api=contact_groups.get_contact_groups,
            async_api=contact_groups.get_contact_groups_async,
            limit=limit,
            offset=offset,
            chunk_size=1000,
            filters=filters,
            dict_unpack_value='contactGroups',
        )

        if to_dictionary:
            return objects
        return [ContactGroup.from_dict(source=obj, connection=connection) for obj in objects]

    def _set_object_attributes(self, **kwargs) -> None:
        super()._set_object_attributes(**kwargs)
        memberships = kwargs.get("memberships")

        memberships_objs = [self.from_dict(m, self.connection)
                            for m in memberships] if memberships else []
        setattr(self, '_memberships', memberships_objs)

    def add_members(
        self, members: Iterable[Union['ContactGroupMember', 'Contact', 'ContactGroup']]
    ):
        """Add member

        Args:
           members: list of members to add to contact group
        """
        members_ids = [member.id for member in self.members]
        new_members = [
            ContactGroupMember.from_contact_or_contact_group(obj)
            if not isinstance(obj, ContactGroupMember) else obj
            for obj in members
            if obj.id not in members_ids
        ]

        self.alter(members=new_members + self.members)

    def remove_members(
        self, members: Iterable[Union['ContactGroupMember', 'Contact', 'ContactGroup']]
    ):
        """Remove member

        Args:
           members: list of members to remove from contact group
        """
        ids_to_remove = [member.id for member in members]
        new_member_list = [member for member in self.members if member.id not in ids_to_remove]

        self.alter(members=new_member_list)

    @property
    def memberships(self):
        return self._memberships
