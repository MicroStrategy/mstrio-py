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
from mstrio.types import ObjectTypes, ObjectSubTypes, ExtendedType  # noqa
from mstrio.utils import helper
from mstrio.utils.acl import ACE, ACLMixin, Rights
from mstrio.utils.dependence_mixin import DependenceMixin
from mstrio.utils.time_helper import bulk_str_to_datetime, DatetimeFormats, map_str_to_datetime

if TYPE_CHECKING:
    from mstrio.server import Project

T = TypeVar("T")


class EntityBase(helper.Dictable):
    """This class is for objects that do not have a specified MSTR type.

    Attributes:
        connection: A MicroStrategy connection object
        id: Object ID
        type: Object type set to None
        name: Object name
    """
    _OBJECT_TYPE: ObjectTypes = ObjectTypes.NONE  # MSTR object type defined in ObjectTypes
    _REST_ATTR_MAP: Dict[str, str] = {}
    _API_GETTERS: Dict[Union[str, tuple], Callable] = {}
    _FROM_DICT_MAP: Dict[str, Callable] = {
        'type': ObjectTypes
    }  # map attributes to Enums and Composites
    _AVAILABLE_ATTRIBUTES: Dict[str, type] = {}  # fetched on runtime from all Getters
    _API_PATCH: dict = {}
    _PATCH_PATH_TYPES: Dict[str, type] = {}  # used in update_properties method
    _API_DELETE: Callable = staticmethod(objects.delete_object)

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
        kwargs = self._rest_to_python(kwargs)
        # create _AVAILABLE_ATTRIBUTES map
        self._AVAILABLE_ATTRIBUTES.update({key: type(val) for key, val in kwargs.items()})
        self._connection = kwargs.get("connection")
        self._id = kwargs.get("id")
        self._type = self._OBJECT_TYPE if 'type' in self._FROM_DICT_MAP else kwargs.get(
            "type", self._OBJECT_TYPE)
        self.name = kwargs.get("name")
        self._altered_properties = dict()

    def fetch(self, attr: Optional[str] = None) -> None:  # NOSONAR
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
            param_value_dict = auto_match_args_entity(func, self)

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
    def _rest_to_python(cls, response: dict) -> dict:
        """Map REST API field names to Python API field names."""
        for rest_name, python_name in cls._REST_ATTR_MAP.items():
            if rest_name in response:
                old = response.pop(rest_name)
                if python_name:
                    response[python_name] = old
        return response

    @classmethod
    def _python_to_rest(cls, response: dict) -> dict:
        """Map Python API field names to REST API field names."""
        for rest_name, python_name in cls._REST_ATTR_MAP.items():
            if python_name and python_name in response:
                response[rest_name] = response.pop(python_name)
        return response

    def __construct_component(self, key, val):
        """Construct component instance using info in `self._FROM_DICT_MAP`"""

        if key in self._FROM_DICT_MAP:
            # determine which constructor will be used
            if isinstance(self._FROM_DICT_MAP[key], DatetimeFormats):
                val = map_str_to_datetime(key, val, self._FROM_DICT_MAP)
            elif isinstance(self._FROM_DICT_MAP[key], type(Enum)):
                val = self._FROM_DICT_MAP[key](val)
            elif isinstance(self._FROM_DICT_MAP[key], list) and val is not None:
                if isinstance(self._FROM_DICT_MAP[key][0], type(Enum)):
                    val = [self._FROM_DICT_MAP[key][0](v) for v in val]
                else:
                    val = [
                        self._FROM_DICT_MAP[key][0](source=v, connection=self.connection)
                        for v in val
                    ]
            else:
                val = self._FROM_DICT_MAP[key](source=val, connection=self.connection)

        return val

    def _set_object(self, **kwargs) -> None:
        """Set object attributes programmatically by providing keyword args.
        Support ENUMs and creating component objects."""

        object_info = helper.camel_to_snake(kwargs)
        object_info = self._rest_to_python(object_info)

        properties = set(
            (elem[0]
             for elem in inspect.getmembers(self.__class__, lambda x: isinstance(x, property))))

        for key, val in object_info.items():  # type: ignore
            # if self is a composite, create component instance
            val = self.__construct_component(key, val)

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
    def from_dict(cls: T, source: Dict[str, Any], connection: Connection,
                  to_snake_case: bool = True) -> T:
        """Instantiate an object from response without calling any additional
        getters."""
        obj = cls.__new__(cls)  # Does not call __init__
        object_source = helper.camel_to_snake(source) if to_snake_case else source
        obj._init_variables(connection=connection, **object_source)
        return obj

    def __str__(self):
        if self.__dict__.get("name"):
            return "{} object named: '{}' with ID: '{}'".format(self.__class__.__name__, self.name,
                                                                self.id)
        else:
            return "{} object with ID: '{}'".format(self.__class__.__name__, self.id)

    def __repr__(self):
        param_value_dict = auto_match_args_entity(self.__init__, self, exclude=['self'],
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
        elif isinstance(other, dict):
            # check all items in other dict equal entity object attributes
            return all(
                (getattr(self, k) == v if hasattr(self, k) else False for k, v in other.items()))
        else:
            return NotImplemented  # don't attempt to compare against unrelated types

    @classmethod
    def to_csv(  # NOSONAR
            cls: T, objects: Union[T, List[T]], name: str, path: Optional[str] = None,
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

    def __partial_put_body(self, attrs, camel_properties) -> dict:
        body = {}
        for name, value in camel_properties.items():
            if stringcase.snakecase(name) in attrs:
                value = self._obj_to_dict(name, value, camel_case=True)
                body[name] = self._validate_type(name, value)
        return body

    def __put_body(self, attrs, properties) -> dict:
        for name, value in properties.items():
            if name in attrs:
                setattr(self, name, self._validate_type(name, value))
        return self.to_dict()

    def __patch_body(self, attrs, camel_properties, op) -> dict:
        body = {"operationList": []}
        for name, value in camel_properties.items():
            if stringcase.snakecase(name) in attrs:
                value = self._obj_to_dict(name, value, camel_case=True)
                body['operationList'].append({
                    "op": op,
                    "path": "/{}".format(name),
                    "value": self._validate_type(name, value)
                })
        return body

    def _send_proper_patch_request(self, properties: dict, op: str = 'replace') -> List[bool]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships.

        Args:
            properties: dictionary of required changes
            op: operation type, 'replace' by default

        Returns:
            List of successful or unsuccessful requests.
        """
        changed = []
        camel_properties = helper.snake_to_camel(properties)
        for attrs, (func, func_type) in self._API_PATCH.items():
            if func_type == 'partial_put':
                body = self.__partial_put_body(attrs, camel_properties)
            elif func_type == 'put':  # Update using the generic update_object()
                body = self.__put_body(attrs, properties)
            elif func_type == 'patch':
                body = self.__patch_body(attrs, camel_properties, op)
            else:
                msg = f"{func} function is not supported by `_send_proper_patch_request`"
                raise NotImplementedError(msg)

            if not body:
                continue
            # send patch request from the specified update wrapper
            param_value_dict = auto_match_args_entity(func, self, exclude=["body"])
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
            if already_tracked:
                current_val = self._altered_properties[name][0]
            elif name in self.__dict__:
                current_val = self.__dict__[name]
            else:
                current_val = None
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

    def _set_dates(self, **kwargs):
        """Transform all date strings provided in kwargs to datetime object.
        Date format strings have to be provided in `_FROM_DICT_MAP`"""
        kwargs = bulk_str_to_datetime(kwargs, self._FROM_DICT_MAP)
        for key, val in self._FROM_DICT_MAP.items():
            if isinstance(val, DatetimeFormats):
                if kwargs.get(key):
                    setattr(self, key, kwargs.get(key))
                elif len(key) > 1 and key[0] == '_' and kwargs.get(key[1:]):
                    setattr(self, key, kwargs.get(key[1:]))

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


class Entity(EntityBase, ACLMixin, DependenceMixin):
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
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
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
         'ancestors', 'certified_info', 'acg', 'acl', 'comments', 'project_id', 'hidden',
         'target_info'): objects.get_object_info
    }
    _API_PATCH: dict = {
        ('name', 'description', 'abbreviation'): (objects.update_object, 'partial_put')
    }
    _PATCH_PATH_TYPES = {"name": str, "description": str, "abbreviation": str}
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'ext_type': ExtendedType,
        'date_created': DatetimeFormats.FULLDATETIME,
        'date_modified': DatetimeFormats.FULLDATETIME,
        'acl': [ACE.from_dict],
        'acg': Rights,
    }

    def _init_variables(self, **kwargs) -> None:
        """Initialize variables given kwargs."""
        from mstrio.users_and_groups.user import User
        from mstrio.utils.certified_info import CertifiedInfo
        super(Entity, self)._init_variables(**kwargs)
        self._date_created = map_str_to_datetime("date_created", kwargs.get("date_created"),
                                                 self._FROM_DICT_MAP)
        self._date_modified = map_str_to_datetime("date_modified", kwargs.get("date_modified"),
                                                  self._FROM_DICT_MAP)
        self.description = kwargs.get("description")
        self.abbreviation = kwargs.get("abbreviation")
        self._subtype = kwargs.get("subtype")
        self._ext_type = ExtendedType(kwargs["ext_type"]) if kwargs.get("ext_type") else None
        self._version = kwargs.get("version")
        self._owner = User.from_dict(
            kwargs.get("owner"),
            self.connection,
        ) if kwargs.get("owner") else None
        self._icon_path = kwargs.get("icon_path")
        self._view_media = kwargs.get("view_media")
        self._ancestors = kwargs.get("ancestors")
        self._certified_info = CertifiedInfo.from_dict(
            kwargs.get("certified_info"),
            self.connection) if kwargs.get("certified_info") else None
        self._hidden = kwargs.get("hidden")
        self._project_id = kwargs.get("project_id")
        self._comments = kwargs.get("comments")
        self._target_info = kwargs.get("target_info")
        self._acg = Rights(kwargs.get("acg")) if kwargs.get("acg") else None
        self._acl = ([ACE.from_dict(ac, self._connection) for ac in kwargs.get("acl")]
                     if kwargs.get("acl") else None)

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

    @property
    def hidden(self):
        return self._hidden

    @property
    def project_id(self):
        return self._project_id

    @property
    def comments(self):
        return self._comments

    @property
    def target_info(self):
        return self._target_info


class CopyMixin:
    """CopyMixin class adds creating copies of objects functionality.

    Currently project objects are not supported. Must be mixedin with
    Entity or its subclasses.
    """

    def create_copy(self: Entity, name: Optional[str] = None, folder_id: Optional[str] = None,
                    project: Optional[Union["Project", str]] = None) -> Any:
        """Create a copy of the object on the I-Server.

        Args:
            name: New name of the object. If None, a default name is generated,
                such as 'Old Name (1)'
            folder_id: ID of the destination folder. If None, the object is
                saved in the same folder as the source object.
            project: By default, the project selected when
                creating Connection object. Override `project` to specify
                project where the current object exists.

        Returns:
                New python object holding the copied object.
        """
        if self._OBJECT_TYPE.value in [32]:
            raise NotImplementedError("Object cannot be copied yet.")
        # TODO if object uniqueness depends on project_id extract proj_id
        # TODO automatically
        response = objects.copy_object(self.connection, id=self.id, name=name, folder_id=folder_id,
                                       object_type=self._OBJECT_TYPE.value, project_id=project)
        return self.from_dict(source=response.json(), connection=self.connection)


class DeleteMixin:
    """DeleteMixin class adds deleting objects functionality.
    Must be mixedin with Entity or its subclasses.
    """

    _delete_confirm_msg: Optional[str] = None
    _delete_success_msg: Optional[str] = None

    def delete(self: Entity, force: bool = False) -> bool:
        """Delete object.

        Args:
            force: If True, then no additional prompt will be shown before
                deleting object.

        Returns:
            True on success. False otherwise.
        """
        object_name = self.__class__.__name__

        user_input = 'N'
        if not force:
            message = self._delete_confirm_msg or (
                f"Are you sure you want to delete {object_name} "
                f"'{self.name}' with ID: {self._id}? [Y/N]: ")
            user_input = input(message) or 'N'
        if force or user_input == 'Y':
            param_value_dict = auto_match_args_entity(self._API_DELETE, self)
            response = self._API_DELETE(**param_value_dict)
            if response.status_code == 204 and config.verbose:
                print(self._delete_success_msg
                      or f"Successfully deleted {object_name} with ID: {self._id}.")
            return response.ok
        else:
            return False


class CertifyMixin:
    """CertifyMixin class adds certifying and decertifying functionality.
    Must be mixedin with Entity or its subclasses.
    """

    def _toggle_certification(self: Entity, certify: bool = True, success_msg: str = None) -> bool:
        object_name = self.__class__.__name__
        expected_result = 'certified' if certify else 'decertified'

        self.fetch()
        if certify == self.certified_info.certified:
            print(f"The {object_name} with ID: '{self._id}' is already {expected_result}")
            return True

        response = objects.toggle_certification(connection=self._connection, id=self._id,
                                                object_type=self._OBJECT_TYPE.value,
                                                certify=certify)
        if response.ok and config.verbose:
            self._set_object(**response.json())
            print(success_msg
                  or f"The {object_name} with ID: '{self._id}' has been {expected_result}.")
        return response.ok

    def certify(self: Entity) -> bool:
        """Certify object.
        Args:
           success_msg: Custom message displayed on success.
        Returns:
                True on success, False otherwise."""
        return self._toggle_certification(certify=True)

    def decertify(self: Entity) -> bool:
        """Decertify object.
        Args:
           success_msg: Custom message displayed on success.
        Returns:
                True on success, False otherwise."""
        return self._toggle_certification(certify=False)


class VldbMixin:
    """VLDBMixin class adds vldb management for supporting objects.

    Objects currently supporting VLDB settings are dataset, document, dossier.
    Must be mixedin with Entity or its subclasses.
    """
    _parameter_error = "Please specify the project parameter."

    def list_vldb_settings(self: Entity, project: Optional[str] = None) -> list:
        """List VLDB settings."""
        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        response = objects.get_vldb_settings(connection, self.id, self._OBJECT_TYPE.value, project)
        return response.json()

    def alter_vldb_settings(self: Entity, property_set_name: str, name: str, value: dict,
                            project: Optional[str] = None) -> None:
        """Alter VLDB settings for a given property set."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        body = [{"name": name, "value": value}]
        response = objects.set_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                             property_set_name, body, project)
        if config.verbose and response.ok:
            print("VLDB settings altered")

    def reset_vldb_settings(self: Entity, project: Optional[str] = None) -> None:
        """Reset VLDB settings to default values."""

        connection = self.connection if hasattr(self, 'connection') else self._connection
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        response = objects.delete_vldb_settings(connection, self.id, self._OBJECT_TYPE.value,
                                                project)
        if config.verbose and response.ok:
            print("VLDB settings reset to default")


def auto_match_args_entity(func: Callable, obj: EntityBase, exclude: list = [],
                           include_defaults: bool = True) -> dict:
    """Automatically match `obj` object data to function arguments.

    Handles default parameters. Extracts value from Enums. Returns matched
    arguments as dict.

    Args:
        function: function for which args will be matched
        obj: object to use for matching the function args
        exclude: set `exclude` parameter to exclude specific param-value pairs
        include_defaults: if `False` then values which have the same value as
            default will not be included in the result
    Raises:
        KeyError: could not match all required arguments
    """
    # convert names starting with '_'
    obj_dict = {key[1:] if key.startswith("_") else key: val for key, val in obj.__dict__.items()}
    kwargs = helper.auto_match_args(func, obj_dict, exclude, include_defaults)

    if "object_type" in kwargs:
        kwargs.update({"object_type": obj._OBJECT_TYPE.value})

    return kwargs
