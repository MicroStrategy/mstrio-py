from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from enum import auto
from logging import getLogger
from typing import TYPE_CHECKING, Callable
from uuid import uuid4
from xml.etree import ElementTree as XMLETree

from mstrio import config
from mstrio.api import administration
from mstrio.utils.entity import auto_match_args_entity
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable, get_response_json
from mstrio.utils.time_helper import DatetimeFormats
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.users_and_groups.user import User


logger = getLogger(__name__)


class LockType(AutoName):
    """Enum representing the type of lock applied to a target
    (project or configuration).

    `TEMPORAL_INDIVIDUAL`: A temporary lock that restricts all other sessions
        except the current user's session from editing the project or
        configuration. It does not affect objects. This lock disappears when the
        user's session expires.
    `TEMPORAL_CONSTITUENT`: A temporary lock that restricts all other sessions
        except the current user's session from editing the project or
        configuration and all related objects. This lock disappears when the
        user's session expires.
    `PERMANENT_INDIVIDUAL`: A permanent lock that prevents all users from
        editing the project or configuration. It does not affect objects.
        This lock does not expire and must be removed before the project or
        configuration can be edited again.
    `PERMANENT_CONSTITUENT`: A permanent lock that prevents all users from
        editing the project or configuration and all related objects. This lock
        does not expire and must be removed before the affected scope can be
        edited again.
    `NOT_LOCKED`: Represents the state where the target is not locked
        and can be edited by users.
    """

    TEMPORAL_INDIVIDUAL = auto()
    TEMPORAL_CONSTITUENT = auto()
    PERMANENT_INDIVIDUAL = auto()
    PERMANENT_CONSTITUENT = auto()
    NOT_LOCKED = auto()


@dataclass
class LockStatus(Dictable):
    """Object representation of lock status (configuration, project).

    Attributes:
        lock_type: Lock type
        lock_time: Lock time
        comment: Lock comment
        machine_name: Machine name
        owner: User object
    """

    @staticmethod
    def _parse_owner(source, connection):
        """Parses owner from the API response."""
        from mstrio.users_and_groups import User

        return User.from_dict(source, connection)

    _FROM_DICT_MAP = {
        "lock_type": LockType,
        "lock_time": DatetimeFormats.FULLDATETIME,
        "owner": _parse_owner,
    }

    lock_type: LockType
    lock_time: datetime | None = None
    comment: str | None = None
    machine_name: str | None = None
    owner: "User | None" = None


class BaseLock(metaclass=ABCMeta):
    connection: "Connection"
    _API_GET_LOCK: Callable
    _API_UPDATE_LOCK: Callable
    _API_DELETE_LOCK: Callable
    _TARGET_STR: str = ""
    _status: LockStatus | None = None

    def __init__(self, connection: "Connection"):
        self.connection = connection

    @property
    def status(self) -> LockStatus:
        """Lock status of the target."""
        if self._status is None:
            self.fetch()
        return self._status

    def _get(self) -> dict:
        """Retrieve the lock status of the target from the API.
        This does not update properties.

        Returns:
            dict: Dictionary containing lock status information.
        """
        param_value_dict = auto_match_args_entity(self._API_GET_LOCK, self)
        response = self._API_GET_LOCK(**param_value_dict)
        json = (
            response
            if isinstance(response, (dict, list))
            else get_response_json(response)
        )
        return json

    def fetch(self):
        """Fetch the lock status of the target."""
        json = self._get()
        self._status = LockStatus.from_dict(json, self.connection)

    def lock(self, lock_type: str | LockType, lock_id: str | None = None) -> None:
        """Lock the target.

        Args:
            lock_type (str, LockType): Lock type.
            lock_id (str, optional): Lock ID. Will be generated if not provided.
        """
        self.fetch()

        if self.status.lock_type != LockType.NOT_LOCKED:
            msg = (
                f"Target ({self._TARGET_STR}) is already locked "
                f"with the lock type `{self.status.lock_type}`. "
                f"Please unlock it before applying a new lock."
            )
            raise ValueError(msg)

        lock_type = get_enum_val(lock_type, LockType)
        # Generate a lock ID if not provided. Empty ID works but is undocumented
        if lock_id is None:
            lock_id = uuid4().hex
        body = {"lockType": lock_type, "lockId": lock_id}

        param_value_dict = auto_match_args_entity(self._API_UPDATE_LOCK, self)
        param_value_dict["body"] = body
        self._API_UPDATE_LOCK(**param_value_dict)

        if config.verbose:
            logger.info(f"Target ({self._TARGET_STR}) locked.")

        self.fetch()

    def unlock(
        self,
        lock_type: str | LockType | None = None,
        lock_id: str | None = None,
        force: bool = False,
    ) -> None:
        """Unlock the target.

        Args:
            lock_type (str, LockType, optional): Lock type. Optional only if
                `force` is set to True.
            lock_id (str, optional): Lock ID.
            force (bool, optional): If True, will force-unlock the target.
        """
        self.fetch()

        if self.status.lock_type == LockType.NOT_LOCKED:
            msg = f"Target ({self._TARGET_STR}) is not locked."
            raise ValueError(msg)

        if not force and not (lock_id and lock_type):
            msg = (
                "`lock_id` and `lock_type` must be provided to unlock the target "
                "when `force` is False."
            )
            raise ValueError(msg)

        if force and not lock_type:
            lock_type = self.status.lock_type

        lock_type = get_enum_val(lock_type, LockType)

        param_value_dict = auto_match_args_entity(self._API_DELETE_LOCK, self)
        param_value_dict["lock_type"] = lock_type
        param_value_dict["lock_id"] = lock_id
        param_value_dict["force"] = force
        self._API_DELETE_LOCK(**param_value_dict)

        if config.verbose:
            logger.info(f"Target ({self._TARGET_STR}) unlocked.")

        self.fetch()

    @property
    def lock_id(self) -> str | None:
        """Lock ID of the target."""
        if not (comment := self.status.comment):
            return None
        try:
            tree = XMLETree.fromstring(comment)
        except XMLETree.ParseError:
            return None
        if (lock_id_element := tree.find(".//LOCKID")) is None:
            return None
        return lock_id_element.text


@class_version_handler("11.3.0600")
class ConfigurationLock(BaseLock):
    _API_GET_LOCK = staticmethod(administration.get_configuration_lock)
    _API_UPDATE_LOCK = staticmethod(administration.update_configuration_lock)
    _API_DELETE_LOCK = staticmethod(administration.delete_configuration_lock)
    _TARGET_STR = "Configuration"
