from mstrio.api import schedules
from mstrio.connection import Connection
from mstrio.utils import helper


class ScheduleManager:
    """Manage schedules associated with subscription.

    Attributes:
        connection: A MicroStrategy connection object
    """

    def __init__(self, connection: Connection):
        """Initialize the ScheduleManager object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
        """
        self.connection = connection

    def list_schedules(self, **filters):
        """List all schedules.

        Args:
            **filters: Available filter parameters:['name':,
                                                    'id',
                                                    'description',
                                                    'scheduleType',
                                                    'scheduleNextDelivery',]
        """
        # TODO add limit, and support for objects, to_datafram, to_dictionary
        response = schedules.list_schedules(self.connection)
        if response.ok:
            response = helper.camel_to_snake(response.json()["schedules"])
            return helper.filter_list_of_dicts(response, **filters)


class Schedule:
    """Class representation of MicroStrategy Schedule object.

    Attributes:
        connection: A MicroStrategy connection object
        name: Schedule name
        id: Schedule ID
        description: Schedule description
        schedule_type: Schedule type
        schedule_next_delivery: Schedule next delivery date
    """

    _AVAILABLE_ATTRIBUTES = {}

    def __init__(self, connection: Connection, id: str = None, name: str = None) -> None:
        """Initialize the Schedule object, populates it with I-Server data.
        Specify either `id` or `name`. When `id` is provided (not `None`),
        `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Schedule ID
            name: Schedule name
        """

        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.")
        if id is None:
            sm = ScheduleManager(connection)
            schedule = sm.list_schedules(name=name)
            if schedule:
                id = schedule[0]['id']
            else:
                helper.exception_handler(
                    "There is no schedule with the given name: '{}'".format(name),
                    exception_type=ValueError)

        self.connection = connection
        self.id = id
        self.__fetch()

    def __fetch(self) -> None:
        """Retrieve object metadata."""
        response = schedules.get_schedule(self.connection, self.id)

        if response.ok:
            response = response.json()
            response = helper.camel_to_snake(response)
            for key, value in response.items():
                self._AVAILABLE_ATTRIBUTES.update({key: type(value)})
                self.__setattr__(key, value)

    def list_properties(self) -> dict:
        """List all properties for a schedule."""
        # self.__fetch()
        return {
            key: self.__dict__[key]
            for key in sorted(self.__dict__, key=helper.sort_object_properties)
            if key != 'connection'
        }
