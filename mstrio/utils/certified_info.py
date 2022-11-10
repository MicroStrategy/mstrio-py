from typing import Optional

from mstrio.connection import Connection
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import auto_match_args_entity
from mstrio.utils.helper import Dictable


class CertifiedInfo(Dictable):
    """Certification status, time of certification and information
    about the certifier (currently only for document and report).

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        certified: Specifies whether the object is trusted,
            as determined by the standards set by the certifier
        date_certified: time when the object was certified,
            "yyyy-MM-dd HH:mm:ss" in UTC
        certifier: information about the entity certifying
            the object, User object
    """

    def __init__(
        self,
        connection: Connection,
        certified: bool,
        date_certified: Optional[str] = None,
        certifier: Optional[dict] = None
    ):
        self._connection = connection
        self._certified = certified
        self._date_certified = date_certified
        self._certifier = User.from_dict(certifier, self._connection) if certifier else None

    def __str__(self):
        if not self.certified:
            return 'Object is not certified.'
        return f"Object certified on {self.date_certified} by {self._certifier}"

    def __repr__(self):
        param_value_dict = auto_match_args_entity(
            self.__init__, self, exclude=['self'], include_defaults=False
        )
        params_list = []
        for param, value in param_value_dict.items():
            if param == "connection" and isinstance(value, Connection):
                params_list.append("connection")
            else:
                params_list.append(f"{param}={repr(value)}")
        formatted_params = ", ".join(params_list)
        return f"{self.__class__.__name__}({formatted_params})"

    @property
    def connection(self) -> Connection:
        return self._connection

    @property
    def certified(self) -> Optional[bool]:
        return self._certified

    @property
    def date_certified(self) -> Optional[str]:
        return self._date_certified

    @property
    def certifier(self) -> Optional[User]:
        return self._certifier
