from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from mstrio.utils.helper import Dictable
from mstrio.utils.time_helper import DatetimeFormats


class SubscriptionState(Enum):
    """State of the subscription"""

    INVALID = 0
    SUCCESS = 1
    FAIL = 2
    CANCELED = 3
    TIMEOUT = 4
    SKIP = 5


class SubscriptionStage(Enum):
    """Stage of the subscription"""

    INVALID = 0
    EXECUTING = 1
    FINISHED = 2


@dataclass
class StatusError(Dictable):
    """Subscription status error

    Attributes:
        code (int): Error code.
        message (str): Error message.
    """

    code: int
    message: str


@dataclass
class StatusContent(Dictable):
    """Subscription status content

    Attributes:
        name (str): Content name
        node_name (str): Node name
        error (StatusError): Error
    """

    _FROM_DICT_MAP = {
        'error': lambda source, connection: (StatusError.from_dict(source, connection)),
    }

    name: str
    node_name: str | None = None
    error: StatusError | None = None


@dataclass
class StatusDestination(Dictable):
    """Subscription status destination

    Attributes:
        address (str): Address
        destination (str): Destination
        start (datetime): Start time
        end (datetime): End time
        node_name (str): Node name
        contents (list[StatusContent]): Subscription contents
        error (StatusError): Error
    """

    _FROM_DICT_MAP = {
        'start': DatetimeFormats.FULLDATETIME,
        'end': DatetimeFormats.FULLDATETIME,
        'contents': lambda source, connection: [
            StatusContent.from_dict(content, connection) for content in source
        ],
        'error': lambda source, connection: (StatusError.from_dict(source, connection)),
    }

    address: str
    destination: str
    start: datetime
    node_name: str
    end: datetime | None = None
    contents: list[StatusContent] | None = None
    error: StatusError | None = None


@dataclass
class StatusDetail(Dictable):
    """Subscription status detail

    Attributes:
        recipient (str): Recipient
        contents (list[StatusContent]): Subscription contents
        destinations (list[StatusDestination]): Destinations
        error (StatusError): Error
    """

    _FROM_DICT_MAP = {
        'contents': lambda source, connection: [
            StatusContent.from_dict(content, connection) for content in source
        ],
        'destinations': lambda source, connection: [
            StatusDestination.from_dict(content, connection) for content in source
        ],
        'error': lambda source, connection: (StatusError.from_dict(source, connection)),
    }

    recipient: str
    contents: list[StatusContent]
    destinations: list[StatusDestination]
    error: StatusError | None = None


@dataclass
class SubscriptionStatus(Dictable):
    """Subscription status

    Attributes:
        id (str): Subscription ID
        stage (SubscriptionStage): Stage of the subscription
        state (SubscriptionState): State of the subscription
        total (int): Total number of statuses
        estimate (int): Estimated time remaining in seconds
        start (datetime): Subscription start time
        end (datetime): Subscription end time
        contents (list[StatusContent]): Subscription contents
        statuses (list[StatusDetail]): Subscription detailed statuses
        expiration (str): Subscription expiration time
    """

    _FROM_DICT_MAP = {
        'contents': lambda source, connection: [
            StatusContent.from_dict(content, connection) for content in source
        ],
        'start': DatetimeFormats.FULLDATETIME,
        'end': DatetimeFormats.FULLDATETIME,
        'stage': SubscriptionStage,
        'state': SubscriptionState,
        'statuses': lambda source, connection: [
            StatusDetail.from_dict(content, connection) for content in source
        ],
    }

    id: str
    stage: SubscriptionStage
    state: SubscriptionState
    total: int
    estimate: int
    start: datetime
    contents: list[StatusContent]
    statuses: list[StatusDetail]
    end: datetime | None = None
    expiration: str | None = None
