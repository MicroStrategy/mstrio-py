from enum import auto

from mstrio.utils.enum_helper import AutoName


class RefreshPolicy(AutoName):
    ADD = auto()
    DELETE = auto()
    UPDATE = auto()
    UPSERT = auto()
    REPLACE = auto()
