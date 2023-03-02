from dataclasses import asdict, dataclass
from enum import auto, Enum
from typing import Optional, Type, TYPE_CHECKING

from stringcase import camelcase, capitalcase, snakecase

from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, snake_to_camel, delete_none_values

if TYPE_CHECKING:
    from mstrio.connection import Connection


class DynamicDateTimeType(AutoName):
    """Enumeration constant indicating type of dynamic date time object"""
    DATE = auto()
    TIME = auto()
    DATE_TIME = auto()


class DateMode(AutoName):
    """Enumeration constant indicating mode of date"""
    DYNAMIC = auto()
    STATIC = auto()


class HourMode(AutoName):
    """Enumeration constant indicating mode of hour"""
    DYNAMIC = auto()
    STATIC = auto()


class MinuteAndSecondMode(AutoName):
    """Enumeration constant indicating mode of minute and second"""
    DYNAMIC = auto()
    STATIC = auto()


class DayOfWeek(Enum):
    """Enumeration used to indicate day of week"""
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


class VersatileDate(Dictable):
    """Base class for classes representing dynamic or static date objects"""

    _MODE = None

    @staticmethod
    def dispatch(source, connection: Optional['Connection'] = None) -> Type['VersatileDate']:
        """Returns an appropriate VersatileDate type object from the
            provided source

        Args:
            source: object that specifies the VersatileDate object that
                will be returned
            connection (optional): MicroStrategy connection object returned
            by `connection.Connection()`"""
        mode = DateMode(source.get('mode'))
        if mode == DateMode.DYNAMIC:
            cls = DynamicVersatileDate
        elif mode == DateMode.STATIC:
            cls = StaticVersatileDate

        return cls.from_dict(source, connection)


class DateAdjustment(Dictable):
    """Base class for date adjustment objects"""

    pass


@dataclass(frozen=True)
class AdjustmentNone(DateAdjustment):
    """Indicate that there is no further adjustments"""

    pass


@dataclass
class AdjustmentWeeklyByDayOfWeek(DateAdjustment):
    """Adjustment at the week level by day of week

    Attributes:
        day_of_week: day of week, value of DayOfWeek enum
    """

    _FROM_DICT_MAP = {'day_of_week': DayOfWeek}
    day_of_week: DayOfWeek


@dataclass
class AdjustmentMonthlyByDay(DateAdjustment):
    """Adjustment at the month level by day

    Attributes:
        day: day of month (1 - 31)
    """

    day: int


@dataclass
class AdjustmentMonthlyByDayOfWeek(DateAdjustment):
    """Adjustment at the month level by day of week

    Attributes:
        week_ordinal: number indicating 1st, 2nd, 3rd, etc.
        day_of_week: day of week, value of DayOfWeek enum
    """

    _FROM_DICT_MAP = {'day_of_week': DayOfWeek}
    week_ordinal: int
    day_of_week: DayOfWeek


@dataclass
class AdjustmentMonthlyByReverseCount(DateAdjustment):
    """Adjustment at the month level by reverse count

    Attributes:
        days: number of days to reverse count
        months: number of months to reverse count
    """

    days: int
    months: int


@dataclass
class AdjustmentQuarterlyByDay(DateAdjustment):
    """Adjustment at the quarter level by day

    Attributes:
        day: day in the quarter
    """

    day: int


@dataclass
class AdjustmentQuarterlyByDayOfWeek(DateAdjustment):
    """Adjustment at the quarter level by day of week

    Attributes:
        month_ordinal: number indicating 1st, 2nd, or 3rd month in the quarter
        week_ordinal: number indicating 1st, 2nd, 3rd, etc.
        day_of_week: day of week, value of DayOfWeek enum
    """

    _FROM_DICT_MAP = {'day_of_week': DayOfWeek}
    month_ordinal: int
    week_ordinal: int
    day_of_week: DayOfWeek


@dataclass
class AdjustmentQuarterlyByReverseCount(DateAdjustment):
    """Adjustment at the quarter level by reverse count

    Attributes:
        days: number of days to reverse count
    """

    days: int


@dataclass
class AdjustmentYearlyByDate(DateAdjustment):
    """Adjustment at the year level by date

    Attributes:
        month: Month of the year (1 - 12)
        day: Day of month (1 - 31)
    """

    month: int
    day: int


@dataclass
class AdjustmentYearlyByDayOfWeek(DateAdjustment):
    """Adjustment at the year level by day of week

    Attributes:
        month: Month of the year (1 - 12)
        week_ordinal: Number indicating 1st, 2nd, 3rd, etc.
        day_of_week: day of week, value of DayOfWeek enum
    """

    _FROM_DICT_MAP = {'day_of_week': DayOfWeek}
    month: int
    week_ordinal: int
    day_of_week: DayOfWeek


@dataclass
class DynamicVersatileDate(VersatileDate):
    """Object that represents a dynamic date.
    Its various settings define a function that will resolve to a date using
    the current date as the input.

    Attributes:
        day_offset: The day offset
        month_offset: The month offset
        exclude_weekends: Whether weekend days should be excluded during
            calculation, default: False
        adjustment: adjustment of a date, instance of one of classes inheriting
            from DateAdjustment class
    """

    _MODE = DateMode.DYNAMIC
    _ALLOW_NONE_ATTRIBUTES = ['adjustment_none']
    day_offset: int
    month_offset: int
    adjustment: DateAdjustment = AdjustmentNone()
    exclude_weekends: Optional[bool] = None

    def to_dict(self, camel_case: bool = True) -> dict:
        result = asdict(self)
        result['mode'] = self._MODE.value

        # every type of adjustment has its own unique attribute name
        # and only one can be present in json
        # so generate it based on class name
        attr_name = snakecase(self.adjustment.__class__.__name__)
        result[attr_name] = result.pop('adjustment')

        result = delete_none_values(
            result, recursion=False, whitelist_attributes=self._ALLOW_NONE_ATTRIBUTES
        )
        return snake_to_camel(result) if camel_case else result

    @classmethod
    def from_dict(
        cls, source: dict, connection: Optional['Connection'] = None, to_snake_case=True
    ) -> 'DynamicVersatileDate':
        try:
            key, value = next(
                (key, value) for key, value in source.items() if key.startswith('adjustment'))
        except StopIteration:
            raise AttributeError("Missing field for adjustment of a date in source data.")

        cls_name = capitalcase(camelcase(key))
        cls_obj = globals()[cls_name]
        adjustment = cls_obj(**value)

        result = super().from_dict(source, connection, to_snake_case)
        result.adjustment = adjustment

        return result


@dataclass
class StaticVersatileDate(VersatileDate):
    """Object that represents a static date

    Attributes:
        value: ISO 8601 string of the date component
    """

    _MODE = DateMode.STATIC
    value: str

    def to_dict(self, camel_case: bool = True) -> dict:
        result = asdict(self)
        result['mode'] = self._MODE.value

        return snake_to_camel(result) if camel_case else result


@dataclass
class VersatileTime(Dictable):
    """Object that represents either a dynamic time or a static time

    Attributes:
        hour_mode: The hour component (0-23). Used when the hour is static.
        hour_offset: The offset from the current hour. Used when the hour
            is dynamic.
        minute_and_second_mode: The minute component (0-59). Used when
            the minute is static.
        minute_offset: The offset from the current minute. Used when
            the minute is dynamic.
        second: The second component (0-59). Used when the second is static.
        second_offset: The offset from the current second. Used when the second
            is dynamic.
    """

    _FROM_DICT_MAP = {
        'hour_mode': HourMode,
        'minute_and_second_mode': MinuteAndSecondMode,
    }
    hour_mode: HourMode
    minute_and_second_mode: MinuteAndSecondMode
    hour: Optional[int] = None
    hour_offset: Optional[int] = None
    minute: Optional[int] = None
    minute_offset: Optional[int] = None
    second: Optional[int] = None
    second_offset: Optional[int] = None


@dataclass
class DynamicDateTimeStructure(Dictable):
    """Object that represents a date/time. It can be date-only, or time-only,
    or date-time. The date part and the time part can be dynamic or static
    independently. Typically, this object is used when at least one of the two
    parts is dynamic. Although it's capable of describing a static date/time,
    the much simpler Variant is preferable in that case.

    Attributes:
        type: represents what part is being used, either date, time or date/time
        date: Object that represents either a dynamic date or a static date
        time: Object that represents either a dynamic time or a static time
    """

    _FROM_DICT_MAP = {
        'type': DynamicDateTimeType,
        'date': VersatileDate.dispatch,
        'time': VersatileTime,
    }
    type: DynamicDateTimeType
    date: Optional[VersatileDate] = None
    time: Optional[VersatileTime] = None
