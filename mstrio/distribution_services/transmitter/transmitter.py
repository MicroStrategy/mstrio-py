from collections import defaultdict
from enum import auto
import logging
from typing import List, Optional, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api import objects, transmitters
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable, fetch_objects

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


class RecipientFieldType(AutoName):
    TO = auto()
    CC = auto()
    BCC = auto()


class TransmitterDeliveryType(AutoName):
    EMAIL = auto()
    FTP = auto()
    FILE = auto()
    PRINT = auto()
    IPHONE = auto()
    IPAD = auto()
    ANDROID = auto()
    UNSUPPORTED = auto()


class EmailTransmitterProperties(Dictable):
    """Representation of email transmitter properties object. Those properties
    are specific for Email Transmitters.

    Attributes:
        sender_display_name: name used in the email headers to indicate message
            sender
        sender_email_address: address used in the email headers to indicate
            message sender
        reply_to_display_name: name used in the email headers to indicate
            destination for replies
        reply_to_email_address: address used in the email headers to indicate
            destination for replies
        recipient_field_type: default field in which recipient address appear
            (eg. to/cc/bcc). Default value is `RecipientFieldType.TO`.
        save_message_to_file: specifies whether to save message output to file,
            default value is `False`
        send_message_via_smtp: specifies whether to send messages to recipients
            via SMTP, default value is `False`
        save_file_path: the folder path to save the email output,
            default is `None`
        notify_on_success: specifies whether to request notification on success,
            default is `False`
        notify_on_failure: specifies whether to request notification on failure,
            default is `False`
        notification_email_address: email address for notification, default is
            `None`
    """
    _DELETE_NONE_VALUES_RECURSION = True
    _FROM_DICT_MAP = {'recipient_field_type': RecipientFieldType}

    def __init__(self, sender_display_name: str, sender_email_address: str,
                 reply_to_display_name: str, reply_to_email_address: str,
                 recipient_field_type: RecipientFieldType = RecipientFieldType.TO,
                 save_message_to_file: bool = False, send_message_to_file: bool = False,
                 send_message_via_smtp: bool = False, save_file_path: Optional[str] = None,
                 notify_on_success: bool = False, notify_on_failure: bool = False,
                 notification_email_address: Optional[str] = None):
        self.sender_display_name = sender_display_name
        self.sender_email_address = sender_email_address
        self.reply_to_display_name = reply_to_display_name
        self.reply_to_email_address = reply_to_email_address
        self.recipient_field_type = recipient_field_type
        self.save_message_to_file = save_message_to_file
        self.send_message_to_file = send_message_to_file
        self.send_message_via_smtp = send_message_via_smtp
        self.save_file_path = save_file_path
        self.notify_on_success = notify_on_success
        self.notify_on_failure = notify_on_failure
        self.notification_email_address = notification_email_address


def list_transmitters(connection: "Connection", to_dictionary: bool = False,
                      limit: Optional[int] = None,
                      **filters) -> Union[List["Transmitter"], List[dict]]:
    """Get all transmitters as list of Transmitter objects or
    dictionaries.

    Optionally filter the transmitters by specifying filters.

    Args:
        connection(object): MicroStrategy connection object
        to_dictionary: If True returns a list of transmitter dicts,
            otherwise returns a list of transmitter objects
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'delivery_type']
    """
    return Transmitter._list_transmitters(connection=connection, to_dictionary=to_dictionary,
                                          limit=limit, **filters)


class Transmitter(Entity, DeleteMixin):
    """Object representation of MicroStrategy Transmitter object

    Attributes:
        name: transmitter's name
        id: transmitter's id
        description: transmitter's description
        delivery_type: type of the transmitter
        email_transmitter_properties: properties specific to email transmitters
            (available only when `delivery_type` equals
            `TransmitterDeliveryType.EMAIL`)
    """
    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.SUBSCRIPTION_TRANSMITTER
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP, 'owner': User.from_dict,
        'delivery_type': TransmitterDeliveryType,
        'email_transmitter_properties': EmailTransmitterProperties.from_dict
    }
    _API_GETTERS = {
        ('abbreviation', 'type', 'subtype', 'ext_type', 'date_created', 'date_modified', 'version',
         'owner', 'icon_path', 'view_media', 'ancestors', 'certified_info',
         'acl'): objects.get_object_info,
        ('id', 'name', 'description', 'delivery_type',
         'email_transmitter_properties'): transmitters.get_transmitter
    }
    _API_DELETE = staticmethod(transmitters.delete_transmitter)
    _API_PATCH: dict = {
        ("name", "description", "email_transmitter_properties"):
            (transmitters.update_transmitter, "put")
    }
    _PATCH_PATH_TYPES = {"name": str, "description": str, "email_transmitter_properties": dict}

    def __init__(self, connection: "Connection", id: Optional[str] = None,
                 name: Optional[str] = None):
        """Initialize Transmitter object.

        Note:
            In case both `id` and `name` are provided, then `id` is used when
            fetching.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str, optional): Identifier of a pre-existing transmitter
            name (str, optional): Name of the pre-existing transmitter

        Raises:
            `ValueError` when neither `id` nor `name` are specified.
        """

        if id is None and name is None:
            raise ValueError("Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            objects_info = Transmitter._list_transmitters(
                connection=connection,
                name=name,
                to_dictionary=True,
            )
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no Transmitter: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._delivery_type = TransmitterDeliveryType(
            kwargs["delivery_type"]) if kwargs.get("delivery_type") else None
        self.email_transmitter_properties = EmailTransmitterProperties.from_dict(
            kwargs["email_transmitter_properties"]) if kwargs.get(
                "email_transmitter_properties") else None

    @classmethod
    def create(
        cls, connection: "Connection", name: str,
        delivery_type: Union[str, TransmitterDeliveryType], description: Optional[str] = None,
        email_transmitter_properties: Optional[Union[dict, EmailTransmitterProperties]] = None
    ) -> "Transmitter":
        """Create transmitter.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            delivery_type: type of the transmitter
            name (str): transmitter's name
            description (str): transmitter's description
            email_transmitter_properties (dict or object): properties specific
                to email transmitter. In transmitter with type `email` those
                properties must be provided. Otherwise they cannot be provided.

        Returns:
            `Transmitter` object
        """
        delivery_type = get_enum_val(delivery_type, TransmitterDeliveryType)
        email_transmitter_properties = email_transmitter_properties.to_dict() if isinstance(
            email_transmitter_properties,
            EmailTransmitterProperties) else email_transmitter_properties
        body = {
            'name': name,
            'description': description,
            'deliveryType': delivery_type,
            'emailTransmitterProperties': email_transmitter_properties
        }

        res = transmitters.create_transmitter(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created transmitter named: '{res.get('name')}' "
                f"with ID: '{res.get('id')}'"
            )
        return cls.from_dict(res, connection)

    def alter(self, name: Optional[str] = None, description: Optional[str] = None,
              email_transmitter_properties: Optional[Union[dict,
                                                           EmailTransmitterProperties]] = None):
        """Alter transmitter properties.

        Args:
            name (str): transmitter's name
            description (str): transmitter's description
            email_transmitter_properties (dict or object): properties specific
                to email transmitter. Only in transmitter with type `email`
                altering those properties is possible
        """
        email_transmitter_properties = email_transmitter_properties.to_dict() if isinstance(
            email_transmitter_properties,
            EmailTransmitterProperties) else email_transmitter_properties
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        defaults_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = defaultdict(dict)
        for property_key in defaults_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_transmitters(cls, connection: "Connection", to_dictionary: bool = False,
                           limit: Optional[int] = None,
                           **filters) -> Union[List["Transmitter"], List[dict]]:
        """Helper method for listing transmitters."""
        objects = fetch_objects(
            connection=connection,
            api=transmitters.get_transmitters,
            limit=limit,
            filters=filters,
            dict_unpack_value="transmitters",
        )

        if to_dictionary:
            return objects
        return [Transmitter.from_dict(source=obj, connection=connection) for obj in objects]

    @property
    def delivery_type(self):
        return self._delivery_type
