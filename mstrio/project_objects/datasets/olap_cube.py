import logging
from typing import List, Optional, Union

import pandas as pd

from mstrio.api import cubes
from mstrio.connection import Connection
from mstrio.object_management.search_operations import full_search, SearchPattern
from mstrio.utils.entity import ObjectSubTypes, ObjectTypes
from mstrio.utils.helper import exception_handler

from .cube import _Cube, load_cube

logger = logging.getLogger(__name__)


def list_olap_cubes(connection: Connection, name_begins: Optional[str] = None,
                    to_dictionary: bool = False, limit: Optional[int] = None,
                    **filters) -> Union[List["OlapCube"], List[dict]]:
    """Get list of OlapCube objects or dicts with them. Optionally filter cubes
    by specifying 'name_begins'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name_begins':
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins (string, optional): characters that the cube name must begin
            with
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns OlapCube objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        **filters: Available filter parameters: ['id', 'name', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'owner',
            'ext_type', 'view_media', 'certified_info']

    Returns:
        list with OlapCubes or list of dictionaries
    """
    connection._validate_project_selected()
    objects_ = full_search(connection, object_types=ObjectSubTypes.OLAP_CUBE,
                           project=connection.project_id, name=name_begins,
                           pattern=SearchPattern.BEGIN_WITH, limit=limit, **filters)
    if to_dictionary:
        return objects_
    else:
        return [OlapCube.from_dict(obj_, connection) for obj_ in objects_]


class OlapCube(_Cube):
    """Manage single table cube - according to EnumDSSXMLObjectSubTypes its
    subtype is  776 (DssXmlSubTypeReportCube). It inherits all properties from
    Cube.

    Attributes:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`.
        id: Identifier of a pre-existing cube.
        instance_id (str): Identifier of a cube instance if already initialized,
            None by default.
        name: name of the OlapCube
        size(integer): size of cube
        status(integer): status of cube
        path(string): full path of the cube on environment
        owner_id(string): ID of cube's owner
        attributes(list): all attributes of cube
        metrics(list): all metrics of cube
        attr_elements(list): all attributes elements of cube
        selected_attributes(list): IDs of filtered attributes
        selected_metrics(list): IDs of filtered metrics
        selected_attr_elements(list): IDs of filtered attribute elements
        dataframe(object): content of a cube extracted into a
            Pandas `DataFrame`
        table_definition
    """
    _OBJECT_SUBTYPE = ObjectSubTypes.OLAP_CUBE.value
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: Connection, id: str, name: Optional[str] = None,
                 instance_id: Optional[str] = None, parallel: bool = True,
                 progress_bar: bool = True):
        """Initialize an Olap Cube instance.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify cube.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing cube.
            name (str): Name of a cube.
            instance_id (str): Identifier of an instance if cube instance has
                already been initialized, None by default.
            parallel (bool, optional): If True (default), utilize optimal number
                of threads to increase the download speed. If False, this
                feature will be disabled.
            progress_bar(bool, optional): If True (default), show the download
                progress bar.
        """
        # NOTE use the super.init from _Cube once cube_id is deprecated
        super().__init__(connection, id=id, name=name, instance_id=instance_id, parallel=parallel,
                         progress_bar=progress_bar)

    @classmethod
    def available_metrics(cls, connection: Connection, basic_info_only: bool = True,
                          to_dataframe: bool = False) -> Union[List[dict], List[pd.DataFrame]]:
        """Get all metrics available on I-Server.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                metric. When False, then all properties of each metric will be
                returned.
            to_dataframe: When False (default value) then metrics are returned
                as a list of dictionaries. When True then metrics are returned
                as Pandas 'DataFrame'.

        Returns:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.METRIC, basic_info_only,
                                       to_dataframe)

    @classmethod
    def available_attributes(cls, connection: Connection, basic_info_only: bool = True,
                             to_dataframe: bool = False) -> Union[List[dict], List[pd.DataFrame]]:
        """Get all attributes available on I-Server.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                attribute. When False, then all properties of each attribute
                will be returned.
            to_dataframe: When False (default value) then attributes are
                returned as a list of dictionaries. When True then attributes
                are returned as Pandas 'DataFrame'.

        Returns:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.ATTRIBUTE, basic_info_only,
                                       to_dataframe)

    @classmethod
    def available_attribute_forms(
            cls, connection: Connection, basic_info_only: bool = True,
            to_dataframe: bool = False) -> Union[List[dict], List[pd.DataFrame]]:
        """Get all attribute forms available on I-Server.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            basic_info_only(boolean, optional): When True (default value) only
                values of `id`, `name` and `type` will be returned for each
                attribute form. When False, then all properties of each
                attribute form will be returned.
            to_dataframe: When False (default value) then attribute forms are
                returned as a list of dictionaries. When True then attribute
                forms are returned as Pandas 'DataFrame'.

        Returns:
            List of attribute forms or attribute forms as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.ATTRIBUTE_FORM, basic_info_only,
                                       to_dataframe)

    @classmethod
    def __available_objects(cls, connection: Connection, object_type=Union[ObjectTypes,
                                                                           ObjectSubTypes],
                            basic_info_only: bool = True,
                            to_dataframe: bool = False) -> Union[List[dict], List[pd.DataFrame]]:
        """Helper function to get available objects based on their type. It
        should be used to get only available attribute, metrics or attribute
        forms."""
        connection._validate_project_selected()
        avl_objects = full_search(
            connection=connection,
            object_types=object_type,
            project=connection.project_id
        )
        for a in avl_objects:
            new_type = None
            if a['type'] == ObjectTypes.METRIC.value:
                new_type = 'metric'
            elif a['type'] == ObjectTypes.ATTRIBUTE.value:
                new_type = 'attribute'
            elif a['type'] == ObjectTypes.ATTRIBUTE_FORM.value:
                new_type = 'form'
            if new_type:
                a['type'] = new_type

        if basic_info_only:
            avl_objects = [{
                'id': a['id'],
                'name': a['name'],
                'type': a['type']
            } for a in avl_objects]
        if to_dataframe:
            avl_objects = pd.DataFrame.from_dict(avl_objects)

        return avl_objects

    @classmethod
    def create(cls, connection: "Connection", name: str, folder_id: str, description: str = None,
               overwrite: bool = False, attributes: List[dict] = [],
               metrics: List[dict] = []) -> Union['OlapCube', None]:
        """Create an OLAP Cube by defining its name, description, destination
        folder, attributes and metrics.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name(string): OLAP Cube name.
            folder_id(string): Object ID of the folder where the cube should be
                saved.
            description(string, optional): OLAP Cube description
            overwrite(boolean, optional): Default value (False) not allow to
                overwrite the object with the same name.
            attributes(list of dicts, optional): list with dicts of attributes
                dicts to be in the working set of OLAP Cube. Each attribute dict
                should have keys: `id`, `name` and `type`. Attributes can be
                found with method `OlapCube.available_attributes`.
            metrics(list of dicts, optional): list with dicts of metrics to be
                in the working set of OLAP Cube. Each metric dict should have
                keys: `id`, `name` and `type`. Metrics can be found with
                method `OlapCube.available_metrics`.

        Returns:
            Newly created OLAP Cube or None in case of wrongly provided
            attributes or metrics.

        Raises:
            `requests.exceptions.HTTPError` when response returned from request
            to I-Server to create new OLAP Cube was not ok.
        """
        if not OlapCube.__check_objects(attributes, 'attribute'):
            return None
        if not OlapCube.__check_objects(metrics, 'metric'):
            return None

        definition = {'availableObjects': {'attributes': attributes, 'metrics': metrics}}
        cube_id = cubes.create(connection, name, folder_id, overwrite, description,
                               definition).json()['id']
        return load_cube(connection, cube_id)

    @staticmethod
    def __check_objects(objects_: List[dict], obj_name: str) -> bool:
        """Check objects (attribute or metrics) before creation or update of an
        OLAP Cube."""
        for obj in objects_:
            if not OlapCube.__check_object(obj, obj_name):
                return False
        return True

    @staticmethod
    def __check_object(object_: dict, obj_name: str) -> bool:
        """Check a single object (attribute or metric) represented as dictionary
        before creation or update of OLAP Cube. Each dictionary must have keys:
        `id` and `name`. When it has key `type` then it must be the same as
        value of parameter `obj_name`. When this key is missing its value will
        be set to value of parameter `obj_name`."""
        if 'name' not in object_:
            msg = f"Each element in dictionary with {obj_name}s must have key 'name'."
            exception_handler(msg, Warning, True)
            return False

        if 'id' not in object_:
            msg = f"{obj_name.capitalize()} '{object_['name']}' is missing key 'id'."
            exception_handler(msg, Warning, True)
            return False

        if 'type' not in object_:
            object_['type'] = obj_name
        elif object_['type'] != obj_name:
            msg = f"Each element in dictionary with {obj_name}s must be of a type '{obj_name}'."
            exception_handler(msg, Warning, True)
            return False
        return True

    def update(self, attributes: List[dict] = [], metrics: List[dict] = []) -> bool:
        """Update an OLAP Cube. When Cube is unpublished, then it is possible to
         add or remove attributes and metrics to/from its definition and
         rearrange existing one. When cube is published it is possible only to
         rearrange attributes and metrics existing in its definition. After this
         operation cube will have only attributes and metrics provided in
         parameters.

         Args:
            attributes(list of dicts, optional): list with dicts of attributes
                dicts to be in the working set of OLAP Cube. Each attribute dict
                should have keys: `id`, `name` and `type`. Attributes can be
                found with method `OlapCube.available_attributes`.
            metrics(list of dicts, optional): list with dicts of metrics to be
                in the working set of OLAP Cube. Each metric dict should have
                keys: `id`, `name` and `type`. Metrics can be found with
                method `OlapCube.available_metrics`.

        Returns:
            True when update was successful. False otherwise.

        Raises:
            `requests.exceptions.HTTPError` when response returned from request
            to I-Server to update new OLAP Cube was not ok.
        """
        if not OlapCube.__check_attributes_update(attributes, self.attributes, self.status):
            return False
        if not OlapCube.__check_metrics_update(metrics, self.metrics, self.status):
            return False

        definition = {
            'availableObjects': {
                'attributes': attributes,
                'metrics': metrics
            },
        }

        res = cubes.update(self._connection, self._id, definition)
        # refresh definition of cube
        self._get_definition()
        return res.ok

    @staticmethod
    def __check_attributes_update(attributes: List[dict], existing_attributes: List[dict],
                                  status: int) -> bool:
        """Check dictionaries with attributes before update of an OLAP Cube."""
        return OlapCube.__check_objects_update(attributes, existing_attributes, 'attribute',
                                               status)

    @staticmethod
    def __check_metrics_update(metrics: List[dict], existing_metrics: List[dict],
                               status: int) -> bool:
        """Check dictionaries with metrics before update of an OLAP Cube."""
        return OlapCube.__check_objects_update(metrics, existing_metrics, 'metric', status)

    @staticmethod
    def __check_objects_update(objects_: List[dict], existing_objects: List[dict],
                               object_name: str, status: int) -> bool:
        """Check objects (attributes or metrics) represented as dictionaries
        before update of an OLAP Cube. When status of cube is 0, then it is not
        published and it is possible to freely add or delete objects. Otherwise
        it is possible to only rearrange existing objects. For each object it is
        done also the same check as before creation of an OLAP Cube.
        """
        existing_ids = [o['id'] for o in existing_objects]
        reorganised_objects_count = 0  # to check if all existing objects were provided
        msg = f"It is not possible to add new {object_name}s when editing published cube."
        for object_ in objects_:
            # check if structure of dictionary with an object is correct
            if not OlapCube.__check_object(object_, object_name):
                return False
            # check if status of cube is correct in case of new objects
            if object_['id'] not in existing_ids:
                if status != 0:
                    exception_handler(msg, Warning)
                    return False
            else:
                reorganised_objects_count += 1

        # check if status of cube is correct in case of removing objects
        if reorganised_objects_count != len(existing_ids) and status != 0:
            msg = f"It is not possible delete existing {object_name}s when editing published cube."
            exception_handler(msg, Warning)
            return False

        return True

    def publish(self) -> None:
        """Publish an OLAP Cube. Request to publish an OLAP Cube is an
        asynchronous operation, so the result of it can be seen after calling
        method `refresh_status()` inherited from Cube class."""
        cubes.publish(self._connection, self._id)
        logger.info(f"Request for publishing cube '{self.name}' was sent.")

    def export_sql_view(self):
        """Export SQL View of an OLAP Cube.

        Returns:
            SQL View of an OLAP Cube.
        """
        res = cubes.get_sql_view(self._connection, self._id)
        sql_statement = res.json()['sqlStatement']
        return sql_statement
