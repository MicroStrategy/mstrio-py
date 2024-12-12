from dataclasses import dataclass
from typing import TYPE_CHECKING

from mstrio.server.project import Project
from mstrio.utils.helper import Dictable

if TYPE_CHECKING:
    from mstrio.connection import Connection


@dataclass
class Node(Dictable):
    _FROM_DICT_MAP = {'projects': [Project.from_dict]}

    name: str | None = None
    address: str | None = None
    service_control: bool | None = None
    port: int | None = None
    status: str | None = None
    load: int | None = None
    projects: list[Project] | None = None
    default: bool | None = None

    @classmethod
    def from_dict(cls, source: dict, connection: 'Connection | None' = None):
        if not source.get('name'):
            source['name'] = source['node']
        if source.get('ipAddress'):
            source['address'] = source['ipAddress']
        return super().from_dict(source, connection=connection)


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
