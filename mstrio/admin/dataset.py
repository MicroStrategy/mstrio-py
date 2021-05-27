from typing import Optional, Union, List

from mstrio.api import objects
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.entity import Entity, VldbMixin, ObjectTypes
from pandas import DataFrame
# NOTE Keep until end of deprecation and move to

from mstrio.utils.helper import deprecation_warning

deprecation_warning(
    "mstrio.admin.dataset",
    ("mstrio.application_objects.datasets.super_cube "
     "and mstrio.application_objects.datasets.olap_cube"),
    "11.3.2.101",
)


def list_datasets(connection, name: Optional[str] = None, to_dictionary: bool = False,
                  to_dataframe: bool = False, limit: Optional[int] = None, **filters):
    """Get all Datasets stored on the server.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact name of the document to list
        to_dictionary(bool, optional): if True, return datasets as
            list of dicts
        to_dataframe(bool, optional): if True, return datasets as
            pandas DataFrame
        limit: limit the number of elements returned. If `None`, all objects are
            returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'description', 'subtype', 'date_created', 'date_modified',
            'version', 'acg', 'owner', 'ext_type']

    Returns:
            List of datasets.
    """
    return Dataset._list_all(connection, name=name, to_dictionary=to_dictionary,
                             to_dataframe=to_dataframe, limit=limit, **filters)


class Dataset(Entity, VldbMixin):
    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 name: Optional[str] = None):
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
                msg = (f"There is no {self.__class__.__name__} associated with "
                       f"the given name: '{name}'")
                raise ValueError(msg)
        super().__init__(connection=connection, object_id=id, name=name)

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter Dataset name or/and description.

        Args:
            name: new name of the Dataset
            description: new description of the Dataset
        """
        func = self.alter
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__  # type: ignore
        default_dict = dict(zip(args[-len(defaults):], defaults)) if defaults else {}
        local = locals()
        properties = {}
        for property_key in default_dict.keys():
            if local[property_key] is not None:
                properties[property_key] = local[property_key]
        self._alter_properties(**properties)

    @classmethod
    def _list_all(cls, connection: Connection, name: Optional[str] = None,
                  to_dictionary: bool = False, to_dataframe: bool = False,
                  limit: Optional[int] = None,
                  **filters) -> Union[List["Dataset"], List[dict], DataFrame]:
        DATASET_SUBTYPES = [776, 779]
        DSS_XML_SEARCH_TYPE_EXACTLY = 2

        msg = "Error creating an instance for searching objects"
        res_e = objects.create_search_objects_instance(connection=connection, name=name,
                                                       pattern=DSS_XML_SEARCH_TYPE_EXACTLY,
                                                       object_type=cls._OBJECT_TYPE.value,
                                                       error_msg=msg)
        search_id = res_e.json()['id']
        msg = "Error retrieving datasets from the environment."
        res_o = helper.fetch_objects_async(
            connection,
            api=objects.get_objects,
            async_api=objects.get_objects_async,
            dict_unpack_value=None,
            limit=limit,
            chunk_size=1000,
            error_msg=msg,
            filters=filters,
            search_id=search_id,
        )
        datasets = [r for r in res_o if r['subtype'] in DATASET_SUBTYPES]

        if to_dictionary:
            return datasets
        elif to_dataframe:
            return DataFrame(datasets)
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in datasets]
