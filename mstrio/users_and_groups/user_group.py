from typing import Dict, List, Optional, TYPE_CHECKING, Union

from pandas import DataFrame

from mstrio import config
from mstrio.access_and_security.privilege_mode import PrivilegeMode
from mstrio.access_and_security.security_role import SecurityRole
from mstrio.api import objects, usergroups
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.acl import TrusteeACLMixin
from mstrio.utils.entity import Entity, ObjectTypes, DeleteMixin

if TYPE_CHECKING:
    from mstrio.access_and_security.privilege import Privilege
    from mstrio.access_and_security.security_filter import SecurityFilter
    from mstrio.server import Project
    from mstrio.users_and_groups.user import User


def list_user_groups(connection: Connection, name_begins: Optional[str] = None,
                     to_dictionary: bool = False, limit: Optional[int] = None,
                     **filters) -> List["UserGroup"]:
    """Get list of User Group objects or User Group dicts. Optionally filter
    the User Groups by specifying 'name_begins' or other filters.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Wildcards available for name_begins:
        ? - any character
        * - 0 or more of any characters
        e.g name_begins = ?onny wil return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins: Begining of a User Groups name which we want to list
        to_dictionary: If True returns dict, by default (False) returns
            User Group objects
        limit: limit the number of elements returned. If `None` (default), all
            objects are returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'abbreviation', 'description', 'subtype', 'date_created',
            'date_modified', 'version', 'acg', 'owner', 'ext_type']


    Examples:
        >>> list_user_groups(connection, name_begins='Group',
        >>>                  description='New group')
    """
    return UserGroup._get_user_groups(connection=connection, name_begins=name_begins,
                                      to_dictionary=to_dictionary, limit=limit, **filters)


class UserGroup(Entity, DeleteMixin, TrusteeACLMixin):
    """Object representation of MicroStrategy User Group object.

    Attributes:
        connection: A MicroStrategy connection object
        memberships: User Groups that the User Group is a member of
        memebers: users that are members of User Group
        security_roles: security roles that the User Group is a member of
        privileges: user privileges per project
        id: User ID
        name: User name
        type: Object type
        subtype: Object subtype
        ext_type: Object extended type
        abbreviation: Object abbreviation
        description: Object description
        date_created: Creation time, DateTime object
        date_modified: Last modification time, DateTime object
        version: Object version ID
        owner: Owner name and ID
        ancestors: List of ancestor folders
        settings: Settings of User Group
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _SUPPORTED_PATCH_OPERATIONS = {"add": "add", "remove": "remove", "change": "replace"}
    _OBJECT_TYPE = ObjectTypes.USERGROUP
    _API_GETTERS = {
        ('id', 'name', 'type', 'subtype', 'ext_type', 'abbreviation', 'date_created',
         'date_modified', 'version', 'owner', 'ancestors', 'acg',
         'acl'): usergroups.get_user_group_info,
        'memberships': usergroups.get_memberships,
        'members': usergroups.get_members,
        'security_roles': usergroups.get_security_roles,
        'privileges': usergroups.get_privileges,
        'settings': usergroups.get_settings
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "abbreviation": str,
    }
    _API_PATCH: dict = {
        ('abbreviation'): (objects.update_object, 'partial_put'),
        ('name', 'description', 'memberships', 'security_roles', 'members', 'privileges'):
            (usergroups.update_user_group_info, 'patch')
    }

    def __init__(self, connection: Connection, name: Optional[str] = None,
                 id: Optional[str] = None) -> None:
        """Initialize UserGroup object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: name of User Group
            id: ID of User Group
        """
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.")

        if id is None:
            user_groups = UserGroup._get_user_group_ids(connection=connection, name_begins=name,
                                                        name=name)
            if user_groups:
                id = user_groups[0]
            else:
                helper.exception_handler(
                    "There is no User Group with the given name: '{}'".format(name),
                    exception_type=ValueError)
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)

        self._memberships = kwargs.get('memberships')
        self._members = kwargs.get("members")
        self._security_roles = kwargs.get("security_roles")
        self._privileges = kwargs.get("privileges")
        self._settings = kwargs.get('settings')

    @classmethod
    def create(cls, connection: Connection, name: str, description: Optional[str] = None,
               memberships: List[str] = [], members: List[str] = []):
        """Create a new User Group on the I-Server. Returns `UserGroup` object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            name: Name of a newly created User Group
            description: Description of a newly created User Group
            memberships: Specify User Groups which newly created User Group
                will be member
            members: Specify Users which will be members of newly created User
                Group
        """
        body = {
            "name": name,
            "description": description,
            "memberships": memberships,
            "members": members
        }
        response = usergroups.create_user_group(connection, body)
        if response.ok:
            response = response.json()
            if config.verbose:
                print("Successfully created user group '{}' with ID: '{}'".format(
                    name, response.get('id')))
            return cls.from_dict(source=response, connection=connection)

    @classmethod
    def _get_user_groups(cls, connection: Connection, name_begins: Optional[str] = None,
                         to_dictionary: bool = False, limit: Optional[int] = None,
                         **filters) -> List["UserGroup"]:
        msg = "Error getting information for a set of User Groups."
        objects = helper.fetch_objects_async(connection, usergroups.get_info_all_user_groups,
                                             usergroups.get_info_all_user_groups_async,
                                             limit=limit, chunk_size=1000, error_msg=msg,
                                             name_begins=name_begins, filters=filters)
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @classmethod
    def _get_user_group_ids(cls, connection: Connection, name_begins: Optional[str] = None,
                            limit: Optional[int] = None, **filters) -> List[str]:
        group_dicts = UserGroup._get_user_groups(connection=connection, name_begins=name_begins,
                                                 to_dictionary=True, limit=limit, **dict(filters))
        return [group['id'] for group in group_dicts]

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter User Group name or/and description.

        Args:
            name: New name of the User Group
            description: New description of the User Group
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

    def add_users(self, users: Union[str, List[str], "User", List["User"]]) -> None:
        """Add members to the User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, "members", "add")
        if succeeded and config.verbose:
            print("Added {} user(s) to group {}".format(succeeded, self.name))
        if failed and config.verbose:
            print("User(s) {} is/are already a member of '{}'".format(failed, self.name))

    def remove_users(self, users: Union[str, List[str], "User", List["User"]]) -> None:
        """Remove members from User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, 'members', "remove")
        if succeeded and config.verbose:
            print("Removed user(s) '{}' from group {}".format(succeeded, self.name))
        if failed and config.verbose:
            print("User(s) {} is/are not members of '{}'".format(failed, self.name))

    def remove_all_users(self) -> None:
        """Remove all members from user group."""
        to_be_removed = [member['id'] for member in self.members]
        self.remove_users(to_be_removed)

    def list_members(self, **filters) -> List[dict]:
        """List user group members.

        Optionally filter the results by passing filter keyword arguments.

        Args:
            **filters: Available filter parameters: 'name', 'id', 'type',
                'abbreviation', subtype', 'date_created', 'date_modified',
                'version', 'acg', 'owner', source', ext_type', 'username',
                full_name', enabled'
        """
        self.fetch('members')
        return helper.filter_list_of_dicts(self.members, **filters)

    def add_to_user_groups(self, groups: Union[str, List[str], "UserGroup",
                                               List["UserGroup"]]) -> None:
        """Add User Group to passed groups.

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(groups, "memberships", "add")
        if succeeded and config.verbose:
            print("Added group '{}' to group(s): {}".format(self.name, succeeded))
        if failed and config.verbose:
            print("Group '{}' is already a member of {} group(s)".format(self.name, failed))

    def remove_from_user_groups(
            self, groups: Union[str, List[str], "UserGroup", List["UserGroup"]]) -> None:
        """Remove User Group from passed groups

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(groups, 'memberships', "remove")
        if succeeded and config.verbose:
            print("Removed group '{}' from group(s): {}".format(self.name, succeeded))
        if failed and config.verbose:
            print("Group '{}' is not a member of {} group(s)".format(self.name, failed))

    def grant_privilege(self, privilege: Union[str, List[str], "Privilege",
                                               List["Privilege"]]) -> None:
        """Grant privileges directly to the User Group.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege
        privileges = [
            priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)
        ]
        existing_ids = [
            privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')
        ]
        succeeded, failed = self._update_nested_properties(privileges, "privileges", "add",
                                                           existing_ids)

        if succeeded:
            self.fetch('privileges')  # fetch the object privileges
            if config.verbose:
                print("Granted privilege(s) {} to '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User Group '{}' already has privilege(s) {}".format(self.name, failed))

    def revoke_privilege(self, privilege: Union[str, List[str], "Privilege",
                                                List["Privilege"]]) -> None:
        """Revoke directly granted User Group privileges.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege
        privileges = set(
            [priv['id'] for priv in Privilege._validate_privileges(self.connection, privilege)])
        existing_ids = [
            privilege['privilege']['id'] for privilege in self.list_privileges(mode='ALL')
        ]
        directly_granted = set(
            [privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')])
        to_revoke = list(privileges.intersection(directly_granted))
        not_directly_granted = list(
            (set(existing_ids) - directly_granted).intersection(privileges))

        if not_directly_granted:
            msg = (f"Privileges {sorted(not_directly_granted)} are inherited and will be "
                   "ommited. Only directly granted privileges can be revoked by this method.")
            helper.exception_handler(msg, exception_type=Warning)

        succeeded, failed = self._update_nested_properties(to_revoke, "privileges", "remove",
                                                           existing_ids)
        if succeeded:
            self.fetch('privileges')  # fetch the object privileges
            if config.verbose:
                print("Revoked privilege(s) {} from '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("User group '{}' does not have privilege(s) {}".format(self.name, failed))

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke directly granted group privileges.

        Args:
            force: If True, no additional prompt will be shown before revoking
                all privileges from User Group
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to revoke all privileges from user group '{}'? [Y/N]: "
                .format(self.name))
        if force or user_input == 'Y':
            to_revoke = [
                privilege['privilege']['id'] for privilege in self.list_privileges(mode='GRANTED')
            ]
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                print("User Group '{}' does not have any directly granted privileges".format(
                    self.name))

    def list_privileges(self, mode: PrivilegeMode = PrivilegeMode.ALL,
                        to_dataframe: bool = False) -> list:
        """List privileges for user group.

        Args:
            mode: Specifies which privileges to list.
                See: `privilege.PrivilegeMode` enum.
            to_dataframe: If True, return a DataFrame object containing
                privileges
        """
        self.fetch('privileges')

        def to_df(priv_list):
            priv_dict = {}
            for priv in priv_list:
                priv_dict[priv['privilege']['id']] = priv['privilege']['name']
            df = DataFrame.from_dict(priv_dict, orient='index', columns=['Name'])
            df.index.name = 'ID'
            return df

        if not isinstance(mode, PrivilegeMode):
            try:
                mode = PrivilegeMode(mode)
            except ValueError:
                msg = ("Wrong privilege mode has been passed, allowed modes are "
                       "['ALL'/'INHERITED'/'GRANTED']. See: `privilege.PrivilegeMode` enum.")
                helper.exception_handler(msg, ValueError)

        privileges = list()
        if mode == PrivilegeMode.ALL:
            privileges = self.privileges
        elif mode == PrivilegeMode.INHERITED:
            for privilege in self.privileges:
                is_inherited = False
                for source in privilege['sources']:
                    is_inherited = not source['direct'] or is_inherited
                if is_inherited:
                    privileges.append(privilege)
        else:  # GRANTED
            for privilege in self.privileges:
                is_granted = False
                for source in privilege['sources']:
                    is_granted = source['direct'] or is_granted
                if is_granted:
                    privileges.append(privilege)

        return to_df(privileges) if to_dataframe else privileges

    def assign_security_role(self, security_role: Union[SecurityRole,
                                                        str], application: Union["Project", str],
                             project: Union["Project", str] = None) -> None:  # NOSONAR
        """Assigns a Security Role to the User Group for given project.

        Args:
            security_role: Security Role ID or object
            application: Project name or object. Will be removed from 11.3.4.101
            project: Will replace application from 11.3.4.101
        """
        helper.deprecation_warning(
            '`application`',
            '`project`',
            '11.3.4.101',  # NOSONAR
            False,
            False)
        project = application

        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.grant_to([self.id], project)
        if config.verbose:
            print("Assigned Security Role '{}' to group: '{}'".format(
                security_role.name, self.name))

    def revoke_security_role(self, security_role: Union[SecurityRole,
                                                        str], application: Union["Project", str],
                             project: Union["Project", str] = None) -> None:  # NOSONAR
        """Removes a Security Role from the User Group for given project.

        Args:
            security_role: Security Role ID or object
            application: Project name or object. Will be removed from 11.3.4.101
            project: Will replace application from 11.3.4.101
        """
        helper.deprecation_warning(
            '`application`',
            '`project`',
            '11.3.4.101',  # NOSONAR
            False,
            False)
        project = application

        security_role = security_role if isinstance(security_role, SecurityRole) else SecurityRole(
            self.connection, id=str(security_role))

        security_role.revoke_from([self.id], project)
        if config.verbose:
            print("Revoked Security Role '{}' from group: '{}'".format(
                security_role.name, self.name))

    def apply_security_filter(self, security_filter: Union["SecurityFilter", str]):
        """Apply a security filter to the user group.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be applied to the user group.
        Returns:
            True when applying was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.access_and_security.security_filter import SecurityFilter
            security_filter = SecurityFilter.from_dict({"id": security_filter}, self.connection)
        return security_filter.apply(self.id)

    def revoke_security_filter(self, security_filter: Union["SecurityFilter", str]):
        """Revoke a security filter from the user group.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be revoked from the user
                group.

        Returns:
            True when revoking was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.access_and_security.security_filter import SecurityFilter
            security_filter = SecurityFilter.from_dict({"id": security_filter}, self.connection)
        return security_filter.revoke(self.id)

    def get_settings(self) -> Dict:
        """Get the User Group settings from the I-Server."""
        res = self._API_GETTERS.get('settings')(self.connection, self.id,
                                                include_access=True)  # type: ignore
        return res.json()

    @property
    def memberships(self):
        return self._memberships

    @property
    def members(self):
        return self._members

    @property
    def security_roles(self):
        return self._security_roles

    @property
    def privileges(self):
        return self._privileges

    @property
    def settings(self):
        return self._settings
