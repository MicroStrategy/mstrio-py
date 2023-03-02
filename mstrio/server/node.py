from dataclasses import dataclass
from typing import Optional

from mstrio.utils.helper import Dictable


@dataclass
class Node(Dictable):

    name: Optional[str] = None
    address: Optional[str] = None
    service_control: Optional[bool] = None

    @classmethod
    def from_dict(cls, source: dict):
        if not source.get('name'):
            source['name'] = source['node']
        return super().from_dict(source)


@dataclass
class Service(Dictable):

    id: str
    service: str
    port: int
    status: str
    tags: Optional[dict] = None
    output: Optional[str] = None


@dataclass
class ServiceWithNode(Dictable):

    node: str
    address: str
    id: str
    service_control: bool
    port: int
    status: str
    service_address: str
    tags: Optional[dict] = None
    output: Optional[str] = None
