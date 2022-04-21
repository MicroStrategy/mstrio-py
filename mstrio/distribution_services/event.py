import logging
from typing import List, Optional, Union

from packaging import version

from mstrio import config
from mstrio.api import events, objects
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.entity import DeleteMixin, Entity, ObjectTypes

logger = logging.getLogger(__name__)


def list_events(connection: Connection, to_dictionary: bool = False, limit: int = None,
                **filters) -> Union[List["Event"], List[dict]]:
    """List event objects or event dictionaries. Optionally filter list.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        to_dictionary(bool, optional): if True, return event as
            list of dicts
        limit(int, optional): maximum number of Events returned.
        **filters: Available filter parameters:['name':,
                                                'id',
                                                'description']
    """
    _objects = helper.fetch_objects(connection=connection, api=events.list_events, limit=limit,
                                    filters=filters, dict_unpack_value='events')

    if to_dictionary:
        return _objects
    else:
        return [Event.from_dict(source=obj, connection=connection) for obj in _objects]


class Event(Entity, DeleteMixin):
    """Class representation of MicroStrategy Event object.

    Attributes:
        connection: A MicroStrategy connection object
        name: Event name
        id: Event ID
        description: Event descriptions
    """
    _DELETE_NONE_VALUES_RECURSION = True
    _PATCH_PATH_TYPES = {'name': str, 'description': str}
    _OBJECT_TYPE = ObjectTypes.SCHEDULE_EVENT
    _API_GETTERS = {
        ('abbreviation', 'type', 'subtype', 'ext_type', 'date_created', 'date_modified', 'version',
         'owner', 'icon_path', 'view_media', 'ancestors', 'certified_info', 'acg',
         'acl'): objects.get_object_info,
    }
    _API_DELETE = staticmethod(events.delete_event)
    _API_PATCH = {
        ('name', 'description'): (events.update_event, 'put')
    }

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 name: Optional[str] = None) -> None:
        """Initialize the Event object, populates it with I-Server data.
        Specify either `id` or `name`. When `id` is provided (not `None`),
        `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Event ID
            name: Event name
        """
        self._API_GETTERS[('id', 'name', 'description')] = \
            events.get_event if version.parse(connection.web_version) >= \
            version.parse('11.3.0200') else objects.get_object_info

        if id is None and name is None:
            raise AttributeError(
                "Please specify either 'name' or 'id' parameter in the constructor.")
        if id is None:
            objects_info = list_events(connection, name=name, to_dictionary=True)
            if objects_info:
                object_info, object_info["connection"] = objects_info[0], connection
                self._init_variables(**object_info)
            else:
                raise ValueError(f"There is no event with the given name: '{name}'")
        else:
            super().__init__(connection=connection, object_id=id, name=name)

    def trigger(self):
        """Trigger the Event"""
        response = events.trigger_event(self.connection, self.id)
        if response.ok and config.verbose:
            logger.info(f"Event '{self.name}' with ID : '{self.id}' has been triggered.")
        return response.ok

    @classmethod
    def create(cls, connection: Connection, name: str,
               description: Optional[str] = None) -> "Event":
        """Create an Event

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            name: Name of the new Event
            description: Description of the new Event
        """
        body = helper.delete_none_values({
            "name": name,
            "description": description,
        }, recursion=True)
        response = events.create_event(connection, body)
        return cls.from_dict(response.json(), connection)

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter the Event's properties

        Args:
            name: New name for the Event
            description: New description for the Event
        """
        args = helper.delete_none_values({
            "name": name,
            "description": description,
        }, recursion=True)
        self._alter_properties(**args)
        if config.verbose:
            logger.info(f"Updated subscription '{self.name}' with ID: {self.id}.")
