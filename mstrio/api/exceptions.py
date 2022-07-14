from typing import Dict, List

from mstrio.utils.dict_filter import filter_list_of_dicts


class MstrException(Exception):
    """Base class for exceptions returned by the MicroStrategy REST API.

    Attributes:
        code: Error code
        message: Error message
        ticket_id: MSTR Ticket ID
    """

    def __init__(self, err_data: Dict):
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

    def __init__(self, data: List[dict]):
        assert isinstance(data, list)

        self.succeeded = data
        self.full_message = (f"Operation successful:\n{len(self.succeeded)} succeeded requests")
        super().__init__(self.full_message)

    def __bool__(self):
        return True


class PartialSuccess(Exception):
    """This error holds details about the requested operation.

    Attributes:
        succeeded: list of succeeded operations dict elements
        failed: list of failed operations dict elements
    """

    def __init__(self, data: List[dict]):
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
