import csv
import inspect
import logging
from collections.abc import Callable
from enum import Enum
from os.path import join as joinpath
from pprint import pprint
from sys import version_info
from typing import TYPE_CHECKING, Any, TypeVar

import humps
from pandas import DataFrame

from mstrio import config
from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.helpers import NotSupportedError, Rights, VersionException
from mstrio.types import MISSING, ExtendedType, ObjectSubTypes, ObjectTypes
from mstrio.utils import helper
from mstrio.utils.acl import ACE, ACLMixin
from mstrio.utils.dependence_mixin import DependenceMixin
from mstrio.utils.helper import (
    get_response_json,
    get_valid_project_id,
    rename_dict_keys,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.time_helper import (
    DatetimeFormats,
    bulk_str_to_datetime,
    map_str_to_datetime,
)
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import method_version_handler

if TYPE_CHECKING:
    from mstrio.object_management import Folder, Shortcut
    from mstrio.server import Project

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EntityBase(helper.Dictable):
    """This class is for objects that do not have a specified Strategy One type.

    Class attributes:
    _OBJECT_TYPE (ObjectTypes): Strategy One Object type defined in ObjectTypes
    _OBJECT_SUBTYPES (list[ObjectSubTypes] | None): Strategy One Object subtype
        defined in ObjectSubTypes. It contains a list of subtypes, which the
        class supports. Used in fetch(), to verify whether the retrieved object
        is supported. None means that subtype won't be verified.
    _REST_ATTR_MAP (Dict[str, str]): A dictionary whose keys are names of
        fields of an HTTP response from the server, and values are their
        respective Python API mappings. This dictionary is mainly used when
        overriding `_init_variables` function to convert field names to
        attribute names before the object's attributes initialization. For
        example, if a value of the `job_type` field should be stored in a 'type'
        attribute, one can specify this dictionary as: {"job_type" : "type"} and
        override `_init_variables` method to implement this mapping such as:
         ```
            kwargs = self._rest_to_python(kwargs)
            self._AVAILABLE_ATTRIBUTES.update({key: type(val) for key, val
                in kwargs.items()})
            # init logic follows
        ```
    _API_GETTERS (dict[str | tuple, Callable]): A dictionary whose keys
        are either a name of an attribute (as a string) or names of attributes
        (as a tuple), and values are the REST API wrapper functions used to
        fetch related data from a server. For example:
        {'id': objects.get_object_info} or
        {('id', 'name', 'description): objects.get_object_info}
    _FROM_DICT_MAP (dict[str, Callable]): A dictionary whose keys are
        attribute's name and values are the attribute's type. This mapping is
        required to determine a proper composite form in which a value will be
        stored (such as an Enum, list of Enums etc.). Therefore, only attributes
        with composite and not primitive data types should be included here.
    _AVAILABLE_ATTRIBUTES (dict[str, type]): A dictionary which keys are
        object's attribute names as strings, and which values are types of
        attributes value. It is used for validating attribute's type during the
        process of properties update. This dictionary is created from keyword
        arguments passed to an object's constructor.
    _API_PATCH (dict[tuple[str], tuple[Callable | str]]): A dictionary
        whose keys are tuples with an object's attribute names as strings, and
        values are tuples with two elements: first element is a REST API wrapper
        function used to update the object's properties, and the second element
        is a definition (as a string) how this update should be performed. For
        example:
        {('name', 'description', 'abbreviation'):
            (objects.update_object, 'partial_put')}
    _PATCH_PATH_TYPES (dict[str, type]): A dictionary whose keys are names of
        object's attributes and values are attribute types. Used to
        validate correctness of a new value during the process of properties
        update. For example: {'id': str, 'enabled': bool}
    _API_DELETE(Callable): A function which is used to delete an object from the
        server. Defaults to staticmethod(objects.delete_object).


    Instance attributes:
        connection (Connection): A Strategy One connection object
        id (str): Object's ID
        type (ObjectTypes): Strategy One Object Type
        name (str): Object's name
        _altered_properties (dict): This is a private attribute which is used to
            track and validate local changes to the object. It is used whenever
            an attribute is trying to be set on the object (see `__setattr__`).
            It is also used to determine which properties should be updated on
            a server (see `update_properties`)
        _fetched_attributes (set): This is a private attribute which is used to
            track which attributes have been already fetched from the server.
            The logic of `__getattribute__` method is based on information
            in this set.
        subtype (ObjectSubTypes): The enumeration constant used to specify the
            object's sub-type, which reveals more specific information than the
            object's type.
        ext_type (ExtendedType): A part of an object stored in the metadata.
            It is used is to store additional custom information that can be
            used to achieve new functionality. For example, to display a report
            as a map and save it as part of the Report object, you can create an
            extended property for displaying a report as a map and store it on
            a server in the object's properties set.
        date_created (DatetimeFormats): The object's creation time.
        date_modified (DatetimeFormats): The object's last modification time.
        version (str): The object's version ID. Used to compare if two Strategy
            One objects are identical. If both objects IDs and objects version
            IDs are the same, Strategy One Object Manager determines that
            objects as 'Exists Indentically'. Otherwise, if their IDs match
            but their version IDs mismatch, Strategy One Object Manager
            determines that objects 'Exists Differently'.
        owner (User): The object's owner information.
        icon_path (str): A path to a location where the object's icon is stored.
        view_media (int): The enumeration constant used to represent the default
            mode of a RSD or a dashboard, and available modes of a RSD or a
            dashboard.
        ancestors (list[dict]): A list of the object's ancestor folders.
        certified_info (CertifiedInfo): The object's certification status,
            time of certification, and information about the certifier
            (currently only for document and report)
        acg (Rights): The enumeration constant used to specify the access
            granted attribute of the object.
        acl (list[ACE]): A list of permissions on the object so that users, or
            user groups have control over individual objects in the system.
            Those permissions decide whether or not a user can perform a
            particular class of operations on a particular object. For example,
            a user may have permissions to view and execute a report , but
            cannot modify the report definition or delete the report.
        hidden (bool): Determines whether the object is hidden on a server.
        project_id (str): The ID of a project in which the object resides.
        comments (list[str]): Custom user's comments related to the object
        target_info (dict): ?
    """

    _OBJECT_TYPE: ObjectTypes = (
        ObjectTypes.NOT_SUPPORTED
    )  # Strategy One object type defined in ObjectTypes
    _OBJECT_SUBTYPES: list[ObjectSubTypes] | None = (
        None  # None means subtype won't be verified.
    )
    _REST_ATTR_MAP: dict[str, str] = {}
    _API_GETTERS: dict[str | tuple, Callable] = {}
    _FROM_DICT_MAP: dict[str, Callable] = {
        'type': ObjectTypes
    }  # map attributes to Enums and Composites
    _AVAILABLE_ATTRIBUTES: dict[str, type] = {}  # fetched on runtime from all Getters
    _API_PATCH: dict[tuple[str], tuple[Callable | str]] = {}
    _PATCH_PATH_TYPES: dict[str, type] = {}  # used in update_properties method
    _API_DELETE: Callable = staticmethod(objects.delete_object)
    _WITH_MISSING_VALUE: bool = False

    def __init__(
        self, connection: Connection, object_id: str, default_value=None, **kwargs
    ) -> None:
        self._init_variables(
            connection=connection, id=object_id, default_value=default_value, **kwargs
        )
        if config.fetch_on_init and self._find_func("id") is not None:
            self.fetch("id")
        if config.verbose:
            logger.info(self)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        """Initializes object's attributes from kwargs. This method is often
        overridden by subclasses of Entity / EntityBase to abstract the process
        of initialization as it automatically sets attributes mutual for all
        entities, adds information about object-specific attributes to
        `_AVAILABLE_ATTRIBUTES` dictionary and creates a `_altered_properties`
        dictionary which is used to track and validate any local
        changes to the object. `_altered_properties` is later used to
        properly update object's properties on a server.

        Note: attributes not accepted by any implementation of this function
            in the inheritance chain will be disregarded.
        """
        kwargs = self._rest_to_python(kwargs)
        # create _AVAILABLE_ATTRIBUTES map
        self._AVAILABLE_ATTRIBUTES.update(
            {key: type(val) for key, val in kwargs.items()}
        )
        self._connection = kwargs.get("connection")
        self._id = kwargs.get("id", default_value)
        self._type = (
            self._OBJECT_TYPE
            if 'type' in self._FROM_DICT_MAP
            else kwargs.get("type", self._OBJECT_TYPE)
        )
        self.name = kwargs.get("name", default_value)
        self._altered_properties = {}

    def fetch(self, attr: str | None = None) -> None:  # NOSONAR
        """Fetch the latest object's state from the I-Server.

        Note:
            This method can overwrite local changes made to the object.

        Args:
            attr (Optional[str]): Attribute name to be fetched. If not specified
            it will use all getters specified in `_API_GETTERS` dictionary.
            Defaults to None.
        Raises:
            ValueError: If `attr` cannot be fetched.
        """
        functions = self._API_GETTERS  # by default fetch all endpoints

        if (
            attr is not None
        ):  # if attr is specified fetch endpoint matched to the attribute name
            function_ = self._find_func(attr)
            if not function_:
                raise ValueError(
                    f"The attribute `{attr}` cannot be fetched for this object"
                )
            else:
                functions = {
                    attr: func for attr, func in functions.items() if func == function_
                }

        for key, func in functions.items():  # call respective API getters
            param_value_dict = auto_match_args_entity(func, self)

            try:
                response = func(**param_value_dict)
            except VersionException:
                logger.error(
                    'Cannot fetch attribute "%s" due to minimum required '
                    'IServer version not being met',
                    key,
                )
                continue

            if response:
                json = (
                    response
                    if isinstance(response, (dict, list))
                    else get_response_json(response)
                )

                # In some cases the endpoint does not include subtype in
                # response. We can skip the subtype check, because in cases
                # where subtype must be populated, it is included (and checked
                # for) in one of the _API_GETTERS.
                if (
                    self._OBJECT_SUBTYPES
                    and 'subtype' in json
                    and (subtype := json['subtype'])
                ):
                    self._check_object_subtype(subtype)
                if isinstance(json, dict):
                    object_dict = {
                        key if isinstance(key, str) and len(json) == 1 else k: v
                        for k, v in json.items()
                    }

                    if self._WITH_MISSING_VALUE:
                        self._add_missing_attributes(key, json)

                    self._set_object_attributes(**object_dict)
                elif isinstance(json, list):
                    self._set_object_attributes(**{key: json})

            # keep track of fetched attributes
            self._add_to_fetched(key)

    @classmethod
    def _check_object_subtype(cls, subtype: int) -> None:
        """Check if subtype is supported by a class.

        Args:
            subtype(int): number representing object's subtype.

        Returns:
            None

        Raises:
            NotSupportedError: If subtype is not in _OBJECT_SUBTYPES list.
        """
        if cls._OBJECT_SUBTYPES and not cls._is_subtype_supported(subtype):
            raise NotSupportedError(
                f"Objects with subtype {ObjectSubTypes(subtype) !r} are not supported."
            )

    @classmethod
    def _is_subtype_supported(cls, subtype: int) -> bool:
        """Check if subtype is supported by a class.

        Args:
            subtype (int): number representing object's subtype.

        Returns:
            True if subtype is supported by class.
            False if subtype is not supported.
        """
        return subtype in [item.value for item in cls._OBJECT_SUBTYPES]

    def _add_missing_attributes(self, key, json) -> None:
        # Set the keys that are missing in the response to None
        expected_keys = {key} if isinstance(key, str) else {*key}
        response_dict = self._rest_to_python(helper.camel_to_snake(json))
        received_keys = response_dict.keys()
        missing_keys = expected_keys - received_keys - self._fetched_attributes

        if missing_keys:
            properties = helper.get_object_properties(self)
            for key in missing_keys:
                name = f'_{key}' if key in properties else key
                self.__setattr__(name, None)

    def _add_to_fetched(self, keys: str | tuple) -> None:
        """Adds name/-s of attribute/-s to the `_fetched_attributes` set.

        Args:
            keys (str | tuple): Name, or tuple with names of attributes.
        """
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            key = key[1:] if key.startswith("_") else key
            self._fetched_attributes.add(key)

    @classmethod
    def _find_func(cls, attr: str) -> Callable | None:
        """Searches cls._API_GETTERS dictionary for a REST API wrapper function
        used to fetch `attr` from a server.

        Args:
            attr (str): Name of an attribute to be fetched from the server.

        Raises:
            TypeError: `attr` not passed as a string.
            ValueError: cls._API_GETTERS dictionary was not specified
            properly.

        Returns:
            Optional[Callable]: REST API wrapper function corresponding with
                `attr` parameter, else None.
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
                raise ValueError
        return None

    @classmethod
    def _rest_to_python(cls, response: dict) -> dict:
        """Map REST API field names to Python API field names as specified in
        cls._REST_ATTR_MAP.

        Args:
            response (dict): A dictionary representing an HTTP response.

        Returns:
            dict: A dictionary with field names converted to Python API names.
        """

        return rename_dict_keys(response, cls._REST_ATTR_MAP)

    @classmethod
    def _python_to_rest(cls, request_body: dict) -> dict:
        """Map Python API field names to REST API field names as specified in
        cls._REST_ATTR_MAP.

        Args:
            request_body (dict): A dictionary representing an HTTP request body.

        Returns:
            dict: A dictionary with field names converted to REST API names.
        """
        body = request_body.copy()
        for rest_name, python_name in cls._REST_ATTR_MAP.items():
            if python_name in body:
                body[rest_name] = body.pop(python_name)
        return body

    def __compose_val(self, key: str, val: Any) -> Any:
        """Converts a value to a correct composite form such as Datetime, Enum,
        list of Enums etc. Information about the correct form of the value is
        stored in the `self._FROM_DICT_MAP`

        Args:
            key (str): An object's attribute name used to determine the correct
                form of a value.
            val (Any): A value which will be converted to a correct form
        Returns:
            Any: A value converted to a correct form.
        """
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
                        self._FROM_DICT_MAP[key][0](
                            source=v, connection=self.connection
                        )
                        for v in val
                    ]
            elif val == {}:
                return None
            else:
                val = self._FROM_DICT_MAP[key](source=val, connection=self.connection)

        return val

    def _set_object_attributes(self, **kwargs) -> None:
        """Set object's attributes programmatically by providing keyword args.
        Support ENUMs and creating composites. This function inspects whether
        the attribute was set as a property, and if yes it stores the attribute
        with '_' prefix"""

        object_info = helper.camel_to_snake(kwargs, whitelist=self._KEEP_CAMEL_CASE)
        object_info = self._rest_to_python(object_info)

        # determine which attributes should be private
        properties = helper.get_object_properties(self)

        for key, val in object_info.items():  # type: ignore
            # update _AVAILABLE_ATTRIBUTES map
            self._AVAILABLE_ATTRIBUTES.update({key: type(val)})

            # if self is a composite, create component instance
            val = self.__compose_val(key, val)

            # check if attr is read-only and if yes return '_' version of it
            if key in properties:
                key = "_" + key

            setattr(self, key, val)

    def list_properties(self, excluded_properties: list[str] | None = None) -> dict:
        """Fetches all attributes from the server and converts all properties of
        the object to a dictionary.

        Args:
            excluded_properties (list[str], optional): A list of
                object properties that should be excluded from the dict.
                Defaults to None.

        Returns:
            dict: A dictionary which keys are object's attribute names, and
                which values are object's attribute values.
        """
        if hasattr(self, "_API_GETTERS"):  # fetch attributes not loaded on init
            attr = [attr for attr in self._API_GETTERS.keys() if isinstance(attr, str)]
            for key in self._API_GETTERS.keys():
                if isinstance(key, tuple):
                    attr += list(key)
            attr += [
                element[0]
                for element in inspect.getmembers(
                    self.__class__, lambda x: isinstance(x, property)
                )
            ]
            attr = list(set(attr))
            excluded_properties = excluded_properties or []
            for a in attr:
                try:
                    getattr(self, a)
                except (VersionException, AttributeError, NotSupportedError):
                    if isinstance(a, list):
                        excluded_properties += a
                    else:
                        excluded_properties.append(a)
        properties = inspect.getmembers(
            self.__class__,
            lambda x: isinstance(x, property)
            and x.fget.__name__ not in excluded_properties,
        )
        properties = {elem[0]: elem[1].fget(self) for elem in properties}
        attributes = {
            key: val
            for key, val in vars(self).items()
            if not key.startswith('_') and key not in excluded_properties
        }
        attributes = {**properties, **attributes}

        return {
            key: attributes[key]
            for key in sorted(attributes, key=helper.sort_object_properties)
        }

    def to_dataframe(self) -> DataFrame:
        """Converts all properties of the object to a dataframe.

        Returns:
            DataFrame: A `DataFrame` object containing object properties.
        """
        return DataFrame.from_dict(
            self.list_properties(), orient='index', columns=['value']
        )

    def print(self) -> None:
        """Pretty Print all properties of the object."""
        if version_info.major >= 3 and version_info.minor >= 8:
            pprint(self.list_properties(), sort_dicts=False)  # type: ignore
        else:
            pprint(self.list_properties())

    @classmethod
    def from_dict(
        cls: T,
        source: dict[str, Any],
        connection: Connection,
        to_snake_case: bool = True,
        with_missing_value: bool = False,
    ) -> type[T]:
        """Overrides `Dictable.from_dict()` to instantiate an object from
            a dictionary without calling any additional getters.

        Args:
            cls (T): Class (type) of an object that should be created.
            source (dict[str, Any]): a dictionary from which an object will be
                constructed.
            connection (Connection): A Strategy One Connection object.
            to_snake_case (bool, optional): Set to True if attribute names
                should be converted from camel case to snake case, default True.
            with_missing_value: (bool, optional): If True, class attributes
                possible to fetch and missing in `source` will be set as
                `MissingValue` objects.

        Returns:
            T: An object of type T.
        """

        obj = cls.__new__(cls)  # Does not call __init__
        object_source = helper.camel_to_snake(source) if to_snake_case else source
        obj._WITH_MISSING_VALUE = with_missing_value
        default_value = MISSING if with_missing_value else None
        obj._init_variables(
            connection=connection, default_value=default_value, **object_source
        )
        return obj

    def __str__(self) -> str:
        """Overrides default `__str__` method to provide more informative
        description of an object.

        Returns:
            str: A formatted string consisting of object's type, name and id.
        """
        if self.__dict__.get("name"):
            return "{} object named: '{}' with ID: '{}'".format(
                self.__class__.__name__, self.name, self.id
            )
        else:
            return f"{self.__class__.__name__} object with ID: '{self.id}'"

    def __repr__(self):
        param_value_dict = auto_match_args_entity(
            self.__init__, self, exclude=['self'], include_defaults=False
        )
        params_list = []
        for param, value in param_value_dict.items():
            if param == "connection" and isinstance(value, Connection):
                params_list.append("connection")
            else:
                params_list.append(f"{param}={repr(value)}")
        formatted_params = ", ".join(params_list)
        return f"{self.__class__.__name__}({formatted_params})"

    def __hash__(self):
        type_value = self._OBJECT_TYPE.value if self._OBJECT_SUBTYPES else None
        return hash((self.id, type_value))

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
                (
                    getattr(self, k) == v if hasattr(self, k) else False
                    for k, v in other.items()
                )
            )
        else:
            return NotImplemented  # don't attempt to compare against unrelated types

    @classmethod
    def to_csv(  # NOSONAR
        cls: T,
        objects: T | list[T],
        name: str,
        path: str | None = None,
        properties: list[str] | None = None,
    ) -> None:
        """Exports MSTR objects to a csv file.

        Optionally, saves only the object properties specified in the properties
        parameter.

        Args:
            objects (T | list[T]): List of objects of the same type that
            will be exported.
            name (str): The name of the csv file ending with '.csv'
            path (Optional[str], optional): A path to the directory where the
                file will be saved. Defaults to None.
            properties (Optional[list[str]], optional): A list of object's
                attribute names that should be included in the exported file.
                Defaults to None.

        Raises:
            TypeError: If `objects` is not of type `T` or list of type `T`
            objects.
        """
        file_ = joinpath(path, name) if path else name
        list_of_objects = []
        if not name.endswith('.csv'):
            msg = (
                "The file extension is different than '.csv', please note that using a "
                "different extension might disrupt opening the file correctly."
            )
            helper.exception_handler(msg, exception_type=Warning)

        if not isinstance(objects, list):
            objects = [objects]
        for obj in objects:
            if not isinstance(obj, cls):
                helper.exception_handler(
                    (
                        f"Object '{obj}' of type '{type(obj)}' is not supported."
                        f"Objects should be of type {cls.__name__} or "
                        f"list of {cls.__name__}."
                    ),
                    exception_type=TypeError,
                )
            if properties:
                list_of_objects.append({key: getattr(obj, key) for key in properties})
            else:
                list_of_objects.append(obj.list_properties())

        with open(file_, 'w') as f:
            fieldnames = list_of_objects[0].keys()
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(list_of_objects)
        if config.verbose:
            logger.info(f"Object exported successfully to '{file_}'")

    def update_properties(self) -> None:
        """Save compatible local changes of the object attributes to the
        I-Server. Changes are retrieved from the `self._altered_properties`
        dictionary. After the process of update has finished,
        `self._altered_properties` is cleared. For this method to work
        properly, you must override the `_alter_properties()` method in a
        subclass.

        Raises:
            requests.HTTPError: If I-Server raises exception
        """
        changes = {k: v[1] for k, v in self._altered_properties.items()}
        self._alter_properties(**changes)
        self._altered_properties.clear()

    def __partial_put_body(self, attrs: tuple, camel_properties: dict) -> dict:
        """Prepares the 'partial put' update request's body.

        Args:
            attrs (tuple): A tuple consisting of name/-s of attributes.
                Corresponds to keys in a `_API_PATCH` dictionary.
            camel_properties (dict): A dictionary representation of an object's
                attribute names (in camel case) and values.

        Returns:
            dict: A dictionary used as a PUT request body.
        """
        body = {}
        for name, value in camel_properties.items():
            snake_case_name = humps.decamelize(name)
            if snake_case_name in attrs:
                value = self._unpack_objects(name, value, camel_case=True)
                body[name] = self._validate_type(snake_case_name, value)
        return body

    def __put_body(self, attrs: tuple, properties: dict) -> dict:
        """Prepares the 'put' update request's body.

        Args:
            attrs (tuple): A tuple consisting of name/-s of attributes.
                Corresponds to keys in a `_API_PATCH` dictionary.
            properties (dict): A dictionary representation of an object's
                attribute names (in snake case) and values.

        Returns:
            dict: A dictionary used as a PUT request body.
        """
        for name, value in properties.items():
            if name in attrs:
                value = self._unpack_objects(name, value, camel_case=True)
                setattr(self, name, self._validate_type(name, value))
        return self.to_dict()

    def __patch_body(self, attrs: tuple, camel_properties: dict, op: str) -> dict:
        """Prepares the 'patch' update request's body.

        Args:
            attrs (tuple): A tuple consisting of name/-s of attributes.
                Corresponds to keys in a `_API_PATCH` dictionary.
            camel_properties (dict): A dictionary representation of an object's
                attribute names (in snake case) and values.
            op (str): An operation type. Possible values are add, replace,
                remove, removeElement, addElement, removeElements or
                addElements.

        Returns:
            dict: A dictionary used as a PATCH request body.
        """

        body = {"operationList": []}
        for name, value in camel_properties.items():
            snake_case_name = humps.decamelize(name)
            if snake_case_name in attrs:
                value = self._unpack_objects(name, value, camel_case=True)
                body['operationList'].append(
                    {
                        "op": op,
                        "path": f"/{name}",
                        "value": self._validate_type(snake_case_name, value),
                    }
                )
        # Prevent sending body with no operations
        return body if body['operationList'] else {}

    def _send_proper_patch_request(
        self, properties: dict, op: str = 'replace'
    ) -> list[bool]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships. Automatically converts `properties` keys from
        a snake case to a camel case. The update's type is specified in the
        `self._API_PATCH` dictionary and be described as follows:
        - 'patch' : Used when the REST API provides a PATCH endpoint to update
            the object.
        - 'put': Used when the REST API requires that a body of a request
            consists of all the object's attributes.
        - 'partial_put': Used when the REST API requires that a body of a
            request consists only of attributes that are being updated. Although
            it resembles and imitates PATCH request, a PUT HTTP method is used,
            hence its name.

        Args:
            properties (dict): A dictionary of required changes
            op (str): An operation type. Possible values are add, replace,
                remove, removeElement, addElement, removeElements or
                addElements. Defaults to 'replace'.

        Returns:
            A list of successful or unsuccessful requests.

        Raises:
            NotSupportedError: If there is no information in `self._API_PATCH`
                dictionary about the update's type ('partial_put', 'put' or
                'patch').
        """
        changed = []
        camel_properties = helper.snake_to_camel(
            properties, whitelist=self._KEEP_CAMEL_CASE
        )
        for attrs, (func, func_type) in self._API_PATCH.items():
            if func_type == 'partial_put':
                translated_properties = self._python_to_rest(camel_properties)
                body = self.__partial_put_body(attrs, translated_properties)
            elif func_type == 'put':  # Update using the generic update_object()
                body = self.__put_body(attrs, properties)
                body = self._python_to_rest(body)
            elif func_type == 'patch':
                translated_properties = self._python_to_rest(camel_properties)
                body = self.__patch_body(attrs, translated_properties, op)
            else:
                msg = (
                    f"{func} function is not supported by `_send_proper_patch_request`"
                )
                raise NotSupportedError(msg)

            if not body:
                continue
            # send patch request from the specified update wrapper
            param_value_dict = auto_match_args_entity(func, self, exclude=["body"])
            param_value_dict['body'] = body
            response = func(**param_value_dict)

            if response:
                changed.append(True)
                json = (
                    response
                    if isinstance(response, (dict, list))
                    else get_response_json(response)
                )
                if isinstance(json, dict):
                    self._set_object_attributes(**json)
            else:
                changed.append(False)
        return changed

    def _alter_properties(self, **properties) -> None:
        """Generic alter method that has to be implemented in child classes
        where arguments will be specified. If a **properties dictionary is empty
        the method will not dispatch any request. If there is at least one entry
        in **properties, an update will be performed according to the update
        type specified in `_API_PATCH` dictionary. A message with update status
        is printed both on failure and success."""
        if not properties:
            if config.verbose:
                logger.info(
                    f"No changes specified for {type(self).__name__} '{self.name}'."
                )
            return None

        changed = self._send_proper_patch_request(properties)

        if config.verbose and all(changed):
            msg = (
                f"{type(self).__name__} '{self.name}' has been modified on the server. "
                "Your changes are saved locally."
            )
            logger.info(msg)

    def _update_nested_properties(
        self,
        objects: Any | list[Any],
        path: str,
        op: str,
        existing_ids: list[str] | None = None,
    ) -> tuple[str, str]:
        """Internal method to update objects with the specified patch wrapper.
        Used for adding and removing objects from nested properties of an
        object like memberships.

        Args:
            objects (Any | list[Any]): An id, object or list of objects
                or/ and object ids on which nested properties should be updated.
            path (str): The name of an attribute that nests other objects.
            op (str): An operation type. Non-ignored values are 'add' or
                'remove'.
            existing_ids (Optional[list[str]], optional): IDs of objects which
                are already nested in `path` attribute. Defaults to None.

        Returns:
            tuple[list[str]]: A tuple whose first element is a list of IDs of
                successful operations, and second element is a list of IDs of
                failed operations.
        """
        from mstrio.access_and_security.privilege import Privilege

        # check whether existing_ids are supplied
        if existing_ids is None:
            existing_ids = [obj.get('id') for obj in getattr(self, path)]

        # create list of objects from strings/objects/lists
        objects_list = objects if isinstance(objects, list) else [objects]
        object_map = {
            obj.id: obj.name for obj in objects_list if isinstance(obj, Entity)
        }

        object_ids_list = [
            obj.id if isinstance(obj, (EntityBase, Privilege)) else str(obj)
            for obj in objects_list
        ]

        # check if objects can be manipulated by comparing to existing values
        if op == "add":
            filtered_object_ids = sorted(
                filter(lambda x: x not in existing_ids, object_ids_list)
            )
        elif op == "remove":
            filtered_object_ids = sorted(
                filter(lambda x: x in existing_ids, object_ids_list)
            )
        if filtered_object_ids:
            properties = {path: filtered_object_ids}
            self._send_proper_patch_request(properties, op)

        failed = sorted(set(object_ids_list) - set(filtered_object_ids))
        failed_formatted = [
            object_map.get(object_id, object_id) for object_id in failed
        ]
        succeeded_formatted = [
            object_map.get(object_id, object_id) for object_id in filtered_object_ids
        ]
        return (succeeded_formatted, failed_formatted)

    def _validate_type(self, name: str, value: T) -> T:
        """Uses information specified in `self._AVAILABLE_ATTRIBUTES` and
        `self._PATCH_PATH_TYPES` dictionaries to validate type of `value` of an
        attribute with a specified `name`.

        Args:
            name (str): An attribute's name
            value (T): A value to be validated.

        Raises:
            TypeError: If value's type is incorrect.

        Returns:
            T: Unchanged `value` parameter.
        """
        type_map = {**self._AVAILABLE_ATTRIBUTES, **self._PATCH_PATH_TYPES}
        value_type = type_map.get(name, 'Not Found')

        if value_type != 'Not Found' and not isinstance(value, value_type):
            raise TypeError(
                f"'{name}' has incorrect type. Expected type: '{value_type}'"
            )
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        """Overloads the __setattr__ method to validate if this attribute can
        be set for current object. If type of `value` or its literal differs
        from the one that is currently stored, the change will be tracked in a
        dictionary `self._altered_properties` which is later used to update
        properties on a server.
        """

        def track_changes():
            already_tracked = name in self._altered_properties
            if already_tracked:
                current_val = self._altered_properties[name][0]
            else:
                current_val = self.__dict__.get(name)
            is_changed = not (type(current_val) is type(value) and current_val == value)
            if is_changed:
                self._altered_properties.update({name: (current_val, value)})
            elif already_tracked:
                del self._altered_properties[name]

        # Keep track of changed properties if value is already fetched
        if hasattr(self, "_fetched_attributes"):
            if name in self._PATCH_PATH_TYPES and name in self._fetched_attributes:
                track_changes()
            # if object was initialized from `search_operations.full_search`
            # and value is not instance of MissingValue class then treat as
            # fetched
            if self._WITH_MISSING_VALUE:
                if value is not MISSING:
                    self._add_to_fetched(name)
            # Otherwise if object was initialized from `__init__` and value
            # is not None then treat as fetched
            elif value is not None:
                self._add_to_fetched(name)

        super().__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        """On first fetch, it creates a set `_fetched_attributes` used to track
        attributes that were already fetched from the server. Additionally,
        it checks if there is an API getter in a `_API_GETTERS` dictionary
        that corresponds to the attribute's name. If there is and the object
        has an id and it has not been fetched yet it will fetch the value
        from the server. If not, it will return the value straight away."""
        val = super().__getattribute__(name)

        if name in ["_fetched_attributes", "_find_func"]:
            return val
        if not hasattr(self, "_fetched_attributes"):
            self._fetched_attributes = set()
        if hasattr(self, "_fetched_attributes") and hasattr(self, "_find_func"):
            _name = name[1:] if name.startswith("_") else name
            was_fetched = _name in self._fetched_attributes
            can_fetch = (
                self._find_func(_name) is not None and "id" in self._fetched_attributes
            )
            if can_fetch and not was_fetched:
                self.fetch(_name)  # fetch the relevant object data
            val = super().__getattribute__(name)

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

    @property
    def connection(self) -> Connection:
        """An object representation of Strategy One connection specific to the
        object."""
        return self._connection

    @property
    def id(self) -> str:
        """The object's id."""
        return self._id

    @property
    def type(self) -> ObjectTypes:
        """The object's type."""
        return self._type


class Entity(EntityBase, ACLMixin, DependenceMixin, TranslationMixin):
    """Base class representation of the Strategy One object.

    Provides methods to fetch, update, and view the object. To implement
    this base class all class attributes have to be provided.

    Attributes:
        connection: A Strategy One connection object
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
        location: path to the Object
        certified_info: Certification status, time of certification, and
            information about the certifier (currently only for document and
            report)
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
        hidden: Specifies if a object is hidden
    """

    _API_GETTERS: dict[str | tuple, Callable] = {
        (
            'id',
            'name',
            'description',
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
            'acl',
            'comments',
            'project_id',
            'hidden',
            'target_info',
        ): objects_processors.get_info,
    }
    _API_PATCH: dict = {
        ('name', 'description', 'abbreviation', 'hidden', 'comments'): (
            objects_processors.update,
            'partial_put',
        )
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "abbreviation": str,
        "hidden": bool,
        "comments": str,
        "owner": str,
    }
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        'ext_type': ExtendedType,
        'date_created': DatetimeFormats.FULLDATETIME,
        'date_modified': DatetimeFormats.FULLDATETIME,
        'acl': [ACE.from_dict],
        'acg': Rights,
        'location': str,
    }

    def _init_variables(self, default_value=None, **kwargs) -> None:
        """Initialize variables given kwargs."""
        from mstrio.users_and_groups.user import User
        from mstrio.utils.certified_info import CertifiedInfo

        super()._init_variables(default_value=default_value, **kwargs)
        self._date_created = (
            map_str_to_datetime(
                "date_created", kwargs.get("date_created"), self._FROM_DICT_MAP
            )
            if kwargs.get("date_created")
            else default_value
        )
        self._date_modified = (
            map_str_to_datetime(
                "date_modified", kwargs.get("date_modified"), self._FROM_DICT_MAP
            )
            if kwargs.get("date_modified")
            else default_value
        )
        self.description = kwargs.get("description", default_value)
        self.abbreviation = kwargs.get("abbreviation", default_value)
        self._subtype = kwargs.get("subtype", default_value)
        self._ext_type = (
            ExtendedType(kwargs["ext_type"])
            if kwargs.get("ext_type")
            else default_value
        )
        self._version = kwargs.get("version", default_value)
        self._owner = (
            User.from_dict(kwargs.get("owner"), self.connection)
            if kwargs.get("owner")
            else default_value
        )
        self._icon_path = kwargs.get("icon_path", default_value)
        self._view_media = kwargs.get("view_media", default_value)
        self._ancestors = kwargs.get("ancestors", default_value)
        self._location = None
        self._certified_info = (
            CertifiedInfo.from_dict(kwargs.get("certified_info"), self.connection)
            if kwargs.get("certified_info")
            else default_value
        )
        self._hidden = kwargs.get("hidden", default_value)
        self._project_id = kwargs.get("project_id")
        self._comments = kwargs.get("comments", default_value)
        self._target_info = kwargs.get("target_info", default_value)
        self._acg = Rights(kwargs.get("acg")) if kwargs.get("acg") else default_value
        self._acl = (
            [ACE.from_dict(ac, self._connection) for ac in kwargs.get("acl")]
            if kwargs.get("acl")
            else default_value
        )

    @method_version_handler(version="11.3.0200")
    def create_shortcut(
        self,
        target_folder_id: str | None = None,
        target_folder_path: str | None = None,
        target_folder: 'Folder | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
        project: 'Project | None' = None,
        to_dictionary: bool = False,
    ) -> 'Shortcut':
        """Create a shortcut to the object.

        Args:
            target_folder_id (str, optional): ID of the target folder. Target
                folder must be specified, but `target_folder_id` may be
                substituted with `target_folder_path` or `target_folder`.
            target_folder_path (str, optional): Path to the target folder, e.g.
                '/MicroStrategy Tutorial/Public Objects'.
                May be used instead of `target_folder_id`.
            target_folder (Folder, optional): Target folder object.
                May be used instead of `target_folder_id`.
            project_id (str, optional): ID of the target project of the new
                shortcut. The project may be specified by either `project_id`,
                `project_name` or `project`. If the project is not specified in
                either way, the project from the `connection` object is used.
            project_name (str, optional): Name of the target project.
                May be used instead of `project_id`.
            project (Project, optional): Project object specifying the target
                project. May be used instead of `project_id`.
            to_dictionary (bool, optional): If True, the method will return
                a dictionary with the shortcut's properties instead of a
                Shortcut object. Defaults to False.

        """
        from mstrio.object_management.folder import get_folder_id_from_path
        from mstrio.object_management.shortcut import Shortcut

        if target_folder:
            target_folder_id = target_folder.id
        elif target_folder_path:
            target_folder_id = get_folder_id_from_path(
                self.connection, target_folder_path
            )
        if not target_folder_id:
            raise ValueError("Target folder not specified.")

        if project_id is None and project is not None:
            project_id = project.id
        project_id = get_valid_project_id(
            connection=self.connection,
            project_id=project_id,
            project_name=project_name,
            with_fallback=True,
        )

        body = {
            'folderId': target_folder_id,
        }

        res = objects.create_shortcut(
            connection=self.connection,
            id=self.id,
            object_type=self._OBJECT_TYPE.value,
            body=body,
            project_id=project_id,
        )
        body = res.json()
        shortcut_id = body.get('id')
        if config.verbose:
            logger.info(
                f"Successfully created Shortcut for object named '{self.name}' "
                f"with ID: '{self.id}'. Shortcut ID: '{shortcut_id}'."
            )
        if to_dictionary:
            return body
        return Shortcut.from_dict(source=body, connection=self.connection)

    def get(self, name):
        """Get object's attribute by its name."""
        return getattr(self, name)

    @property
    def subtype(self) -> ObjectSubTypes:
        return self._subtype

    @property
    def ext_type(self) -> ExtendedType:
        return self._ext_type

    @property
    def date_created(self) -> DatetimeFormats:
        return self._date_created

    @property
    def date_modified(self) -> DatetimeFormats:
        return self._date_modified

    @property
    def version(self) -> str:
        return self._version

    @property
    def owner(self):
        return self._owner

    @property
    def icon_path(self) -> str:
        return self._icon_path

    @property
    def view_media(self) -> int:
        return self._view_media

    @property
    def ancestors(self) -> list[dict]:
        return self._ancestors

    @property
    def certified_info(self):
        return self._certified_info

    @property
    def acg(self) -> Rights:
        return self._acg

    @property
    def acl(self) -> list[ACE]:
        return self._acl

    @property
    def hidden(self) -> bool:
        return self._hidden

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def comments(self) -> list[str]:
        return self._comments

    @property
    def target_info(self) -> dict:
        return self._target_info

    @property
    def location(self) -> str:
        if self.ancestors:
            self._location = ''
            for ancestor in self.ancestors:
                self._location += '/' + ancestor.get('name')
            self._location += '/' + self.name
        return self._location


class CopyMixin:
    """CopyMixin class adds creating copies of objects functionality.

    Currently project objects are not supported. Must be mixedin with
    Entity or its subclasses.
    """

    def create_copy(
        self: Entity,
        name: str | None = None,
        folder_id: str | None = None,
        project: 'Project | str | None' = None,
    ) -> Any:
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
            raise NotSupportedError("Copying of object with type 32 is not supported.")

        from mstrio.server.project import Project

        response = objects.copy_object(
            self.connection,
            id=self.id,
            name=name,
            folder_id=folder_id,
            object_type=self._OBJECT_TYPE.value,
            project_id=project.id if isinstance(project, Project) else project,
        )
        return self.from_dict(source=response.json(), connection=self.connection)


class MoveMixin:
    """MoveMixin class adds moving objects functionality.
    Must be mixedin with Entity or its subclasses.
    """

    def move(self: Entity, folder: 'Folder | str'):
        """Move the object to a folder on the I-Server.

        Args:
            folder: Destination folder, specified either by id
                or the Folder object.
        """
        from mstrio.object_management.folder import Folder

        folder = folder.id if isinstance(folder, Folder) else folder
        self._alter_properties(folder_id=folder)


class DeleteMixin:
    """DeleteMixin class adds deleting objects functionality.
    Must be mixedin with Entity or its subclasses.
    """

    _DELETE_CONFIRM_MSG: str | None = None
    _DELETE_SUCCESS_MSG: str | None = None
    _DELETE_PROMPT_ANSWER: str = 'Y'

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
            message = self._DELETE_CONFIRM_MSG or (
                f"Are you sure you want to delete {object_name} "
                f"'{self.name}' with ID: {self._id}? [Y/N]: "
            )
            user_input = input(message) or 'N'

        if force or user_input == self._DELETE_PROMPT_ANSWER:
            param_value_dict = auto_match_args_entity(self._API_DELETE, self)

            response = self._API_DELETE(**param_value_dict)

            if response.status_code == 204 and config.verbose:
                msg = (
                    self._DELETE_SUCCESS_MSG
                    or f"Successfully deleted {object_name} with ID: '{self._id}'."
                )
                logger.info(msg)

            return response.ok

        return False


class CertifyMixin:
    """CertifyMixin class adds certifying and decertifying functionality.
    Must be mixedin with Entity or its subclasses.
    """

    def _toggle_certification(
        self: Entity, certify: bool = True, success_msg: str = None
    ) -> bool:
        object_name = self.__class__.__name__
        expected_result = 'certified' if certify else 'decertified'

        self.fetch()
        if certify == self.certified_info.certified:
            logger.warning(
                f"The {object_name} with ID: '{self._id}' is already {expected_result}"
            )
            return True

        response = objects.toggle_certification(
            connection=self._connection,
            id=self._id,
            object_type=self._OBJECT_TYPE.value,
            certify=certify,
        )
        if response.ok and config.verbose:
            self._set_object_attributes(**response.json())
            id_ = self._id
            msg = (
                success_msg
                or f"The {object_name} with ID: '{id_}' has been {expected_result}."
            )
            logger.info(msg)
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

    Objects currently supporting VLDB settings are dataset, dashboard, document.
    Must be mixedin with Entity or its subclasses.
    """

    _parameter_error = "Please specify the project parameter."
    _vldb_settings: dict = {}

    def list_vldb_settings(self: Entity, project: str | None = None) -> list:
        """List VLDB settings."""
        connection = (
            self.connection if hasattr(self, 'connection') else self._connection
        )
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        response = objects.get_vldb_settings(
            connection, self.id, self._OBJECT_TYPE.value, project
        )
        return response.json()

    def alter_vldb_settings(
        self: Entity,
        property_set_name: str,
        name: str,
        value: dict,
        project: str | None = None,
    ) -> None:
        """Alter VLDB settings for a given property set."""

        connection = (
            self.connection if hasattr(self, 'connection') else self._connection
        )
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        body = [{"name": name, "value": value}]
        response = objects.set_vldb_settings(
            connection,
            self.id,
            self._OBJECT_TYPE.value,
            property_set_name,
            body,
            project,
        )
        self.fetch_vldb_settings()
        if config.verbose and response.ok:
            logger.info('VLDB settings altered.')

    def reset_vldb_settings(self: Entity, project: str | None = None) -> None:
        """Reset VLDB settings to default values."""

        connection = (
            self.connection if hasattr(self, 'connection') else self._connection
        )
        if not project and not connection.project_id:
            raise ValueError(self._parameter_error)

        response = objects.delete_vldb_settings(
            connection, self.id, self._OBJECT_TYPE.value, project
        )
        self.fetch_vldb_settings()
        if config.verbose and response.ok:
            logger.info('VLDB settings reset to default.')

    def fetch_vldb_settings(self):
        for property_set in self.list_vldb_settings():
            for property in property_set['properties']:
                default_value = property.get('defaultValue')
                info = {
                    'property_set_name': property_set['name'],
                    'name': property['name'],
                    'default_value': default_value,
                    'value': property.get('value', default_value),
                    'type': property.get('type'),
                }
                self._vldb_settings[property['name']] = info

    @property
    def vldb_settings(self) -> dict:
        if not self._vldb_settings:
            self.fetch_vldb_settings()
        return self._vldb_settings


def auto_match_args_entity(
    func: Callable,
    obj: EntityBase,
    exclude: list | None = None,
    include_defaults: bool = True,
) -> dict:
    """Automatically match `obj` object data to function arguments.

    Handles default parameters. Extracts value from Enums. Returns matched
    arguments as dict.

    Args:
        func: function for which args will be matched
        obj: object to use for matching the function args
        exclude: set `exclude` parameter to exclude specific param-value pairs
        include_defaults: if `False` then values which have the same value as
            default will not be included in the result
    Raises:
        KeyError: could not match all required arguments
    """
    exclude = exclude or None
    # convert names starting with '_'
    obj_dict = {
        key[1:] if key.startswith("_") else key: val
        for key, val in obj.__dict__.items()
    }
    kwargs = helper.auto_match_args(func, obj_dict, exclude, include_defaults)

    if "object_type" in kwargs:
        kwargs.update({"object_type": obj._OBJECT_TYPE.value})

    return kwargs
