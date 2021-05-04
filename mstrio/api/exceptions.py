from typing import Dict


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
        self.full_message = (f"{self.code}: {self.message} (Ticket ID: {self.ticket_id}, "
                             f"iServerCode: {self.iserver_code})")
        super().__init__(self.full_message)


class MstrTimeoutError(MstrException):
    pass


class VersionException(Exception):
    pass


class IServerException(Exception):
    pass


class PromptedContentError(Exception):
    pass
