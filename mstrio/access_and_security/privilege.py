from typing import List, Optional, Union, TYPE_CHECKING

from pandas import DataFrame

from mstrio.api import security
from mstrio.connection import Connection
from mstrio.users_and_groups.user_group import UserGroup
from mstrio.utils import helper
from mstrio.utils.entity import EntityBase
from mstrio.utils.version_helper import class_version_handler

if TYPE_CHECKING:
    from mstrio.users_and_groups.user import User


@class_version_handler('11.2.0100')
class Privilege(EntityBase):
    """Object representation of MicroStrategy Privilege object.

    Attributes:
        connection: A MicroStrategy connection object
        id: privilege ID
        name: privilege name
        description: privilege description
        categories: privilege category
        is_project_level_privilege: specify if privilege is compatible with
            server configuration level or project level
    """

    def __init__(
        self, connection: Connection, name: Optional[str] = None, id: Optional[str] = None
    ) -> None:
        """Initialize Privilege object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted. To explore all available
        privileges use the `list_privileges()` method.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            name: exact name of privilege
            id: ID of privilege
        """
        if name is None and id is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.",
                exception_type=ValueError
            )

        if name is None or (name and id):
            privileges = Privilege.list_privileges(
                connection=connection, to_dictionary=True, id=str(id)
            )
            if privileges:
                [privilege] = privileges
                self._set_object_attributes(**privilege)
            else:
                helper.exception_handler(
                    f"There is no Privilege with the given id: '{id}'", exception_type=ValueError
                )
        if id is None:
            privileges = Privilege.list_privileges(
                connection=connection, to_dictionary=True, name=name
            )
            if privileges:
                [privilege] = privileges
                self._set_object_attributes(**privilege)
            else:
                helper.exception_handler(
                    f"There is no Privilege with the given name: '{name}'",
                    exception_type=ValueError
                )
        super().__init__(connection, self.id, name=self.name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._is_project_level_privilege = kwargs.get("is_project_level_privilege")
        self._categories = kwargs.get("categories")

    @classmethod
    def list_privileges(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        **filters
    ) -> Union[List["Privilege"], List[dict], DataFrame]:
        """Get list of privilege objects or privilege dicts. Filter the
        privileges by specifying the `filters` keyword arguments.

        Optionally use `to_dictionary` or `to_dataframe` to choose output
        format.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            to_dictionary: If `True` returns dict, by default (False) returns
                User objects.
            to_dataframe: If `True`, returns `DataFrame`.
            **filters: Available filter parameters: ['id', 'name',
                'description', 'categories', 'is_project_level_privilege']

        Examples:
            >>> Privilege.list_privileges(connection, to_dataframe=True,
            >>>                           is_project_level_privilege='True',
            >>>                           id=[1,2,3,4,5])
        """
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either `to_dictionary=True` or `to_dataframe=True`, but not both.",
                ValueError
            )
        objects = helper.fetch_objects(
            connection=connection, api=security.get_privileges, limit=None, filters=filters
        )
        if to_dictionary:
            return objects
        elif to_dataframe:
            return DataFrame(objects)
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    def add_to_user(self, users: List[Union["User", str]]) -> None:
        """Add privilege to user.

        Args:
            users: list of `User` objects or names.
        """
        from mstrio.users_and_groups.user import User
        if isinstance(users, str):
            users = [User(self.connection, name=users)]
        elif isinstance(users, User):
            users = [users]
        elif hasattr(users, '__iter__') and all(isinstance(el, str) for el in users):
            users = [User(self.connection, name=user) for user in users]
        for user in users:
            user.grant_privilege(self.id)

    def revoke_from_user(self, users: List[Union["User", str]]) -> None:
        """Revoke privilege from user.

        Args:
            users: list of `User` objects or names.
        """
        from mstrio.users_and_groups.user import User
        if isinstance(users, str):
            users = [User(self.connection, name=users)]
        elif isinstance(users, User):
            users = [users]
        elif hasattr(users, '__iter__') and all(isinstance(el, str) for el in users):
            users = [User(self.connection, name=user) for user in users]
        for user in users:
            user.revoke_privilege(self.id)

    def add_to_user_group(self, groups: List[Union["UserGroup", str]]) -> None:
        """Add privilege to User Group.

        Args:
            groups: list of `UserGroup` objects or names.
        """
        if isinstance(groups, str):
            groups = [UserGroup(self.connection, name=groups)]
        elif isinstance(groups, UserGroup):
            groups = [groups]
        elif hasattr(groups, '__iter__') and all(isinstance(el, str) for el in groups):
            groups = [UserGroup(self.connection, name=group) for group in groups]
        for group in groups:
            group.grant_privilege(self.id)

    def revoke_from_user_group(self, groups: List[Union["UserGroup", str]]) -> None:
        """Revoke privilege from User Group.

        Args:
            groups: list of `UserGroup` objects or names.
        """
        if isinstance(groups, str):
            groups = [UserGroup(self.connection, name=groups)]
        elif isinstance(groups, UserGroup):
            groups = [groups]
        elif hasattr(groups, '__iter__') and all(isinstance(el, str) for el in groups):
            groups = [UserGroup(self.connection, name=group) for group in groups]
        for group in groups:
            group.revoke_privilege(self.id)

    @staticmethod
    def _validate_privileges(
        connection: Connection,
        privileges: Union[Union["Privilege", int, str], List[Union["Privilege", int, str]]]
    ) -> List[dict]:
        """This function validates if the privilege ID/Name/Object is valid and
        returns the IDs.

        If invalid, raise ValueError.
        """

        all_privileges = Privilege.list_privileges(connection=connection, to_dictionary=True)
        validated = []

        privileges = privileges if isinstance(privileges, list) else [privileges]

        for privilege in privileges:
            is_str_name = type(privilege) == str and len(privilege) > 3
            is_str_id = type(privilege) == str and len(privilege) > 0 and len(privilege) <= 3
            is_int_id = isinstance(privilege, int) and privilege < 300 and privilege >= 0
            privilege_ok = False

            if is_str_name:
                temp_priv = helper.filter_list_of_dicts(all_privileges, name=privilege)
                privilege_ok = bool(temp_priv)
            elif is_str_id or is_int_id:
                temp_priv = helper.filter_list_of_dicts(all_privileges, id=str(privilege))
                privilege_ok = bool(temp_priv)

            if privilege_ok:
                validated.append({'id': temp_priv[0]['id'], 'name': temp_priv[0]['name']})
            elif isinstance(privilege, Privilege):
                validated.append({'id': privilege.id, 'name': privilege.name})
            else:
                docs_url = (
                    "https://lw.microstrategy.com/msdz/msdl/GARelease_Current/docs/"
                    + "ReferenceFiles/reference/com/microstrategy/webapi/"
                    + "EnumDSSXMLPrivilegeTypes.html"
                )
                msg = (
                    f"'{privilege}' is not a valid privilege. Possible values can be found in "
                    "EnumDSSXMLPrivilegeTypes: \n" + docs_url
                )
                helper.exception_handler(msg, exception_type=ValueError)
        return validated

    @property
    def description(self):
        return self._description

    @property
    def categories(self):
        return self._categories

    @property
    def is_project_level_privilege(self):
        return self._is_project_level_privilege


class PrivilegeList:
    """Class for browsing MSTR privileges.

    Attributes:
        connection: A MicroStrategy connection object
    """

    def __init__(self, connection: Connection):
        """Initialize PrivilegeList object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
        """
        self.connection = connection
        self.__privileges = Privilege.list_privileges(self.connection)

    @property
    def privileges(self):
        """Returns privileges list."""
        return self.__privileges

    def to_dict(self):
        """Returns list of privileges dicts."""
        return {int(p.id): p.name for p in self.__privileges}

    def to_dataframe(self):
        """Returns DataFrame with privileges."""
        return DataFrame([[p.id, p.name, p.description, p.categories] for p in self.__privileges])
