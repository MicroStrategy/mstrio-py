from typing import Optional

from mstrio.utils.helper import Dictable


class Node(Dictable):

    def __init__(self, name: str, address: Optional[str] = None,
                 service_control: Optional[bool] = None) -> None:
        self.name = name
        self.address = address
        self.service_control = service_control
