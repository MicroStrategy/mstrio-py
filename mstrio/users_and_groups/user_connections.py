import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

from packaging import version

from mstrio import config
from mstrio.api import monitors
from mstrio.connection import Connection
from mstrio.server import Cluster
from mstrio.utils import helper

if TYPE_CHECKING:
    from mstrio.users_and_groups.user import User

logger = logging.getLogger(__name__)


class UserConnections:
    """Browse and manage active user connections on the environment. Use the
    `fetch()` method to fetch the latest active user connections. Filter the
    `user_connections` by using `filter_connections()` method.

    Attributes:
        connection: A MicroStrategy connection object
        user_connections: All active user connections on the environment
    """

    def __init__(self, connection: Connection):
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

    def filter_connections(self, **filters) -> Union[List[Dict[str, Any]], None]:
        """Filter the user connections stored in the `UserConnections` object
        by specifying the `filters` keyword arguments.

        Args:
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'project_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        """
        filtered_connections = None
        if not self.user_connections:
            helper.exception_handler(
                "Populate the `UserConnections` object with `UserConnections.fetch` first.",
                Warning
            )
        else:
            filtered_connections = helper.filter_list_of_dicts(self.user_connections, **filters)
        return filtered_connections

    def list_connections(self, nodes: Union[str, List[str]] = None, limit: Optional[int] = None,
                         **filters) -> List[Dict[str, Any]]:
        """Get all active user connections. Optionally filter the connections
        by specifying the `filters` keyword arguments.

        Args:
            nodes: Node (server) names on which users will be disconnected.
            limit: limit the number of elements returned. If `None`, all objects
                are returned.
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'project_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        """
        # TODO: This fully initialises a Cluster object every time the function
        # is run. It would be better to somehow cache it for a given connection.
        all_nodes = Cluster(self.connection).list_nodes(to_dictionary=True)
        all_connections = []
        if nodes is None:
            nodes = [node['name'] for node in all_nodes if node['status'] == 'running']
        else:
            nodes = nodes if isinstance(nodes, list) else [nodes]

        msg = 'Error fetching chunk of active user connections.'
        for node in nodes:
            all_connections.extend(
                helper.fetch_objects_async(self.connection, monitors.get_user_connections,
                                           monitors.get_user_connections_async,
                                           dict_unpack_value="userConnections", limit=limit,
                                           chunk_size=1000, error_msg=msg, node_name=node,
                                           filters=filters))
        return all_connections

    def disconnect_users(self, connection_ids: Union[str, List[str]] = None,
                         users: Optional[Union[List["User"],
                                               List[str]]] = None, nodes: Union[str,
                                                                                List[str]] = None,
                         force: bool = False, **filters) -> Union[List[dict], None]:
        """Disconnect user connections by passing in users (objects) or
        connection_ids. Optionally disconnect users by specifying the `filters`
        keyword arguments.

        Args:
            connection_ids: chosen ids that can be retrieved with
                `list_connections()`
            users: List of User objects or usernames
            nodes: Node (server) names on which users will be disconnected
            force: if True, no additional prompt will be shown before
                disconnecting users
            **filters: Available filter parameters: ['id', 'parent_id',
                'username', 'user_full_name', 'project_index', 'project_id',
                'project_name', 'open_jobs_count', 'project_type',
                'date_connection_created', 'duration', 'session_id', 'client',
                'config_level']
        Returns:
            - list of statuses of disconnecting chosen connections with theirs
              ids and messages from the I-Server:
                status code 200 is when all connections were disconnected
                status code 207 is when some connections were disconnected
                status code 403 without error code is when no connections were
                disconnected
            - in case of error of nothing to disconnect it returns None


        """
        from mstrio.users_and_groups.user import User  # import here to avoid circular imports

        if self.connection and not connection_ids and not users and not filters and not force:
            msg = ("You need to pass connection_ids or users or specify filters. To disconnect "
                   "all connections use `disconnect_all_users()` method.")
            helper.exception_handler(msg)

        if connection_ids:
            # disconnect specific user connections without fetching connections
            return self.__disconnect_by_connection_id(connection_ids)
        else:
            # get all user connections to filter locally
            all_connections = self.list_connections(nodes, **filters)
            if users:  # filter user connections by user objects
                users = users if isinstance(users, list) else [users]
                usernames = []
                for user in users:
                    if isinstance(user, User):
                        usernames.append(user.username)
                    elif isinstance(user, str):
                        usernames.append(user)
                    else:
                        helper.exception_handler(
                            "'user' param must be a list of User objects or usernames.",
                            exception_type=TypeError)

                all_connections = list(
                    filter(lambda conn: conn['username'] in usernames, all_connections))

            if all_connections:
                # extract connection ids and disconnect
                connection_ids = [conn['id'] for conn in all_connections]
                return self.__disconnect_by_connection_id(connection_ids)
            elif config.verbose:
                logger.info('No active user connections.')

    def disconnect_all_users(self, force: bool = False) -> Union[List[dict], None]:
        """Disconnect all user connections.

        Args:
            force: if True, no additional prompt will be shown before
                disconnecting all users

        Returns:
            - list of statuses of disconnecting all connections with their ids
               and messages from the I-Server
            - in case of error it returns None
        """
        if not force:
            user_input = input(
                "Are you sure you want to disconnect all users from the I-Server? [Y/N]: ")
            if user_input != "Y":
                return None
            else:
                force = True

        return self.disconnect_users(force=force)

    def __disconnect_by_connection_id(
            self, connection_ids: Union[str, List[str]]) -> Union[List[dict], None]:
        """It disconnects connections which ids are provided in
        'connection_ids'. It prints information about executed operations.
        Returns list of statuses of for the given connection ids with the
        messages from the I-Server or `None` in case of an error.
        """
        connection_ids = connection_ids if isinstance(connection_ids, list) else [connection_ids]
        server_version = helper.version_cut(self.connection.iserver_version)

        # use monitors.delete_user_connections
        # or monitors.delete_user_connection depending on the server version
        if version.parse(server_version) >= version.parse('11.3.1'):
            res = monitors.delete_user_connections(connection=self.connection, ids=connection_ids)
            if res.status_code in [200, 207] or (res.status_code == 403
                                                 and not res.json().get('code', None)):
                return self._prepare_disconnect_by_id_message(
                    statuses=res.json()['deleteUserConnectionsStatus'])
            else:
                err_msg = f'Error disconnecting user sessions: {connection_ids}.'
                return helper.response_handler(response=res, msg=err_msg, throw_error=False)
        else:
            # TODO: This can probably be made more elegant and potentially
            # performant if we use the ID as dict key and status as value
            # and maybe use comprehension instead of appending in loop.
            statuses: List[Dict[str, Union[str, int]]] = []
            for connection_id in connection_ids:
                response = monitors.delete_user_connection(self.connection, connection_id,
                                                           bulk=True)
                statuses.append({'id': connection_id, 'status': response.status_code})
            return self._prepare_disconnect_by_id_message(statuses=statuses)

    @staticmethod
    def _prepare_disconnect_by_id_message(statuses: List[dict]) -> List[dict]:
        succeeded = []
        failed = []

        for s in statuses:
            status = s['status']
            id = s['id']
            if status >= 200 and status < 300:
                succeeded.append(id)
            elif status >= 400:
                # in most cases there will be status code 403
                failed.append(id)

        if config.verbose:
            if succeeded:
                logger.info(
                    'User connections with ids below were successfully disconnected:\n\t'
                    + ',\n\t'.join(succeeded)
                )
            if failed:
                logger.warning(
                    'User connections with ids below were not disconnected:\n\t'
                    + ',\n\t'.join(failed)
                )

        return statuses
