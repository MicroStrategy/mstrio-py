"""This is the demo script to show how to manage devices.
This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.distribution_services import (
    BackupPrinterProperties, ConnectionParameters, Device, DeviceType, EmailDeviceProperties,
    EmailFormat, EmailSmartHostSettings, FileDeviceProperties, FileLocation, FileProperties,
    FileSystem, IOSDeviceProperties, list_devices, PrinterDeviceProperties, PrinterLocation,
    PrinterProperties, PrinterPdfSettings, Transmitter, UnixWindowsSharity)
from mstrio.connection import get_connection

PROJECT_NAME = '<Project_name>'  # Project to connect to
SMART_HOST_SERVER = '<example.com>'  # server name for smart host
SMART_HOST_PORT = 22  # server port for smart host
FEEDBACK_SERVICE_SERVER = '<Service_name>'  # server name for ios feedback server
FEEDBACK_SERVICE_PORT = 1212  # server port for ios feedback server
FILE_DEVICE_PATH = 'path/to/file'  # path for file device
PRINTER_LOCATION = '<Printer_location>'  # printer location field for printer device properties
TRANSMITTER_ID = '<Transmitter_id>'  # id for Transmitter object
DEVICE_ID = '<Device_id>'  # id for Device object
DEVICE_NAME = '<Name_of_device>'
DEVICE_DESCRIPTION = '<Description_of_device>'

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# create email device properties object
# which is used when creating device
edp = EmailDeviceProperties(
    format=EmailFormat.UU_ENCODED,
    smart_host_settings=EmailSmartHostSettings(server=SMART_HOST_SERVER, port=SMART_HOST_PORT),
)
# see distribution_services/device/device_properties.py for EmailFormat values

# create ios device properties object
# which is used when creating iphone or ipad device
idp = IOSDeviceProperties(
    app_id='com.microstrategy.dossier.iphone',
    server='api.push.apple.com',
    port=443,
    feedback_service_server=FEEDBACK_SERVICE_SERVER,
    feedback_service_port=FEEDBACK_SERVICE_PORT,
)

# create file device properties object
# which is used when creating file device
file_location = FileLocation(file_path=FILE_DEVICE_PATH)
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
    printer_location=PrinterLocation(location=PRINTER_LOCATION),
    printer_properties=printer_properties,
    connection_parameters=ConnectionParameters(retries_count=6),
    backup_printer_properties=BackupPrinterProperties(print_on_backup=True),
)
# get transmitters by id
transmitter = Transmitter(conn, id=TRANSMITTER_ID)

# create a device with device type as `email` (when type is `email` then
# it is mandatory to provide `email_device_properties`)
new_email_device = Device.create(
    connection=conn,
    name=DEVICE_NAME,
    # the DeviceType values can be found in distribution_services/device/device.py
    device_type=DeviceType.EMAIL,
    description=DEVICE_DESCRIPTION,
    transmitter=transmitter,
    device_properties=edp,
)
# create a device with device type as `iphone` (when type is `iphone` then
# it is mandatory to provide `device_properties`). Device type
# can be also passed as a string and `device_properties` can be
# passed as a dictionary
new_iphone_device = Device.create(
    connection=conn,
    name=DEVICE_NAME,
    # the DeviceType values can be found in distribution_services/device/device.py
    device_type=DeviceType.IPHONE,
    description=DEVICE_DESCRIPTION,
    transmitter=transmitter,
    device_properties=idp,
)

# create a device with device type as `ipad`
new_ipad_device = Device.create(
    connection=conn,
    name=DEVICE_NAME,
    # the DeviceType values can be found in distribution_services/device/device.py
    device_type=DeviceType.IPAD,
    description=DEVICE_DESCRIPTION,
    transmitter=transmitter,
    device_properties=idp,
)

# create a device with device type as `file`
new_file_device = Device.create(
    connection=conn,
    name=DEVICE_NAME,
    # the DeviceType values can be found in distribution_services/device/device.py
    device_type=DeviceType.FILE,
    description=DEVICE_DESCRIPTION,
    transmitter=transmitter,
    device_properties=fp,
)

# create a device with device type as `printer`
new_printer_device = Device.create(
    connection=conn,
    name=DEVICE_NAME,
    # the DeviceType values can be found in distribution_services/device/device.py
    device_type=DeviceType.PRINTER,
    description=DEVICE_DESCRIPTION,
    transmitter=transmitter,
    device_properties=pdp,
)

# get list of devices
print(list_devices(conn))

# get device by ID. Device can be also found by its name.
device = Device(conn, id=DEVICE_ID)
device_by_name = Device(conn, name=DEVICE_NAME)

# alter email type device and its properties
edp.smart_host_settings.server = 'microstrategy.com'
edp.smart_host_settings.port = 21
new_email_device.alter(
    name=DEVICE_NAME,
    description=DEVICE_DESCRIPTION,
    device_properties=edp,
)

# list device properties
device.list_properties()

# Delete device. When argument `force` is set to `False` (default value),
# then deletion must be confirmed by selecting appropriate prompt value.
new_email_device.delete(force=True)
new_iphone_device.delete(force=True)
