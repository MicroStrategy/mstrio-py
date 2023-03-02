# NOSONAR
from collections import defaultdict
from enum import auto
import logging
from typing import Iterable, Optional, TYPE_CHECKING

from mstrio import config
from mstrio.api import contacts
from mstrio.users_and_groups.contact_group import ContactGroup
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import auto_match_args_entity, DeleteMixin, EntityBase
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import (
    camel_to_snake,
    delete_none_values,
    Dictable,
    fetch_objects,
    get_args_from_func,
    get_default_args_from_func,
    get_objects_id
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.distribution_services.device.device import Device

logger = logging.getLogger(__name__)


class ContactDeliveryType(AutoName):
    EMAIL = auto()
    FILE = auto()
    PRINTER = auto()
    FTP = auto()
    MOBILE_ANDROID = auto()
    MOBILE_IPHONE = auto()
    MOBILE_IPAD = auto()
    UNSUPPORTED = auto()


class ContactAddress(Dictable):
    """Representation of contact address object

    Attributes:
        id: id of contact address, optional
        name: contact address' name
        physical_address: physical address of contact
        delivery_type: object of type ContactDeliveryType
        is_default: specifies if address is default, optional,
            default value: False
        device: instance of Device or string (containing device's id),
            if device is a string, connection is required
        connection: instance of Connection, optional,
            is required if device is string
    """
    @staticmethod
    def __device_from_dict(source, connection):
        from mstrio.distribution_services.device.device import Device
        return Device.from_dict(source, connection)

    _FROM_DICT_MAP = {'delivery_type': ContactDeliveryType, 'device': __device_from_dict}

    def __init__(
        self,
        name: str,
        physical_address: str,
        delivery_type: ContactDeliveryType | str,
        device: 'Device | str',
        id: Optional[str] = None,
        is_default: bool = False,
        connection: Optional['Connection'] = None
    ):
        self.id = id
        self.name = name
        self.physical_address = physical_address
        self.is_default = is_default

        self.delivery_type = delivery_type if isinstance(delivery_type, ContactDeliveryType
                                                         ) else ContactDeliveryType(delivery_type)

        from mstrio.distribution_services.device.device import Device
        if isinstance(device, Device):
            self.device = device
        else:
            if not connection:
                raise ValueError('Argument: connection is required if device is a string')

            self.device = Device(connection, id=device)

    def __repr__(self) -> str:
        param_dict = auto_match_args_entity(
            self.__init__, self, exclude=['self'], include_defaults=False
        )

        params = [
            f"{param}={self.delivery_type}"
            if param == 'delivery_type' else f'{param}={repr(value)}' for param,
            value in param_dict.items()
        ]
        formatted_params = ', '.join(params)

        return f'ContactAddress({formatted_params})'

    def to_dict(self, camel_case=True) -> dict:
        result = {
            'name': self.name,
            'id': self.id,
            'physicalAddress': self.physical_address,
            'deliveryType': self.delivery_type.value,
            'deviceId': self.device.id,
            'deviceName': self.device.name,
            'isDefault': self.is_default
        }

        return result if camel_case else camel_to_snake(result)

    @classmethod
    def from_dict(cls, source, connection, to_snake_case=True) -> 'ContactAddress':
        source = source.copy()

        device_id = source.pop('deviceId')
        device_name = source.pop('deviceName')

        source['device'] = {'id': device_id, 'name': device_name}

        return super().from_dict(source, connection, to_snake_case)


@method_version_handler('11.3.0100')
def list_contacts(
    connection: 'Connection', to_dictionary: bool = False, limit: Optional[int] = None, **filters
) -> list['Contact'] | list[dict]:
    """Get all contacts as list of Contact objects or dictionaries.

    Optionally filter the contacts by specifying filters.

    Args:
        connection: MicroStrategy connection object
        to_dictionary: If True returns a list of contact dicts,
            otherwise returns a list of contact objects
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters:
            ['id', 'name', 'description', 'enabled']
    """

    return Contact._list_contacts(
        connection=connection, to_dictionary=to_dictionary, limit=limit, **filters
    )


@class_version_handler('11.3.0100')
class Contact(EntityBase, DeleteMixin):
    """Object representation of Microstrategy Contact object

    Attributes:
        name: contact's name
        id: contact's id
        description: contact's description
        enabled: specifies if a contact is enabled
        linked_user: user linked to contact, instance of User
        contact_addresses: list of contact's addresses,
            instances of ContactAddress
        memberships: list of Contact Groups that the contact belongs to
        connection: instance of Connection class, represents connection
                    to MicroStrategy Intelligence Server
    """
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'linked_user': User.from_dict,
        'contact_addresses': [ContactAddress.from_dict],
        'memberships': [ContactGroup.from_dict],
    }
    _API_GETTERS = {
        (
            'id',
            'name',
            'description',
            'enabled',
            'linked_user',
            'memberships',
            'contact_addresses'
        ): contacts.get_contact
    }
    _API_DELETE = staticmethod(contacts.delete_contact)
    _API_PATCH = {
        ('name', 'description', 'enabled', 'linked_user', 'contact_addresses',
         'memberships'): (contacts.update_contact, 'put')
    }
    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'enabled': bool,
        'linked_user': dict,
        'contact_addresses': list,
        'memberships': list
    }

    def __init__(
        self, connection: 'Connection', id: Optional[str] = None, name: Optional[str] = None
    ):
        """Initialize Contact object by passing id or name.
        When `id` is provided, name is omitted.

        Args:
            connection: MicroStrategy connection object
            id: ID of Contact
            name: name of Contact
        """

        if id is None and name is None:
            raise ValueError("Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            result = Contact._list_contacts(connection=connection, name=name, to_dictionary=True)

            if result:
                object_data = result[0]
                object_data['connection'] = connection
                self._init_variables(**object_data)
            else:
                raise ValueError(f"There is no Contact named: '{name}'")
        else:
            super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self.description = kwargs.get('description')
        self.enabled = kwargs.get('enabled')

        linked_user = kwargs.get("linked_user")
        self.linked_user = User.from_dict(linked_user, self.connection) if linked_user else None

        addresses = kwargs.get('contact_addresses')
        self.contact_addresses = [
            ContactAddress.from_dict(address, self.connection) for address in addresses
        ] if addresses else None

        memberships = kwargs.get('memberships')
        self.memberships = [
            ContactGroup.from_dict(m, self.connection) for m in memberships
        ] if memberships else None

    @classmethod
    @method_version_handler('11.3.0200')
    def create(
        cls,
        connection: 'Connection',
        name: str,
        linked_user: 'User | str',
        contact_addresses: Iterable['ContactAddress | dict'],
        description: Optional[str] = None,
        enabled: bool = True
    ) -> 'Contact':
        """Create a new contact.

        Args:
            connection: MicroStrategy connection object
                returned by `connection.Connection()`
            name: contact name
            linked_user: user linked to contact
            contact_addresses: list of contact addresses
            description: description of contact
            enabled: specifies if contact should be enabled
        Returns:
            Contact object
        """
        body = {
            'name': name,
            'description': description,
            'enabled': enabled,
            'linkedUser': {
                'id': get_objects_id(linked_user, User)
            },
            'contactAddresses': [
                address.to_dict() if isinstance(address, ContactAddress) else address
                for address in contact_addresses
            ],
        }
        body = delete_none_values(body, recursion=True)
        response = contacts.create_contact(connection, body).json()

        if config.verbose:
            logger.info(
                f"Successfully created contact named: '{name}' with ID: '{response['id']}'"
            )

        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        linked_user: Optional['User | str'] = None,
        contact_addresses: Optional[Iterable['ContactAddress | dict']] = None
    ):
        """Update properties of a contact

        Args:
           name: name of a contact
           description: description of a contact
           enabled: specifies if a contact is enabled
           linked_user: an object of class User linked to the contact
           contact_addresses: list of contact addresses
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
    def _list_contacts(
        cls,
        connection: 'Connection',
        to_dictionary: bool = False,
        limit: Optional[int] = None,
        **filters
    ) -> list['Contact'] | list[dict]:
        """Get all contacts as list of Contact objects or dictionaries.

        Optionally filter the contacts by specifying filters.

        Args:
            connection: MicroStrategy connection object
            to_dictionary: If True returns a list of contact dicts,
               otherwise returns a list of contact objects
           limit: limit the number of elements returned. If `None` (default),
               all objects are returned.
           **filters: Available filter parameters:
               ['id', 'name', 'description', 'enabled']
        """

        objects = fetch_objects(
            connection=connection,
            api=contacts.get_contacts,
            limit=limit,
            filters=filters,
            dict_unpack_value='contacts'
        )

        if to_dictionary:
            return objects

        return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    def add_to_contact_group(self, contact_group: 'ContactGroup | str'):
        """Add to ContactGroup

        Args:
            contact_group: contact group to which add this contact
        """
        if isinstance(contact_group, str):
            contact_group = ContactGroup(self.connection, id=contact_group)

        contact_group.add_members([self])
        self.fetch()

    def remove_from_contact_group(self, contact_group: 'ContactGroup | str'):
        """Remove from ContactGroup

        Args:
            contact_group: contact group from which to remove this contact
        """
        if isinstance(contact_group, str):
            contact_group = ContactGroup(self.connection, id=contact_group)

        contact_group.remove_members([self])
        self.fetch()
