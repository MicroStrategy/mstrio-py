from typing import TYPE_CHECKING, List, Union, Dict, Any

import mstrio.config as config
from mstrio.admin.server import Cluster
from mstrio.api import monitors
from mstrio.utils import helper

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.admin.user import User


class UserConnections():
    """Browse and manage active user connections on the environment. Use the
    `fetch()` method to fetch the latest active user connections. Filter the
    `user_connections` by using `filter_connections()` method.

    Attributes:
        connection: A MicroStrategy connection object
        user_connections: All active user connections on the environment
    """

    def __init__(self, connection: "Connection"):
        """Initialize the `UserConnections` object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
        """
        self.connection = connection
        self.user_connections: List[Dict[str, Any]] = []

    def fetch(self) -> None:
        """Populate the `UserConnections` object by retrieving all active user
        connections on the environment."""
        self.user_connections = self.list_connections()

    def filter_connections(self, **filters) -> Union[list, None]:
        """Filter the user connections stored in the `UserConnections` object
        by specifying the `filters` keyword arguments.

        Args:
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'application_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        """
        filtered_connections = None
        if not self.user_connections:
            helper.exception_handler("Populate the `UserConnections` object with `UserConnections.fetch` first.", Warning)
        else:
            filtered_connections = helper.filter_list_of_dicts(self.user_connections, **filters)
        return filtered_connections

    def list_connections(self, nodes: Union[str, List[str]] = None,
                         limit: int = None, **filters) -> List[Dict[str, Any]]:
        """Get all active user connections. Optionally filter the connections
        by specifying the `filters` keyword arguments.

        Args:
            nodes: Node (server) names on which users will be disconnected.
            limit: limit the number of elements returned to a sample of
                connections. If `None`, all connections are returned.
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'application_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        """
        all_nodes = Cluster(self.connection).list_nodes()
        all_connections = []
        if nodes is None:
            nodes = [node['name'] for node in all_nodes if node['status'] == 'running']
        else:
            nodes = nodes if isinstance(nodes, list) else [nodes]

        msg = "Error fetching chunk of active user connections."
        for node in nodes:
            all_connections.extend(helper.fetch_objects_async(self.connection,
                                                              monitors.get_user_connections,
                                                              monitors.get_user_connections_async,
                                                              dict_unpack_value="userConnections",
                                                              limit=limit,
                                                              chunk_size=1000,
                                                              error_msg=msg,
                                                              node_name=node,
                                                              filters=filters))
        return all_connections

    def disconnect_users(self, connection_ids: Union[str, List[str]] = None,
                         users: Union[List["User"], List[str]] = None,
                         nodes: Union[str, List[str]] = None,
                         force: bool = False, **filters) -> None:
        """Disconnect user connections by passing in users (objects) or
        connection_ids. Optionally disconnect users by specifying the `filters`
        keyword arguments.

        Args:
            connection_ids: chosen ids that can be retrieved with
                `list_connections()`
            users: List of User objects or usernames
            nodes: Node (server) names on which users will be disconnected
            force: if True, no additional prompt will be showed before
                disconnecting users
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'application_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        """
        from mstrio.admin.user import User    # import here to avoid circular imports

        if self.connection and not connection_ids and not users and not filters and not force:
            helper.exception_handler("You need to pass connection_ids or users or specify filters. To disconnect all connections use `disconnect_all_users()` method.")

        if connection_ids:
            # disconnect specific user connections without fetching connections
            self.__disconnect_by_connection_id(connection_ids)
        else:
            # get all user connections to filter locally
            all_connections = self.list_connections(nodes, **filters)
            if users:       # filter user connections by user objects
                users = users if isinstance(users, list) else [users]
                usernames = []
                for user in users:
                    if isinstance(user, User):
                        usernames.append(user.username)
                    elif isinstance(user, str):
                        usernames.append(user)
                    else:
                        helper.exception_handler("'user' param must be a list of User objects or usernames.",
                                                 exception_type=TypeError)

                all_connections = list(filter(lambda conn: conn['username'] in usernames, all_connections))

            if all_connections:
                # extract connection ids and disconnect
                connection_ids = [conn['id'] for conn in all_connections]
                self.__disconnect_by_connection_id(connection_ids)
            elif config.verbose:
                print("Selected user(s) do not have any active connections")

    def disconnect_all_users(self, force: bool = False) -> None:
        """Disconnect all user connections.

        Args:
            force: if True, no additional prompt will be showed before
                disconnecting all users.
        """
        if not force:
            user_input = input("Are you sure you want to disconnect all users from the I-Server? [Y/N]: ")
            if user_input != "Y":
                return None
            else:
                force = True

        self.disconnect_users(force=force)

    def __disconnect_by_connection_id(self, connection_ids: Union[str, List[str]]) -> None:

        connection_ids = connection_ids if isinstance(connection_ids, list) else [connection_ids]

        failed = []
        for connection_id in connection_ids:
            response = monitors.delete_user_connection(self.connection, connection_id)
            if response.status_code == 204 and config.verbose:
                print("User connection '{}' disconnected".format(connection_id))
            elif not response.ok:       # any whitelisted
                failed.append(connection_id)

        if failed:
            if config.verbose:
                print("""\nCould not disconnect user connections: {}
                        \rI-Server Error ERR001, Failed to disconnect the user connection. It could be that:
                        \r(1) you are not allowed to disconnect yourself from MicroStrategy Intelligence Server
                        \r(2) the user connection does not exist
                        \r(3) you are trying to disconnect a scheduled connection""".format(failed))
