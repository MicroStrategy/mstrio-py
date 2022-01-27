from enum import auto

from mstrio.utils.enum_helper import AutoUpperName


class PrivilegeMode(AutoUpperName):
    ALL = auto()
    INHERITED = auto()
    GRANTED = auto()
