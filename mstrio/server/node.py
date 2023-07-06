from dataclasses import dataclass

from mstrio.utils.helper import Dictable


@dataclass
class Node(Dictable):
    name: str | None = None
    address: str | None = None
    service_control: bool | None = None

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
    tags: dict | None = None
    output: str | None = None


@dataclass
class ServiceWithNode(Dictable):
    node: str
    address: str
    id: str
    service_control: bool
    port: int
    status: str
    service_address: str
    tags: dict | None = None
    output: str | None = None
