from enum import auto

from mstrio.utils.enum_helper import AutoName


class DaysOfWeek(AutoName):
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()
    NONE = None
