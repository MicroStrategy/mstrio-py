from typing import List, Optional, TYPE_CHECKING, Union

from mstrio.access_and_security.security_filter import (
    AttributeRef, ObjectInformation, Qualification
)
from mstrio.api import changesets, security_filters
from mstrio.api.security_filters import ShowExpressionAs, UpdateOperator
from mstrio.object_management import full_search
from mstrio.users_and_groups import User, UserGroup
from mstrio.utils import helper
from mstrio.utils.entity import DeleteMixin, Entity, ObjectSubTypes, ObjectTypes

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.users_and_groups import UserOrGroup


def list_security_filters(connection: "Connection", to_dictionary: bool = False,
                          limit: Optional[int] = None, user: Optional[Union[str, "User"]] = None,
                          user_group: Optional[Union[str, "UserGroup"]] = None,
                          **filters) -> Union[List["SecurityFilter"], List[dict]]:
    """Get list of security filter objects or security filter dicts for the
    project specified in the connection object. It can be filtered by user or
    user group.

    Note: It is not possible to provide both `user` and `user_group` parameter.
        When both arguments are provided error is raised.

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        to_dictionary: If True returns dict, by default (False) returns
            `SecurityFilter` objects.
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        user (str or object, optional): Id of user or `User` object used to
            filter security filters
        user_group (str or object, optional): Id of user group or `UserGroup`
            object used to filter security filters
        **filters: Available filter parameters: ['id', 'name', 'description',
            'type', 'subtype', 'date_created', 'date_modified', 'version',
            'acg', 'icon_path', 'owner']

    Returns:
        list of security filter objects or list of security filter dicts.
    """
    connection._validate_project_selected()
    if user and user_group:
        helper.exception_handler(
            "You cannot filter by both `user` and `user_group` at the same time.")

    if user:
        user = User(connection, id=user) if isinstance(user, str) else user
        # filter security filters by user for project specified in `connection`
        objects_ = user.list_security_filters(connection.project_id,
                                              to_dictionary=True).get(connection.project_name, [])
    elif user_group:
        user_group = UserGroup(connection, id=user_group) if isinstance(user_group,
                                                                        str) else user_group
        # filter security filters by the user group for project specified in
        # `connection`
        objects_ = user_group.list_security_filters(connection.project_id, to_dictionary=True).get(
            connection.project_name, [])
    else:
        objects_ = full_search(connection, object_types=ObjectTypes.SECURITY_FILTER,
                               project=connection.project_id, limit=limit, **filters)
    if to_dictionary:
        return objects_
    return [SecurityFilter.from_dict(obj_, connection) for obj_ in objects_]


class SecurityFilter(Entity, DeleteMixin):

    _OBJECT_TYPE = ObjectTypes.SECURITY_FILTER
    _OBJECT_SUBTYPE = ObjectSubTypes.MD_SECURITY_FILTER.value
    _SIZE_LIMIT = 10000000  # this sets desired chunk size in bytes
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, connection: "Connection", id: str, name: Optional[str] = None):
        """Initialize security filter object by its identifier.

        Note:
            Parameter `name` is not used when fetching. `id` is always used to
            uniquely identify security filter.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id (str): Identifier of a pre-existing security filter containing
                the required data.
            name (str, optional): name of security filter.
        """
        super().__init__(connection, id, name=name)
        connection._validate_project_selected()

    def _get_definition(self):
        """Get the definition of security filter."""
        res = security_filters.read_security_filter(
            self.connection, self.id, self.connection.project_id,
            show_expression_as=ShowExpressionAs.TREE.value).json()
        self._information = ObjectInformation.from_dict(res['information'])
        self._qualification = Qualification.from_dict(res['qualification'])
        self._top_level = [AttributeRef.from_dict(level) for level in res.get('topLevel', [])]
        self._bottom_level = [
            AttributeRef.from_dict(level) for level in res.get('bottomLevel', [])
        ]
        self.__definition_retrieved = True

    def _get_members(self):
        """Get the users and user groups that the specified security filter is
        applied to."""
        res = security_filters.get_security_filter_members(
            self.connection,
            self.id,
            self.connection.project_id,
        ).json()
        self._members = []
        for obj in res['users']:
            if obj['subtype'] == ObjectSubTypes.USER.value:
                self._members.append(User.from_dict(obj, self.connection))
            if obj['subtype'] == ObjectSubTypes.USER_GROUP.value:
                self._members.append(UserGroup.from_dict(obj, self.connection))
        self.__members_retrieved = True

    def _init_variables(self, **kwargs):
        """Init all properties when creating security filter from
        a dictionary."""
        super()._init_variables(**kwargs)
        # properties `information`, `qualification`, `top_level` or
        # `bottom_level` can be lazily fetched
        information = kwargs.get("information")
        self._information = None if information is None else ObjectInformation.from_dict(
            information)
        qualification = kwargs.get("qualification")
        self._qualification = None if qualification is None else Qualification.from_dict(
            qualification)
        top_level = kwargs.get("top_level")
        self._top_level = None if top_level is None else [
            AttributeRef.from_dict(level) for level in top_level
        ]
        bottom_level = kwargs.get("bottom_level")
        self._bottom_level = None if top_level is None else [
            AttributeRef.from_dict(level) for level in bottom_level
        ]
        self.__definition_retrieved = self._information is not None and self._qualification is not\
            None and self._top_level is not None and self._bottom_level is not None
        # property `members` can be lazily fetched
        self._members = kwargs.get("members")
        self.__members_retrieved = self._members is not None

    def fetch(self, attr: Optional[str] = None, fetch_definition: bool = True,
              fetch_members: bool = True) -> None:
        """Fetch the latest security filter state from the I-Server.
        Additionally fetch its definition and members.

        Note:
            This method can overwrite local changes made to the object.

        Args:
            attr (str, optional): Attribute name to be fetched.
            fetch_definition (bool, optional): flag which indicates whether
                definition of security filter is fetched. By default `True`.
            fetch_members (bool, optional): flag which indicates whether
                members of security filter is fetched. By default `True`.

        Raises:
            ValueError: if `attr` cannot be fetched.
        """
        super().fetch(attr)
        if fetch_definition:
            self._get_definition()
        if fetch_members:
            self._get_members()

    @staticmethod
    def __prepare_body(qualification: dict, id: str = None, name: str = None,
                       folder_id: str = None, description: str = None, top_level: List[dict] = [],
                       bottom_level: List[dict] = []) -> dict:
        information = ObjectInformation(object_id=id, sub_type="md_security_filter", name=name,
                                        description=description, destination_folder_id=folder_id)

        return helper.delete_none_values({
            "information": information.to_dict(),
            "qualification": qualification,
            "topLevel": top_level,
            "bottomLevel": bottom_level
        }, recursion=True)

    @staticmethod
    def __create_update_helper(func, connection: "Connection",
                               qualification: Union["Qualification", dict], name: str = None,
                               description: str = None,
                               top_level: Union[List[dict], List["AttributeRef"]] = [],
                               bottom_level: Union[List[dict], List["AttributeRef"]] = [],
                               id: str = None, folder_id: str = None):
        changeset_id = changesets.create_changeset(connection).json()['id']
        qualification = qualification.to_dict() if isinstance(qualification,
                                                              Qualification) else qualification
        top_level_dicts = []
        for level in top_level:
            if isinstance(level, AttributeRef):
                top_level_dicts.append(level.to_dict())
            else:
                top_level_dicts.append(level)
        bottom_level_dicts = []
        for level in bottom_level:
            if isinstance(level, AttributeRef):
                bottom_level_dicts.append(level.to_dict())
            else:
                bottom_level_dicts.append(level)

        res = func(
            connection=connection, changeset_id=changeset_id, throw_error=False, id=id,
            body=SecurityFilter.__prepare_body(qualification, id, name, folder_id, description,
                                               top_level_dicts, bottom_level_dicts))
        # there might be a case when response below is correct but committing
        # changes is incorrect
        res_commit = changesets.commit_changeset_changes(connection, changeset_id,
                                                         throw_error=False)

        changesets.delete_changeset(connection, changeset_id)
        if not res_commit.ok:
            return res_commit
        return res

    @classmethod
    def create(cls, connection: "Connection", qualification: Union["Qualification", dict],
               name: str, folder_id: str, description: str = None,
               top_level: Union[List[dict], List["AttributeRef"]] = [],
               bottom_level: Union[List[dict], List["AttributeRef"]] = []) -> "SecurityFilter":
        """Create a security filter by providing its qualification, name and
        id of folder in which it will be created. Optionally it is possible to
        set description, top level and bottom level of security filter.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            qualification (object or dict): new security filter definition
                written as an expression tree over predicate nodes. It can be
                provided as `Qualification` object or dictionary.
            name (str): name of new security filter
            folder_id (str): id of folder in which new security filter will be
                created
            description (str): optional description of new security filter
            top_level (list of objects or list of dicts): the top level
                attribute list.
            bottom_level (list of object or list of dicts): the bottom level
                attribute list.
        """
        res = SecurityFilter.__create_update_helper(security_filters.create_security_filter,
                                                    connection, qualification, name, description,
                                                    top_level, bottom_level, folder_id=folder_id)
        if res.ok:
            res = res.json()
            return SecurityFilter.from_dict(
                {
                    "id": res['information']['objectId'],
                    **res['information'],
                    **res
                }, connection)
        else:
            return None

    def alter(self, qualification: Union["Qualification",
                                         dict] = None, top_level: Union[List[dict],
                                                                        List["AttributeRef"]] = [],
              bottom_level: Union[List[dict], List["AttributeRef"]] = [], name: str = None,
              description: str = None, folder_id: str = None):
        """Alter the security filter object in the metadata. It is possible to
        change its qualification, top level, bottom level, name, description
        or destination folder.

        Args:
            qualification (object or dict): optional new security filter
                definition written as an expression tree over predicate nodes.
                It can be provided as `Qualification` object or dictionary.
            top_level (list of objects or list of dicts): the top level
                attribute list.
            bottom_level (list of objects or list of dicts): the bottom level
                attribute list.
            name (str): optional new name of security filter
                top_level (list of object): the top level attribute list.
            description (str): optional new description of security filter
            folder_id (str): id of folder to which security filter will be
                moved
        """
        qualification = self.qualification if qualification is None else qualification
        name = self.name if name is None else name
        description = self.description if description is None else description
        folder_id = self.information.destination_folder_id if folder_id is None else folder_id
        res = self.__create_update_helper(security_filters.update_security_filter, self.connection,
                                          qualification, name, description, top_level,
                                          bottom_level, self.id, folder_id)
        if res.ok:
            res = res.json()
            members = self._members
            members_retrieved = self.__members_retrieved
            self._init_variables(**res.get('information'), id=res.get('information',
                                                                      {}).get('objectId'),
                                 connection=self.connection)
            self._members = members
            self.__members_retrieved = members_retrieved
            self._information = res.get('information')
            self._qualification = res.get('qualification')
            self._top_level = res.get('top_level')
            self._bottom_level = res.get('bottom_level')
            self.__definition_retrieved = self._information is not None and self._qualification is\
                not None and self._top_level is not None and self._bottom_level is not None

    @staticmethod
    def __retrieve_ids_from_list(
        objects: Union[str, "User", "UserGroup", List[Union[str, "User",
                                                            "UserGroup"]]]) -> List[str]:
        """Parsing a list which can contain at the same time User object(s),
        UserGroup object(s), id(s) to a list with id(s)."""
        objects = objects if isinstance(objects, list) else [objects]
        ids = []
        for obj in objects:
            ids.append(obj if isinstance(obj, str) else obj.id)
        return ids

    def __update_members(self, op: UpdateOperator,
                         users_and_groups: Union["UserOrGroup", List["UserOrGroup"]] = []) -> bool:
        """Update members of security filter."""
        users_or_groups = self.__retrieve_ids_from_list(users_and_groups)
        body = {"operationList": [{"op": op.value, "path": "/members", "value": users_or_groups}]}
        res = security_filters.update_security_filter_members(self.connection, self.id, body,
                                                              self.connection.project_id,
                                                              throw_error=False)
        if res.ok:
            self._get_members()
        return res.ok

    def apply(self, users_and_groups: Union["UserOrGroup", List["UserOrGroup"]] = []) -> bool:
        """Apply security filter to user(s) and/or user group(s).

        Args:
            users_and_groups (string, object, list of strings or objects): list
            or a single element specifying to which users and user groups
            security filter will be applied. It is possible to provide the whole
            User or UserGroup object(s) or just id(s) of those objects. When
            providing a list it can contain User object(s), UserGroup object(s),
            id(s) at the same time.

        Returns:
            True when applying was successful. False otherwise.
        """

        return self.__update_members(UpdateOperator.APPLY, users_and_groups)

    def revoke(self, users_and_groups: Union["UserOrGroup", List["UserOrGroup"]] = []) -> bool:
        """Revoke security filter from user(s) and/or user group(s).

        Args:
            users_and_groups (string, object, list of strings or objects): list
            or a single element specifying from which users and user groups
            security filter will be revoked. It is possible to provide the whole
            User or UserGroup object(s) or just id(s) of those objects. When
            providing a list it can contain User object(s), UserGroup object(s),
            id(s) at the same time

        Returns:
            True when revoking was successful. False otherwise.

        """
        return self.__update_members(UpdateOperator.REVOKE, users_and_groups)

    @property
    def information(self):
        """All of the type-neutral information stored in the metadata about
        a security filter."""
        if not self.__definition_retrieved:
            self._get_definition()
        return self._information

    @property
    def qualification(self):
        """The security filter definition written as an expression tree over
        predicate nodes."""
        if not self.__definition_retrieved:
            self._get_definition()
        return self._qualification

    @property
    def top_level(self):
        """The top level attribute list."""
        if not self.__definition_retrieved:
            self._get_definition()
        return self._top_level

    @property
    def bottom_level(self):
        """The bottom level attribute list."""
        if not self.__definition_retrieved:
            self._get_definition()
        return self._bottom_level

    @property
    def members(self):
        """List of users and user groups that security filter is applied to."""
        if not self.__members_retrieved:
            self._get_members()
        return self._members
