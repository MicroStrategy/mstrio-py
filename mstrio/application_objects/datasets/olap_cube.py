from typing import List, TYPE_CHECKING, Union

import pandas as pd

from mstrio.browsing import list_objects, SearchType
from mstrio.utils.entity import ObjectSubTypes, ObjectTypes

from .cube import _Cube

if TYPE_CHECKING:
    from mstrio.connection import Connection


def list_olap_cubes(connection: "Connection", name_begins: str = None, to_dictionary: bool = False,
                    limit: int = None, **filters) -> Union[List["OlapCube"], List[dict]]:
    """Get list of OlapCube objects or dicts with them. Optionally filter cubes
    by specifying 'name_begins'.

    Optionally use `to_dictionary` to choose output format.

    Wildcards available for 'name_begins':
        ? - any character
        * - 0 or more of any characters
        e.g name_begins = ?onny wil return Sonny and Tonny

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
    connection._validate_application_selected()
    objects_ = list_objects(connection, ObjectSubTypes.OLAP_CUBE, connection.application_id,
                            name=name_begins, pattern=SearchType.BEGIN_WITH, limit=limit,
                            **filters)
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
        last_modified(string): time when was last modification of cube
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

    def __init__(self, connection: "Connection", id: str, name: str = None, instance_id=None,
                 parallel=True, progress_bar=True):
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
    def available_metrics(cls, connection: "Connection", basic_info_only: bool = True,
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

        Return:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.METRIC, basic_info_only,
                                       to_dataframe)

    @classmethod
    def available_attributes(cls, connection: "Connection", basic_info_only: bool = True,
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

        Return:
            List of attributes or attributes as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.ATTRIBUTE, basic_info_only,
                                       to_dataframe)

    @classmethod
    def available_attribute_forms(
            cls, connection: "Connection", basic_info_only: bool = True,
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

        Return:
            List of attribute forms or attribute forms as Pandas `DataFrame`.
        """
        return cls.__available_objects(connection, ObjectTypes.ATTRIBUTE_FORM, basic_info_only,
                                       to_dataframe)

    @classmethod
    def __available_objects(cls, connection: "Connection", object_type=Union[ObjectTypes,
                                                                             ObjectSubTypes],
                            basic_info_only: bool = True,
                            to_dataframe: bool = False) -> Union[List[dict], List[pd.DataFrame]]:
        """Helper function to get available objects based on their type. It
        should be used to get only available attribute, metrics or attribute
        forms."""
        connection._validate_application_selected()
        avl_objects = list_objects(connection=connection, object_type=object_type,
                                   application_id=connection.application_id)
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
