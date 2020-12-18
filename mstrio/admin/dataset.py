from typing import Union, List

from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.entity import Entity, Vldb, ObjectTypes
from pandas import DataFrame


def list_datasets(connection, name: str = None, to_dictionary: bool = False, to_dataframe: bool = False, limit: int = None,
                  **filters):
    """Get all Datasets stored on the server.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact name of the document to list
        to_dictionary(bool, optional): if True, return datasets as
            list of dicts
        to_dataframe(bool, optional): if True, return datasets as
            pandas DataFrame
        limit: limit the number of elements returned to a sample of datasets.
            If `None`, all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'description', 'subtype', 'date_created', 'date_modified',
            'version', 'acg', 'owner', 'ext_type']

    Returns:
            List of datasets.
    """
    return Dataset._list_all(connection, name=name, to_dictionary=to_dictionary,
                             to_dataframe=to_dataframe, limit=limit, **filters)


class Dataset(Entity, Vldb):
    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION.value

    def __init__(self, connection: Connection, id: str = None, name: str = None):
        """Initialize Dataset object by passing name or id.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: name of Dataset
            id: ID of Dataset
        """
        if id is None and name is None:
            raise ValueError("Please specify either 'name' or 'id' parameter in the constructor.")
        if id is None:
            datasets = self._list_all(connection=connection, to_dictionary=True, name=name)
            if datasets:
                id = datasets[0]['id']
            else:
                raise ValueError(f"There is no {self.__class__.__name__} associated with the given name: '{name}'")
        super().__init__(connection=connection, object_id=id)

    def alter(self, name: str = None, description: str = None):
        """Alter Dataset name or/and description.

        Args:
            name: new name of the Dataset
            description: new description of the Dataset
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__    # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_all(cls, connection: Connection,
                  name: str = None,
                  to_dictionary: bool = False,
                  to_dataframe: bool = False,
                  limit: int = None,
                  **filters) -> Union[List["Dataset"], List[dict]]:
        DATASET_SUBTYPES = [776, 779]
        DSS_XML_SEARCH_TYPE_EXACTLY = 2

        msg = "Error creating an instance for searching objects"
        res_e = objects.create_search_objects_instance(connection=connection, name=name, pattern=DSS_XML_SEARCH_TYPE_EXACTLY,
                                                       object_type=cls._OBJECT_TYPE, error_msg=msg)
        search_id = res_e.json()['id']
        msg = "Error retrieving datasets from the environment."
        res_o = helper.fetch_objects_async(connection,
                                           api=objects.get_objects,
                                           async_api=objects.get_objects_async,
                                           dict_unpack_value=None,
                                           limit=limit,
                                           chunk_size=1000,
                                           error_msg=msg,
                                           filters=filters,
                                           search_id=search_id)
        datasets = [r for r in res_o if r['subtype'] in DATASET_SUBTYPES]

        if to_dictionary:
            return datasets
        elif to_dataframe:
            return DataFrame(datasets)
        else:
            return cls._from_bulk_response(connection, datasets)
