import logging
from typing import Any, Callable, Dict, List, Optional, Union

from requests import HTTPError

from mstrio import config
from mstrio.api import datasources, objects
from mstrio.connection import Connection
from mstrio.datasources import DatasourceConnection, DatasourceInstance, DatasourceLogin
from mstrio.server.project import Project
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import Entity, EntityBase, ObjectTypes
from mstrio.utils.helper import get_objects_id

logger = logging.getLogger(__name__)


def list_datasource_mappings(
        connection: Connection, default_connection_map: bool = False,
        project: Optional[Union[Project, str]] = None, to_dictionary: bool = False,
        limit: Optional[int] = None, **filters) -> \
        Union["DatasourceMap", List["DatasourceMap"], dict, List[dict], None]:
    """Get list of DatasourceLogin objects or dicts. Optionally filter the
    logins by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        default_connection_map: True if connection map is default
            Connection Map. Default False
        project: The project (or its id) which maps are to be fetched.
            Optional unless requesting the default map.
        to_dictionary: If True returns dict, by default (False) returns
            User objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['id', 'name', 'description',
            'date_created', 'date_modified', 'acg']

    Returns:
        List["DatasourceMap"] by default
        List[dict] if `to_dict` is True
        DatasourceMap if default map was requested
        dict if default map was requested and `to_dict` is `True`
        None if default map was requested but doesn't exist.

    Examples:
        >>> list_datasource_mappings(connection, name='db_login_name')
    """
    return DatasourceMap._list(connection=connection,
                               default_connection_map=default_connection_map, project=project,
                               to_dictionary=to_dictionary, limit=limit, **filters)


class Locale(Entity):
    _DELETE_NONE_VALUES_RECURSION = True
    _OBJECT_TYPE = ObjectTypes.LOCALE
    _API_GETTERS = {
        ('name', 'id'): objects.get_object_info,
    }

    def __init__(self, connection: Connection, id: str):
        """Initialize the Locale object and populate it with I-Server data.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Locale ID
        """
        if id is None:
            raise AttributeError("Please specify 'id' parameter in the constructor.")
        else:
            super().__init__(connection=connection, object_id=id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)


class DatasourceMap(EntityBase):
    """Object representation of MicroStrategy Datasource Map Object

    The Datasource Map provides mapping between a user and a datasource login
    for the given datasource and datasource connection.

    Attributes:
        connection: A MicroStrategy connection object
        id: The Map's ID.
        project: The project the Map is assigned to.
        default_connection_map: Whether the Map is the default
            for the project.
        ds_connection: The mapped Datasource Connection
        datasource: The mapped Datasource Instance
        user: The mapped User
        login: The mapped Datasource Login
        locale: The Map's locale
    """
    _DELETE_NONE_VALUES_RECURSION = True
    _API_GETTERS: Dict[Union[str, tuple], Callable] = {
        ('id', 'projectId', 'connection', 'datasource', 'user', 'login',
         'locale'): datasources.get_datasource_mapping,
    }
    _API_PATCH: List[Callable] = []
    _FROM_DICT_MAP = {
        "ds_connection": DatasourceConnection.from_dict,
        "datasource": DatasourceInstance.from_dict,
        "user": User.from_dict,
        "login": DatasourceLogin.from_dict,
        "locale": Locale.from_dict
    }

    def __init__(self, connection: Connection, id: Optional[str] = None,
                 project: Optional[Union[Project,
                                         str]] = None, default_connection_map: bool = False,
                 ds_connection: Optional["DatasourceConnection"] = None,
                 datasource: Optional["DatasourceInstance"] = None, user: Optional["User"] = None,
                 login: Optional["DatasourceLogin"] = None, locale: Optional[Locale] = None):
        """Initialise Datasource Map object by passing the ID or by passing
        True for `default_connection_map` and the project for which to
        fetch the default map.

        To explore all available DatasourceMap objects use the
        `list_datasource_mappings()` method.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id: ID of Datasource Map
            project: Project object or ID for restricting the search to
                just this project.
            default_connection_map: Whether to fetch the project's
                default map.
        """
        if id is None:
            if project is None or not default_connection_map:
                helper.exception_handler(
                    "Please either specify the `id` or `default_connection_map` and"
                    " the `project` to find the default map for the given project.")
            else:
                mapping: DatasourceMap = self._list(connection, True, project)
                if mapping:
                    mapping = mapping[0]
                    id = mapping.id
                    ds_connection = mapping.ds_connection
                    datasource = mapping.datasource
                    user = mapping.user
                    login = mapping.login
                    self.__init__(connection, id, project, default_connection_map, ds_connection,
                                  datasource, user, login, locale)
                else:
                    helper.exception_handler(
                        f"The project {project} has no default datasource map.",
                        exception_type=ValueError)
        else:
            super().__init__(connection, id, project=project,
                             default_connection_map=default_connection_map,
                             ds_connection=ds_connection, datasource=datasource, user=user,
                             login=login, locale=locale)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.project: str = kwargs.get("project")
        self.default_connection_map: bool = kwargs.get("default_connection_map")
        self.ds_connection = kwargs.get("ds_connection")
        self.datasource = kwargs.get("datasource")
        self.user = kwargs.get("user")
        self.login = kwargs.get("login")
        self.locale = kwargs.get("locale")

    def delete(self, force: bool = False) -> bool:
        """Deletes the DatasourceMap.

        Note: Default connection maps cannot be deleted.

        Args:
            force: If True, no additional prompt will be shown before deleting.
                Default False.

        Returns:
            True for success. False otherwise.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to delete datasource map with ID: {self.id}? [Y/N]: ")
        if force or user_input == 'Y':
            response = datasources.delete_datasource_mapping(self.connection, self.id)
            if response.status_code == 204 and config.verbose:
                logger.info(f"Successfully deleted datasource map with ID: '{self.id}'")
            return response.ok
        else:
            return False

    @classmethod
    def _list(cls, connection: Connection, default_connection_map: Optional[bool] = False,
              project: Optional[Union[Project, str]] = None, to_dictionary: bool = False,
              limit: Optional[int] = None, **filters) -> Union[List["DatasourceMap"], List[dict]]:
        project_id = project.id if isinstance(project, Project) else project
        try:
            mappings = helper.fetch_objects(connection=connection,
                                            api=datasources.get_datasource_mappings,
                                            default_connection_map=default_connection_map,
                                            project_id=project_id, limit=limit,
                                            dict_unpack_value="mappings", filters=filters)
        except HTTPError as err:
            if err.errno == 404:
                if config.verbose:
                    logger.info('No mapping found.')
                return None
            else:
                raise err
        if to_dictionary:
            return mappings
        else:
            return [cls.from_dict(source=elem, connection=connection) for elem in mappings]

    @classmethod
    def create(cls, connection: Connection, project: Union[Project, str],
               user: Union[User, str], ds_connection: Union[DatasourceConnection, str],
               datasource: Union[DatasourceInstance, str], login: Union[DatasourceLogin, str],
               locale: Optional[Locale] = None, locale_id: Optional[str] = None,
               locale_name: Optional[str] = None) -> "DatasourceMap":
        """Create a new Datasource Map object on the server.
        If more than one locale related parameters are provided,
        `locale` has priority, then `locale_id`.

        Args:
            connection: A MicroStrategy connection object
            project: The project the Map is to be assigned to
            user: The User to be mapped
            ds_connection: The Datasource Connection to be mapped
            datasource: The Datasource Instance to be mapped
            login: The Datasource Login to be mapped
            locale: The locale to be mapped.
            locale_id: The id of locale to be mapped.
            locale_name: The name of locale to be mapped.

        Returns:
            DatasourceMap object
        """
        project_id = get_objects_id(project, Project)
        user_id = get_objects_id(user, User)
        connection_id = get_objects_id(ds_connection, DatasourceConnection)
        datasource_id = get_objects_id(datasource, DatasourceInstance)
        login_id = get_objects_id(login, DatasourceLogin)
        body = {
            "projectId": project_id,
            "user": {
                "id": user_id
            },
            "connection": {
                "id": connection_id
            },
            "datasource": {
                "id": datasource_id
            },
            "login": {
                "id": login_id
            },
        }
        if locale and isinstance(locale, Locale):
            body["locale"] = locale.to_dict()
        elif locale_id and isinstance(locale_id, str):
            body["locale"] = {"id": locale}
        elif locale_name and isinstance(locale_name, str):
            body["locale"] = {"name": locale}

        jresponse = datasources.create_datasource_mapping(connection=connection, body=body).json()
        if config.verbose:
            logger.info(
                f"Successfully created datasource connection map with ID: '{jresponse.get('id')}'"
            )
        return cls.from_dict(source=helper.camel_to_snake(jresponse), connection=connection)

    # TODO: improve to/from dict methods to allow renaming
    # on _FROM_DICT_MAP level.

    @classmethod
    def from_dict(cls, source: Dict[str, Any], connection: Connection) -> "DatasourceMap":

        def translate_names(name: str):
            if name == "connection":
                return "ds_connection"
            elif name == "project_id":
                return "project"
            else:
                return name

        modified_source = {translate_names(key): val for key, val in source.items()}
        return super(EntityBase, cls).from_dict(modified_source, connection)

    def to_dict(self, camel_case):

        def translate_names(name: str):
            if name == "ds_connection":
                return "connection"
            elif name == "project":
                return "project_id"
            else:
                return name

        thedict = super().to_dict(camel_case=camel_case)
        return {translate_names(key): val for key, val in thedict.items()}
