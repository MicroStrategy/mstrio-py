from mstrio.connection import get_connection
from mstrio.distribution_services import (
    Device, DeviceType, EmailDeviceProperties, EmailFormat, EmailSmartHostSettings, list_devices,
    Transmitter
)

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# create email device properties object
# which is used when creating device
edp = EmailDeviceProperties(
    format=EmailFormat.UU_ENCODED,
    smart_host_settings=EmailSmartHostSettings(server='mstr.com', port=22),
)

# get list of devices
print(list_devices(conn))

# get transmitter by id
transmitter = Transmitter(conn, id="transmitter_id")
print(transmitter)

# create a device with device type as `email` (when type is `email` then
# it is mandatory to provide `email_device_properties`)
new_device = Device.create(
    connection=conn,
    name='Tmp Device Name',
    device_type=DeviceType.EMAIL,
    description="Description of a new device",
    transmitter=transmitter,
    device_properties=edp,
)

# get device by id
d = Device(conn, id=new_device.id)
print(d)

# print name, description and properties of email type device
print(d.name)
print(d.description)
print(d.device_properties.to_dict())

# alter email transmitter and its properties
edp.smart_host_settings.server = "microstrategy.com"
edp.smart_host_settings.port = 21
d.alter(
    name='Tmp Device Name (altered)',
    description='Device was altered',
    device_properties=edp,
)

# print name, description and properties of email device after altering
print(d.name)
print(d.description)
print(d.device_properties.to_dict())

# delete a device
d.delete(force=True)
