"""This is the demo script to show how to manage devices.
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.distribution_services import (
    BackupPrinterProperties, ConnectionParameters, Device, DeviceType, EmailDeviceProperties,
    EmailFormat, EmailSmartHostSettings, FileDeviceProperties, FileLocation, FileProperties,
    FileSystem, IOSDeviceProperties, list_devices, PrinterDeviceProperties, PrinterLocation,
    PrinterProperties, PrinterPdfSettings, Transmitter, UnixWindowsSharity
)

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# create email device properties object
# which is used when creating device
edp = EmailDeviceProperties(
    format=EmailFormat.UU_ENCODED,
    smart_host_settings=EmailSmartHostSettings(server='mstr.com', port=22),
)

# create ios device properties object
# which is used when creating iphone or ipad device
idp = IOSDeviceProperties(
    app_id='com.microstrategy.dossier.iphone',
    server='api.push.apple.com',
    port=443,
    feedback_service_server='service_name',
    feedback_service_port=1212,
)

# create file device properties object
# which is used when creating file device
file_location = FileLocation(file_path='file_path')
file_system = FileSystem(create_folder=False)
fp = FileDeviceProperties(
    file_location=file_location,
    file_system=file_system,
    connection_parameters=ConnectionParameters(retries_count=6),
    file_properties=FileProperties(read_only=False),
    unix_windows_sharity=UnixWindowsSharity(sharity_enabled=False),
)

# create print device properties object
# which is used when creating print device
printer_properties = PrinterProperties(pdf_setting=PrinterPdfSettings(post_script_level=1))
pdp = PrinterDeviceProperties(
    printer_location=PrinterLocation(location='printer_location'),
    printer_properties=printer_properties,
    connection_parameters=ConnectionParameters(retries_count=6),
    backup_printer_properties=BackupPrinterProperties(print_on_backup=True),
)

# get transmitters by id
email_transmitter = Transmitter(conn, id="email_transmitter_id")
iphone_transmitter = Transmitter(conn, id="iphone_transmitter_id")
ipad_transmitter = Transmitter(conn, id="ipad_transmitter_id")
file_transmitter = Transmitter(conn, id="file_transmitter_id")
print_transmitter = Transmitter(conn, id="print_transmitter_id")


# create a device with device type as `email` (when type is `email` then
# it is mandatory to provide `email_device_properties`)
new_email_device = Device.create(
    connection=conn,
    name='Name of email device',
    device_type=DeviceType.EMAIL,
    description="Description of a new email device",
    transmitter=email_transmitter,
    device_properties=edp,
)
# create a device with device type as `iphone` (when type is `iphone` then
# it is mandatory to provide `device_properties`). Device type
# can be also passed as a string and `device_properties` can be
# passed as a dictionary
new_iphone_device = Device.create(
    connection=conn,
    name='Name of iphone device',
    device_type=DeviceType.IPHONE,
    description="Description of iphone device",
    transmitter=iphone_transmitter,
    device_properties=idp,
)

# create a device with device type as `ipad`
new_ipad_device = Device.create(
    connection=conn,
    name='Name of ipad device',
    device_type=DeviceType.IPAD,
    description="Description of ipad device",
    transmitter=ipad_transmitter,
    device_properties=idp,
)

# create a device with device type as `file`
new_file_device = Device.create(
    connection=conn,
    name='Name of file device',
    device_type=DeviceType.FILE,
    description="Description of file device",
    transmitter=file_transmitter,
    device_properties=fp,
)

# create a device with device type as `printer`
new_printer_device = Device.create(
    connection=conn,
    name='Name of printer device',
    device_type=DeviceType.PRINTER,
    description="Description of printer device",
    transmitter=print_transmitter,
    device_properties=pdp,
)

# get list of devices
print(list_devices(conn))

# get device by ID. Device can be also found by its name.
d = Device(conn, id='device_id')
d_by_name = Device(conn, name='Name of device')

# alter email type device and its properties
edp.smart_host_settings.server = "microstrategy.com"
edp.smart_host_settings.port = 21
new_email_device.alter(
    name='New name of device',
    description='New description of device',
    device_properties=edp,
)

# list device properties
d.list_properties()

# Delete device. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
new_email_device.delete(force=True)
new_iphone_device.delete(force=True)
