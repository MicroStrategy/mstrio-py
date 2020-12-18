import csv
from copy import deepcopy
from enum import Enum
from pprint import pprint
from sys import version_info
from typing import List, Union, Tuple, Dict

import dictdiffer
from pandas import DataFrame
from requests import HTTPError

import mstrio.config as config
from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.utils import helper


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
    APPLICATION = 32
    USER = 34
    USERGROUP = 34
    CONFIGURATION = 36
    SECURITY_ROLE = 44
    CONSOLIDATION = 47
    DOCUMENT_DEFINITION = 55
    NONE = None


class EntityBase(object):
    """This class is for objects that do not have a specified MSTR type."""

    _OBJECT_TYPE = None
    _ENUM_MAP = {'type': ObjectTypes}
    _HIDDEN_ATTRIBUTES = ['connection']  # hidden attributes from object
    _AVAILABLE_ATTRIBUTES: Dict[str, type] = {}      # fetched on runtime from all Getters

    def __init__(self, connection: Connection, id: str, name: str) -> None:
        self.connection = connection
        self.id = id
        self.name = name
        self.type = ObjectTypes(self._OBJECT_TYPE).name
        if config.verbose:
            print(self)

    def list_properties(self) -> dict:
        """List all properties of the object."""
        return {key: self.__dict__[key] for key in sorted(self.__dict__, key=helper.sort_object_properties) if key not in self._HIDDEN_ATTRIBUTES and not key.startswith('_')}

    def to_dataframe(self) -> DataFrame:
        """Return a `DataFrame` object containing object properties."""
        return DataFrame.from_dict(self.list_properties(), orient='index', columns=['value'])

    @property
    def info(self) -> None:
        """Print all properties of the object."""
        if version_info.major >= 3 and version_info.minor >= 8:
            pprint(self.list_properties(), sort_dicts=False)
        else:
            pprint(self.list_properties())

    @classmethod
    def _from_bulk_response(cls, connection: Connection, response) -> list:
        """Instantiate list of objects from bulk 'get object requests' without
        calling any additional getters."""
        return [cls._from_single_response(connection, r) for r in response]

    @classmethod
    def _from_single_response(cls, connection: Connection, response):
        """Instantiate an object from response without calling any additional
        getters."""
        obj = cls.__new__(cls)  # Does not call __init__
        super(EntityBase, obj).__init__()  # call any polymorphic base class initializers
        super(EntityBase, obj).__setattr__("connection", connection)
        response = helper.camel_to_snake(response)
        if type(response) == dict:
            for key, value in response.items():
                cls._AVAILABLE_ATTRIBUTES.update({key: type(value)})
                value = cls._ENUM_MAP[key](value).name if cls._ENUM_MAP.get(key) else value
                super(EntityBase, obj).__setattr__(key, value)
        return obj

    def __str__(self):
        if hasattr(self, 'name') and self.name is not None:
            return "{} object named: '{}' with ID: '{}'".format(self.__class__.__name__, self.name, self.id)
        else:
            return "{} object with ID: '{}'".format(self.__class__.__name__, self.id)

    def __repr__(self):
        param_value_dict = helper.auto_match_args(self.__init__, self, exclude=['self'])
        params_list = []
        for param, value in param_value_dict.items():
            if param == 'connection':
                params_list.append("connection")
            elif value is not None:
                params_list.append(f"{param}='{value}'")
        formatted_params = ", ".join(params_list)
        return f"{self.__class__.__name__}({formatted_params})"

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


class Entity(EntityBase):
    """Base class representation of the MSTR object.

    Provides methods to fetch, update, and view the object. To implement
    this base class all class attributes have to be provided.
    """

    _API_GETTERS = {None: objects.get_object_info}
    _API_PATCH = [objects.update_object]
    _PATCH_PATH_TYPES: Dict[str, type] = {}          # used in update_properties method
    _SETTABLE_ATTRIBUTES: List[str] = []       # additional attributes which can be set
    _ALLOWED_ATTRIBUTES: List[str] = []        # used to lazy fetch object attributes
    _SUPPORTED_PATCH_OPERATIONS = {"add": "add", "remove": "remove", "change": "replace"}

    def __init__(self, connection: Connection, object_id: str) -> None:
        super().__setattr__("connection", connection)
        super().__setattr__("id", object_id)
        super().__setattr__("type", ObjectTypes(self._OBJECT_TYPE).name)
        self.fetch()    # fetch the object properties and set object attributes
        if config.verbose:
            print(self)

    def fetch(self, attr: str = None) -> None:
        """Fetch the latest object state from the I-Server.

        This will overwrite object attribute values by calling all REST
        API endpoints defining this object.
        """

        functions = self._API_GETTERS
        if attr:
            functions = {k: v for k, v in self._API_GETTERS.items() if k == attr}
            functions = functions if functions else self._API_GETTERS

        for key, func in functions.items():
            param_value_dict = helper.auto_match_args(func, self)
            response = func(**param_value_dict)
            if response.ok:
                response = response.json()
                response = helper.camel_to_snake(response)
                if type(response) == dict:
                    for k, v in response.items():
                        k = key if key and len(response) == 1 else k
                        # use keys and values to propagate AVAILABLE_ATTRIBUTES dict on runtime
                        self._AVAILABLE_ATTRIBUTES.update({k: type(v)})
                        # Check if any attributes need mapping from defined ENUMs
                        v = self._ENUM_MAP[k](v).name if self._ENUM_MAP.get(k) else v
                        super().__setattr__(k, v)
                if type(response) == list:
                    self._AVAILABLE_ATTRIBUTES.update({key: type(response)})
                    super().__setattr__(key, response)

    def is_modified(self, to_list: bool = False) -> Union[bool, list]:
        """Compare the current object to the object on I-Server.

        Args:
            to_list: If True, return a list of tuples with object differences
        """
        temp = deepcopy(self)
        temp.fetch()
        differences = list(dictdiffer.diff(temp.__dict__, self.__dict__))
        if len(differences) == 0:
            if config.verbose:
                print("There are no differences between local and remote '{}' object.".format(ObjectTypes(self.type).name))
            return differences if to_list else False
        else:
            return differences if to_list else True

    def update_properties(self) -> None:
        """Save compatible local changes of the object attributes to the
        I-Server."""

        body = {}
        changed_parameters = self.is_modified(to_list=True)
        supported_changes = list(filter(lambda diff: (diff[1][0] if type(diff[1]) == list else diff[1])
                                        in self._PATCH_PATH_TYPES.keys(), changed_parameters))
        if supported_changes == [] and config.verbose:
            print("The object is already up to date.")
        else:
            func = self._API_PATCH[0]
            if func == objects.update_object:   # Update using the generic update_object()
                for operation, path, value in supported_changes:
                    value = [value[0][1]] if type(value) == list else value[1]
                    body[path] = value
            else:       # Update using different update method, if one was specified
                body = {"operationList": []}
                for operation, path, value in supported_changes:

                    mstr_op = self._SUPPORTED_PATCH_OPERATIONS.get(operation)
                    value = [value[0][1]] if type(value) == list else value[1]
                    # check if the value to be added or removed already exists to avoid I-Server error
                    body['operationList'].append({"op": mstr_op,
                                                  "path": "/{}".format(path),
                                                  "value": value})

            # send patch request from the specified update wrapper
            param_value_dict = helper.auto_match_args(func, self)
            param_value_dict['body'] = body
            try:
                response = func(**param_value_dict)
            except HTTPError as e:
                self.fetch()
                raise e
            if response.ok:
                response = response.json()
                if type(response) == dict:
                    for key, value in response.items():
                        super().__setattr__(key, value)
                if config.verbose:
                    print("Successfully updated '{}' properties:\n".format(self.name))
                    for op, path, value in supported_changes:
                        print("{} - {}: {} -> {}".format(path, op, value[0], value[1]))
                    print("")

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
            helper.exception_handler(
                'The file extension is different than ".csv", please note that using a different extension might disrupt opening the file correctly.', exception_type=Warning)
        if isinstance(objects, cls):
            properties = objects.list_properties().keys() if properties is None else properties
            list_of_objects.append(
                {key: value for key, value in objects.list_properties().items() if key in properties})
        elif isinstance(objects, list):
            properties = objects[0].list_properties().keys() if properties is None else properties
            for obj in objects:
                if isinstance(obj, cls):
                    list_of_objects.append(
                        {key: value for key, value in obj.list_properties().items() if key in properties})
                else:
                    helper.exception_handler("Object '{}' of type '{}' is not supported.".format(obj, type(obj)),
                                             exception_type=Warning, throw_error=False)
        else:
            helper.exception_handler("Objects should be of type {} or list of {}.".format(ObjectTypes(
                cls._OBJECT_TYPE).name, ObjectTypes(cls._OBJECT_TYPE).name), exception_type=TypeError)

        with open(file, 'w') as f:
            fieldnames = list_of_objects[0].keys()
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(list_of_objects)
        if config.verbose:
            print("Object exported successfully to '{}'".format(file))

    def create_copy(self, name: str = None, folder_id: str = None):
        """Create a copy of the object on the I-Server.

        Args:
            name: New name of the object. If None, a default name is generated,
                such as 'Old Name (1)'
            folder_id: ID of the destination folder. If None, the object is
                saved in the same folder as the source object.

        Returns:
             copy of the object
        """
        if self._OBJECT_TYPE not in []:
            helper.exception_handler("'{}' object cannot be copied at this time.".format(
                self.type), exception_type=NotImplementedError)
        response = objects.copy_object(self.connection, id=self.id, name=name,
                                       folder_id=folder_id, type=self._OBJECT_TYPE)
        return self._from_single_response(self.connection, response)

    def _alter_properties(self, **properties):
        """Generic alter method that has to be implemented in child classes
        where arguments will be specified."""
        body = {}
        func = self._API_PATCH[0]
        properties = helper.snake_to_camel(properties)

        if func == objects.update_object:   # Update using the generic update_object()
            for property, value in properties.items():
                body[property] = self._validate_type(property, value)
        else:       # Update using different update method, if one was specified
            body = {"operationList": []}
            for property, value in properties.items():
                body['operationList'].append({"op": "replace",
                                              "path": "/{}".format(property),
                                              "value": self._validate_type(property, value)})

        # send patch request from the specified update wrapper
        param_value_dict = helper.auto_match_args(func, self)
        param_value_dict['body'] = body
        response = func(**param_value_dict)

        if response.ok:
            if config.verbose:
                print("{} '{}' has been modified.".format(type(self).__name__, self.name))
            response = response.json()
            if type(response) == dict:
                response = helper.camel_to_snake(response)
                for key, value in response.items():
                    super().__setattr__(key, value)

    def _update_nested_properties(self, objects, path: str, op: str, existing_ids: List[str] = None) -> Tuple[str, str]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships.

        Returns:
            IDs of succeeded and failed operations by filtering by existing IDs.
        """
        from mstrio.admin.privilege import Privilege
        # check whether existing_ids are supplied
        if existing_ids is None:
            existing_ids = [obj.get('id') for obj in self.__dict__[path]]

        # create list of objects from strings/objects/lists
        objects_list = objects if isinstance(objects, list) else [objects]
        object_map = {obj.id: obj.name for obj in objects_list if isinstance(obj, Entity)}

        object_ids_list = [obj.id if isinstance(obj, (Entity, Privilege)) else str(obj) for obj in objects_list]

        # check if objects can be manipulated by comparing to existing values
        if op == "add":
            filtered_object_ids = sorted(list(filter(lambda x: x not in existing_ids, object_ids_list)))
        elif op == "remove":
            filtered_object_ids = sorted(list(filter(lambda x: x in existing_ids, object_ids_list)))

        if filtered_object_ids:
            body = {"operationList": [{"op": op,
                                       "path": '/{}'.format(path),
                                       "value": filtered_object_ids}]}
            res = self._API_PATCH[0](self.connection, self.id, body)
            if type(res.json()) == dict:
                for key, value in res.json().items():
                    super(Entity, self).__setattr__(key, value)

        failed = list(sorted(set(object_ids_list) - set(filtered_object_ids)))
        failed_formatted = [object_map.get(object_id, object_id) for object_id in failed]
        succeeded_formatted = [object_map.get(object_id, object_id) for object_id in filtered_object_ids]

        return (succeeded_formatted, failed_formatted)

    def _validate_type(self, name, value):
        """Validates whether the attribute is set using correct type.

        Raises:
            TypeError if incorrect.
        """
        type_map = {**self._PATCH_PATH_TYPES, **self._AVAILABLE_ATTRIBUTES}
        value_type = type_map.get(name, 'Not Found')
        if value_type != 'Not Found':
            if type(value) != value_type:
                helper.exception_handler("'{}' has incorrect type. Expected type: '{}'".format(name, value_type),
                                         exception_type=TypeError)
        return value

    def __setattr__(self, name, value):
        """Overloads the __setattr__ method to validate if this attribute can
        be set for current object and verify value data types."""
        valid_attr = list(self._AVAILABLE_ATTRIBUTES.keys()) + list(self._PATCH_PATH_TYPES.keys()) + list(self._SETTABLE_ATTRIBUTES)
        mutable_attr = list(self._PATCH_PATH_TYPES.keys()) + self._SETTABLE_ATTRIBUTES

        # test if attribute name exists
        if name in valid_attr:
            if name in mutable_attr:
                super(Entity, self).__setattr__(name, self._validate_type(name, value))
            else:
                helper.exception_handler("Attribute '{}' is immutable and cannot be changed. Mutable attributes are {}".format(
                    name, mutable_attr), exception_type=AttributeError)
        else:
            helper.exception_handler("Attribute '{}' is not allowed to be set for object of type '{}'".format(
                name, ObjectTypes(self._OBJECT_TYPE).name), exception_type=AttributeError)

    def __getattr__(self, name):
        """Overloads the __getattr__ method to allow for lazy fetching of
        particular object attributes if missing."""
        if name in self._ALLOWED_ATTRIBUTES:
            self.fetch(name)            # fetch the relevant object data
        res = self.__dict__.get(name)   # check if the attribute is now available
        if res is not None:
            return res                  # return if available
        else:
            raise AttributeError("{} object has no attribute '{}'".format(self.__class__.__name__, name))


class Vldb(object):
    """Adds VLDB management for object.

    Objects supporting VLDB settings are dataset, document, dossier.
    Requires implementation of EntityBase. Needs to be implemented
    together with BaseEntity class.
    """

    def list_vldb_settings(self, application: str = None):
        """List VLDB settings."""

        if not application and self.connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        response = objects.get_vldb_settings(self.connection, self.id, self._OBJECT_TYPE, application)
        return response.json()

    def alter_vldb_settings(self, property_set_name: str, name: str, value: dict, application: str = None):
        """Alter VLDB settings for a given property set."""

        if not application and self.connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        body = [{"name": name,
                 "value": value
                 }]
        response = objects.set_vldb_settings(self.connection, self.id, self._OBJECT_TYPE, property_set_name, body, application)
        if config.verbose and response.ok:
            print("VLDB settings altered")

    def reset_vldb_settings(self, application: str = None):
        """Reset VLDB settings to default values."""

        if not application and self.connection.session.headers.get('X-MSTR-ProjectID') is None:
            raise ValueError("Please specify the application parameter.")

        response = objects.delete_vldb_settings(self.connection, self.id, self._OBJECT_TYPE, application)
        if config.verbose and response.ok:
            print("VLDB settings reset to default")


class EntityACL(Entity):
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
        #                    denied=None, inheritable=None, types=None) to separate AccesControlEntry class
        if op not in ["ADD", "REMOVE", "REPLACE"]:
            helper.exception_handler(
                "Wrong ACL operator passed. Please use ADD, REMOVE or REPLACE"
            )

        if rights not in range(256) and rights not in range(536_870_912, 536_871_168):
            helper.exception_handler(
                "Wrong `rights` value, please provide value in range 0-255, or to control inheritability use value 536870912")

        if denied is None:
            denied = dict(zip(ids, [False] * len(ids)))

        if inheritable is None:
            inheritable = dict(zip(ids, [False] * len(ids)))

        body = {
            "acl": [
                {
                    "op": op,
                    "trustee": id,
                    "rights": rights,
                    "type": 1,
                    "denied": denied.get(id),
                    "inheritable": inheritable.get(id)
                }

                for id in ids
            ]
        }

        if isinstance(propagate_to_children, bool):
            body["propagateACLToChildren"] = propagate_to_children

        objects.update_object(connection=self.connection, id=self.id, body=body,
                              type=self._OBJECT_TYPE)

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
                   propagate_to_children: bool = None, denied: bool = None,
                   inheritable: bool = None, verbose: bool = True):
    if op not in ["ADD", "REMOVE", "REPLACE"]:
        helper.exception_handler(
            "Wrong ACL operator passed. Please use ADD, REMOVE or REPLACE"
        )

    if rights not in range(256) and rights not in range(536_870_912, 536_871_168):
        helper.exception_handler(
            "Wrong `rights` value, please provide value in range 0-255, or to control inheritability use value 536870912")

    if isinstance(ids, str):
        ids = [ids]
    for id in ids:
        response = objects.get_object_info(connection=connection,
                                           id=id, type=object_type)
        if inheritable is None:
            tmp = [ace['inheritable']
                   for ace in response.json().get('acl', []) if
                   ace['trusteeId'] == trustee_id and
                   ace['deny'] == denied]
            if not tmp:
                inheritable = False
            else:
                inheritable = tmp[0]

        body = {
            "acl": [
                {
                    "op": op,
                    "trustee": trustee_id,
                    "rights": rights,
                    "type": 1,
                    "denied": denied,
                    "inheritable": inheritable
                }
            ]
        }

        if isinstance(propagate_to_children, bool):
            body["propagateACLToChildren"] = propagate_to_children

        objects.update_object(connection=connection, id=id, body=body,
                              type=object_type, verbose=verbose)


def _get_custom_right_value(right: Union[str, List[str]]):
    custom_rights_map = {**EntityACL.RIGHTS_MAP}
    right_value = 0
    if isinstance(right, list):
        for r in right:
            if r not in custom_rights_map:
                helper.exception_handler(
                    "Invalid `right` value. Available values are: Execute, Use, Control, Delete, Write, Read, Browse.")
            right_value += custom_rights_map[r]
    else:
        if right not in custom_rights_map:
            helper.exception_handler(
                "Invalid custom `right` value. Available values are: Execute, Use, Control, Delete, Write, Read, Browse.")
        right_value += custom_rights_map[right]
    return right_value


def _modify_custom_rights(connection, trustee_id, right: Union[str, List[str]], to_objects: List[str],
                          object_type: int, denied: bool, default: bool = False,
                          propagate_to_children: bool = None):
    right_value = _get_custom_right_value(right)
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE', rights=right_value,
                       ids=to_objects, object_type=object_type, denied=(not denied),
                       propagate_to_children=propagate_to_children, verbose=False)
    except HTTPError:
        pass

    op = 'REMOVE' if default else 'ADD'
    verbose = False if default else True
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op=op, rights=right_value,
                       ids=to_objects, object_type=object_type, denied=denied,
                       propagate_to_children=propagate_to_children, verbose=verbose)
    except HTTPError:
        pass


def set_permission(connection, trustee_id, permission: str, to_objects: Union[str, List[str]],
                   object_type: int, propagate_to_children: bool = None):
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
        propagate_to_children: flag used in the request to determine if those
            rights will be propagated to children of the trustee
    Returns:
        None
    """

    permissions_map = {**EntityACL.AGGREGATED_RIGHTS_MAP}
    if permission not in permissions_map:
        helper.exception_handler(
            "Invalid `permission` value. Available values are: 'View', 'Modify', 'Full Control', 'Denied All', 'Default All'.")
    right_value = permissions_map[permission]
    if permission == 'Denied All':
        denied = True
    else:
        denied = False

    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE', rights=255,
                       ids=to_objects, object_type=object_type, denied=(not denied),
                       propagate_to_children=propagate_to_children, verbose=False)
    except HTTPError:
        pass
    try:
        _modify_rights(connection=connection, trustee_id=trustee_id, op='REMOVE', rights=255,
                       ids=to_objects, object_type=object_type, denied=denied,
                       propagate_to_children=propagate_to_children, verbose=False)
    except HTTPError:
        pass

    if not permission == "Default All":
        _modify_rights(connection=connection, trustee_id=trustee_id, op='ADD', rights=right_value,
                       ids=to_objects, object_type=object_type, denied=denied,
                       propagate_to_children=propagate_to_children)


def set_custom_permissions(connection, trustee_id, to_objects: Union[str, List[str]],
                           object_type: int, execute: str = None,
                           use: str = None, control: str = None,
                           delete: str = None, write: str = None,
                           read: str = None, browse: str = None):
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
            "Invalid value of the right. Available values are 'grant', 'deny', 'default' or None."
        )
    grant_list = [right for right, value in rights_dict.items() if value == 'grant']
    deny_list = [right for right, value in rights_dict.items() if value == 'deny']
    default_list = [right for right, value in rights_dict.items() if value == 'default']

    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=grant_list,
                          to_objects=to_objects, object_type=object_type, denied=False)
    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=deny_list,
                          to_objects=to_objects, object_type=object_type, denied=True)
    _modify_custom_rights(connection=connection, trustee_id=trustee_id, right=default_list,
                          to_objects=to_objects, object_type=object_type, denied=True, default=True)
