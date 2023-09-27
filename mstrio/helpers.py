from enum import Enum, IntFlag

from mstrio.utils.dict_filter import filter_list_of_dicts


class NotSupportedError(Exception):
    pass


class IServerError(IOError):
    def __init__(self, message, http_code):
        super().__init__(message)
        self.http_code = http_code


class MstrException(Exception):
    """Base class for exceptions returned by the MicroStrategy REST API.

    Attributes:
        code: Error code
        message: Error message
        ticket_id: MSTR Ticket ID
    """

    def __init__(self, err_data: dict):
        self.code = err_data.get("code")
        self.message = err_data.get("message")
        self.ticket_id = err_data.get("ticketId")
        self.iserver_code = err_data.get("iServerCode")
        self.full_message = (
            f"{self.code}: {self.message} (Ticket ID: {self.ticket_id}, "
            f"iServerCode: {self.iserver_code})"
        )
        super().__init__(self.full_message)


class MstrTimeoutError(MstrException):
    pass


class VersionException(Exception):
    pass


class IServerException(Exception):
    pass


class PromptedContentError(Exception):
    pass


class Success(Exception):
    """This error holds details about the requested operation.

    Attributes:
        succeeded: list of succeeded operations dict elements
    """

    def __init__(self, data: list[dict]):
        assert isinstance(data, list)

        self.succeeded = data
        self.full_message = (
            f"Operation successful:\n{len(self.succeeded)} succeeded requests"
        )
        super().__init__(self.full_message)

    def __bool__(self):
        return True


class PartialSuccess(Exception):
    """This error holds details about the requested operation.

    Attributes:
        succeeded: list of succeeded operations dict elements
        failed: list of failed operations dict elements
    """

    def __init__(self, data: list[dict]):
        assert isinstance(data, list)

        self.succeeded = filter_list_of_dicts(data, status=[200, 204])
        self.failed = filter_list_of_dicts(data, status=">=400")
        self.full_message = (
            f"Operation partially successful:\n{len(self.failed)} failed "
            f"requests\n{len(self.succeeded)} succeeded requests"
        )
        super().__init__(self.full_message)

    def __bool__(self):
        return False


class Rights(IntFlag):
    """ "Enumeration constants used to specify the access granted attribute of
    the DSS objects."""

    EXECUTE = 0b10000000
    USE = 0b01000000
    CONTROL = 0b00100000
    DELETE = 0b00010000
    WRITE = 0b00001000
    READ = 0b00000100
    USE_EXECUTE = 0b00000010  # This constant is deprecated
    BROWSE = 0b00000001
    INHERITABLE = 0b100000000000000000000000000000


class Permissions(Enum):
    """Enumeration constants used to specify combination of Rights values
    similar to workstation Security Access.

    This has to be string-based to discern between 'Denied All'
    and 'Full Control', which have the same mask.
    """

    DENIED_ALL = 'Denied All'
    DEFAULT_ALL = 'Default All'
    CONSUME = 'Consume'
    VIEW = 'View'
    MODIFY = 'Modify'
    FULL_CONTROL = 'Full Control'


class AggregatedRights(IntFlag):
    """Enumeration constants used to specify combination of Rights values."""

    NONE = 0b00000000
    CONSUME = 0b01000101
    VIEW = 0b11000101
    MODIFY = 0b11011101
    ALL = 0b11111111
