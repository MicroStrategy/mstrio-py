import logging
from enum import auto
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import administration
from mstrio.connection import Connection
from mstrio.server.project import Project
from mstrio.users_and_groups.user_group import UserGroup
from mstrio.utils.entity import ChangeJournalMixin, DeleteMixin, EntityBase
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import fetch_objects, find_object_with_name
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.users_and_groups.user import User

logger = logging.getLogger(__name__)


class FenceType(AutoName):
    USER_FENCE = auto()
    WORKLOAD_FENCE = auto()


@method_version_handler('11.3.0800')
def list_fences(
    connection: Connection,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list['Fence'] | list[dict]:
    """Get list of fences.

    Args:
        connection (Connection): Strategy One connection object returned by
            `connection.Connection()`
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns objects.
        limit (int, optional): limit the number of elements returned. If `None`
            (default), all objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type', 'rank']

    Returns:
        A list of fences objects or dictionaries representing them.
    """

    fences = fetch_objects(
        connection=connection,
        api=administration.list_fences,
        to_dictionary=to_dictionary,
        filters=filters,
        limit=limit,
        dict_unpack_value='fences',
    )

    if to_dictionary:
        return fences
    return [Fence.from_dict(fence, connection) for fence in fences]


@class_version_handler('11.3.0800')
class Fence(EntityBase, ChangeJournalMixin, DeleteMixin):
    """Python representation of a Strategy One Fence object.

    Attributes:
        id (str): ID of the fence.
        name (str): Name of the fence.
        rank (int): Rank or precedence of the fence.
        type (FenceType): Type of fence.
        nodes (list[str]): List of nodes across which the fence is applied.
        users (list[User]): List of users, to which the fence is applied.
        user_groups (list[UserGroup]): List of user groups, to which the fence
            is applied.
        projects (list[Project]): List of projects, to which the fence
            is applied.
    """

    _REST_ATTR_MAP = {
        'usergroups': 'user_groups',
    }

    _API_GETTERS = {
        (
            'id',
            'name',
            'rank',
            'type',
            'nodes',
            'users',
            'user_groups',
            'projects',
        ): administration.get_fence
    }

    _API_DELETE = staticmethod(administration.delete_fence)

    @staticmethod
    def _parse_users(
        source: list[dict], connection: 'Connection', to_snake_case: bool = True
    ):
        from mstrio.users_and_groups.user import User

        return [
            User.from_dict(content, connection, to_snake_case) for content in source
        ]

    _FROM_DICT_MAP = {
        'type': FenceType,
        'users': _parse_users,
        'user_groups': lambda source, connection: [
            UserGroup.from_dict(content, connection) for content in source
        ],
        'projects': lambda source, connection: [
            Project.from_dict(content, connection) for content in source
        ],
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initializes a new instance of a Fence class

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            id (str, Optional): ID of the fence.
            name (str, Optional): Name of the fence.

        Note:
            Parameter `name` is not used when fetching. If only `name` parameter
            is provided, `id` will be found automatically if such object exists.

        Raises:
            ValueError: if both `id` and `name` are not provided
                or if Fence with the given `name` doesn't exist.
        """

        if not id:
            if name:
                fence = find_object_with_name(
                    connection=connection,
                    cls=self.__class__,
                    name=name,
                    listing_function=list_fences,
                )
                id = fence['id']
            else:
                raise ValueError("Please provide either 'id' or 'name' argument.")

        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.name = kwargs.get('name')
        self.rank = kwargs.get('rank')
        self.nodes = kwargs.get('nodes')
        self.users = kwargs.get('users')
        self.user_groups = kwargs.get('user_groups')
        self.projects = kwargs.get('projects')
        self._type = kwargs.get('type')

    @staticmethod
    def _prepare_fence_body(
        rank: int | None,
        name: str | None,
        type: FenceType | None,
        nodes: str | list[str] | None,
        users: 'User | list[User] | None',
        user_groups: UserGroup | list[UserGroup] | None,
        projects: Project | list[Project] | None,
    ) -> dict:
        from mstrio.users_and_groups.user import User

        def to_list_or_none(item, cls) -> list | None:
            if isinstance(item, cls):
                return [item]
            return item if isinstance(item, list) else None

        nodes = to_list_or_none(nodes, str)
        users = to_list_or_none(users, User)
        user_groups = to_list_or_none(user_groups, UserGroup)
        projects = to_list_or_none(projects, Project)

        body = {
            'rank': rank,
            'name': name,
            'type': get_enum_val(type, FenceType) if type else None,
            'nodes': nodes,
            'users': (
                [{'id': user.id, 'name': user.name} for user in users]
                if users is not None
                else None
            ),
            'usergroups': (
                [
                    {'id': user_group.id, 'name': user_group.name}
                    for user_group in user_groups
                ]
                if user_groups is not None
                else None
            ),
            'projects': (
                [{'id': project.id, 'name': project.name} for project in projects]
                if projects is not None
                else None
            ),
        }
        return body

    @classmethod
    def create(
        cls,
        connection: Connection,
        rank: int,
        name: str,
        type: FenceType,
        nodes: str | list[str],
        users: 'User | list[User] | None' = None,
        user_groups: UserGroup | list[UserGroup] | None = None,
        projects: Project | list[Project] | None = None,
    ) -> 'Fence':
        """Create a new Fence.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            rank (int): Rank or precedence of the fence.
            name (str): Name of the fence.
            type (FenceType): Type of fence.
            nodes (str | list[str]): List of nodes across which the fence
                is applied.
            users (User | list[User], optional):  List of users, to which the
                fence is applied.
            user_groups (UserGroup | list[UserGroup], optional):
                List of user groups, to which the fence is applied.
            projects (Project | list[Project], optional): List of projects,
                to which the fence is applied.

        Returns:
            Fence object
        """

        if type == FenceType.USER_FENCE and not any([users, user_groups]):
            raise ValueError(
                "At least one of the following parameters must be provided: "
                "`users` or `user_groups`."
            )

        body = cls._prepare_fence_body(
            rank, name, type, nodes, users, user_groups, projects
        )
        fence = cls.from_dict(
            source=administration.create_fence(connection=connection, body=body).json(),
            connection=connection,
        )
        fence.fetch()
        if config.verbose:
            logger.info(
                f"Successfully created Fence named: '{name}' with ID: '{fence.id}'"
            )
        return fence

    def alter(
        self,
        rank: int | None = None,
        nodes: str | list[str] | None = None,
        users: 'User | list[User] | None' = None,
        user_groups: UserGroup | list[UserGroup] | None = None,
        projects: Project | list[Project] | None = None,
    ) -> None:
        """Alter the Fence object.

        Args:
            rank (int, optional): Rank or precedence of the fence.
            nodes (str | list[str], optional): List of nodes across which the
                fence is applied.
            users (User | list[User], optional):  List of users, to which
                the fence is applied.
            user_groups (UserGroup | list[UserGroup], optional):
                List of user groups, to which the fence is applied.
            projects (Project | list[Project], optional): List of projects,
                to which the fence is applied.
        """
        body = self._prepare_fence_body(
            rank, None, None, nodes, users, user_groups, projects
        )
        operation_list = [
            {'op': 'replace', 'path': path, 'value': value}
            for path, value in [
                ('/rank', body.get('rank')),
                ('/nodes', body.get('nodes')),
                ('/users', body.get('users')),
                ('/usergroups', body.get('usergroups')),
                ('/projects', body.get('projects')),
            ]
            if value is not None
        ]

        response = administration.update_fence(
            connection=self.connection,
            id=self.id,
            body={'operationList': operation_list},
        ).json()
        if config.verbose:
            logger.info(f"Successfully altered Fence ID: {self.id}")
        self._set_object_attributes(**response)

    @property
    def type(self) -> FenceType:
        return self._type
