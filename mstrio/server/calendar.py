from logging import getLogger
from mstrio import config
import mstrio.api.calendars as calendars_api
from mstrio.connection import Connection
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity
from mstrio.utils.enums import DaysOfWeek
from mstrio.utils.response_processors import (
    objects as objects_processors,
    calendars as calendars_processors,
)
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = getLogger(__name__)


@method_version_handler(version='11.3.0700')
def list_calendars(
    connection: Connection,
    to_dictionary=False,
    limit: int | None = None,
    offset: int | None = None,
    only_system_calendars: bool | None = None,
    only_custom_calendars: bool | None = None,
):
    """List all available calendar objects.

    Args:
        connection (Connection): MicroStrategy connection object returned
            by `connection.Connection()`
        to_dictionary: If True, returns a list of dicts,
            otherwise returns a list of Calendar objects
        limit (int, optional): Limit the number of calendars returned
        offset (int, optional): Starting point within the collection of
            returned results. Used to control paging behavior.
        only_system_calendars (bool, optional): If True, returns only system
            calendars. Cannot be used with `only_custom_calendars`
        only_custom_calendars (bool, optional): If True, returns only custom
            calendars. Cannot be used with `only_system_calendars`

    Returns:
    A list of calendars as Calendar objects or dicts."""

    return Calendar._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        offset=offset,
        only_system_calendars=only_system_calendars,
        only_custom_calendars=only_custom_calendars,
    )


@class_version_handler(version='11.3.0700')
class Calendar(Entity, CopyMixin, DeleteMixin):

    _OBJECT_TYPE = ObjectTypes.CALENDAR
    _API_GETTERS = {
        (
            'name',
            'description',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'acg',
            'acl',
            'comments',
            'hidden',
        ): objects_processors.get_info,
        (
            'id',
            'base_calendar',
            'calendar_begin_static',
            'calendar_begin_offset',
            'calendar_end_static',
            'calendar_end_offset',
            'table_prefix',
            'week_start_day',
        ): calendars_processors.get_calendar,
    }

    @staticmethod
    def _parse_owner(source, connection, to_snake_case: bool = True):
        """Parses owner from the API response."""
        from mstrio.users_and_groups import User

        return User.from_dict(source, connection, to_snake_case)

    @staticmethod
    def _parse_base_calendar(
        source, connection, to_snake_case: bool = True
    ) -> 'Calendar':
        """Parses base calendar from the API response."""

        return Calendar.from_dict(source, connection, to_snake_case)

    @classmethod
    def _validate_year_definition_deltas(
        cls,
        calendar_begin_static: int | None,
        calendar_begin_offset: int | None,
        calendar_end_static: int | None,
        calendar_end_offset: int | None,
    ) -> None:
        if calendar_begin_static is not None and calendar_begin_offset is not None:
            raise ValueError(
                "You must provide either 'calendar_begin_static' "
                "or 'calendar_begin_offset', not both."
            )
        if calendar_end_static is not None and calendar_end_offset is not None:
            raise ValueError(
                "You must provide either 'calendar_end_static' or "
                "'calendar_end_offset', not both."
            )

    @classmethod
    def _validate_year_definitions(
        cls,
        calendar_begin_static: int | None,
        calendar_begin_offset: int | None,
        calendar_end_static: int | None,
        calendar_end_offset: int | None,
    ) -> None:
        cls._validate_year_definition_deltas(
            calendar_begin_static=calendar_begin_static,
            calendar_begin_offset=calendar_begin_offset,
            calendar_end_static=calendar_end_static,
            calendar_end_offset=calendar_end_offset,
        )
        if calendar_begin_static is None and calendar_begin_offset is None:
            raise ValueError(
                "You must provide either 'calendar_begin_static' "
                "or 'calendar_begin_offset'."
            )
        if calendar_end_static is None and calendar_end_offset is None:
            raise ValueError(
                "You must provide either 'calendar_end_static' "
                "or 'calendar_end_offset'."
            )

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'subtype': ObjectSubTypes,
        'owner': User.from_dict,
        'week_start_day': DaysOfWeek,
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        if not id:
            if name:
                # not using helper functions because they're suited to Response
                # objects and not extracted/wrangled dicts returned by
                # response_processors functions
                cals_with_name = [
                    c
                    for c in Calendar._list_all(
                        connection=connection, to_dictionary=True
                    )
                    if c['name'] == name
                ]
                if not cals_with_name:
                    raise ValueError(f"Calendar with name '{name}' not found.")
                if (num_of_cals := len(cals_with_name)) > 1:
                    raise ValueError(
                        f"Found {num_of_cals} calendars with name '{name}'. "
                        "Please provide 'id' argument."
                    )
                id = cals_with_name[0]['id']
            else:
                raise ValueError("Please provide either 'id' or 'name' argument.")
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.base_calendar = kwargs.get('base_calendar')
        self.table_prefix = kwargs.get('table_prefix')
        if calendar_begin_static := kwargs.get('calendar_begin_static'):
            self.calendar_begin_static = int(calendar_begin_static)
        if calendar_begin_offset := kwargs.get('calendar_begin_offset'):
            self.calendar_begin_offset = int(calendar_begin_offset)
        if calendar_end_static := kwargs.get('calendar_end_static'):
            self.calendar_end_static = int(calendar_end_static)
        if calendar_end_offset := kwargs.get('calendar_end_offset'):
            self.calendar_end_offset = int(calendar_end_offset)
        if week_start_day := kwargs.get('week_start_day'):
            self.week_start_day = DaysOfWeek(week_start_day.lower())

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        base_calendar: 'str | Calendar',
        week_start_day: DaysOfWeek,
        table_prefix: str,
        description: str | None = None,
        calendar_begin_static: int | None = None,
        calendar_begin_offset: int | None = None,
        calendar_end_static: int | None = None,
        calendar_end_offset: int | None = None,
    ) -> 'Calendar':
        """Create a new calendar with the specified properties.

        Args:
            connection (Connection): MicroStrategy connection object returned by
                `connection.Connection()`
            name (str): Name of the calendar object
            base_calendar (str or Calendar, optional): Reference (ID or Calendar
                object) to the base calendar
            week_start_day (DaysOfWeek): First day of the week
            table_prefix (str): Prefix used to create tables in the warehouse.
                Defaults to an empty string
            description (str, optional): Description of the calendar object
            calendar_begin_static (int, optional): Beginning year for the
                calendar. Must be provided if and only if
                `calendar_begin_offset` is not
            calendar_begin_offset (int, optional): Beginning year for the
                calendar as an offset from the current year. Must be provided
                if and only if `calendar_begin_static` is not
            calendar_end_static (int, optional): Ending year for the calendar.
                Must be provided if and only if `calendar_end_offset` is not
            calendar_end_offset (int, optional): Ending year for the calendar
                as an offset from the current year. Must be provided if and
                only if `calendar_end_static` is not
        """

        cls._validate_year_definitions(
            calendar_begin_static=calendar_begin_static,
            calendar_begin_offset=calendar_begin_offset,
            calendar_end_static=calendar_end_static,
            calendar_end_offset=calendar_end_offset,
        )

        base_calendar_id = (
            base_calendar.id if isinstance(base_calendar, cls) else base_calendar
        )
        body = {
            "information": {"name": name, "description": description},
            "tablePrefix": table_prefix,
            "baseCalendar": {
                "objectId": base_calendar_id,
            },
            "calendarBegin": {
                "staticYear": calendar_begin_static,
                "dynamicYearOffset": calendar_begin_offset,
            },
            "calendarEnd": {
                "staticYear": calendar_end_static,
                "dynamicYearOffset": calendar_end_offset,
            },
            "weekStartDay": week_start_day.value,
        }

        body = helper.delete_none_values(source=body, recursion=True)
        new_cal = cls.from_dict(
            source=calendars_processors.create_calendar(
                connection=connection, body=body
            ),
            connection=connection,
        )
        if config.verbose:
            logger.info(
                f"Successfully created Calendar named: '{name}' with ID:"
                f" '{new_cal.id}'"
            )
        return new_cal

    def alter(
        self,
        name: str | None = None,
        week_start_day: DaysOfWeek | None = None,
        description: str | None = None,
        base_calendar: 'str | Calendar | None' = None,
        table_prefix: str | None = None,
        calendar_begin_static: int | None = None,
        calendar_begin_offset: int | None = None,
        calendar_end_static: int | None = None,
        calendar_end_offset: int | None = None,
    ) -> None:
        self._validate_year_definition_deltas(
            calendar_begin_static=calendar_begin_static,
            calendar_begin_offset=calendar_begin_offset,
            calendar_end_static=calendar_end_static,
            calendar_end_offset=calendar_end_offset,
        )

        if base_calendar is None:
            base_calendar_id = self.base_calendar
        elif isinstance(base_calendar, Calendar):
            base_calendar_id = base_calendar.id
        else:
            base_calendar_id = base_calendar

        name = name or self.name
        table_prefix = table_prefix or self.table_prefix
        if calendar_begin_static is None and calendar_begin_offset is None:
            calendar_begin_static = self.calendar_begin_static
            calendar_begin_offset = self.calendar_begin_offset
        if calendar_end_static is None and calendar_end_offset is None:
            calendar_end_static = self.calendar_end_static
            calendar_end_offset = self.calendar_end_offset
        week_start_day = week_start_day or self.week_start_day

        body = {
            "information": {"name": name, "description": description},
            "tablePrefix": table_prefix,
            "baseCalendar": {"objectId": base_calendar_id},
            "calendarBegin": {
                "staticYear": calendar_begin_static,
                "dynamicYearOffset": calendar_begin_offset,
            },
            "calendarEnd": {
                "staticYear": calendar_end_static,
                "dynamicYearOffset": calendar_end_offset,
            },
            "weekStartDay": week_start_day.value,
        }

        body = helper.delete_none_values(source=body, recursion=True)
        calendars_api.update_calendar(connection=self.connection, id=self.id, body=body)
        self.fetch()

    def get_calendar_begin(self, base_year: int | None) -> int:
        if self.calendar_begin_offset is None:
            return self.calendar_begin_static
        else:
            if base_year is None:
                raise ValueError(
                    'Base year is required to calculate the year with offset.'
                )
            return base_year + self.calendar_begin_offset

    def get_calendar_end(self, base_year: int | None) -> int:
        if self.calendar_end_offset is None:
            return self.calendar_end_static
        else:
            if base_year is None:
                raise ValueError(
                    'Base year is required to calculate the year with offset.'
                )
            return base_year + self.calendar_end_offset

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        limit: int | None = None,
        offset: int | None = None,
        only_system_calendars: bool | None = None,
        only_custom_calendars: bool | None = None,
    ) -> list['Calendar'] | list[dict]:
        if only_system_calendars and only_custom_calendars:
            raise ValueError(
                "You can use only one "
                "of 'only_system_calendars' and 'only_custom_calendars' arguments."
            )

        subtype = None
        if only_system_calendars:
            subtype = "calendar_system"
        elif only_custom_calendars:
            subtype = "calendar_custom"

        objects = calendars_processors.list_calendars(
            connection=connection,
            limit=limit,
            offset=offset,
            subtype=subtype,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]
