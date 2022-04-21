from typing import List, TYPE_CHECKING, Union

from mstrio.api import datasources
from mstrio.utils import helper
from mstrio.utils.entity import EntityBase, ObjectTypes

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_available_dbms(connection: "Connection", to_dictionary: bool = False, limit: int = None,
                        **filters) -> Union[List["Dbms"], List[dict]]:
    """List all available database management systems (DBMSs) objects or dicts.
    Optionally filter the DBMS by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'version']

    Examples:
        >>> list_available_dbms(connection)
    """
    return Dbms._list_available_dbms(
        connection=connection,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class Dbms(EntityBase):
    """Object representation of MicroStrategy Database management system (DBMS)

    Attributes:
        name: Database management system (DBMS) name.
        id: Database management system (DBMS) ID.
        type: Database management system (DBMS) type.
        version: Database management system (DBMS) version.
    """
    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.NONE
    _FROM_DICT_MAP = {}  # map attributes to Enums and Composites
    _DBMS_CACHE = set()

    def __init__(self, connection: "Connection", name: str = None, id: str = None,
                 type: str = None, version: str = None):
        """Initialize Dbms object."""
        if name is None and id is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.",
                exception_type=ValueError)
        temp_dbms = None

        for dbms in self._DBMS_CACHE:
            if name == dbms.name or id == dbms.id:
                temp_dbms = dbms
                super().__init__(connection=connection, object_id=temp_dbms.id,
                                 name=temp_dbms.name, type=temp_dbms.type,
                                 version=temp_dbms.version)

        if not temp_dbms:
            if id:
                temp_dbms = Dbms._list_available_dbms(connection, id=id, to_dictionary=True)
            elif name:
                temp_dbms = Dbms._list_available_dbms(connection, name=name, to_dictionary=True)

            if temp_dbms:
                [temp_dbms] = temp_dbms
                super().__init__(connection=connection, object_id=temp_dbms["id"],
                                 name=temp_dbms["name"], type=temp_dbms["type"],
                                 version=temp_dbms["version"])
            else:
                identifier = name if name else id
                raise ValueError(f"There is no Dbms: '{identifier}'")

    def _init_variables(self, **kwargs) -> None:
        """Set object attributes by providing keyword args."""
        super()._init_variables(**kwargs)
        self._version = kwargs.get("version")

    @classmethod
    def _list_available_dbms(cls, connection: "Connection", to_dictionary: bool = False,
                             limit: int = None, **filters) -> Union[List["Dbms"], List[dict]]:

        objects = helper.fetch_objects(connection=connection, api=datasources.get_available_dbms,
                                       limit=None, filters=None)
        cls._DBMS_CACHE.update(
            [cls.from_dict(source=obj, connection=connection) for obj in objects])

        if limit:
            objects = objects[:limit]
        if filters:
            objects = helper.filter_list_of_dicts(objects, **filters)
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @property
    def version(self) -> str:
        return self._version
