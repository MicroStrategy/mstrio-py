from typing import Optional, TYPE_CHECKING, List, Union, Dict, Any

import mstrio.config as config
from mstrio.api import security
from mstrio.utils import helper
from mstrio.utils.entity import Entity, ObjectTypes
from pandas import DataFrame
from mstrio.connection import Connection

if TYPE_CHECKING:
    from mstrio.access_and_security.privilege import Privilege
    from mstrio.server.application import Application
    from mstrio.users_and_groups import UserOrGroup


def list_security_roles(connection: Connection, to_dictionary: bool = False,
                        to_dataframe: bool = False, limit: Optional[int] = None, **filters):
    """Get all Security Roles stored on the server.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.

    Args:
        connection(object): MicroStrategy connection object returned
            by 'connection.Connection()'
        to_dictionary(bool, optional): if True, return Security Roles as
            list of dicts
        limit(int, optional): maximum number of security roles returned.
        **filters: Available filter parameters: ['name', 'id', 'type',
            'description', 'subtype', 'date_created', 'date_modified',
            'version', 'acg', 'owner', 'ext_type']

    Returns:
            List of security roles.
    """
    return SecurityRole._list_security_roles(connection, to_dictionary=to_dictionary,
                                             to_dataframe=to_dataframe, limit=limit, **filters)


class SecurityRole(Entity):
    """A security role is a set of privileges that can be assigned to users and
    reused from project to project. Security roles enable you to assign a
    unique set of privileges to users on a per project basis. They are created
    and maintained at the project source level and assigned to users at the
    project level.

    Attributes:
        connection: A MicroStrategy connection object
        id: Security Role ID
        name: Security Role name
        description: Security Role description
        type: Object type
        subtype: Object subtype
        date_created: Creation time, "yyyy-MM-dd HH:mm:ss" in UTC
        date_modified: Last modification time, "yyyy-MM-dd
        version: Version ID
        owner: owner ID and name
        privileges: Security Role privileges per project
        projects: Project members tuple for the security role
        acg: Access rights (See EnumDSSXMLAccessRightFlags for possible values)
        acl: Object access control list
    """

    _OBJECT_TYPE = ObjectTypes.SECURITY_ROLE
    _PATCH_PATH_TYPES = {"name": str, "description": str}
    _API_GETTERS = {
        ('id', 'name', 'description', 'type', 'subtype', 'date_created', 'date_modified',
         'version', 'owner', 'privileges', 'projects', 'acg', 'acl'): security.get_security_role
    }
    _API_PATCH = [security.update_security_role]

    def __init__(self, connection: Connection, name: Optional[str] = None,
                 id: Optional[str] = None):
        """Initialize Security Role object by passing name or id.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`.
            name: name of Security Role
            id: ID of Security Role
        """
        # initialize either by ID or name
        if id is None and name is None:
            helper.exception_handler(
                "Please specify either 'name' or 'id' parameter in the constructor.", ValueError)

        if id is None:
            security_roles = SecurityRole._list_security_role_ids(connection=connection, name=name)
            if security_roles:
                id = security_roles[0]
            else:
                helper.exception_handler(
                    "There is no Security Role associated with the given name: '{}'".format(name),
                    exception_type=ValueError)
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self._projects = kwargs.get("projects")
        self._privileges = kwargs.get("privileges")

    @classmethod
    def create(cls, connection: Connection, name: str,
               privileges: Union[Union["Privilege", int, str],
                                 List[Union["Privilege", int, str]]], description: str = ""):
        """Create a new Security Role.

        Args:
            connection(object): MicroStrategy connection object returned
                by 'connection.Connection()'.
            name(string): Name of the Security Role
            privileges: List of privileges which will be assigned to this
                security role. Use privilege IDs or Privilege objects.
            description(string, optional): Description of the Security Role

        Returns:
            Newly created Security Role if the HTTP server has successfully
                created the Security Role.
        """
        # get all project level privileges
        from mstrio.access_and_security.privilege import Privilege
        project_level = [
            priv['id'] for priv in Privilege.list_privileges(connection, to_dictionary=True,
                                                             is_project_level_privilege='True')
        ]

        # validate and filter passed privileges
        privileges = Privilege._validate_privileges(connection, privileges)
        server_level = list(set([priv['id'] for priv in privileges]) - set(project_level))
        privileges = helper.filter_list_of_dicts(privileges, id=project_level)

        body = {"name": name, "description": description, "privileges": privileges}

        response = security.create_security_role(connection, body)
        if response.ok:
            if server_level:
                msg = ("Privileges {} are server-level and will be ommited. Only project-level "
                       "privileges can be granted by this method.").format(sorted(server_level))
                helper.exception_handler(msg, exception_type=Warning)
            return cls(connection=connection, id=response.json()['id'])

    @classmethod
    def _list_security_roles(
            cls, connection: Connection, to_dictionary: bool = False, to_dataframe: bool = False,
            limit: Optional[int] = None,
            **filters) -> Union[List["SecurityRole"], List[Dict[str, Any]], DataFrame]:
        if to_dictionary and to_dataframe:
            helper.exception_handler(
                "Please select either to_dictionary=True or to_dataframe=True, but not both.",
                ValueError)

        objects = helper.fetch_objects(
            connection=connection,
            api=security.get_security_roles,
            limit=limit,
            filters=filters,
        )
        if to_dictionary:
            return objects
        elif to_dataframe:
            return DataFrame(objects)
        else:
            return [cls.from_dict(source=obj, connection=connection) for obj in objects]

    @classmethod
    def _list_security_role_ids(cls, connection: Connection, **filters) -> List[str]:
        sr_dicts = SecurityRole._list_security_roles(connection, to_dictionary=True,
                                                     **dict(filters))
        return [role.get('id') for role in sr_dicts]  # type: ignore

    def alter(self, name: Optional[str] = None, description: Optional[str] = None):
        """Alter Security Role name or/and description.

        Args:
            name: new name of the Security Role
            description: new description of the Security Role
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

    def delete(self, force: bool = False) -> None:
        """Deletes the Security Role. The user will be prompted whether is sure
        or not about this operation.

        Args:
            force(bool, optional): if true the role is deleted without a prompt.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to delete role '{}' with ID: {}? [Y/N]: ".format(
                    self.name, self.id))  # noqa
        if force or user_input == 'Y':
            response = security.delete_security_role(self.connection, self.id)
            if response.ok:
                print("Deleted security role {}.".format(self.id))

    def list_members(self, application_name: Optional[str] = None):
        """List all members of the Security Role. Optionally, filter the
        results by Application name.

        Args:
            application_name(str, optional): Application name
        """
        if application_name is not None:
            [filtered_app] = helper.filter_list_of_dicts(self.projects, name=application_name)
            members = filtered_app['members']
        else:
            members = []
            for project in self.projects:
                for member in project['members']:
                    members.append(member)
        return members

    def grant_to(self, members: Union["UserOrGroup", List["UserOrGroup"]],
                 application: Union["Application", str]) -> None:
        """Assign users/user groups to a Security Role.

        Args:
            members(list): List of objects or IDs of Users or User Groups which
                will be assigned to this Security Role.
            application(Application, str): Application object or name to which
                this removal will apply.
        """
        from mstrio.server.application import Application
        from mstrio.users_and_groups.user import User
        from mstrio.users_and_groups.user_group import UserGroup

        if isinstance(application, Application):
            application_id = application.id
            application_name = application.name
        elif isinstance(application, str):
            application_list = Application._list_applications(connection=self.connection,
                                                              to_dictionary=True, name=application)
            if application_list:
                application_id = application_list[0]['id']
                application_name = application_list[0]['name']
            else:
                helper.exception_handler(
                    "Application name '{}' does not exist.".format(application), ValueError)
        else:
            helper.exception_handler("Application parameter must be of type str or Application.",
                                     TypeError)

        # create list of objects from strings/objects/lists
        members_list = members if isinstance(members, list) else [members]
        members_list = [
            obj.id if isinstance(obj, (User, UserGroup)) else str(obj) for obj in members_list
        ]
        existing_ids = [obj['id'] for obj in self.list_members(application_name=application_name)]
        succeeded = list(set(members_list) - set(existing_ids))
        failed = list(set(existing_ids).intersection(set(members_list)))

        value = {"projectId": application_id, "memberIds": members_list}
        self._update_nested_properties(
            objects=value,
            path="members",
            op='add',
        )
        if config.verbose:
            if succeeded:
                print("Granted Security Role '{}' to {}".format(self.name, succeeded))
            if failed:
                print("Security Role '{}' already has member(s) {}".format(self.name, failed))

    def revoke_from(self, members: Union["UserOrGroup", List["UserOrGroup"]],
                    application: Union["Application", str]) -> None:
        """Remove users/user groups from a Security Role.

        Args:
            members(list): List of objects or IDs of Users or User Groups
                which will be removed from this Security Role.
            application(Application, str): Application object or name
                to which this removal will apply.
        """
        from mstrio.server.application import Application
        from mstrio.users_and_groups.user import User
        from mstrio.users_and_groups.user_group import UserGroup

        if isinstance(application, Application):
            application_id = application.id
            application_name = application.name
        elif isinstance(application, str):
            application_list = Application._list_applications(connection=self.connection,
                                                              to_dictionary=True, name=application)
            if application_list:
                application_id = application_list[0]['id']
                application_name = application_list[0]['name']
            else:
                helper.exception_handler(
                    "Application name '{}' does not exist.".format(application))
        else:
            helper.exception_handler("Application parameter must be of type str or Application.",
                                     TypeError)

        # create list of objects from strings/objects/lists
        members_list = members if isinstance(members, list) else [members]
        members_list = [
            obj.id if isinstance(obj, (User, UserGroup)) else str(obj) for obj in members_list
        ]

        existing_ids = [obj['id'] for obj in self.list_members(application_name=application_name)]
        succeeded = list(set(members_list).intersection(set(existing_ids)))
        failed = list(set(members_list) - set(succeeded))

        value = {"projectId": application_id, "memberIds": members_list}
        self._update_nested_properties(
            objects=value,
            path="members",
            op='remove',
        )

        if succeeded and config.verbose:
            print("Revoked Security Role '{}' from {}".format(self.name, succeeded))
        if failed and config.verbose:
            print("Security Role '{}' does not have member(s) {}".format(self.name, failed))

    def grant_privilege(
        self, privilege: Union[Union["Privilege", int, str], List[Union["Privilege", int,
                                                                        str]]]) -> None:
        """Grant new project-level privileges to the Security Role.

        Args:
            privilege: list of privilege objects, ids or names
        """
        # get all project level privileges
        from mstrio.access_and_security.privilege import Privilege
        project_level = [
            priv['id'] for priv in Privilege.list_privileges(self.connection, to_dictionary=True,
                                                             is_project_level_privilege='True')
        ]

        # validate and filter passed privileges
        privileges = Privilege._validate_privileges(self.connection, privilege)
        server_level = list(set([priv['id'] for priv in privileges]) - set(project_level))
        privileges = helper.filter_list_of_dicts(privileges, id=project_level)

        # create lists for print purposes
        privilege_ids = [priv['id'] for priv in privileges]
        existing_ids = [obj['id'] for obj in self.privileges]
        succeeded = list(set(privilege_ids) - set(existing_ids))
        failed = list(set(existing_ids).intersection(set(privilege_ids)))

        if server_level:
            msg = ("Privileges {} are server-level and will be ommited. Only project-level "
                   "privileges can be granted by this method.").format(sorted(server_level))
            helper.exception_handler(msg, exception_type=Warning)

        self._update_nested_properties(
            objects=privileges,
            path="privileges",
            op="addElement",
        )
        if succeeded:
            self.fetch()  # fetch the object properties and set object attributes
            if config.verbose:
                print("Granted privilege(s) {} to '{}'".format(succeeded, self.name))
        if failed and config.verbose:
            print("Security Role '{}' already has privilege(s) {}".format(self.name, failed))

    def revoke_privilege(
        self, privilege: Union[Union["Privilege", int, str], List[Union["Privilege", int,
                                                                        str]]]) -> None:
        """Revoke project-level privileges from the Security Role.

        Args:
            privilege: list of privilege objects, ids or names
        """
        # get all project level privileges
        from mstrio.access_and_security.privilege import Privilege
        project_level = [
            priv['id'] for priv in Privilege.list_privileges(self.connection, to_dictionary=True,
                                                             is_project_level_privilege='True')
        ]

        # validate and filter passed privileges
        privileges = Privilege._validate_privileges(self.connection, privilege)
        server_level = list(set([priv['id'] for priv in privileges]) - set(project_level))
        privileges = helper.filter_list_of_dicts(privileges, id=project_level)

        # create lists for print purposes
        privilege_ids = [priv['id'] for priv in privileges]
        existing_ids = [obj['id'] for obj in self.privileges]
        succeeded = list(set(privilege_ids).intersection(set(existing_ids)))
        failed = list(set(privilege_ids) - set(succeeded))

        if server_level:
            msg = ("Privilege(s) {} are server-level and will be ommited. Only project-level "
                   "privileges can be granted by this method.").format(sorted(server_level))
            helper.exception_handler(msg, exception_type=Warning)

        self._update_nested_properties(objects=privileges, path="privileges", op="removeElement")
        if succeeded:
            self.fetch()  # fetch the object properties and set object attributes
            if config.verbose:
                print("Revoked privilege(s) {} from '{}'".format(succeeded, self.name))
        elif failed and config.verbose:
            print("Security Role '{}' does not have privilege(s) {}".format(self.name, failed))

    def revoke_all_privileges(self, force: bool = False) -> None:
        """Revoke all granted project-level privileges.

        Args:
            force(bool, optional): If true, overrides the prompt.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                "Are you sure you want to revoke all privileges from Security Role '{}'? [Y/N]: "
                .format(self.name))
        if force or user_input == 'Y':
            from mstrio.access_and_security.privilege import Privilege
            project_level = [
                priv['id'] for priv in Privilege.list_privileges(
                    self.connection, to_dictionary=True, is_project_level_privilege='True')
            ]
            existing_ids = [obj['id'] for obj in self.privileges]
            to_revoke = list(set(project_level).intersection(set(existing_ids)))
            if to_revoke:
                self.revoke_privilege(privilege=to_revoke)
            else:
                print("Security Role '{}' does not have any privilege(s)".format(self.name))

    def list_privileges(self, to_dataframe: bool = False) -> Union[dict, DataFrame]:
        """List ALL privileges for Security Role. Optionally return a
        `DataFrame` object.

        Args:
            to_dataframe: If True, return a `DataFrame` object containing
                privileges
        """
        self.fetch()
        priv_dict = {int(v[1]): k[1] for k, v in [x.items() for x in self.privileges]}

        if to_dataframe:
            df = DataFrame.from_dict(priv_dict, orient='index', columns=['Name'])
            df.index.name = 'ID'
            return df
        else:
            return priv_dict

    def _update_nested_properties(self, objects, path: str, op: str) -> None:
        body = {
            "operationList": [{
                "op": op,
                "path": '/{}'.format(path),
                "value": objects
            }],
        }

        response = security.update_security_role(self.connection, self.id, body)
        response = response.json()
        if type(response) == dict:
            self._set_object(**response)

    @property
    def projects(self):
        return self._projects

    @property
    def privileges(self):
        return self._privileges
