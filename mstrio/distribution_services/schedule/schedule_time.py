from enum import auto
from typing import List, Optional, Union

from mstrio.utils import helper
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable


class ScheduleEnums:
    """Object representations of recurrence information of a time-based schedule
    """

    class DaysOfWeek(AutoName):
        MONDAY = auto()
        TUESDAY = auto()
        WEDNESDAY = auto()
        THURSDAY = auto()
        FRIDAY = auto()
        SATURDAY = auto()
        SUNDAY = auto()
        NONE = None

    class WeekOffset(AutoName):
        FIRST = auto()
        SECOND = auto()
        THIRD = auto()
        FOURTH = auto()
        LAST = auto()
        NONE = None

    class RecurrencePattern(AutoName):
        DAILY = auto()
        WEEKLY = auto()
        MONTHLY = auto()
        YEARLY = auto()

    class ExecutionPattern(AutoName):
        ONCE = auto()
        REPEAT = auto()

    class DailyPattern(AutoName):
        DAY = auto()
        WEEKDAY = auto()
        NONE = None

    class MonthlyPattern(AutoName):
        DAY = auto()
        DAY_OF_WEEK = auto()
        WEEKDAY = auto()
        LAST_DAY = auto()
        DAYS_OF_MONTH = auto()
        NONE = None

    class WeekdayOffset(AutoName):
        FIRST = auto()
        LAST = auto()
        NONE = None

    class YearlyPattern(AutoName):
        DAY = auto()
        DAYOFWEEK = auto()
        NONE = None


class ScheduleTime(Dictable):
    """Object representation of details of time-based schedule"""

    class Execution(Dictable):
        """Object representation of the execution information of the schedule"""
        _DELETE_NONE_VALUES_RECURSION = True
        _FROM_DICT_MAP = {
            'execution_pattern': ScheduleEnums.ExecutionPattern,
        }

        def __init__(self, execution_pattern: Union[ScheduleEnums.ExecutionPattern,
                                                    str] = ScheduleEnums.ExecutionPattern.ONCE,
                     execution_time: Optional[str] = None, start_time: Optional[str] = None,
                     stop_time: Optional[str] = None, repeat_interval: Optional[int] = 1):
            """Set attributes representing execution information of the schedule

            Args:
                execution_pattern (ScheduleEnums.ExecutionPattern, optional):
                    The execution pattern of the schedule.
                    Possible values are ONCE or REPEAT.
                    Defaults to ScheduleEnums.ExecutionPattern.ONCE.
                execution_time (str, optional):
                    The execution time of the execution day, if
                    execution_pattern is once. Format should be HH:mm:ss.
                    Defaults to ''.
                start_time (str, optional):
                    The start time of the execution day, if execution_pattern
                    is repeat. Format should be HH:mm:ss. Defaults to ''.
                stop_time (str, optional):
                    The stop time of the execution day, if execution_pattern is
                    repeat. Format should be HH:mm:ss. Defaults to ''.
                repeat_interval (int, optional):
                    The repeat interval of minutes of the execution day, if
                    executionPattern is repeat. Defaults to 1.
            Raises:
                ValueError: when execution_repeat_interval = None if
                execution_pattern == REPEAT
            """
            if (execution_pattern == ScheduleEnums.ExecutionPattern.REPEAT
                    and repeat_interval is None):
                helper.exception_handler(
                    msg=('Value error: execution_repeat_interval '
                         'cannot be None, '
                         'for execution_pattern == ExecutionPattern.Repeat'),
                    exception_type=ValueError)
            if execution_pattern == ScheduleEnums.ExecutionPattern.REPEAT:
                self.start_time = start_time
                self.stop_time = stop_time
                self.repeat_interval = repeat_interval
            else:
                self.execution_time = execution_time
            self.execution_pattern = execution_pattern if isinstance(
                execution_pattern, ScheduleEnums.ExecutionPattern
            ) else ScheduleEnums.ExecutionPattern(execution_pattern)

    class Daily(Dictable):
        """Object representation of daily recurrence information of the schedule
        """
        _DELETE_NONE_VALUES_RECURSION = True
        _FROM_DICT_MAP = {'daily_pattern': ScheduleEnums.DailyPattern}

        def __init__(self, daily_pattern: Union[ScheduleEnums.DailyPattern,
                                                str] = ScheduleEnums.DailyPattern.DAY,
                     repeat_interval: int = 1):
            """Set attributes representing daily recurrence information of the
            schedule

            Args:
                daily_pattern (ScheduleEnums.DailyPattern, optional):
                    The daily recurrence pattern of the schedule.Possible values
                    are DAY, WEEKDAY.Defaults to ScheduleEnums.DailyPattern.DAY.
                repeat_interval (int, optional):
                    The repeat interval of days of daily schedule,
                    if daily_pattern is DAY. Defaults to 1.
            """
            self.daily_pattern = daily_pattern if isinstance(
                daily_pattern,
                ScheduleEnums.DailyPattern) else ScheduleEnums.DailyPattern(daily_pattern)
            if daily_pattern == ScheduleEnums.DailyPattern.DAY:
                self.repeat_interval = repeat_interval

    class Weekly(Dictable):
        """Object representation of weekly recurrence information of the
        schedule"""
        _DELETE_NONE_VALUES_RECURSION = True
        _FROM_DICT_MAP = {'days_of_week': [ScheduleEnums.DaysOfWeek]}

        def __init__(self, days_of_week: Optional[Union[List[ScheduleEnums.DaysOfWeek],
                                                        List[str]]] = None,
                     repeat_interval: int = 1):
            """Set attributes representing weekly recurrence information of the
            schedule.

            Args:
                days_of_week (List[ScheduleEnums.DaysOfWeek], optional):
                    The days of week of weekly schedule. Possible values are:
                    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY,
                    SUNDAY. Defaults to None.
                repeat_interval (int, optional):
                    The repeat interval of weeks of weekly schedule.
                    Defaults to 1.
            """
            if days_of_week is None:
                self.days_of_week = []
            else:
                days_of_week = [
                    ScheduleEnums.DaysOfWeek(item)
                    if not isinstance(item, ScheduleEnums.DaysOfWeek) else item
                    for item in days_of_week
                ]
                self.days_of_week = days_of_week

            self.repeat_interval = repeat_interval

    class Monthly(Dictable):
        """Object representation of monthly recurrence information of the
        schedule"""
        _DELETE_NONE_VALUES_RECURSION = True
        _FROM_DICT_MAP = {
            'monthly_pattern': ScheduleEnums.MonthlyPattern,
            'week_offset': ScheduleEnums.WeekOffset,
            'day_of_week': ScheduleEnums.DaysOfWeek,
            'weekday_offset': ScheduleEnums.WeekdayOffset
        }

        def __init__(self, monthly_pattern: Union[ScheduleEnums.MonthlyPattern, str],
                     repeat_interval: int, day: Optional[int] = None,
                     week_offset: Optional[Union[ScheduleEnums.WeekOffset, str]] = None,
                     day_of_week: Optional[Union[ScheduleEnums.DaysOfWeek, str]] = None,
                     weekday_offset: Optional[Union[ScheduleEnums.WeekdayOffset, str]] = None,
                     days_of_month: Optional[str] = None):
            """Set attributes representing monthly recurrence information of the
            schedule.

            Args:
                monthly_pattern (ScheduleEnums.MonthlyPattern):
                    The monthly recurrence pattern of the schedule. Possible
                    values are: DAY, DAY_OF_WEEK, WEEKDAY, LAST_DAY,
                    DAYS_OF_MONTH.
                repeat_interval (int):
                    The repeat interval of months of monthly schedule.
                day (Optional[int], optional):
                    The day in month of monthly schedule, if monthly_pattern is
                    DAY. Defaults to None.
                week_offset (Optional[ScheduleEnums.WeekOffset], optional):
                    The week offset in month of monthly schedule, if
                    monthly_pattern is DAY_OF_WEEK. Possible values are:
                    FIRST, SECOND, THIRD, FOURTH, LAST. Defaults to None.
                day_of_week (Optional[ScheduleEnums.DaysOfWeek], optional):
                    The day of week in month of monthly schedule, if
                    monthly_pattern is DAY_OF_WEEK. Possible values are:
                    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY,
                    SUNDAY. Defaults to None.
                weekday_offset (Optional[ScheduleEnums.WeekdayOffset], optional)
                    The weekday offset in month of monthly schedule,
                    if monthly_pattern is WEEKDAY. Possible values are: FIRST,
                    LAST. Defaults to None.
                days_of_month (Optional[str], optional):
                    The days of month of monthly schedule, if monthly_pattern
                    is DAYS_OF_MONTH. Must be provided as a list of one or more
                    stringified digits (from '1' to '31'). Defaults to None.
            """

            self.monthly_pattern = monthly_pattern if isinstance(
                monthly_pattern,
                ScheduleEnums.MonthlyPattern) else ScheduleEnums.MonthlyPattern(monthly_pattern)
            self.repeat_interval = repeat_interval

            if monthly_pattern == ScheduleEnums.MonthlyPattern.DAY:
                self.day = day
            elif monthly_pattern == ScheduleEnums.MonthlyPattern.DAY_OF_WEEK:
                self.week_offset = week_offset if isinstance(
                    week_offset,
                    ScheduleEnums.WeekOffset) else ScheduleEnums.WeekOffset(week_offset)
                self.day_of_week = day_of_week if isinstance(
                    day_of_week,
                    ScheduleEnums.DaysOfWeek) else ScheduleEnums.DaysOfWeek(day_of_week)
            elif monthly_pattern == ScheduleEnums.MonthlyPattern.WEEKDAY:
                self.weekday_offset = weekday_offset if isinstance(
                    weekday_offset,
                    ScheduleEnums.WeekdayOffset) else ScheduleEnums.WeekdayOffset(weekday_offset)
            elif monthly_pattern == ScheduleEnums.MonthlyPattern.DAYS_OF_MONTH:
                self.days_of_month = days_of_month

    class Yearly(Dictable):
        """Object representation of yearly recurrence information of the
        schedule"""
        _DELETE_NONE_VALUES_RECURSION = True
        _FROM_DICT_MAP = {
            'yearly_pattern': ScheduleEnums.YearlyPattern,
            'week_offset': ScheduleEnums.WeekOffset,
            'day_of_week': ScheduleEnums.DaysOfWeek
        }

        def __init__(self, yearly_pattern: Union[ScheduleEnums.YearlyPattern,
                                                 str] = ScheduleEnums.YearlyPattern.DAY,
                     month: int = 1, day: int = 1,
                     week_offset: Optional[Union[ScheduleEnums.WeekOffset, str]] = None,
                     day_of_week: Optional[Union[ScheduleEnums.DaysOfWeek, str]] = None):
            """Set attributes representing yearly recurrence information of the
            schedule

            Args:
                yearly_pattern (ScheduleEnums.YearlyPattern, optional):
                    The yearly recurrence pattern of the schedule. Possible
                    values are DAY, DAY_OF_WEEK.
                    Defaults to ScheduleEnums.YearlyPattern.DAY.
                month (int, optional):
                    The month in year of yearly schedule. Defaults to 1.
                day (int, optional):
                    The day in month of yearly schedule, if yearly_pattern
                    is DAY. Defaults to 1.
                week_offset (ScheduleEnums.WeekOffset, optional):
                    The week offset in year of yearly schedule, if
                    yearly_pattern is DAY_OF_WEEK. Possible values are FIRST,
                    SECOND, THIRD, FOURTH, LAST. Defaults to None.
                day_of_week (ScheduleEnums.DaysOfWeek, optional):
                    The day of week in year of yearly schedule,
                    if yearly_pattern is DAY_OF_WEEK. Possible values are:
                    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY,
                    SUNDAY. Defaults to None.
            """
            self.yearly_pattern = yearly_pattern if isinstance(
                yearly_pattern,
                ScheduleEnums.YearlyPattern) else ScheduleEnums.YearlyPattern(yearly_pattern)
            self.month = month
            if yearly_pattern == ScheduleEnums.YearlyPattern.DAY:
                self.day = day
            if yearly_pattern == ScheduleEnums.YearlyPattern.DAYOFWEEK:
                self.week_offset = week_offset if isinstance(
                    week_offset,
                    ScheduleEnums.WeekOffset) else ScheduleEnums.WeekOffset(week_offset)
                self.day_of_week = day_of_week if isinstance(
                    day_of_week,
                    ScheduleEnums.DaysOfWeek) else ScheduleEnums.DaysOfWeek(day_of_week)

    _DELETE_NONE_VALUES_RECURSION = True
    _FROM_DICT_MAP = {
        'recurrence_pattern': ScheduleEnums.RecurrencePattern,
        'days_of_week': ScheduleEnums.DaysOfWeek,
        'execution': Execution.from_dict,
        'daily': Daily.from_dict,
        'weekly': Weekly.from_dict,
        'monthly': Monthly.from_dict,
        'yearly': Yearly.from_dict
    }

    def __init__(self, recurrence_pattern: Optional[Union[ScheduleEnums.RecurrencePattern,
                                                          str]] = None,
                 execution: Optional[Execution] = None, daily: Optional[Daily] = None,
                 weekly: Optional[Weekly] = None, monthly: Optional[Monthly] = None,
                 yearly: Optional[Yearly] = None):
        """Set attributes representing details of the time-based schedule.

        Args:
            recurrence_pattern (ScheduleEnums.RecurrencePattern, optional):
                The recurrence pattern of the schedule. Possible values are
                DAILY, WEEKLY, MONTHLY, YEARLY. Defaults to None.
            execution (Execution, optional):
                Object representing the execution information of the schedule.
                Defaults to None.
            daily (Daily, optional):
                Object representing daily recurrence information of the
                schedule. Defaults to None.
            weekly (Weekly, optional):
                Object representing weekly recurrence information of the
                schedule. Defaults to None.
            monthly (Monthly, optional):
                Object representing monthly recurrence information of the
                schedule. Defaults to None.
            yearly (Yearly, optional):
                Object representing yearly recurrence information of the
                schedule. Defaults to None.
        """

        self.recurrence_pattern = recurrence_pattern if isinstance(
            recurrence_pattern, ScheduleEnums.RecurrencePattern
        ) else ScheduleEnums.RecurrencePattern(recurrence_pattern)
        self.execution = execution
        if daily:
            self.daily = daily
        elif weekly:
            self.weekly = weekly
        elif monthly:
            self.monthly = monthly
        elif yearly:
            self.yearly = yearly

    @classmethod
    def from_details(cls, recurrence_pattern: Union[ScheduleEnums.RecurrencePattern, str],
                     execution_pattern: Union[ScheduleEnums.ExecutionPattern,
                                              str], execution_time: Optional[str] = None,
                     start_time: Optional[str] = None, stop_time: Optional[str] = None,
                     execution_repeat_interval: Optional[int] = None,
                     daily_pattern: Optional[Union[ScheduleEnums.DailyPattern,
                                                   str]] = ScheduleEnums.DailyPattern.NONE,
                     repeat_interval: Optional[int] = None,
                     days_of_week: Optional[Union[List[ScheduleEnums.DaysOfWeek],
                                                  List[str]]] = None, day: Optional[int] = None,
                     month: Optional[int] = None,
                     week_offset: Optional[Union[ScheduleEnums.WeekOffset,
                                                 str]] = ScheduleEnums.WeekOffset.NONE,
                     day_of_week: Optional[Union[ScheduleEnums.DaysOfWeek,
                                                 str]] = ScheduleEnums.DaysOfWeek.NONE,
                     weekday_offset: Optional[str] = None,
                     days_of_month: Optional[List[str]] = None,
                     monthly_pattern: Optional[Union[ScheduleEnums.MonthlyPattern,
                                                     str]] = ScheduleEnums.MonthlyPattern.NONE,
                     yearly_pattern: Optional[Union[ScheduleEnums.YearlyPattern,
                                                    str]] = ScheduleEnums.YearlyPattern.NONE):
        """
        Uses provided properties to create object representation of details of a
        time-based schedule.

        This object is used as 'time' part of request body and is needed for
        creating and updating schedule.

        Args:
            recurrence_pattern (ScheduleEnums.RecurrencePattern, optional):
                The recurrence pattern of the schedule.
                Possible values are DAILY, WEEKLY, MONTHLY, YEARLY
                Defaults to None.
            execution_pattern (ScheduleEnums.ExecutionPattern, optional):
                The execution pattern of the schedule.
                Possible values are ONCE, REPEAT. Defaults to None.
            execution_time (str, optional):
                The execution time of the execution day, if execution_pattern
                is ONCE. Format should be HH:mm:ss. Defaults to ''.
            start_time (str, optional):
                The start time of the execution day, if execution_pattern
                is REPEAT. Format should be HH:mm:ss. Defaults to ''.
            stop_time (str, optional):
                The stop time of the execution day, if execution_pattern
                is REPEAT. Format should be HH:mm:ss.
                Defaults to ''.
            execution_repeat_interval (int, optional):
                The repeat interval of minutes of the execution day, if
                execution_pattern is REPEAT. Defaults to None.
            daily_pattern (ScheduleEnums.DailyPattern, optional):
                The daily recurrence pattern of the schedule.
                Possible values are DAY, WEEKDAY.
                Defaults to None.
            repeat_interval (int, optional):
                The repeat interval of days of daily schedule, if daily_pattern
                is DAY or, The repeat interval of weeks of weekly schedule or,
                The repeat interval of months of monthly schedule.
                Defaults to None.
            day (int, optional):
                The day in month of monthly schedule, if monthly_pattern is DAY
                or, The day in month of yearly schedule, if yearly_pattern is
                DAY. Defaults to None.
            month (int, optional):
                The month in year of yearly schedule.
                Defaults to None.
            week_offset (ScheduleEnums.WeekOffset, optional):
                The week offset in month of monthly schedule, if monthly_pattern
                is DAY_OF_WEEK or, The week offset in year of yearly schedule,
                if yearly_pattern is DAY_OF_WEEK. Possible values are FIRST,
                SECOND, THIRD, FOURTH, LAST. Defaults to None.
            day_of_week (ScheduleEnums.DaysOfWeek, optional):
                The days of week of weekly schedule or, The day of week in month
                of monthly schedule, if monthly_pattern is DAY_OF_WEEK or,
                The day of week in year of yearly schedule, if yearly_pattern is
                DAY_OF_WEEK. Possible values are: MONDAY, TUESDAY, WEDNESDAY,
                THURSDAY, FRIDAY, SATURDAY, SUNDAY. Defaults to None.
            weekday_offset (ScheduleEnums.WeekdayOffset, optional):
                The weekday offset in month of monthly schedule, if
                monthly_pattern is WEEKDAY. Possible values are: FIRST, LAST.
                Defaults to None.
            days_of_month (List[str], optional):
                The days of month of monthly schedule, if monthly_pattern is
                DAYS_OF_MONTH. Must be provided as a list of one or more
                stringified digits (from '1' to '31'). Defaults to None.
            monthly_pattern (ScheduleEnums.MonthlyPattern, optional):
                The monthly recurrence pattern of the schedule. Possible values
                are: DAY, DAY_OF_WEEK, WEEKDAY, LAST_DAY, DAYS_OF_MONTH.
                Defaults to None.
            yearly_pattern (ScheduleEnums.YearlyPattern, optional):
                The yearly recurrence pattern of the schedule. Possible values
                are DAY, DAY_OF_WEEK. Defaults to None.
        Returns:
            ScheduleTime: Object representation of details of time-based
            schedule.
        """

        if execution_pattern == ScheduleEnums.ExecutionPattern.ONCE:
            execution = cls.Execution.from_dict({
                'execution_pattern': execution_pattern,
                'execution_time': execution_time
            })
        elif execution_pattern == ScheduleEnums.ExecutionPattern.REPEAT:
            execution = cls.Execution.from_dict({
                'execution_pattern': execution_pattern,
                'start_time': start_time,
                'stop_time': stop_time,
                'repeat_interval': execution_repeat_interval
            })
        else:
            helper.exception_handler(msg='Error: Wrong value of execution_pattern',
                                     exception_type=ValueError)

        if recurrence_pattern == ScheduleEnums.RecurrencePattern.DAILY:
            daily = cls.Daily.from_dict({
                'daily_pattern': daily_pattern,
                'repeat_interval': repeat_interval
            })
            return cls(recurrence_pattern=recurrence_pattern, execution=execution, daily=daily)
        elif recurrence_pattern == ScheduleEnums.RecurrencePattern.WEEKLY:
            if days_of_week and type(days_of_week) is not list:
                helper.exception_handler(msg='Error: days_of_week must be provided as a list',
                                         exception_type=ValueError)
            weekly = cls.Weekly.from_dict({
                'repeat_interval': repeat_interval,
                'days_of_week': days_of_week
            })
            return cls(recurrence_pattern=recurrence_pattern, execution=execution, weekly=weekly)
        elif recurrence_pattern == ScheduleEnums.RecurrencePattern.MONTHLY:
            monthly = cls.Monthly.from_dict({
                "monthly_pattern": monthly_pattern,
                "repeatInterval": repeat_interval,
                "day": day,
                "week_offset": week_offset,
                "day_of_week": day_of_week,
                "WeekdayOffset": weekday_offset,
                "days_of_month": days_of_month
            })
            return cls(recurrence_pattern=recurrence_pattern, execution=execution, monthly=monthly)
        elif recurrence_pattern == ScheduleEnums.RecurrencePattern.YEARLY:
            yearly = cls.Yearly.from_dict({
                'yearly_pattern': yearly_pattern,
                'month': month,
                'day': day,
                'week_offset': week_offset,
                'day_of_week': day_of_week
            })
            return cls(recurrence_pattern=recurrence_pattern, execution=execution, yearly=yearly)
        else:
            helper.exception_handler(msg='Error: Wrong value of recurrence_pattern',
                                     exception_type=ValueError)

    def update_properties(
            self, recurrence_pattern: Optional[Union[ScheduleEnums.RecurrencePattern, str]] = None,
            execution_pattern: Optional[Union[ScheduleEnums.ExecutionPattern, str]] = None,
            execution_time: Optional[str] = None, start_time: Optional[str] = None,
            stop_time: Optional[str] = None, execution_repeat_interval: Optional[int] = None,
            daily_pattern: Optional[Union[ScheduleEnums.DailyPattern,
                                          str]] = None, repeat_interval: Optional[int] = None,
            days_of_week: Optional[Union[List[ScheduleEnums.DaysOfWeek],
                                         List[str]]] = None, day: Optional[int] = None,
            month: Optional[int] = None, week_offset: Optional[Union[ScheduleEnums.WeekOffset,
                                                                     str]] = None,
            day_of_week: Optional[Union[ScheduleEnums.DaysOfWeek, str]] = None,
            weekday_offset: Optional[Union[ScheduleEnums.WeekdayOffset,
                                           str]] = None, days_of_month: Optional[List[str]] = None,
            monthly_pattern: Optional[Union[ScheduleEnums.MonthlyPattern, str]] = None,
            yearly_pattern: Optional[Union[ScheduleEnums.YearlyPattern, str]] = None):
        """
        Updates ScheduleTime object according to provided parameters. If a
        provided parameter is not None then update it, else use its current
        value.

        Args:
            recurrence_pattern (ScheduleEnums.RecurrencePattern, optional):
                The recurrence pattern of the schedule. Possible values are
                DAILY, WEEKLY, MONTHLY, YEARLY. Defaults to None.
            execution_pattern (ScheduleEnums.ExecutionPattern, optional):
                The execution pattern of the schedule. Possible values are ONCE,
                REPEAT. Defaults to None.
            execution_time (str, optional):
                The execution time of the execution day, if execution_pattern is
                ONCE. Format should be HH:mm:ss. Defaults to ''.
            start_time (str, optional):
                The start time of the execution day, if execution_pattern is
                REPEAT. Format should be HH:mm:ss. Defaults to ''.
            stop_time (str, optional):
                The stop time of the execution day, if execution_pattern is
                REPEAT. Format should be HH:mm:ss. Defaults to ''.
            execution_repeat_interval (int, optional):
                The repeat interval of minutes of the execution day, if
                execution_pattern is REPEAT. Defaults to None.
            daily_pattern (ScheduleEnums.DailyPattern, optional):
                The daily recurrence pattern of the schedule. Possible values
                are DAY, WEEKDAY. Defaults to None.
            repeat_interval (int, optional):
                The repeat interval of days of daily schedule, if daily_pattern
                is DAY. Defaults to None.
            day (int, optional):
                The day in month of monthly schedule, if monthly_pattern is DAY
                or The day in month of yearly schedule, if yearly_pattern is
                DAY. Defaults to None.
            month (int, optional):
                The month in year of yearly schedule. Defaults to None.
            week_offset (ScheduleEnums.WeekOffset, optional):
                The week offset in month of monthly schedule, if monthly_pattern
                is DAY_OF_WEEK or, The week offset in year of yearly schedule,
                if yearly_pattern is DAY_OF_WEEK. Possible values are FIRST,
                SECOND, THIRD, FOURTH, LAST. Defaults to None.
            day_of_week (ScheduleEnums.DaysOfWeek, optional):
                The days of week of weekly schedule or, The day of week in month
                of monthly schedule, if monthly_pattern is DAY_OF_WEEK or,
                The day of week in year of yearly schedule, if yearly_pattern is
                DAY_OF_WEEK. Possible values are: MONDAY, TUESDAY, WEDNESDAY,
                THURSDAY, FRIDAY, SATURDAY, SUNDAY. Defaults to None.
            weekday_offset (ScheduleEnums.WeekdayOffset, optional):
                The weekday offset in month of monthly schedule, if
                monthly_pattern is WEEKDAY. Defaults to None.
            days_of_month (List[str], optional):
                The days of month of monthly schedule, if monthly_pattern is
                DAYS_OF_MONTH. Must be provided as a list of one or more
                stringified digits (from '1' to '31'). Defaults to None.
            monthly_pattern (ScheduleEnums.MonthlyPattern, optional):
                The monthly recurrence pattern of the schedule. Possible values
                are: DAY, DAY_OF_WEEK, WEEKDAY, LAST_DAY, DAYS_OF_MONTH.
                Defaults to None.
            yearly_pattern (ScheduleEnums.YearlyPattern, optional):
                The yearly recurrence pattern of the schedule. Possible values
                are DAY, DAY_OF_WEEK. Defaults to None.
        """
        # todo days of week vs day of week
        if execution_pattern:
            execution_pattern = execution_pattern if isinstance(
                execution_pattern, ScheduleEnums.ExecutionPattern
            ) else ScheduleEnums.ExecutionPattern(execution_pattern)
        self.execution.execution_pattern = execution_pattern or self.execution.execution_pattern
        if recurrence_pattern:
            recurrence_pattern = recurrence_pattern if isinstance(
                recurrence_pattern, ScheduleEnums.RecurrencePattern
            ) else ScheduleEnums.RecurrencePattern(recurrence_pattern)
        self.recurrence_pattern = recurrence_pattern or self.recurrence_pattern

        if self.execution.execution_pattern == ScheduleEnums.ExecutionPattern.ONCE:
            self.execution = self.Execution.from_dict({
                'execution_pattern': execution_pattern or self.execution.execution_pattern,
                'execution_time': execution_time or self.execution.execution_time
            })
        elif self.execution.execution_pattern == ScheduleEnums.ExecutionPattern.REPEAT:
            self.execution = self.Execution.from_dict({
                'execution_pattern': execution_pattern or self.execution.execution_pattern,
                'start_time': start_time or self.execution.start_time,
                'stop_time': stop_time or self.execution.stop_time,
                'repeat_interval': execution_repeat_interval or self.execution.repeat_interval
            })

        if self.recurrence_pattern == ScheduleEnums.RecurrencePattern.DAILY:
            if hasattr(self, 'daily') and self.daily:
                self.daily = self.Daily.from_dict({
                    'daily_pattern': daily_pattern or self.daily.daily_pattern,
                    'repeat_interval': (repeat_interval
                                        or getattr(self.daily, 'repeat_interval', None))
                })
            else:
                self.daily = self.Daily.from_dict({
                    'daily_pattern': daily_pattern,
                    'repeat_interval': repeat_interval
                })

        if self.recurrence_pattern == ScheduleEnums.RecurrencePattern.WEEKLY:
            if hasattr(self, 'weekly') and self.weekly:
                self.weekly = self.Weekly.from_dict({
                    'repeat_interval': repeat_interval or self.weekly.repeat_interval,
                    'days_of_week': days_of_week or self.weekly.days_of_week
                })
            else:
                self.weekly = self.Weekly.from_dict({
                    'repeat_interval': repeat_interval,
                    'days_of_week': days_of_week
                })

        if self.recurrence_pattern == ScheduleEnums.RecurrencePattern.MONTHLY:
            if hasattr(self, 'monthly') and self.monthly:
                self.monthly = self.Monthly.from_dict({
                    "monthly_pattern": monthly_pattern or self.monthly.monthly_pattern,
                    "repeat_interval": repeat_interval or self.monthly.repeat_interval,
                    "day": day or getattr(self.monthly, 'day', None),
                    "week_offset": week_offset or getattr(self.monthly, 'week_offset', None),
                    "day_of_week": day_of_week or getattr(self.monthly, 'day_of_week', None),
                    "weekday_offset": (weekday_offset
                                       or getattr(self.monthly, 'weekday_offset', None)),
                    "days_of_month": days_of_month or getattr(self.monthly, 'days_of_month', None)
                })
            else:
                self.monthly = self.Monthly.from_dict({
                    "monthly_pattern": monthly_pattern,
                    "repeat_interval": repeat_interval,
                    "day": day,
                    "week_offset": week_offset,
                    "day_of_week": day_of_week,
                    "weekday_offset": weekday_offset,
                    "days_of_month": days_of_month
                })

        if self.recurrence_pattern == ScheduleEnums.RecurrencePattern.YEARLY:
            if hasattr(self, 'yearly') and self.yearly:
                self.yearly = self.Yearly.from_dict({
                    'yearly_pattern': yearly_pattern or self.yearly.yearly_pattern,
                    'month': month or getattr(self.yearly, 'month', None),
                    'day': day or getattr(self.yearly, 'day', None),
                    'week_offset': week_offset or getattr(self.yearly, 'week_offset', None),
                    'day_of_week': day_of_week or getattr(self.yearly, 'day_of_week', None),
                })
            else:
                self.yearly = self.Yearly.from_dict({
                    'yearly_pattern': yearly_pattern,
                    'month': month,
                    'day': day,
                    'week_offset': week_offset,
                    'day_of_week': day_of_week
                })
