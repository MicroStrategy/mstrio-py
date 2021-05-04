from copy import deepcopy
import csv
from enum import Enum
import inspect
from pprint import pprint
from sys import version_info
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

import dictdiffer
from pandas import DataFrame
from requests import HTTPError

from mstrio.api import objects
from mstrio.api.exceptions import VersionException
import mstrio.config as config
from mstrio.connection import Connection
from mstrio.utils import helper

if TYPE_CHECKING:
    from mstrio.server.application import Application


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
    DOCUMENT_DEFINITION = 55
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
    NONE = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


class EntityBase(helper.Dictable):
    """This class is for objects that do not have a specified MSTR type."""
    _OBJECT_TYPE: ObjectTypes = ObjectTypes.NONE  # MSTR object type defined in ObjectTypes
    _FROM_DICT_MAP = {'type': ObjectTypes}  # map attributes to Enums and Composites
    _AVAILABLE_ATTRIBUTES: Dict[str, type] = {}  # fetched on runtime from all Getters
    _PATCH_PATH_TYPES: Dict[str, type] = {"name": str}  # used in update_properties method

    def __init__(self, connection: Connection, object_id: str, **kwargs) -> None:
        self._init_variables(connection=connection, id=object_id, **kwargs)
        if config.verbose:
            print(self)

    def _init_variables(self, **kwargs):
        """Set object attributes by providing keyword args."""
        # create _AVAILABLE_ATTRIBUTES map
        self._AVAILABLE_ATTRIBUTES.update({key: type(val) for key, val in kwargs.items()})
        self._connection = kwargs.get("connection")
        self._id = kwargs.get("id")
        self._type = self._OBJECT_TYPE
        self.name = kwargs.get("name")

    def _set_object(self, **kwargs) -> None:
        """Set object attributes programatically by providing keyword args.
        Support ENUMs and creating component objects."""

        object_info = helper.camel_to_snake(kwargs)

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
            if key not in self._PATCH_PATH_TYPES:
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
    def from_dict(cls, source: Dict[str, Any], connection: Connection):
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
            elif value is not None:
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

    # TODO add docstrings
    @property
    def connection(self):
        return self._connection

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type


class Entity(EntityBase):
    """Base class representation of the MSTR object.

    Provides methods to fetch, update, and view the object. To implement
    this base class all class attributes have to be provided.
    """

    _API_GETTERS: dict = {
        ('id', 'name', 'description', 'abbreviation', 'type', 'subtype', 'ext_type',
         'date_created', 'date_modified', 'version', 'owner', 'icon_path', 'view_media',
         'ancestors', 'certified_info', 'acg', 'acl'): objects.get_object_info
    }
    # TODO refactor API_PATCH to be like API_GETTERS
    _API_PATCH: list = [objects.update_object]
    _PATCH_PATH_TYPES = {"name": str, "description": str, "abbreviation": str}

    def __init__(self, connection: Connection, object_id: str, **kwargs) -> None:
        self._init_variables(connection=connection, id=object_id, **kwargs)
        if config.fetch_on_init:
            self.fetch("id")
        if config.verbose:
            print(self)

    def _init_variables(self, **kwargs) -> None:
        """Initialize variables given kwargs."""
        from mstrio.users_and_groups.user import User
        self._altered_properties = dict()
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

    def fetch(self, attr: str = None) -> None:
        """Fetch the latest object state from the I-Server.

        Args:
            attr: Attribute name to be fetched.
        Note:
            This method can overwrite local changes made to the object.
        Raises:
            ValueError: if `attr` cannot be fetched.
        """
        functions = self._API_GETTERS  # by default fetch all endpoints

        if attr:  # if attr is specified fetch endpoint matched to the attribute name
            function = self._find_func(attr)
            if not function:
                raise ValueError("The attribute cannot be fetched for this object")
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

                # keep track of fetched attributes
                self._add_to_fetched(key)

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

    @classmethod
    def to_csv(cls, objects, name: str, path: str = None, properties: List[str] = None) -> None:
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
        file = path + '/' + name if path else name
        list_of_objects = []
        if not name.endswith('.csv'):
            msg = ("The file extension is different than '.csv', please note that using a "
                   "different extension might disrupt opening the file correctly.")
            helper.exception_handler(msg, exception_type=Warning)
        if isinstance(objects, cls):
            properties = objects.list_properties().keys() if properties is None else properties
            list_of_objects.append({
                key: value for key, value in objects.list_properties().items() if key in properties
            })
        elif isinstance(objects, list):
            properties = objects[0].list_properties().keys() if properties is None else properties
            for obj in objects:
                if isinstance(obj, cls):
                    list_of_objects.append({
                        key: value
                        for key, value in obj.list_properties().items()
                        if key in properties
                    })
                else:
                    helper.exception_handler(
                        "Object '{}' of type '{}' is not supported.".format(obj, type(obj)),
                        exception_type=Warning)
        else:
            raise TypeError((f"Objects should be of type {cls._OBJECT_TYPE.name} or "
                             f"list of {cls._OBJECT_TYPE.name}."))

        with open(file, 'w') as f:
            fieldnames = list_of_objects[0].keys()
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(list_of_objects)
        if config.verbose:
            print("Object exported successfully to '{}'".format(file))

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

    def _alter_properties(self, **properties) -> None:
        """Generic alter method that has to be implemented in child classes
        where arguments will be specified."""
        if not properties and config.verbose:
            print(f"No changes specified for {type(self).__name__} '{self.name}'.")
            return None

        body = {}
        # TODO use _find_func(attr) to search for
        func = self._API_PATCH[0]
        properties = helper.snake_to_camel(properties)

        if func == objects.update_object:  # Update using the generic update_object()
            for name, value in properties.items():
                body[name] = self._validate_type(name, value)
        else:  # Update using different update method, if one was specified
            body = {"operationList": []}
            for name, value in properties.items():
                body['operationList'].append({
                    "op": "replace",
                    "path": "/{}".format(name),
                    "value": self._validate_type(name, value)
                })

        # send patch request from the specified update wrapper
        param_value_dict = helper.auto_match_args(func, self, exclude=["body"])
        # param_value_dict = self.auto_match_args(func, exclude=["body"])
        param_value_dict['body'] = body
        response = func(**param_value_dict)

        if response.ok:
            if config.verbose:
                print("{} '{}' has been modified.".format(type(self).__name__, self.name))
            response = response.json()
            if type(response) == dict:
                self._set_object(**response)

    def _update_nested_properties(self, objects, path: str, op: str,
                                  existing_ids: List[str] = None) -> Tuple[str, str]:
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
            obj.id if isinstance(obj, (Entity, Privilege)) else str(obj) for obj in objects_list
        ]

        # check if objects can be manipulated by comparing to existing values
        if op == "add":
            filtered_object_ids = sorted(
                list(filter(lambda x: x not in existing_ids, object_ids_list)))
        elif op == "remove":
            filtered_object_ids = sorted(list(filter(lambda x: x in existing_ids,
                                                     object_ids_list)))
        if filtered_object_ids:
            body = {
                "operationList": [{
                    "op": op,
                    "path": '/{}'.format(path),
                    "value": filtered_object_ids
                }]
            }
            response = self._API_PATCH[0](self.connection, self.id, body).json()
            if type(response) == dict:
                self._set_object(**response)

        failed = list(sorted(set(object_ids_list) - set(filtered_object_ids)))
        failed_formatted = [object_map.get(object_id, object_id) for object_id in failed]
        succeeded_formatted = [
            object_map.get(object_id, object_id) for object_id in filtered_object_ids
        ]
        return (succeeded_formatted, failed_formatted)

    def _validate_type(self, name: str, value: Any) -> Any:
        """Validates whether the attribute is set using correct type.

        Raises:
            TypeError if incorrect.
        """
        type_map = {**self._AVAILABLE_ATTRIBUTES, **self._PATCH_PATH_TYPES}
        value_type = type_map.get(name, 'Not Found')
        if value_type != 'Not Found':
            if type(value) != value_type:
                raise TypeError(f"'{name}' has incorrect type. Expected type: '{value_type}'")
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        """Overloads the __setattr__ method to validate if this attribute can
        be set for current object and verify value data types."""
        # TODO decide if this is necessary here
        # self._validate_type(name, value)
        # Keep track of changed properties if value is already fetched
        if hasattr(self, "_fetched_attributes"):
            if name in self._PATCH_PATH_TYPES and name in self._fetched_attributes:
                self._altered_properties.update({name: (self.__dict__[name], value)})
                changes = self._altered_properties[name]
                if changes[0] == changes[1]:
                    del self._altered_properties[name]
            # if value not equal to None then treat as fetched
            if value is not None:
                self._add_to_fetched(name)
        super(Entity, self).__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        """Fetch attributes if not fetched."""
        val = super(Entity, self).__getattribute__(name)

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
            val = super(Entity, self).__getattribute__(name)

        return val

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

    def create_copy(self: Entity, name: str = None, folder_id: str = None,
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

    def list_vldb_settings(self: Entity, application: str = None) -> list:
        """List VLDB settings."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        response = objects.get_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                             application)
        return response.json()

    def alter_vldb_settings(self: Entity, property_set_name: str, name: str, value: dict,
                            application: str = None) -> None:
        """Alter VLDB settings for a given property set."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        body = [{"name": name, "value": value}]
        response = objects.set_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                             property_set_name, body, application)
        if config.verbose and response.ok:
            print("VLDB settings altered")

    def reset_vldb_settings(self: Entity, application: str = None) -> None:
        """Reset VLDB settings to default values."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not application and connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        response = objects.delete_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                                application)
        if config.verbose and response.ok:
            print("VLDB settings reset to default")


class EntityACL(Entity):
    # TODO Convert to AclMixin class
    # TODO streamline methods
    # TODO inherit from this class in supporting objects
    """Entity subclass for ACL management."""
    RIGHTS_MAP = {
        "Execute": 128,
        "Use": 64,
        "Control": 32,
        "Delete": 16,
        "Write": 8,
        "Read": 4,
        "UseExecute": 2,
        "Browse": 1,
    }
    AGGREGATED_RIGHTS_MAP = {
        "View": 197,
        "Modify": 221,
        "Full Control": 255,
        "Denied All": 255,
        "Default All": 0,
        "Consume": 69,
    }

    def update_acl(self, op: str, rights: int, ids: List[str], propagate_to_children: bool = None,
                   denied: bool = None, inheritable: bool = None):
        """Updates the access control list for this entity, performs operation
        defined by the `op` parameter on all objects from `ids` list.

        Args:
            op (str): ACL update operator, available values are "ADD",
                "REMOVE" and "REPLACE"
            rights (int): value of rights to use by the operator
            ids (list of str): list of ids to update the acl on
            propagate_to_children (optional, bool): used for folder objects
                only,  default value is None, if set to True/False adds
                `propagateACLToChildren` keyword to the request body
                and sets its value accordingly
        """

        # TODO move (op, rights, ids, propagate_to_children=None,
        # denied=None, inheritable=None, types=None) to
        # separate AccesControlEntry class
        if op not in ["ADD", "REMOVE", "REPLACE"]:
            helper.exception_handler(
                "Wrong ACL operator passed. Please use ADD, REMOVE or REPLACE")

        if rights not in range(256) and rights not in range(536_870_912, 536_871_168):
            msg = ("Wrong `rights` value, please provide value in range 0-255, or to control "
                   "inheritability use value 536870912")
            helper.exception_handler(msg)

        if denied is None:
            denied = dict(zip(ids, [False] * len(ids)))

        if inheritable is None:
            inheritable = dict(zip(ids, [False] * len(ids)))

        body = {
            "acl": [{
                "op": op,
                "trustee": id,
                "rights": rights,
                "type": 1,
                "denied": denied.get(id),
                "inheritable": inheritable.get(id)
            } for id in ids]
        }

        if isinstance(propagate_to_children, bool):
            body["propagateACLToChildren"] = propagate_to_children

        objects.update_object(connection=self.connection, id=self.id, body=body,
                              type=self._OBJECT_TYPE.value)

    def update_acl_add(self, rights: int, ids: List[str], propagate_to_children: bool = None):
        """
        Args:
            rights (int): value of rights to use by the operator
            ids (list of str): list of ids to update the acl on
            propagate_to_children (optional, bool): used for folder objects
                only,  default value is None, if set to True/False adds
                `propagateACLToChildren` keyword to the request body
                and sets its value accordingly
        """
        self.update_acl(op="ADD", rights=rights, ids=ids,
                        propagate_to_children=propagate_to_children)

    def update_acl_remove(self, rights: int, ids: List[str], propagate_to_children: bool = None):
        """
        Args:
            rights (int): value of rights to use by the operator
            ids (list of str): list of ids to update the acl on
            propagate_to_children (optional, bool): used for folder objects
                only,  default value is None, if set to True/False adds
                `propagateACLToChildren` keyword to the request body
                and sets its value accordingly
        """
        self.update_acl(op="REMOVE", rights=rights, ids=ids,
                        propagate_to_children=propagate_to_children)

    def update_acl_replace(self, rights: int, ids: List[str], propagate_to_children: bool = None):
        """
        Args:
            rights (int): value of rights to use by the operator
            ids (list of str): list of ids to update the acl on
            propagate_to_children (optional, bool): used for folder objects
                only,  default value is None, if set to True/False adds
                `propagateACLToChildren` keyword to the request body
                and sets its value accordingly
        """
        self.update_acl(op="REPLACE", rights=rights, ids=ids,
                        propagate_to_children=propagate_to_children)

    # TODO make list_acl with df option
    def _parse_acl_rights_bin_to_dict(self, rights_bin: int):
        rights_map = [
            (128, "Execute"),
            (64, "Use"),
            (32, "Control"),
            (16, "Delete"),
            (8, "Write"),
            (4, "Read"),
            (2, "UseExecute"),
            (1, "Browse"),
        ]
        output = {}
        rights_map = sorted(rights_map, key=lambda x: -x[0])

        for value, right in rights_map:
            if rights_bin >= value:
                rights_bin -= value
                output[right] = True
            else:
                output[right] = False
        return output

    def _parse_acl_rights_dict_to_bin(self, rights_dict: dict):
        output = 0
        for key, value in rights_dict.items():
            if value:
                output += self.RIGHTS_MAP[key]
        return output

    def set_acl_by_dict(self, rights_dict: dict, ids: List[str]):
        rights = self._parse_acl_rights_dict_to_bin(rights_dict)
        self.update_acl(op='REPLACE', rights=rights, ids=ids)
        self.fetch(None)


def _modify_rights(connection, trustee_id, op: str, rights: int, object_type: int, ids: List[str],
                   application: Union[str,
                                      "Application"] = None, propagate_to_children: bool = None,
                   denied: bool = None, inheritable: bool = None, verbose: bool = True):
    if op not in ["ADD", "REMOVE", "REPLACE"]:
        helper.exception_handler("Wrong ACL operator passed. Please use ADD, REMOVE or REPLACE")

    if rights not in range(256) and rights not in range(536_870_912, 536_871_168):
        msg = ("Wrong `rights` value, please provide value in range 0-255, or to control "
               "inheritability use value 536870912")
        helper.exception_handler(msg)

    if application:
        application = application if isinstance(application, str) else application.id

    if isinstance(ids, str):
        ids = [ids]
    for id in ids:
        response = objects.get_object_info(connection=connection, id=id, type=object_type,
                                           application_id=application)
        if inheritable is None:
            tmp = [
                ace['inheritable']
                for ace in response.json().get('acl', [])
                if ace['trusteeId'] == trustee_id and ace['deny'] == denied
            ]
            if not tmp:
                inheritable = False
            else:
                inheritable = tmp[0]

        body = {
            "acl": [{
                "op": op,
                "trustee": trustee_id,
                "rights": rights,
                "type": 1,
                "denied": denied,
                "inheritable": inheritable
            }]
        }

        if isinstance(propagate_to_children, bool):
            body["propagateACLToChildren"] = propagate_to_children

        objects.update_object(connection=connection, id=id, body=body, type=object_type,
                              application_id=application, verbose=verbose)


def _get_custom_right_value(right: Union[str, List[str]]):
    custom_rights_map = {**EntityACL.RIGHTS_MAP}
    right_value = 0
    if isinstance(right, list):
        for r in right:
            if r not in custom_rights_map:
                msg = ("Invalid `right` value. Available values are: Execute, Use, Control, "
                       "Delete, Write, Read, Browse.")
                helper.exception_handler(msg)
            right_value += custom_rights_map[r]
    else:
        if right not in custom_rights_map:
            msg = ("Invalid custom `right` value. Available values are: Execute, Use, "
                   "Control, Delete, Write, Read, Browse.")
            helper.exception_handler(msg)
        right_value += custom_rights_map[right]
    return right_value


def _modify_custom_rights(connection, trustee_id, right: Union[str,
                                                               List[str]], to_objects: List[str],
                          object_type: int, denied: bool, application: Union[str,
                                                                             "Application"] = None,
                          default: bool = False, propagate_to_children: bool = None):
    right_value = _get_custom_right_value(right)
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE',
                       rights=right_value, ids=to_objects, object_type=object_type,
                       application=application, denied=(not denied),
                       propagate_to_children=propagate_to_children, verbose=False)
    except HTTPError:
        pass

    op = 'REMOVE' if default else 'ADD'
    verbose = False if default else True
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op=op, rights=right_value,
                       ids=to_objects, object_type=object_type, application=application,
                       denied=denied, propagate_to_children=propagate_to_children, verbose=verbose)
    except HTTPError:
        pass


def set_permission(connection, trustee_id, permission: str, to_objects: Union[str, List[str]],
                   object_type: int, application: Union[str, "Application"] = None,
                   propagate_to_children: bool = None):
    """Set permission to perform actions on given object(s).

    Function is used to set permission of the trustee to perform given actions
    on the provided objects. Within one execution of the function permission
    will be set in the same manner for each of the provided objects. The only
    available values of permission are: 'View', 'Modify', 'Full Control',
    'Denied All', 'Default All'. Permission is the predefined set of rights. All
    objects to which the rights will be given have to be of the same type which
    is also provided.

    Args:
        connection (Connection): connection to MicroStrategy I-Server
        trustee_id (int): identifier of entity which will (not) have rights
        permission (str): name of permission which defines set of rights.
            Available values are 'View', 'Modify', 'Full Control', 'Denied All',
            'Default All'.
        to_objects: (str, list(str)): list of object ids on access list to which
            the permissions will be set
        object_type (int): type of objects on access list
        application (str, Application): Object or id of Application in which the
            object is located. If not passed, Application (application_id)
            selected in Connection object is used.
        propagate_to_children: flag used in the request to determine if those
            rights will be propagated to children of the trustee
    Returns:
        None
    """

    permissions_map = {**EntityACL.AGGREGATED_RIGHTS_MAP}
    if permission not in permissions_map:
        msg = ("Invalid `permission` value. Available values are: 'View', "
               "'Modify', 'Full Control', 'Denied All', 'Default All'.")
        helper.exception_handler(msg)
    right_value = permissions_map[permission]
    if permission == 'Denied All':
        denied = True
    else:
        denied = False

    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE', rights=255,
                       ids=to_objects, object_type=object_type, application=application,
                       denied=(not denied), propagate_to_children=propagate_to_children,
                       verbose=False)
    except HTTPError:
        pass
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE', rights=255,
                       ids=to_objects, object_type=object_type, application=application,
                       denied=denied, propagate_to_children=propagate_to_children, verbose=False)
    except HTTPError:
        pass

    if not permission == "Default All":
        _modify_rights(connection=connection, trustee_id=trustee_id, op='ADD', rights=right_value,
                       ids=to_objects, object_type=object_type, application=application,
                       denied=denied, propagate_to_children=propagate_to_children)


def set_custom_permissions(connection, trustee_id, to_objects: Union[str,
                                                                     List[str]], object_type: int,
                           application: Union[str, "Application"] = None, execute: str = None,
                           use: str = None, control: str = None, delete: str = None,
                           write: str = None, read: str = None, browse: str = None):
    """Set custom permissions to perform actions on given object(s).

    Function is used to set rights of the trustee to perform given actions on
    the provided objects. Within one execution of the function rights will be
    set in the same manner for each of the provided objects. None of the rights
    is necessary, but if provided then only possible values are 'grant'
    (to grant right), 'deny' (to deny right), 'default' (to reset right) or None
    which is default value and means that nothing will be changed for this
    right. All objects to which the rights will be given have to be of the same
    type which is also provided.

    Args:
        connection (Connection): connection to MicroStrategy I-Server
        trustee_id (int): identifier of entity which will (not) have rights
        to_objects: (str, list(str)): list of object ids on access list to which
            the permissions will be set
        object_type (int): type of objects on access list
        application (str, Application): Object or id of Application in which the
            object is located. If not passed, Application (application_id)
            selected in Connection object is used.
        execute (str): value for right "Execute". Available are 'grant', 'deny',
            'default' or None.
        use (str): value for right "Use". Available are 'grant', 'deny',
            'default' or None.
        control (str): value for right "Control". Available are 'grant', 'deny',
            'default' or None.
        delete (str): value for right "Delete". Available are 'grant', 'deny',
            'default' or None.
        write  (str): value for right "Write". Available are 'grant', 'deny',
            'default' or None.
        read (str): value for right "Read". Available are 'grant', 'deny',
            'default' or None.
        browse (str): value for right "Browse. Available are 'grant', 'deny',
            'default' or None.
    Returns:
        None
    """
    rights_dict = {
        "Execute": execute,
        "Use": use,
        "Control": control,
        "Delete": delete,
        "Write": write,
        "Read": read,
        "Browse": browse
    }
    if not set(rights_dict.values()).issubset({'grant', 'deny', 'default', None}):
        helper.exception_handler(
            "Invalid value of the right. Available values are 'grant', 'deny', 'default' or None.")
    grant_list = [right for right, value in rights_dict.items() if value == 'grant']
    deny_list = [right for right, value in rights_dict.items() if value == 'deny']
    default_list = [right for right, value in rights_dict.items() if value == 'default']

    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=grant_list,
                          to_objects=to_objects, object_type=object_type, denied=False,
                          application=application)
    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=deny_list,
                          to_objects=to_objects, object_type=object_type, denied=True,
                          application=application)
    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=default_list,
                          to_objects=to_objects, object_type=object_type, denied=True,
                          application=application, default=True)
