from collections import defaultdict
from enum import auto
import logging
from typing import List, Optional, TYPE_CHECKING, Union

from mstrio import config
from mstrio.api import devices, objects
from mstrio.distribution_services.device.device_properties import (
    AndroidDeviceProperties,
    EmailDeviceProperties,
    FileDeviceProperties,
    FtpDeviceProperties,
    IOSDeviceProperties,
    PrinterDeviceProperties
)
from mstrio.distribution_services.transmitter import Transmitter
from mstrio.types import ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, Entity
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import (
    delete_none_values,
    Dictable,
    fetch_objects,
    get_args_from_func,
    get_default_args_from_func,
    get_objects_id
)
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection

logger = logging.getLogger(__name__)


class DeviceType(AutoName):
    EMAIL = auto()
    FTP = auto()
    FILE = auto()
    PRINTER = auto()
    IPHONE = auto()
    IPAD = auto()
    ANDROID = auto()
    ALL = auto()
    UNSUPPORTED = auto()


def list_devices(
    connection: "Connection", to_dictionary: bool = False, limit: int = None, **filters
) -> Union[List["Device"], List[dict]]:
    """Get list of Device objects or dicts. Optionally filter the
    devices by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            Device objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Examples:
        >>> list_devices(connection, name='device_name')
    """
    return Device._list_devices(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


@class_version_handler('11.3.0100')
class Device(Entity, DeleteMixin):
    """Devices are Distribution Services components that specify the format
     and transmission process of subscribed reports and documents.
     They are instances of transmitters that contain specific settings
     specific to a user’s environments.

    Attributes:
        name: name of the device
        id: identifier of the Device
        description: description of the device
        device_type: type of the Device, DeviceType Enum
        transmitter: information of Transmitter attached
        device_properties: properties of the device,
            different for every device type
        ancestors: List of ancestor folders
        type: Object type. Enum
        subtype: Object subtype
        ext_type: Object extended type.
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        owner: User object that is the owner
        version: Object version ID
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.SUBSCRIPTION_DEVICE
    _DEVICE_TYPE_MAP = {
        "android": AndroidDeviceProperties,
        "email": EmailDeviceProperties,
        "file": FileDeviceProperties,
        "ftp": FtpDeviceProperties,
        "ipad": IOSDeviceProperties,
        "iphone": IOSDeviceProperties,
        "printer": PrinterDeviceProperties
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'device_type': DeviceType,
        'owner': User.from_dict,
        'transmitter': Transmitter.from_dict,
        'device_properties': lambda source,
        connection,
        device_type_map=_DEVICE_TYPE_MAP: device_type_map[next(iter(source))].
        from_dict(source[next(iter(source))], connection)
    }
    _API_GETTERS = {
        (
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl'
        ): objects.get_object_info,
        ('id', 'name', 'description', 'device_type', 'transmitter',
         'device_properties'): devices.get_device
    }
    _API_DELETE = staticmethod(devices.delete_device)
    _API_PATCH: dict = {
        ("name", "description", "device_properties"): (devices.update_device, "put")
    }
    _PATCH_PATH_TYPES = {"name": str, "description": str, "device_properties": dict}

    def __init__(self, connection: "Connection", name: str = None, id: str = None):
        """Initialize Device object."""

        if id is None and name is None:
            raise ValueError("Please specify either 'id' or 'name' parameter in the constructor.")

        if id is None:
            objects_info = Device._list_devices(
                connection=connection,
                name=name,
                to_dictionary=True,
            )
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no Device: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        device_type = kwargs.get("device_type")
        self._device_type = DeviceType(device_type) if device_type else None
        self._transmitter = Transmitter.from_dict(kwargs.get("transmitter"), self.connection
                                                  ) if kwargs.get("transmitter") else None
        device_properties = kwargs.get("device_properties")
        self.device_properties = self._DEVICE_TYPE_MAP[device_type].from_dict(
            device_properties[device_type],
            self.connection,
        ) if device_properties and device_type else None

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        device_type: Union[DeviceType, str],
        transmitter: Union[Transmitter, str],
        device_properties: Union[dict, Dictable],
        description: str = None
    ) -> "Device":
        """Create a new device.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name: device object name
            device_type: type of the device
            transmitter: Transmitter object
            description: device object description
            device_properties: properties of the device
        Returns:
            Device object.
        """
        device_type = get_enum_val(device_type, DeviceType)
        device_properties = device_properties.to_dict(
        ) if isinstance(device_properties, Dictable) else device_properties
        transmitter_id = get_objects_id(transmitter, Transmitter)
        body = {
            "name": name,
            "description": description,
            "deviceType": device_type,
            "transmitter": {
                "id": transmitter_id,
            },
            "deviceProperties": {
                device_type: device_properties
            }
        }
        body = delete_none_values(body, recursion=True)
        response = devices.create_device(connection, body).json()
        if config.verbose:
            logger.info(
                f"Successfully created device named: '{name}' with ID: '{response['id']}'."
            )
        return cls.from_dict(source=response, connection=connection)

    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        device_properties: Optional[Union[Dictable, dict]] = None
    ):
        """Alter the device object properties.

        Args:
            name: device object name
            description: device object description
            device_properties: properties of the device, specific for each
                device type
        """
        device_properties = self.device_properties if not device_properties else device_properties
        device_properties = device_properties.to_dict(
        ) if isinstance(device_properties, Dictable) else device_properties
        func = self.alter
        args = get_args_from_func(func)
        defaults = get_default_args_from_func(func)
        defaults_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = defaultdict(dict)
        for property_key in defaults_dict.keys():
            if property_key == 'device_properties':
                properties[property_key][self.device_type.value] = device_properties
            elif local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    def update_properties(self) -> None:
        """Save compatible local changes of the object attributes to the
        I-Server.

        Raises:
            requests.HTTPError: if I-Server raises exception
        """
        changes = {k: v[1] for k, v in self._altered_properties.items()}
        if "device_properties" in changes:
            device_properties = changes["device_properties"]
            del changes["device_properties"]
        else:
            device_properties = self.device_properties
        changes["device_properties"] = {}
        changes["device_properties"][self.device_type.value] = device_properties.to_dict(
        ) if not isinstance(device_properties, dict) else device_properties
        self._alter_properties(**changes)
        self._altered_properties.clear()

    @classmethod
    def _list_devices(
        cls, connection: "Connection", to_dictionary: bool = False, limit: int = None, **filters
    ) -> Union[List["Device"], List[dict]]:
        objects = fetch_objects(
            connection=connection,
            api=devices.get_devices,
            dict_unpack_value="devices",
            limit=limit,
            filters=filters,
        )
        if to_dictionary:
            return objects
        return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @property
    def device_type(self):
        return self._device_type

    @property
    def transmitter(self):
        return self._transmitter
