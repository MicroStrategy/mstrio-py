from typing import List, Optional, Union

from pandas import DataFrame

from mstrio.api import documents
from mstrio.connection import Connection
from mstrio.project_objects.document import Document
from mstrio.server.environment import Environment
from mstrio.utils import helper


def list_dossiers(connection: Connection, name: Optional[str] = None, to_dictionary: bool = False,
                  to_dataframe: bool = False, limit: Optional[int] = None,
                  **filters) -> List["Dossier"]:
    """Get all Dossiers stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact name of the document to list
        to_dictionary(bool, optional): if True, return Dossiers as
            list of dicts
        to_dataframe(bool, optional): if True, return Dossiers as
            pandas DataFrame
        limit(int): limit the number of elements returned to a sample of
            dossiers
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
            List of dossiers.
    """
    if connection.project_id is None:
        msg = ("Please log into a specific project to load dossiers within it. To load "
               "all dossiers across the whole environment use "
               f"{list_dossiers_across_projects.__name__} function")
        raise ValueError(msg)
    return Dossier._list_all(connection, to_dictionary=to_dictionary, name=name, limit=limit,
                             to_dataframe=to_dataframe, **filters)


def list_dossiers_across_projects(connection: Connection, name: Optional[str] = None,
                                  to_dictionary: bool = False, to_dataframe: bool = False,
                                  limit: Optional[int] = None, **filters) -> List["Dossier"]:
    """Get all Dossiers stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        name: exact names of the dossiers to list
        to_dictionary(bool, optional): if True, return Dossiers as
            list of dicts
        to_dataframe(bool, optional): if True, return Dossiers as
            pandas DataFrame
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'subtype', 'date_created', 'date_modified', 'version', 'acg',
            'owner', 'ext_type', 'view_media', 'certified_info', 'project_id']

    Returns:
        List of documents.
    """
    project_id_before = connection.project_id
    env = Environment(connection)
    projects = env.list_projects()
    output = []
    for project in projects:
        connection.select_project(project_id=project.id)
        output.extend(
            Dossier._list_all(connection, to_dictionary=to_dictionary, name=name, limit=limit,
                              to_dataframe=to_dataframe, **filters))
        output = list(set(output))
    connection.select_project(project_id=project_id_before)
    return output


class Dossier(Document):
    _DELETE_NONE_VALUES_RECURSION = True

    @classmethod
    def _list_all(cls, connection: Connection, name: Optional[str] = None,
                  to_dictionary: bool = False, to_dataframe: bool = False,
                  limit: Optional[int] = None,
                  **filters) -> Union[List["Dossier"], List[dict], DataFrame]:
        msg = "Error retrieving documents from the environment."
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either to_dictionary=True or to_dataframe=True, but not both.",
                ValueError)
        objects = helper.fetch_objects_async(connection, api=documents.get_dossiers,
                                             async_api=documents.get_dossiers_async,
                                             dict_unpack_value='result', limit=limit,
                                             chunk_size=1000, error_msg=msg, filters=filters,
                                             search_term=name)
        if to_dictionary:
            return objects
        elif to_dataframe:
            return DataFrame(objects)
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]
