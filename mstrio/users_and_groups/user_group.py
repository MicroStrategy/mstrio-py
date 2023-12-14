import logging
from typing import TYPE_CHECKING

from pandas import DataFrame

from mstrio import config
from mstrio.access_and_security.privilege_mode import PrivilegeMode
from mstrio.access_and_security.security_role import SecurityRole
from mstrio.api import usergroups
from mstrio.connection import Connection
from mstrio.types import ObjectSubTypes
from mstrio.utils.acl import TrusteeACLMixin
from mstrio.utils.entity import DeleteMixin, Entity, ObjectTypes
from mstrio.utils.helper import (
    exception_handler,
    fetch_objects_async,
    filter_list_of_dicts,
    filter_params_for_func,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.translation_mixin import TranslationMixin
from mstrio.utils.version_helper import method_version_handler
from mstrio.utils.response_processors import usergroups as usergroups_processors

if TYPE_CHECKING:
    from mstrio.access_and_security.privilege import Privilege
    from mstrio.modeling.security_filter import SecurityFilter
    from mstrio.server import Project
    from mstrio.users_and_groups.user import User

logger = logging.getLogger(__name__)


def list_user_groups(
    connection: Connection,
    name_begins: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list["UserGroup"]:
    """Get list of User Group objects or User Group dicts. Optionally filter
    the User Groups by specifying 'name_begins' or other filters.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Wildcards available for name_begins:
        ? - any character
        * - 0 or more of any characters
        e.g. name_begins = ?onny will return Sonny and Tonny

    Args:
        connection: MicroStrategy connection object returned by
            `connection.Connection()`
        name_begins: Beginning of a User Groups name which we want to list
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
    return UserGroup._get_user_groups(
        connection=connection,
        name_begins=name_begins,
        to_dictionary=to_dictionary,
        limit=limit,
        **filters,
    )


class UserGroup(Entity, DeleteMixin, TrusteeACLMixin, TranslationMixin):
    """Object representation of MicroStrategy User Group object.

    Attributes:
        connection: A MicroStrategy connection object
        memberships: User Groups that the User Group is a member of
        members: users that are members of User Group
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

    @staticmethod
    def _parse_members(
        source: list[dict], connection: 'Connection', to_snake_case: bool = True
    ):
        """Parse members from response."""
        from mstrio.users_and_groups.user import User

        return [
            User.from_dict(member, connection, to_snake_case)
            if member['subtype'] == ObjectSubTypes.USER.value
            else UserGroup.from_dict(member, connection, to_snake_case)
            for member in source
        ]

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "members": _parse_members,
    }

    _SUPPORTED_PATCH_OPERATIONS = {
        "add": "add",
        "remove": "remove",
        "change": "replace",
    }
    _OBJECT_TYPE = ObjectTypes.USERGROUP
    _API_GETTERS = {
        (
            'id',
            'name',
            'type',
            'subtype',
            'ext_type',
            'abbreviation',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'ancestors',
            'acg',
            'acl',
            'ldapdn',
        ): usergroups.get_user_group_info,
        'memberships': usergroups.get_memberships,
        'members': usergroups.get_members,
        'security_roles': usergroups.get_security_roles,
        'privileges': usergroups.get_privileges,
        'settings': usergroups.get_settings,
    }
    _PATCH_PATH_TYPES = {
        "name": str,
        "description": str,
        "abbreviation": str,
    }
    _API_PATCH: dict = {
        'abbreviation': (objects_processors.update, 'partial_put'),
        (
            'name',
            'description',
            'memberships',
            'security_roles',
            'members',
            'privileges',
            'ldapdn',
        ): (usergroups_processors.update_user_group_info, 'patch'),
    }

    def __init__(
        self,
        connection: Connection,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """Initialize UserGroup object by passing `name` or `id`. When `id` is
        provided (not `None`), `name` is omitted.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            name: name of User Group
            id: ID of User Group
        """
        if id is None and name is None:
            exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor."
            )

        if id is None:
            user_groups = UserGroup._get_user_group_ids(
                connection=connection, name_begins=name, name=name
            )
            if user_groups:
                id = user_groups[0]
            else:
                exception_handler(
                    f"There is no User Group with the given name: '{name}'",
                    exception_type=ValueError,
                )
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.ldapdn = kwargs.get("ldapdn")

        self._memberships = kwargs.get('memberships')
        self._members = kwargs.get('members')
        self._security_roles = kwargs.get('security_roles')
        self._privileges = kwargs.get('privileges')
        self._settings = kwargs.get('settings')
        self._security_filters = kwargs.get('security_filters')

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        description: str | None = None,
        memberships: list[str] | None = None,
        members: list[str] | None = None,
        ldapdn: str | None = None,
    ):
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
            ldapdn: User group's LDAP distinguished name
        """
        memberships = memberships or []
        members = members or []
        body = {
            "name": name,
            "description": description,
            "memberships": memberships,
            "members": members,
            "ldapdn": ldapdn,
        }
        response = usergroups.create_user_group(connection, body)
        if response.ok:
            response = response.json()
            if config.verbose:
                logger.info(
                    f"Successfully created user group '{name}' with ID: "
                    f"'{response.get('id')}'"
                )
            return cls.from_dict(source=response, connection=connection)

    @classmethod
    def _get_user_groups(
        cls,
        connection: Connection,
        name_begins: str | None = None,
        to_dictionary: bool = False,
        limit: int | None = None,
        **filters,
    ) -> list["UserGroup"]:
        msg = "Error getting information for a set of User Groups."
        objects = fetch_objects_async(
            connection,
            usergroups.get_info_all_user_groups,
            usergroups.get_info_all_user_groups_async,
            limit=limit,
            chunk_size=1000,
            error_msg=msg,
            name_begins=name_begins,
            filters=filters,
        )
        if to_dictionary:
            return objects
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @classmethod
    def _get_user_group_ids(
        cls,
        connection: Connection,
        name_begins: str | None = None,
        limit: int | None = None,
        **filters,
    ) -> list[str]:
        group_dicts = UserGroup._get_user_groups(
            connection=connection,
            name_begins=name_begins,
            to_dictionary=True,
            limit=limit,
            **dict(filters),
        )
        return [group['id'] for group in group_dicts]

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        ldapdn: str = None,
    ):
        """Alter User Group name or/and description.

        Args:
            name: New name of the User Group
            description: New description of the User Group
        """

        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    def add_users(self, users: "str | User | list[str | User]") -> None:
        """Add members to the User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, "members", "add")
        if succeeded and config.verbose:
            logger.info(f"Added {succeeded} user(s) to group {self.name}")
        if failed and config.verbose:
            logger.info(f"User(s) {failed} is/are already a member of '{self.name}'")
        self.fetch('members')

    def remove_users(self, users: "str | User | list[str | User]") -> None:
        """Remove members from User Group.

        Args:
            users: List of User objects or ids
        """
        succeeded, failed = self._update_nested_properties(users, 'members', "remove")
        if succeeded and config.verbose:
            logger.info(f"Removed user(s) '{succeeded}' from group {self.name}")
        if failed and config.verbose:
            logger.warning(f"User(s) {failed} is/are not members of '{self.name}'")
        self.fetch('members')

    def remove_all_users(self) -> None:
        """Remove all members from user group."""
        to_be_removed = [member.id for member in self.members]
        self.remove_users(to_be_removed)

    def list_members(self, **filters) -> list[dict]:
        """List user group members.

        Optionally filter the results by passing filter keyword arguments.

        Args:
            **filters: Available filter parameters: 'name', 'id', 'type',
                'abbreviation', subtype', 'date_created', 'date_modified',
                'version', 'acg', 'owner', source', ext_type', 'username',
                full_name', enabled'
        """
        self.fetch('members')
        return filter_list_of_dicts(
            [member.to_dict() for member in self.members], **filters
        )

    def add_to_user_groups(
        self, groups: "str | UserGroup | list[str | UserGroup]"
    ) -> None:
        """Add User Group to passed groups.

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(groups, "memberships", "add")
        if succeeded and config.verbose:
            logger.info(f"Added group '{self.name}' to group(s): {succeeded}")
        if failed and config.verbose:
            logger.warning(
                f"Group '{self.name}' is already a member of {failed} group(s)"
            )

    def remove_from_user_groups(
        self, groups: "str | UserGroup | list[str | UserGroup]"
    ) -> None:
        """Remove User Group from passed groups

        Args:
            groups: List of User Group objects or ids
        """
        succeeded, failed = self._update_nested_properties(
            groups, 'memberships', "remove"
        )
        if succeeded and config.verbose:
            logger.info(f"Removed group '{self.name}' from group(s): {succeeded}")
        if failed and config.verbose:
            logger.warning(f"Group '{self.name}' is not a member of {failed} group(s)")

    def grant_privilege(
        self, privilege: "str | list[str] | Privilege | list[Privilege]"
    ) -> None:
        """Grant privileges directly to the User Group.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege

        privileges = [
            priv['id']
            for priv in Privilege._validate_privileges(self.connection, privilege)
        ]
        existing_ids = [
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='GRANTED')
        ]
        succeeded, failed = self._update_nested_properties(
            privileges, "privileges", "add", existing_ids
        )

        if succeeded:
            self.fetch('privileges')  # fetch the object privileges
            if config.verbose:
                logger.info(f"Granted privilege(s) {succeeded} to '{self.name}'")
        if failed and config.verbose:
            logger.warning(
                f"User Group '{self.name}' already has privilege(s) {failed}"
            )

    def revoke_privilege(
        self, privilege: "str | list[str] | Privilege | list[Privilege]"
    ) -> None:
        """Revoke directly granted User Group privileges.

        Args:
            privilege: List of privilege objects, ids or names
        """
        from mstrio.access_and_security.privilege import Privilege

        privileges = {
            priv['id']
            for priv in Privilege._validate_privileges(self.connection, privilege)
        }
        existing_ids = [
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='ALL')
        ]
        directly_granted = {
            privilege['privilege']['id']
            for privilege in self.list_privileges(mode='GRANTED')
        }
        to_revoke = list(privileges.intersection(directly_granted))
        not_directly_granted = list(
            (set(existing_ids) - directly_granted).intersection(privileges)
        )

        if not_directly_granted:
            msg = (
                f"Privileges {sorted(not_directly_granted)} are inherited and will be "
                "omitted. Only directly granted privileges can be revoked by this "
                "method."
            )
            exception_handler(msg, exception_type=Warning)

        succeeded, failed = self._update_nested_properties(
            to_revoke, "privileges", "remove", existing_ids
        )
        if succeeded:
            self.fetch('privileges')  # fetch the object privileges
            if config.verbose:
                logger.info(f"Revoked privilege(s) {succeeded} from '{self.name}'")
        if failed and config.verbose:
            logger.warning(
                f"User group '{self.name}' does not have privilege(s) {failed}"
            )

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke directly granted group privileges.

        Args:
            force: If True, no additional prompt will be shown before revoking
                all privileges from User Group
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to revoke all privileges from user group "
                f"'{self.name}'? [Y/N]: "
            )
        if force or user_input == 'Y':
            to_revoke = [
                privilege['privilege']['id']
                for privilege in self.list_privileges(mode='GRANTED')
            ]
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                logger.info(
                    f"User Group '{self.name}' does not have any directly granted "
                    f"privileges"
                )

    def list_privileges(
        self, mode: PrivilegeMode | str = PrivilegeMode.ALL, to_dataframe: bool = False
    ) -> list:
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
                msg = (
                    "Wrong privilege mode has been passed, allowed modes are "
                    "['ALL'/'INHERITED'/'GRANTED']. See: `privilege.PrivilegeMode` "
                    "enum."
                )
                exception_handler(msg, ValueError)

        privileges = []
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

    def assign_security_role(
        self,
        security_role: 'SecurityRole | str',
        project: 'Project | str',
    ) -> None:  # NOSONAR
        """Assigns a Security Role to the User Group for given project.

        Args:
            security_role: Security Role ID or object
            project: Project name or object
        """

        security_role = (
            security_role
            if isinstance(security_role, SecurityRole)
            else SecurityRole(self.connection, id=str(security_role))
        )

        security_role.grant_to([self.id], project)
        if config.verbose:
            logger.info(
                f"Assigned Security Role '{security_role.name}' to group: '{self.name}'"
            )
        self.fetch('security_roles')

    def revoke_security_role(
        self, security_role: SecurityRole | str, project: 'Project | str'
    ) -> None:  # NOSONAR
        """Removes a Security Role from the User Group for given project.

        Args:
            security_role: Security Role ID or object
            project: Project name or object
        """

        security_role = (
            security_role
            if isinstance(security_role, SecurityRole)
            else SecurityRole(self.connection, id=str(security_role))
        )

        security_role.revoke_from([self.id], project)
        if config.verbose:
            logger.info(
                f"Revoked Security Role '{security_role.name}' from group: "
                f"'{self.name}'"
            )
        self.fetch('security_roles')

    @method_version_handler('11.3.0200')
    def list_security_filters(
        self, projects: str | list[str] | None = None, to_dictionary: bool = False
    ) -> dict:
        """Get the list of security filters for user group. They can be filtered
        by the projects' ids.

        Args:
            projects (str or list of str, optional): collection of projects' ids
                which is used for filtering data
            to_dictionary: If True returns security filters as dicts, by default
                (False) returns them as objects.

        Returns:
            Dictionary with project names as keys and list with security
            filters as values. In case of no security filter for the given user
            group in the particular project, then this project is not placed in
            the dictionary.
        """
        from mstrio.modeling.security_filter import SecurityFilter

        objects_ = usergroups.get_security_filters(
            self.connection, self.id, projects
        ).json()
        projects_ = objects_.get("projects")

        objects_ = {
            project_.get("name"): project_.get("securityFilters")
            for project_ in projects_
            if project_.get("securityFilters")
        }

        self._security_filters = {
            name: [
                SecurityFilter.from_dict(sec_filter, self.connection)
                for sec_filter in sec_filters
            ]
            for (name, sec_filters) in objects_.items()
        }
        if to_dictionary:
            return objects_
        return self._security_filters

    def apply_security_filter(self, security_filter: "SecurityFilter | str"):
        """Apply a security filter to the user group.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be applied to the user group.
        Returns:
            True when applying was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.modeling.security_filter import SecurityFilter

            security_filter = SecurityFilter.from_dict(
                {"id": security_filter}, self.connection
            )
        return security_filter.apply(self.id)

    def revoke_security_filter(self, security_filter: "SecurityFilter | str"):
        """Revoke a security filter from the user group.

        Args:
            security_filter (string or object): identifier of security filter or
                `SecurityFilter` object which will be revoked from the user
                group.

        Returns:
            True when revoking was successful. False otherwise.
        """
        if isinstance(security_filter, str):
            from mstrio.modeling.security_filter import SecurityFilter

            security_filter = SecurityFilter.from_dict(
                {"id": security_filter}, self.connection
            )
        return security_filter.revoke(self.id)

    def get_settings(self) -> dict:
        """Get the User Group settings from the I-Server."""
        res = self._API_GETTERS.get('settings')(
            self.connection, self.id, include_access=True
        )  # type: ignore
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
        self.fetch('privileges')
        return self._privileges

    @property
    def settings(self):
        return self._settings

    @property
    def security_filters(self):
        if not self._security_filters:
            self.list_security_filters()
        return self._security_filters
