from copy import deepcopy
import csv
from enum import Enum
import inspect
from os.path import join as joinpath
from pprint import pprint
from sys import version_info
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, TypeVar, Union

import dictdiffer
from pandas import DataFrame
import stringcase

from mstrio import config
from mstrio.api import objects
from mstrio.api.exceptions import VersionException
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.acl import ACLMixin

if TYPE_CHECKING:
    from mstrio.server import Application

T = TypeVar("T")


class ObjectTypes(Enum):
    FILTER = 1
    REPORT_DEFINITION = 3
    METRIC = 4
    AGG_METRIC = 7
    FOLDER = 8
    PROMPT = 10
    ATTRIBUTE = 12
    FACT = 13
    TABLE = 15
    MONITOR = 20
    ATTRIBUTE_FORM = 21
    COLUMN = 26
    DBROLE = 29
    DBLOGIN = 30
    DBCONNECTION = 31
    APPLICATION = 32
    USER = 34
    USERGROUP = 34
    CONFIGURATION = 36
    SECURITY_ROLE = 44
    CONSOLIDATION = 47
    SCHEDULE_EVENT = 49
    SCHEDULE_OBJECT = 50
    SCHEDULE_TRIGGER = 51
    DBTABLE = 53
    DOCUMENT_DEFINITION = 55
    DBMS = 57
    SECURITY_FILTER = 58
    NONE = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


class ObjectSubTypes(Enum):
    OLAP_CUBE = 776
    SUPER_CUBE = 779
    USER = 8704
    USER_GROUP = 8705
    MD_SECURITY_FILTER = 14848
    NONE = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


class EntityBase(helper.Dictable):
    """This class is for objects that do not have a specified MSTR type.

    Attributes:
        connection: A MicroStrategy connection object
        id: Object ID
        type: Object type set to None
        name: Object name
    """
    _OBJECT_TYPE: ObjectTypes = ObjectTypes.NONE  # MSTR object type defined in ObjectTypes
    _API_GETTERS: Dict[Union[str, tuple], Callable] = {}
    _FROM_DICT_MAP: Dict[str, Callable] = {
        'type': ObjectTypes
    }  # map attributes to Enums and Composites
    _AVAILABLE_ATTRIBUTES: Dict[str, type] = {}  # fetched on runtime from all Getters
    _API_PATCH: dict = {}
    _PATCH_PATH_TYPES: Dict[str, type] = {}  # used in update_properties method

    def __init__(self, connection: Connection, object_id: str, **kwargs) -> None:
        self._init_variables(connection=connection, id=object_id, **kwargs)
        if config.fetch_on_init and self._find_func("id") is not None:
            self.fetch("id")
        if config.verbose:
            print(self)

    def _init_variables(self, **kwargs):
        """Initialize variables given kwargs.

        Note: attributes not accepted by any implementation of this function
            in the inheritance chain will be disregarded.
        """
        # create _AVAILABLE_ATTRIBUTES map
        self._AVAILABLE_ATTRIBUTES.update({key: type(val) for key, val in kwargs.items()})
        self._connection = kwargs.get("connection")
        self._id = kwargs.get("id")
        self._type = self._OBJECT_TYPE if 'type' in self._FROM_DICT_MAP else kwargs.get(
            "type", self._OBJECT_TYPE)
        self.name = kwargs.get("name")
        self._altered_properties = dict()

    def fetch(self, attr: Optional[str] = None) -> None:
        """Fetch the latest object state from the I-Server.

        Note:
            This method can overwrite local changes made to the object.

        Args:
            attr: Attribute name to be fetched.
        Raises:
            ValueError: if `attr` cannot be fetched.
        """
        functions = self._API_GETTERS  # by default fetch all endpoints

        if attr is not None:  # if attr is specified fetch endpoint matched to the attribute name
            function = self._find_func(attr)
            if not function:
                raise ValueError(f"The attribute `{attr}` cannot be fetched for this object")
            else:
                functions = {attr: func for attr, func in functions.items() if func == function}

        for key, func in functions.items():  # call respective API getters
            param_value_dict = helper.auto_match_args(func, self)

            response = func(**param_value_dict)
            if response.ok:
                response = response.json()
                if type(response) == dict:
                    object_dict = {
                        key if isinstance(key, str) and len(response) == 1 else k: v
                        for k, v in response.items()
                    }
                    self._set_object(**object_dict)
                elif type(response) == list:
                    self._set_object(**{key: response})
                # TODO: consider changing camel_to_snake logic to work with
                # list of keys
                response = helper.camel_to_snake(response)
                # keep track of fetched attributes
                self._add_to_fetched((response.keys() if isinstance(response, dict) else key))

    def _add_to_fetched(self, keys: Union[str, tuple]) -> None:
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            key = key[1:] if key.startswith("_") else key
            self._fetched_attributes.add(key)

    @classmethod
    def _find_func(cls, attr: str) -> Optional[Callable]:
        """Try to find API endpoint in `cls._API_GETTERS` responsible for chosen
        attribute.

        Returns: Function or None if function not found
        """
        if not isinstance(attr, str):
            raise TypeError("`attr` parameter has to be of type str")

        for attributes, func in cls._API_GETTERS.items():
            if isinstance(attributes, str):
                if attr == attributes:
                    return func
            elif isinstance(attributes, tuple):
                if attr in attributes:
                    return func
            else:
                raise NotImplementedError
        return None

    def _set_object(self, **kwargs) -> None:
        """Set object attributes programatically by providing keyword args.
        Support ENUMs and creating component objects."""

        object_info = helper.camel_to_snake(kwargs)

        properties = set(
            (elem[0]
             for elem in inspect.getmembers(self.__class__, lambda x: isinstance(x, property))))

        for key, val in object_info.items():  # type: ignore
            # if self is a composite, create component instance
            if key in self._FROM_DICT_MAP:
                # determine which constructor will be used
                if isinstance(self._FROM_DICT_MAP[key], type(Enum)):
                    val = self._FROM_DICT_MAP[key](val)
                else:
                    val = self._FROM_DICT_MAP[key](source=val, connection=self.connection)

            # create _AVAILABLE_ATTRIBUTES map
            self._AVAILABLE_ATTRIBUTES.update({key: type(val)})

            # check if attr is read-only and if yes return '_' version of it
            if key in properties:
                key = "_" + key
            setattr(self, key, val)

    def list_properties(self) -> dict:
        """List all properties of the object."""
        if hasattr(self, "_API_GETTERS"):  # fetch attributes not loaded on init
            attr = [
                attr for attr in self._API_GETTERS.keys() if isinstance(attr, str)  # type: ignore
            ]
            for a in attr:
                try:
                    getattr(self, a)
                except VersionException:
                    pass

        properties = inspect.getmembers(self.__class__, lambda x: isinstance(x, property))
        properties = {elem[0]: elem[1].fget(self) for elem in properties}
        attributes = {key: val for key, val in vars(self).items() if not key.startswith('_')}
        attributes = {**properties, **attributes}

        return {
            key: attributes[key] for key in sorted(attributes, key=helper.sort_object_properties)
        }

    def to_dataframe(self) -> DataFrame:
        """Return a `DataFrame` object containing object properties."""
        return DataFrame.from_dict(self.list_properties(), orient='index', columns=['value'])

    def print(self) -> None:
        """Pretty Print all properties of the object."""
        if version_info.major >= 3 and version_info.minor >= 8:
            pprint(self.list_properties(), sort_dicts=False)  # type: ignore
        else:
            pprint(self.list_properties())

    @classmethod
    def from_dict(cls: T, source: Dict[str, Any], connection: Connection) -> T:
        """Instantiate an object from response without calling any additional
        getters."""
        obj = cls.__new__(cls)  # Does not call __init__
        object_source = helper.camel_to_snake(source)
        obj._init_variables(connection=connection, **object_source)
        return obj

    def __str__(self):
        if self.__dict__.get("name"):
            return "{} object named: '{}' with ID: '{}'".format(self.__class__.__name__, self.name,
                                                                self.id)
        else:
            return "{} object with ID: '{}'".format(self.__class__.__name__, self.id)

    def __repr__(self):
        param_value_dict = helper.auto_match_args(self.__init__, self, exclude=['self'],
                                                  include_defaults=False)
        params_list = []
        for param, value in param_value_dict.items():
            if param == "connection" and isinstance(value, Connection):
                params_list.append("connection")
            else:
                params_list.append(f"{param}={repr(value)}")
        formatted_params = ", ".join(params_list)
        return f"{self.__class__.__name__}({formatted_params})"

    def __hash__(self):
        return hash((self.id, self._OBJECT_TYPE.value))

    def __eq__(self, other):
        """Equals operator to compare if an entity is equal to another object.

        We define 2 Entities as being equal if:
            1. the other object is an Entity and also shares the same id
            2. the other object is a string and is equal to either the name or
               id of the Entity
        This allows us to search for Entities in a collection by specifying its
        id, name, or another Entity itself. For example:
            if "user" in users: ...
            if "28ECA8BB11D5188EC000E9ABCA1B1A4F" in users: ...
        """
        if isinstance(other, str):
            return self.id == other or self.name == other
        elif isinstance(other, type(self)):
            return self.id == other.id
        else:
            return NotImplemented  # don't attempt to compare against unrelated types

    @classmethod
    def to_csv(cls: T, objects: Union[T, List[T]], name: str, path: Optional[str] = None,
               properties: Optional[List[str]] = None) -> None:
        """Export MSTR objects to a csv file.

        Optionally, save only the object properties specified in the properties
        parameter.

        Args:
            objects: List of objects of the same type that will be exported
            name: name of the csv file ending with '.csv'
            path: path to the directory where the file will be saved
            properties: list of object attribute names that should be included
                in the exported file
        """
        file = joinpath(path, name) if path else name
        list_of_objects = []
        if not name.endswith('.csv'):
            msg = ("The file extension is different than '.csv', please note that using a "
                   "different extension might disrupt opening the file correctly.")
            helper.exception_handler(msg, exception_type=Warning)
        if isinstance(objects, cls):
            properties_dict = objects.list_properties()
            if properties:
                list_of_objects.append(
                    {key: value for key, value in properties_dict.items() if key in properties})
            else:
                list_of_objects.append(properties_dict)
        elif isinstance(objects, list):
            if not properties:
                properties = objects[0].list_properties().keys()
            for obj in objects:
                if isinstance(obj, cls):
                    list_of_objects.append({
                        key: value
                        for key, value in obj.list_properties().items()
                        if key in properties
                    })
                else:
                    helper.exception_handler(
                        f"Object '{obj}' of type '{type(obj)}' is not supported.",
                        exception_type=Warning)
        else:
            raise TypeError((f"Objects should be of type {cls.__name__} or "
                             f"list of {cls.__name__}."))

        with open(file, 'w') as f:
            fieldnames = list_of_objects[0].keys()
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(list_of_objects)
        if config.verbose:
            print(f"Object exported successfully to '{file}'")

    def is_modified(self, to_list: bool = False) -> Union[bool, list]:
        # TODO decide if needed or just deprecate
        """Compare the current object to the object on I-Server.

        Args:
            to_list: If True, return a list of tuples with object differences
        """
        temp = deepcopy(self)
        temp.fetch()
        differences = list(dictdiffer.diff(temp.__dict__, self.__dict__))
        if len(differences) == 0:
            if config.verbose:
                print("There are no differences between local and remote '{}' object.".format(
                    ObjectTypes(self.type).name))
            return differences if to_list else False
        else:
            return differences if to_list else True

    def update_properties(self) -> None:
        """Save compatible local changes of the object attributes to the
        I-Server.

        Raises:
            requests.HTTPError: if I-Server raises exception
        """
        changes = {k: v[1] for k, v in self._altered_properties.items()}
        self._alter_properties(**changes)
        self._altered_properties.clear()

    def _send_proper_patch_request(self, properties: dict, op: str = 'replace') -> List[bool]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships.

        Args:
            properties: dictionary of required changes
            op: operation type, 'replace' by default

        Returns:
            List of succesfull or unsuccessful requests.
        """
        changed = []
        camel_properties = helper.snake_to_camel(properties)
        for attrs, (func, func_type) in self._API_PATCH.items():
            body = {}
            if func_type == 'partial_put':
                for name, value in camel_properties.items():
                    if stringcase.snakecase(name) in attrs:
                        value = helper.maybe_unpack(value, camel_case=True)
                        body[name] = self._validate_type(name, value)
            elif func_type == 'put':  # Update using the generic update_object()
                for name, value in properties.items():
                    if name in attrs:
                        setattr(self, name, self._validate_type(name, value))
                body = self.to_dict()
            elif func_type == 'patch':
                body = {"operationList": []}
                for name, value in camel_properties.items():
                    if stringcase.snakecase(name) in attrs:
                        value = helper.maybe_unpack(value, camel_case=True)
                        body['operationList'].append({
                            "op": op,
                            "path": "/{}".format(name),
                            "value": self._validate_type(name, value)
                        })
            else:
                msg = f"{func} function is not supported by `_send_proper_patch_request`"
                raise NotImplementedError(msg)

            if not body:
                continue
            # send patch request from the specified update wrapper
            param_value_dict = helper.auto_match_args(func, self, exclude=["body"])
            param_value_dict['body'] = body
            response = func(**param_value_dict)

            if response.ok:
                changed.append(True)
                response = response.json()
                if type(response) == dict:
                    self._set_object(**response)
            else:
                changed.append(False)
        return changed

    def _alter_properties(self, **properties) -> None:
        """Generic alter method that has to be implemented in child classes
        where arguments will be specified."""
        if not properties:
            if config.verbose:
                print(f"No changes specified for {type(self).__name__} '{self.name}'.")
            return None

        changed = self._send_proper_patch_request(properties)

        if config.verbose and all(changed):
            msg = (f"{type(self).__name__} '{self.name}' has been modified on the server. "
                   f"Your changes are saved locally.")
            print(msg)

    def _update_nested_properties(self, objects, path: str, op: str,
                                  existing_ids: Optional[List[str]] = None) -> Tuple[str, str]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships.

        Returns:
            IDs of succeeded and failed operations by filtering by existing IDs.
        """
        from mstrio.access_and_security.privilege import Privilege

        # check whether existing_ids are supplied
        if existing_ids is None:
            existing_ids = [obj.get('id') for obj in getattr(self, path)]

        # create list of objects from strings/objects/lists
        objects_list = objects if isinstance(objects, list) else [objects]
        object_map = {obj.id: obj.name for obj in objects_list if isinstance(obj, Entity)}

        object_ids_list = [
            obj.id if isinstance(obj, (EntityBase, Privilege)) else str(obj)
            for obj in objects_list
        ]

        # check if objects can be manipulated by comparing to existing values
        if op == "add":
            filtered_object_ids = sorted(
                list(filter(lambda x: x not in existing_ids, object_ids_list)))
        elif op == "remove":
            filtered_object_ids = sorted(list(filter(lambda x: x in existing_ids,
                                                     object_ids_list)))
        if filtered_object_ids:
            properties = {path: filtered_object_ids}
            self._send_proper_patch_request(properties, op)

        failed = list(sorted(set(object_ids_list) - set(filtered_object_ids)))
        failed_formatted = [object_map.get(object_id, object_id) for object_id in failed]
        succeeded_formatted = [
            object_map.get(object_id, object_id) for object_id in filtered_object_ids
        ]
        return (succeeded_formatted, failed_formatted)

    def _validate_type(self, name: str, value: T) -> T:
        """Validates whether the attribute is set using correct type.

        Raises:
            TypeError if incorrect.
        """
        type_map = {**self._AVAILABLE_ATTRIBUTES, **self._PATCH_PATH_TYPES}
        value_type = type_map.get(name, 'Not Found')
        if value_type != 'Not Found' and type(value) != value_type:
            raise TypeError(f"'{name}' has incorrect type. Expected type: '{value_type}'")
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        """Overloads the __setattr__ method to validate if this attribute can
        be set for current object and verify value data types."""

        def track_changes():
            already_tracked = name in self._altered_properties
            current_val = self._altered_properties[name][0] if already_tracked \
                else self.__dict__[name]
            is_changed = not (type(current_val) is type(value) and current_val == value)
            if is_changed:
                self._altered_properties.update({name: (current_val, value)})
            elif already_tracked:
                del self._altered_properties[name]

        # Keep track of changed properties if value is already fetched
        if hasattr(self, "_fetched_attributes"):
            if name in self._PATCH_PATH_TYPES and name in self._fetched_attributes:
                track_changes()
            # if value not equal to None then treat as fetched
            if value is not None:
                self._add_to_fetched(name)
        super(EntityBase, self).__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        """Fetch attributes if not fetched."""
        val = super(EntityBase, self).__getattribute__(name)

        if name in ["_fetched_attributes", "_find_func"]:
            return val
        if not hasattr(self, "_fetched_attributes"):
            self._fetched_attributes = set()
        if hasattr(self, "_fetched_attributes") and hasattr(self, "_find_func"):
            _name = name[1:] if name.startswith("_") else name
            was_fetched = _name in self._fetched_attributes
            can_fetch = self._find_func(_name) is not None and "id" in self._fetched_attributes
            if can_fetch and not was_fetched:
                self.fetch(_name)  # fetch the relevant object data
            val = super(EntityBase, self).__getattribute__(name)

        return val

    # TODO add docstrings
    @property
    def connection(self) -> Connection:
        return self._connection

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> ObjectTypes:
        return self._type


class Entity(EntityBase, ACLMixin):
    """Base class representation of the MSTR object.

    Provides methods to fetch, update, and view the object. To implement
    this base class all class attributes have to be provided.

    Attributes:
        connection: A MicroStrategy connection object
        id: Object ID
        name: Object name
        description: Object description
        abbreviation: Object abbreviation
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd HH:mm:ss" in UTC
        version: Version ID
        owner: Owner ID and name
        icon_path: Object icon path
        view_media: View media settings
        ancestors: List of ancestor folders
        certified_info: Certification status, time of certificaton, and
            information about the certifier (currently only for document and
            report)
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _API_GETTERS: Dict[Union[str, tuple], Callable] = {
        ('id', 'name', 'description', 'abbreviation', 'type', 'subtype', 'ext_type',
         'date_created', 'date_modified', 'version', 'owner', 'icon_path', 'view_media',
         'ancestors', 'certified_info', 'acg', 'acl'): objects.get_object_info
    }
    _API_PATCH: dict = {
        ('name', 'description', 'abbreviation'): (objects.update_object, 'partial_put')
    }
    _PATCH_PATH_TYPES = {"name": str, "description": str, "abbreviation": str}

    def _init_variables(self, **kwargs) -> None:
        """Initialize variables given kwargs."""
        from mstrio.users_and_groups.user import User
        super(Entity, self)._init_variables(**kwargs)
        self.description = kwargs.get("description")
        self.abbreviation = kwargs.get("abbreviation")
        self._subtype = kwargs.get("subtype")
        self._ext_type = kwargs.get("ext_type")
        self._date_created = kwargs.get("date_created")
        self._date_modified = kwargs.get("date_modified")
        self._version = kwargs.get("version")
        self._owner = User.from_dict(
            kwargs.get("owner"),
            self.connection,
        ) if kwargs.get("owner") else None
        self._date_created = kwargs.get("date_created")
        self._icon_path = kwargs.get("icon_path")
        self._view_media = kwargs.get("view_media")
        self._ancestors = kwargs.get("ancestors")
        self._certified_info = kwargs.get("certified_info")
        self._acg = kwargs.get("acg")
        self._acl = kwargs.get("acl")

    # TODO add docstrings to all properties
    @property
    def subtype(self):
        return self._subtype

    @property
    def ext_type(self):
        return self._ext_type

    @property
    def date_created(self):
        return self._date_created

    @property
    def date_modified(self):
        return self._date_modified

    @property
    def version(self):
        return self._version

    @property
    def owner(self):
        return self._owner

    @property
    def icon_path(self):
        return self._icon_path

    @property
    def view_media(self):
        return self._view_media

    @property
    def ancestors(self):
        return self._ancestors

    @property
    def certified_info(self):
        return self._certified_info

    @property
    def acg(self):
        return self._acg

    @property
    def acl(self):
        return self._acl


class CopyMixin:
    """CopyMixin class adds creating copies of objects functionality.

    Currently application objects are not supported. Must be mixedin with
    Entity or its subclasses.
    """

    def create_copy(self: Entity, name: Optional[str] = None, folder_id: Optional[str] = None,
                    application: Union["Application", str] = None) -> Any:
        """Create a copy of the object on the I-Server.

        Args:
            name: New name of the object. If None, a default name is generated,
                such as 'Old Name (1)'
            folder_id: ID of the destination folder. If None, the object is
                saved in the same folder as the source object.
            application_id: By default, the application selected when
                creating Connection object. Override `application` to specify
                application where the current object exists.

        Returns:
                New python object holding the copied object.
        """
        if self._OBJECT_TYPE.value in [32]:
            raise NotImplementedError("Object cannot be copied yet.")
        # TODO if object uniqness depends on application_id extract app_id
        # TODO automatically
        response = objects.copy_object(self.connection, id=self.id, name=name, folder_id=folder_id,
                                       type=self._OBJECT_TYPE.value, application_id=application)
        return self.from_dict(source=response.json(), connection=self.connection)


class VldbMixin:
    """VLDBMixin class adds vldb management for supporting objects.

    Objects currently supporting VLDB settings are dataset, document, dossier.
    Must be mixedin with Entity or its subclasses.
    """
    _parameter_error = "Please specify the application parameter."

    def list_vldb_settings(self: Entity, application: Optional[str] = None) -> list:
        """List VLDB settings."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError(self._parameter_error)

        response = objects.get_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                             application)
        return response.json()

    def alter_vldb_settings(self: Entity, property_set_name: str, name: str, value: dict,
                            application: Optional[str] = None) -> None:
        """Alter VLDB settings for a given property set."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError(self._parameter_error)

        body = [{"name": name, "value": value}]
        response = objects.set_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                             property_set_name, body, application)
        if config.verbose and response.ok:
            print("VLDB settings altered")

    def reset_vldb_settings(self: Entity, application: Optional[str] = None) -> None:
        """Reset VLDB settings to default values."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError(self._parameter_error)

        response = objects.delete_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                                application)
        if config.verbose and response.ok:
            print("VLDB settings reset to default")
