from typing import Optional

from mstrio.connection import Connection
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.time_helper import DatetimeFormats, override_datetime_format


@override_datetime_format(DatetimeFormats.YMDHMS.value, DatetimeFormats.FULLDATETIME.value,
                          ('dateCreated', 'dateModified'))
@ErrorHandler(err_msg='Error creating Device.')
def create_device(connection: Connection, body: dict, error_msg: Optional[str] = None):
    """Create a new device.

    Args:
        connection: MicroStrategy REST API connection object
        body: Device creation info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    url = f"{connection.base_url}/api/v2/devices/"
    return connection.post(url=url, json=body)


@override_datetime_format(DatetimeFormats.YMDHMS.value, DatetimeFormats.FULLDATETIME.value,
                          ('dateCreated', 'dateModified'))
@ErrorHandler(err_msg='Error getting Device with ID {id}')
def get_device(connection: Connection, id: str, error_msg: Optional[str] = None):
    """Get device by a specific id.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the device
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/v2/devices/{id}"
    return connection.get(url=url)


@ErrorHandler(err_msg='Error deleting Device with ID {id}')
def delete_device(connection: Connection, id: str, error_msg: Optional[str] = None):
    """Delete a device.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the device
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 204.
    """
    url = f"{connection.base_url}/api/v2/devices/{id}"
    return connection.delete(url=url)


@override_datetime_format(DatetimeFormats.YMDHMS.value, DatetimeFormats.FULLDATETIME.value,
                          ('dateCreated', 'dateModified'))
@ErrorHandler(err_msg='Error updating Device with ID {id}')
def update_device(connection: Connection, id: str, body: dict, error_msg: Optional[str] = None):
    """Update a device.

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of the device
        body: Device update info.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/v2/devices/{id}"
    return connection.put(url=url, json=body)


@ErrorHandler(err_msg="Error getting Devices.")
@override_datetime_format(DatetimeFormats.YMDHMS.value, DatetimeFormats.FULLDATETIME.value,
                          ('dateCreated', 'dateModified'), 'devices')
def get_devices(connection: Connection, device_type: Optional[str] = None,
                fields: Optional[str] = None, error_msg: Optional[str] = None):
    """Get information for all devices.

    Args:
        connection: MicroStrategy REST API connection object
        fields(list, optional): Comma separated top-level field whitelist. This
            allows client to selectively retrieve part of the response model.
        device_type (str, optional): Device type, Supported values are: email,
            file, ftp, printer, ipad, iphone, android, all.
        error_msg (string, optional): Custom Error Message for Error Handling

    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    url = f"{connection.base_url}/api/v2/devices/"
    params = {'fields': fields, 'deviceType': device_type}
    return connection.get(url=url, params=params)
