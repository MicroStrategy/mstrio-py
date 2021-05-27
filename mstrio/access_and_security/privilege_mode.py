from enum import Enum


class PrivilegeMode(str, Enum):
    ALL = 'ALL'
    INHERITED = 'INHERITED'
    GRANTED = 'GRANTED'
