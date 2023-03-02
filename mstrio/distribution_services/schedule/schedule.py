from datetime import datetime, timezone
from enum import auto
import logging
from typing import Optional

from mstrio import config
from mstrio.api import objects, schedules
from mstrio.connection import Connection
from mstrio.distribution_services.event import Event
from mstrio.distribution_services.schedule import ScheduleEnums, ScheduleTime
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import DeleteMixin, Entity, ObjectTypes
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.time_helper import DatetimeFormats, map_datetime_to_str, map_str_to_datetime
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler('11.3.0000')
def list_schedules(
    connection: Connection, to_dictionary: bool = False, limit: int = None, **filters
) -> list["Schedule"] | list[dict]:
    """List schedule objects or schedule dictionaries. Optionally filter list.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection()'
        to_dictionary(bool, optional): if True, return Schedules as
            list of dicts
        limit(int, optional): maximum number of schedules returned.
        **filters: Available filter parameters:['name':,
                                                'id',
                                                'description',
                                                'schedule_type',
                                                'start_date',
                                                'expired']
    Returns:
        list["Schedule"] | list[dict]: [description]
    """

    objects = helper.fetch_objects(
        connection=connection,
        api=schedules.list_schedules,
        limit=limit,
        filters=filters,
        dict_unpack_value='schedules'
    )

    if to_dictionary:
        return objects
    else:
        return [Schedule.from_dict(source=obj, connection=connection) for obj in objects]


class Schedule(Entity, DeleteMixin):
    """Class representation of MicroStrategy Schedule object.

    Attributes:
        connection: A MicroStrategy connection object
        name: Schedule name
        id: Schedule ID
        description: Schedule description
        schedule_type: Schedule type
        schedule_next_delivery: Schedule next delivery date
        time(ScheduleTime): Details of time-based schedule
        event(Event): Details of event-based schedule
    """

    class ScheduleType(AutoName):
        """Class representation of a type of a Microstrategy Schedule."""
        EVENT_BASED = auto()
        TIME_BASED = auto()
        NONE = None

    _OBJECT_TYPE = ObjectTypes.SCHEDULE_TRIGGER

    _API_GETTERS: dict = {
        (
            'id',
            'name',
            'description',
            'expired',
            'schedule_type',
            'schedule_next_delivery',
            'start_date',
            'stop_date',
            'time',
            'event'
        ): schedules.get_schedule,
        (
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl'
        ): objects.get_object_info
    }

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'schedule_type': ScheduleType,
        'time': ScheduleTime.from_dict,
        'event': Event.from_dict,
        'schedule_next_delivery': DatetimeFormats.YMDHMS,
        'start_date': DatetimeFormats.DATE,
        'stop_date': DatetimeFormats.DATE,
    }
    _API_PATCH: dict = {
        ('abbreviation'): (objects.update_object, 'partial_put'),
        ('name', 'description', 'schedule_type', 'start_date', 'stop_date', 'time',
         'event'): (schedules.update_schedule, 'put')
    }

    _PATCH_PATH_TYPES = {
        'name': str,
        'description': str,
        'abbreviation': str,
        'schedule_type': str,
        'start_date': str,
        'stop_date': str,
        'time': dict,
        'event': dict,
    }

    @method_version_handler('11.3.0000')
    def __init__(self, connection: Connection, id: str = None, name: str = None) -> None:
        """Initialize the Schedule object, populates it with I-Server data.
        Specify either `id` or `name`. When `id` is provided (not `None`),
        `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Schedule ID
            name: Schedule name
        Raises:
            AttributeError: when id is None and name is None.
            ValueError: when there is no schedule with a given name on the
            server.
        """

        if id is None and name is None:
            raise AttributeError(
                "Please specify either 'name' or 'id' parameter in the constructor."
            )
        if id is None:
            objects_info = list_schedules(connection=connection, name=name, to_dictionary=True)
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no schedule with the given name: '{name}'")
        else:
            super().__init__(connection, id, name=name)

    @method_version_handler('11.3.0000')
    def _init_variables(self, **kwargs):
        """
        Add Schedule attributes to _AVAILABLE_ATTRIBUTES map.
        Set attributes inherited from Entity object.
        Set attributes related to schedule details.

        Args:
            **kwargs: dict with information about schedule attributes.
        Returns:
            None
        """
        super()._init_variables(**kwargs)
        self.schedule_type = self.ScheduleType(kwargs.get('schedule_type'))
        self.time = ScheduleTime.from_dict(
            kwargs.get('time')
        ) if (self.schedule_type == self.ScheduleType.TIME_BASED and kwargs.get('time')) else None
        self.event = Event.from_dict(kwargs.get('event'), connection=self._connection) if (
            self.schedule_type == self.ScheduleType.EVENT_BASED and kwargs.get('event')
        ) else None
        self._expired = kwargs.get('expired')
        self._schedule_next_delivery = map_str_to_datetime(
            "schedule_next_delivery", kwargs.get("schedule_next_delivery"), self._FROM_DICT_MAP
        )
        self.start_date = map_str_to_datetime(
            "start_date", kwargs.get("start_date"), self._FROM_DICT_MAP
        )

    @method_version_handler('11.3.0000')
    def enable(self, stop_date: str | datetime) -> bool:
        """Enables schedule and sets stop date

        Args:
            stop_date: stop date provided either as a datetime or
            as a string in yyyy-MM-dd format
        Returns:
            Returns `True` if enabled properly, else `False`.
        """
        self._alter_properties(
            stop_date=map_str_to_datetime('stop_date', stop_date, self._FROM_DICT_MAP)
        )

        if config.verbose and not self.expired:
            logger.info(
                f'Schedule \'{self.name}\' with ID {self.id} has been enabled, '
                f'until {self.stop_date}.'
            )
            return True
        elif config.verbose:
            logger.info(f'Schedule \'{self.name}\' with ID {self.id} has NOT been enabled.')
            return False

    @method_version_handler('11.3.0000')
    def disable(self, stop_date: Optional[str | datetime] = None) -> bool:
        """ Disable the schedule. Optional `stop_date` sets the date when
            the schedule should be disabled.

        Args:
            stop_date: stop date provided either as a datetime or
            as a string in yyyy-MM-dd format
        Returns:
            Returns `True` if disabled properly. It does not mean that schedule
            is already expired, as it can take up to one day.
            If operation failed, return `False`.
        """
        stop_date = (
            datetime.now(timezone.utc) if stop_date is None else
            map_str_to_datetime('stop_date', stop_date, self._FROM_DICT_MAP)
        )
        self._alter_properties(stop_date=stop_date)

        if config.verbose and self.expired:
            logger.info(f'Schedule \'{self.name}\' with ID {self.id} has been disabled.')
            return True
        elif config.verbose and self.stop_date.date() == stop_date.date():
            logger.info(
                f"Schedule '{self.name}' with ID '{self.id}' has been set for disabling. "
                f"Depending on the schedule configuration (`event`, `time` and `stop_date`),"
                f" it will be disabled by day after '{self.stop_date.date()}'."
            )
            return True
        else:
            logger.info(f"Schedule '{self.name}' with ID '{self.id}' has NOT been disabled.")
            return False

    @method_version_handler('11.3.0000')
    def list_properties(self):
        """List all properties of the object."""
        attributes = {key: self.__dict__[key] for key in self.__dict__ if not key.startswith('_')}
        attributes = {
            **attributes,
            'expired': self._expired,
            'schedule_next_delivery': self._schedule_next_delivery,
            'id': self.id,
            'type': self.type,
            'subtype': self.subtype,
            'ext_type': self.ext_type,
            'date_created': self.date_created,
            'date_modified': self.date_modified,
            'version': self.version,
            'owner': self.owner,
            'icon_path': self.icon_path,
            'view_media': self.view_media,
            'ancestors': self.ancestors,
            'certified_info': self.certified_info,
            'acg': self.acg,
            'acl': self.acl,
        }

        return {
            key: attributes[key]
            for key in sorted(attributes, key=helper.sort_object_properties)
        }

    @classmethod
    @method_version_handler('11.3.0000')
    def create(
        cls,
        connection: Connection,
        name: str,
        schedule_type: ScheduleType | str,
        start_date: str | datetime,
        description: Optional[str] = None,
        stop_date: Optional[str | datetime] = None,
        event_id: Optional[str] = None,
        time: Optional[ScheduleTime] = None,
        recurrence_pattern: Optional[ScheduleEnums.RecurrencePattern | str] = None,
        execution_pattern: Optional[ScheduleEnums.ExecutionPattern | str] = None,
        execution_time: Optional[str] = None,
        start_time: Optional[str] = None,
        stop_time: Optional[str] = None,
        execution_repeat_interval: Optional[int] = None,
        daily_pattern: Optional[ScheduleEnums.DailyPattern | str] = None,
        repeat_interval: Optional[int] = None,
        days_of_week: Optional[list[ScheduleEnums.DaysOfWeek] | list[str]] = None,
        day: Optional[int] = None,
        month: Optional[int] = None,
        week_offset: Optional[ScheduleEnums.WeekOffset | str] = None,
        day_of_week: Optional[ScheduleEnums.DaysOfWeek | str] = None,
        weekday_off_set: Optional[str] = None,
        days_of_month: Optional[list[str]] = None,
        monthly_pattern: Optional[ScheduleEnums.MonthlyPattern | str] = None,
        yearly_pattern: Optional[ScheduleEnums.YearlyPattern | str] = None
    ):
        """Create a Schedule using provided parameters as data.

        Args:
            recurrence_pattern (ScheduleEnums.RecurrencePattern, optional):
                The recurrence pattern of the schedule. Possible values are
                DAILY, WEEKLY, MONTHLY, YEARLY. Defaults to None.
            execution_pattern (ScheduleEnums.ExecutionPattern, optional):
                The execution pattern of the schedule. Possible values are ONCE,
                REPEAT. Defaults to None.
            execution_time (str, optional):
                The execution time of the execution day, if execution_pattern
                is ONCE. Format should be HH:mm:ss. Defaults to None.
            start_time (str, optional):
                The start time of the execution day, if execution_pattern is
                REPEAT. Format should be HH:mm:ss. Defaults to None.
            stop_time (str, optional):
                The stop time of the execution day, if execution_pattern is
                REPEAT.Format should be HH:mm:ss. Defaults to None.
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
                or, The day in month of yearly schedule, if yearly_pattern is
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
                of monthly schedule, if monthly_pattern is DAY_OF_WEEK or, The
                day of week in year of yearly schedule, if yearly_pattern is
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
        Returns:
            Schedule object with provided parameters.
        """
        time_kwargs = {
            key: val
            for key,
            val in locals().items()
            if val is not None and key not in [
                'event_id',
                'connection',
                'description',
                'name',
                'schedule_type',
                'start_date',
                'stop_date',
                'time',
                'self',
                'cls'
            ]
        }
        # Event based or Time based logic
        if schedule_type == cls.ScheduleType.EVENT_BASED:
            execution_details = {'type': 'event', 'content': {'id': event_id}}
        elif schedule_type == cls.ScheduleType.TIME_BASED:
            if time is None:
                time = ScheduleTime.from_details(**time_kwargs)
            execution_details = {'type': 'time', 'content': time.to_dict()}

        # Datetime dates to string format conversion
        start_date = map_datetime_to_str(
            name='start_date', date=start_date, string_to_date_map=cls._FROM_DICT_MAP
        )
        stop_date = map_datetime_to_str(
            name='stop_date', date=stop_date, string_to_date_map=cls._FROM_DICT_MAP
        )

        # Create body and send request
        body = {
            'name': name,
            'description': description,
            'schedule_type': get_enum_val(schedule_type, cls.ScheduleType),
            'start_date': start_date,
            'stop_date': stop_date,
            execution_details['type']: execution_details['content']
        }
        body = helper.delete_none_values(body, recursion=True)
        body = helper.snake_to_camel(body)
        # Response is already unpacked in wrapper
        response = schedules.create_schedule(connection, body)
        response = response.json()
        if config.verbose:
            logger.info(f"Created schedule '{name}' with ID: {response['id']}")
        return Schedule.from_dict(source=response, connection=connection)

    @method_version_handler('11.3.0000')
    def alter(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str | datetime] = None,
        stop_date: Optional[str | datetime] = None,
        event: Optional[Event] = None,
        event_id: Optional[str] = None,
        time: Optional[ScheduleTime] = None,
        recurrence_pattern: Optional[ScheduleEnums.RecurrencePattern] = None,
        execution_pattern: Optional[ScheduleEnums.ExecutionPattern] = None,
        execution_time: Optional[str] = None,
        start_time: Optional[str] = None,
        stop_time: Optional[str] = None,
        execution_repeat_interval: Optional[int] = None,
        daily_pattern: Optional[ScheduleEnums.DailyPattern] = None,
        repeat_interval: Optional[int] = None,
        days_of_week: Optional[list[ScheduleEnums.DaysOfWeek]] = None,
        day: Optional[int] = None,
        month: Optional[int] = None,
        week_offset: Optional[ScheduleEnums.WeekOffset] = None,
        day_of_week: Optional[ScheduleEnums.DaysOfWeek] = None,
        weekday_offset: Optional[str] = None,
        days_of_month: Optional[list[str]] = None,
        monthly_pattern: Optional[ScheduleEnums.MonthlyPattern] = None,
        yearly_pattern: Optional[ScheduleEnums.YearlyPattern] = None
    ) -> None:
        """Alter Schedule properties.

        Args:
            recurrence_pattern (ScheduleEnums.RecurrencePattern, optional):
                The recurrence pattern of the schedule. Possible values are
                DAILY, WEEKLY, MONTHLY, YEARLY. Defaults to None.
            execution_pattern (ScheduleEnums.ExecutionPattern, optional):
                The execution pattern of the schedule. Possible values are ONCE,
                REPEAT. Defaults to None.
            execution_time (str, optional):
                The execution time of the execution day, if execution_pattern is
                ONCE. Format should be HH:mm:ss. Defaults to None.
            start_time (str, optional):
                The start time of the execution day, if execution_pattern is
                REPEAT. Format should be HH:mm:ss. Defaults to None.
            stop_time (str, optional):
                The stop time of the execution day, if execution_pattern is
                REPEAT. Format should be HH:mm:ss. Defaults to None.
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
                or, The day in month of yearly schedule, if yearly_pattern is
                DAY. Defaults to None.
            month (int, optional):
                The month in year of yearly schedule. Defaults to None.
            week_offset (ScheduleEnums.WeekOffset, optional):
                The week offset in month of monthly schedule, if monthly_pattern
                is DAY_OF_WEEK or, The week offset in year of yearly schedule,
                if yearly_pattern is DAY_OF_WEEK. Possible values are FIRST,
                SECOND, THIRD, FOURTH, LAST. Defaults to None.
            day_of_week (ScheduleEnums.DaysOfWeek, optional):
                The days of week of weekly schedule or,
                The day of week in month of monthly schedule, if monthly_pattern
                is DAY_OF_WEEK or, The day of week in year of yearly schedule,
                if yearly_pattern is DAY_OF_WEEK. Possible values are: MONDAY,
                TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY.
                Defaults to None.
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
        Returns:
            None
        """

        properties = {}

        # Event based or Time based logic
        if time is not None:
            properties['schedule_type'] = self.ScheduleType.TIME_BASED
            properties['time'] = time
        elif event is not None:
            properties['schedule_type'] = self.ScheduleType.EVENT_BASED
            properties['event'] = event
        elif event_id is not None:
            properties['schedule_type'] = self.ScheduleType.EVENT_BASED
            properties['event'] = Event(connection=self._connection, id=event_id)
        elif self.schedule_type == self.ScheduleType.TIME_BASED:
            properties['schedule_type'] = self.ScheduleType.TIME_BASED
            self.time.update_properties(
                recurrence_pattern,
                execution_pattern,
                execution_time,
                start_time,
                stop_time,
                execution_repeat_interval,
                daily_pattern,
                repeat_interval,
                days_of_week,
                day,
                month,
                week_offset,
                day_of_week,
                weekday_offset,
                days_of_month,
                monthly_pattern,
                yearly_pattern
            )
            properties['time'] = self.time

        if name:
            properties['name'] = name
        if description:
            properties['description'] = description
        if start_date:
            properties['start_date'] = map_str_to_datetime(
                'start_date', start_date, self._FROM_DICT_MAP
            )
        if stop_date:
            properties['stop_date'] = map_str_to_datetime(
                'stop_date', stop_date, self._FROM_DICT_MAP
            )

        self._alter_properties(**properties)

        if self.schedule_type == self.ScheduleType.EVENT_BASED and 'time' in self.__dir__():
            delattr(self, 'time')
        elif self.schedule_type == self.ScheduleType.TIME_BASED and 'event' in self.__dir__():
            delattr(self, 'event')

    @method_version_handler('11.3.0000')
    def delete(self) -> bool:
        """Delete the schedule.

        Returns:
            bool: True if deletion was successful else False.
        """
        # When the server behavior changes, and deleting last schedule
        # from subscription will no longer delete subscription,
        # move 'force' param to method definition
        force = False
        self._delete_confirm_msg = (
            "This schedule may be part of a subscription. "
            "Deleting such a schedule will remove the subscription as well. "
            "This action cannot be undone. "
            f"Are you sure you want to delete the schedule '{self.name}'"
            f" with ID: {self.id}?[Y/N]: "
        )
        self._delete_success_msg = (f"Deleted schedule '{self.name}' with ID: {self.id}.")

        return super().delete(force=force)

    @property
    def expired(self):
        """Whether or not the schedule is expired"""
        return self._expired

    @property
    def schedule_next_delivery(self):
        """Next delivery date of time based schedule"""
        return self._schedule_next_delivery
