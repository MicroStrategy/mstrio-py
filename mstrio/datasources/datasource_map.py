import logging
from collections.abc import Callable
from typing import Any

from mstrio import config
from mstrio.api import datasources, objects
from mstrio.connection import Connection
from mstrio.datasources import DatasourceConnection, DatasourceInstance, DatasourceLogin
from mstrio.server.language import Language, list_languages
from mstrio.server.project import Project
from mstrio.users_and_groups import User, UserGroup
from mstrio.utils import helper
from mstrio.utils.entity import DeleteMixin, Entity, EntityBase, ObjectTypes
from mstrio.utils.helper import delete_none_values, deprecation_warning, get_objects_id
from mstrio.utils.resources import locales
from mstrio.utils.version_helper import method_version_handler

logger = logging.getLogger(__name__)


class Locale(Entity):
    """Object representation of Microstrategy Locale

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
        certified_info: Certification status, time of certification, and
            information about the certifier (currently only for document and
            report)
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.LOCALE
    _API_GETTERS = {
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
        ): objects.get_object_info,
    }
    _FROM_DICT_MAP = {**Entity._FROM_DICT_MAP, 'owner': User.from_dict}

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        name: str | None = None,
        abbreviation: str | None = None,
    ):
        """Initialize the Locale object and populate it with I-Server data.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            id: Locale's ID
            name: Locale's name
            abbreviation: Locale's abbreviation
        """
        deprecation_warning(
            deprecated='Locale, list_locales',
            new='Language, list_languages',
            version='11.3.11.102',  # NOSONAR
            module=False,
        )
        if not (id or name or abbreviation):
            raise ValueError(
                "Please specify 'id' or 'name' or 'abbreviation' parameter in the "
                "constructor."
            )
        elif not (locale_id := id):
            if name:
                locale_id = self._get_by_name(name, connection).id
            elif abbreviation:
                locale_id = self._get_by_abbreviation(abbreviation, connection).id

        super().__init__(connection=connection, object_id=locale_id)

    @staticmethod
    def _list(connection: 'Connection', to_dictionary: bool = False):
        if to_dictionary:
            return locales.get_locales(connection=connection)

        return [
            Locale.from_dict(locale, connection)
            for locale in locales.get_locales(connection=connection)
        ]

    @staticmethod
    def _get(connection: Connection, query: str) -> type['Locale']:
        try:
            return Locale._get_by_id(id=query, connection=connection)
        except ValueError:
            pass

        try:
            return Locale._get_by_name(name=query, connection=connection)
        except ValueError:
            pass

        try:
            return Locale._get_by_abbreviation(
                abbreviation=query, connection=connection
            )
        except ValueError:
            raise ValueError(
                f'Locale with id or name or abbreviation: {query} does not exists.'
            )

    @staticmethod
    def _get_by_id(id: str, connection: 'Connection') -> type['Locale']:
        data = [loc for loc in locales.get_locales(connection) if loc['id'] == id]

        try:
            return Locale.from_dict(data[0], connection)
        except LookupError:
            raise ValueError(f"Locale with id: {id} does not exists.")

    @staticmethod
    def _get_by_name(name: str, connection: 'Connection') -> type['Locale']:
        data = [loc for loc in locales.get_locales(connection) if loc['name'] == name]

        try:
            return Locale.from_dict(data[0], connection)
        except LookupError:
            raise ValueError(f"Locale with name: {name} does not exists.")

    @staticmethod
    def _get_by_abbreviation(
        abbreviation: str, connection: 'Connection'
    ) -> type['Locale']:
        data = [
            locale
            for locale in locales.get_locales(connection=connection)
            if locale['abbreviation'] == abbreviation
        ]

        try:
            return Locale.from_dict(data[0], connection)
        except LookupError:
            raise ValueError(
                f"Locale with abbreviation: {abbreviation} does not exists."
            )

    def __repr__(self):
        return (
            f"Locale(connection, name='{self.name}', abbreviation='"
            f"{self.abbreviation}',"
            f" id='{self.id}')"
        )

    def to_dict(self, camel_case: bool = True) -> dict:
        return {'id': self.id, 'name': self.name}


def list_locales(
    connection: 'Connection', to_dictionary: bool = False
) -> list[Locale] | list[dict]:
    """Get list of locales as objects or dicts.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            Locale objects.

    Returns:
        list['Locale'] by default
        list[dict] if `to_dictionary` is True

    Examples:
        >>> list_locales(connection)
    """
    deprecation_warning(
        deprecated='Locale, list_locales',
        new='Language, list_languages',
        version='11.3.11.102',  # NOSONAR
        module=False,
    )
    return Locale._list(connection, to_dictionary)


@method_version_handler('11.3.0000')
def list_datasource_mappings(
    connection: 'Connection',
    project: Project | str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    user: User | UserGroup | str | None = None,
    ds_connection: DatasourceConnection | str | None = None,
    datasource: DatasourceInstance | str | None = None,
    login: DatasourceLogin | str | None = None,
    locale: Language | Locale | str | None = None,
    default_connection_map: bool = False,
) -> list['DatasourceMap'] | list[dict]:
    """Get list of connection mappings: objects or dicts.
    Optionally filter by specifying filters.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        default_connection_map: True if requesting default connection mappings.
            Default False
        project: The project (or its id) which mappings are to be fetched.
            Optional unless requesting the default mappings.
        to_dictionary: If True returns dict, by default (False) returns
            DatasourceMap objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        locale: filter list by locale
        login: filter list by datasource login
        datasource: filter list by datasource instance
        ds_connection: filter list by datasource connection
        user: filter list by user or user group

    Returns:
        list['DatasourceMap'] by default
        list[dict] if `to_dictionary` is True

    Examples:
        >>> list_datasource_mappings(connection)
    """
    return DatasourceMap._list(
        connection=connection,
        project=project,
        to_dictionary=to_dictionary,
        limit=limit,
        user=user,
        ds_connection=ds_connection,
        datasource=datasource,
        login=login,
        locale=locale,
        default_connection_map=default_connection_map,
    )


class DatasourceMap(EntityBase, DeleteMixin):
    """Object representation of MicroStrategy Connection Mapping

    The connection mapping provides mapping between a user or a user group
    and a datasource login for the given datasource and datasource connection.

    Attributes:
        connection: A MicroStrategy connection object
        id: ID of connection mapping.
        project: The project the mapping is assigned to.
        default_connection_map: Whether the mapping is the default
            for the project.
        ds_connection: The mapped Datasource Connection
        datasource: The mapped Datasource Instance
        user: The mapped User or UserGroup
        login: The mapped Datasource Login
        locale: The mapping's locale. When empty, it's equivalent to 'default'
            in Workstation and means that default locale for the environment
            will be used.
    """

    _API_GETTERS: dict[str | tuple, Callable] = {
        (
            'id',
            'projectId',
            'connection',
            'datasource',
            'user',
            'login',
            'locale',
        ): datasources.get_datasource_mapping,
    }
    _API_PATCH: list[Callable] = []
    _API_DELETE = staticmethod(datasources.delete_datasource_mapping)
    _FROM_DICT_MAP = {
        'ds_connection': DatasourceConnection.from_dict,
        'datasource': DatasourceInstance.from_dict,
        'user': lambda source, connection: (
            User.from_dict(source, connection)
            if User.from_dict(source, connection).subtype == 8704
            else UserGroup.from_dict(source, connection)
        ),
        'login': DatasourceLogin.from_dict,
        'locale': Language.from_dict,
        'project': lambda source, connection: Project.from_dict(
            {'id': source}, connection
        ),
    }
    _REST_ATTR_MAP = {
        # 'connection': 'ds_connection',
        'project_id': 'project'
    }

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        project: Project | str | None = None,
        default_connection_map: bool = False,
        ds_connection: DatasourceConnection | None = None,
        datasource: DatasourceInstance | None = None,
        user: User | UserGroup | None = None,
        login: DatasourceLogin | None = None,
        locale: Language | Locale | None = None,
    ):
        """Initialise connection mapping by passing the ID or by passing
        True for `default_connection_map` and the project for which to
        fetch the default mapping.

        To list all connection mappings use the
        `list_datasource_mappings()` method.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id: ID of connection mapping
            project: Project object or ID for restricting the search to
                just this project.
            default_connection_map: Whether to fetch the project's
                default mapping.
        """
        if id is None:
            if project is None or not default_connection_map:
                raise ValueError(
                    "Please either specify the `id` or `default_connection_map` and"
                    " the `project` to find the default mapping for the given project."
                )

            mappings: list[dict] = self._list(
                connection=connection,
                default_connection_map=True,
                project=project,
                to_dictionary=True,
            )

            if not mappings:
                project_id = get_objects_id(project, Project)

                raise ValueError(
                    f"The project: {project_id} has no default datasource mapping."
                )
            elif len(mappings) > 1:
                project_id = get_objects_id(project, Project)

                raise ValueError(
                    f"The project: {project_id} has more than one default connection "
                    f"mapping."
                )
            else:
                data = mappings[0]
                data.update({'ds_connection': data.pop('connection')})
                self._init_variables(connection=connection, **mappings[0])

        else:
            super().__init__(
                connection,
                id,
                default_connection_map=default_connection_map,
                project_id=project,
            )

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        if project_id := kwargs.get('project_id'):
            self.project = Project.from_dict({'id': project_id}, self.connection)
            self._project_id = project_id

        if ds_connection := kwargs.get('ds_connection'):
            self.ds_connection = DatasourceConnection.from_dict(
                ds_connection, self.connection
            )

        if datasource := kwargs.get('datasource'):
            self.datasource = DatasourceInstance.from_dict(datasource, self.connection)

        if user := kwargs.get('user'):
            self.user = User.from_dict(user, self.connection)

            if self.user.subtype == 8705:
                self.user = UserGroup.from_dict(user, self.connection)

        if login := kwargs.get('login'):
            self.login = DatasourceLogin.from_dict(login, self.connection)

        if locale := kwargs.get('locale'):
            self.locale = Language.from_dict(locale, self.connection)
        else:
            self.locale = None

        self.default_connection_map = kwargs.get('default_connection_map')

    @classmethod
    def _list(
        cls,
        connection: 'Connection',
        project: Project | str | None = None,
        to_dictionary: bool = False,
        limit: int | None = None,
        user: User | UserGroup | str | None = None,
        ds_connection: DatasourceConnection | str | None = None,
        datasource: DatasourceInstance | str | None = None,
        login: DatasourceLogin | str | None = None,
        locale: Language | Locale | str | None = None,
        default_connection_map: bool = False,
    ) -> list['DatasourceMap'] | list[dict]:
        project_id = get_objects_id(project, Project)

        if isinstance(locale, Locale):
            locale = locale.to_dict()
        if isinstance(locale, Language):
            locale = {'id': locale.id, 'name': locale.name}
        elif isinstance(locale, str):
            locale = DatasourceMap._get_locale(connection=connection, query=locale)
            locale = {'id': locale.id, 'name': locale.name}

        filters = delete_none_values(
            delete_none_values(
                {
                    'user': {
                        'id': get_objects_id(user, User)
                        or get_objects_id(user, UserGroup),
                    },
                    'connection': {
                        'id': get_objects_id(ds_connection, DatasourceConnection),
                    },
                    'datasource': {
                        'id': get_objects_id(datasource, DatasourceInstance),
                    },
                    'login': {
                        'id': get_objects_id(login, DatasourceLogin),
                    },
                    'locale': locale,
                },
                recursion=True,
            ),
            recursion=False,
        )

        mappings = helper.fetch_objects(
            connection=connection,
            api=datasources.get_datasource_mappings,
            project_id=project_id,
            limit=limit,
            dict_unpack_value='mappings',
            default_connection_map=default_connection_map,
            filters=filters if filters else None,
        )

        if to_dictionary:
            return mappings
        else:
            return [
                cls.from_dict(source=item, connection=connection) for item in mappings
            ]

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        project: Project | str,
        user: User | UserGroup | str,
        ds_connection: DatasourceConnection | str,
        datasource: DatasourceInstance | str,
        login: DatasourceLogin | str,
        locale: Language | Locale | str | None = None,
        locale_id: str | None = None,
        locale_name: str | None = None,
    ) -> 'DatasourceMap':
        """Create a new connection mapping on the server.
        If more than one locale related parameters are provided,
        `locale` has priority, then `locale_id`.

        Args:
            connection: A MicroStrategy connection object
            project: The project the mapping is to be assigned to
            user: The User or UserGroup to be mapped
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
        user_id = get_objects_id(user, User) or get_objects_id(user, UserGroup)
        connection_id = get_objects_id(ds_connection, DatasourceConnection)
        datasource_id = get_objects_id(datasource, DatasourceInstance)
        login_id = get_objects_id(login, DatasourceLogin)
        body = {
            'projectId': project_id,
            'user': {'id': user_id},
            'connection': {'id': connection_id},
            'datasource': {'id': datasource_id},
            'login': {'id': login_id},
        }
        if locale and isinstance(locale, Locale):
            body['locale'] = locale.to_dict()
        if locale and isinstance(locale, Language):
            body['locale'] = {'id': locale.id, 'name': locale.name}
        elif locale and isinstance(locale, str):
            locale = DatasourceMap._get_locale(connection=connection, query=locale)
            body['locale'] = {'id': locale.id, 'name': locale.name}
        elif locale_id and isinstance(locale_id, str):
            locale = Language(connection=connection, id=locale_id)
            body['locale'] = {'id': locale.id, 'name': locale.name}
        elif locale_name and isinstance(locale_name, str):
            locale = Language(connection=connection, name=locale_name)
            body['locale'] = {'id': locale.id, 'name': locale.name}

        response_data = datasources.create_datasource_mapping(
            connection=connection, body=body
        ).json()
        if config.verbose:
            logger.info(
                "Successfully created datasource connection mapping with ID:"
                f" '{response_data.get('id')}'"
            )
        return cls.from_dict(
            source=helper.camel_to_snake(response_data), connection=connection
        )

    @staticmethod
    def __translate_names(name: str):
        return 'ds_connection' if name == 'connection' else name

    @classmethod
    def from_dict(
        cls,
        source: dict[str, Any],
        connection: 'Connection',
        to_snake_case: bool = True,
    ) -> 'DatasourceMap':
        data = {cls.__translate_names(key): val for key, val in source.items()}
        return super().from_dict(data, connection, to_snake_case)

    def to_dict(self, camel_case=True):
        data = super().to_dict(camel_case=camel_case)
        return {self.__translate_names(key): val for key, val in data.items()}

    def alter(
        self,
        user: User | UserGroup | str | None = None,
        ds_connection: DatasourceConnection | str | None = None,
        datasource: DatasourceInstance | str | None = None,
        login: DatasourceLogin | str | None = None,
        locale: Language | Locale | str | None = None,
    ):
        """Replace the connection mapping with a newly created one
        with field values copied unless new ones are specified.

        Args:
            connection: A MicroStrategy connection object
            user: The User or UserGroup to be mapped
            ds_connection: The Datasource Connection to be mapped
            datasource: The Datasource Instance to be mapped
            login: The Datasource Login to be mapped
            locale: The locale to be mapped

        Returns:
            DatasourceMap object
        """
        if (
            user is None
            and ds_connection is None
            and datasource is None
            and login is None
            and locale is None
        ):
            if config.verbose:
                logger.info(
                    f"No changes specified for {type(self).__name__} with ID:'"
                    f"{self.id}'."
                )
            return

        self.delete(force=True)

        new_conn_map = self.create(
            connection=self.connection,
            project=self.project,
            user=user or self.user,
            ds_connection=ds_connection or self.ds_connection,
            datasource=datasource or self.datasource,
            login=login or self.login,
            locale=locale or self.locale,
        )
        self._id = new_conn_map.id
        self.fetch()

    def _get_locale(connection: Connection, query: str):
        locales_list = list_languages(connection=connection, base_language_lcid=0)
        for locale in locales_list:
            if query in [locale.id, locale.name, locale.abbreviation]:
                return locale
        raise ValueError(
            f'Locale with id or name or abbreviation: {query} does not exists.'
        )
