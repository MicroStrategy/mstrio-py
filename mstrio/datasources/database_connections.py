import logging
from typing import Any, Dict, List, Optional, Union

from mstrio import config
from mstrio.api import monitors
from mstrio.connection import Connection
from mstrio.server.cluster import Cluster
from mstrio.utils import helper
from mstrio.utils.sessions import FuturesSessionWithRenewal
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


@class_version_handler('11.2.0000')
class DatabaseConnections:
    """Browse and manage database connections on the environment.

    Attributes:
        connection: A MicroStrategy connection object
    """

    def __init__(self, connection: Connection):
        """Initialize the `DatabaseConnections` object.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
        """
        self.connection = connection

    def list_connections(
        self, nodes: Union[str, List[str]] = None, limit: Optional[int] = None, **filters
    ) -> List[Dict[str, Any]]:
        """Get all active database connections. Optionally filter the
         connections by specifying the `filters` keyword arguments.

        Args:
            nodes: Node (server) names on which databases will be disconnected.
            limit: limit the number of elements returned. If `None`, all objects
                are returned.
            **filters: Available filter parameters: ['status',
                'database_instance_name', 'database_instance_id', 'user_name',
                'database_login_name', 'cluster_node', 'id', 'name', 'type']
        """
        if nodes is None:
            all_nodes = Cluster(self.connection).list_nodes(to_dictionary=True)
            nodes = [n['name'] for n in all_nodes if n['status'] == 'running']

        nodes_names = ",".join(nodes) if isinstance(nodes, list) else nodes
        all_databases = helper.fetch_objects(
            connection=self.connection,
            api=monitors.get_database_connections,
            nodes_names=nodes_names,
            dict_unpack_value="dbConnectionInstances",
            limit=limit,
            filters=filters
        )
        return all_databases

    def disconnect_database(self, connection_id: str, force: bool = False) -> bool:
        """Disconnect database connections by passing in connection_id.

        Args:
            connection_id: Database Connection Instance Id
            force: if True, no additional prompt will be shown before.
                Default False.
            Returns:
                True for success. False otherwise.
        """
        user_input = 'N'
        if not force:
            user_input = input(
                f"Are you sure you want to disconnect database connection "
                f"'with ID:{connection_id}? [Y/N]: "
            )
        if force or user_input == 'Y':
            response = monitors.delete_database_connection(self.connection, connection_id)
            if response.status_code == 204 and config.verbose:
                logger.info(
                    f'Successfully disconnected database connection instance {connection_id}.'
                )
            return response.ok
        else:
            return False

    def disconnect_all_databases(self, force: bool = False) -> Union[List[dict], None]:
        """Disconnect all database connections.

        Args:
            force: if True, no additional prompt will be shown before
                disconnecting all connections

        Returns:
            - list of statuses of disconnecting all connections with their ids
               and messages from the I-Server
            - in case of error it returns None
        """
        if not force:
            user_input = input(
                "Are you sure you want to disconnect all database connections? [Y/N]: "
            )
            if user_input != "Y":
                return None
            else:
                force = True

        connections = self.list_connections()
        threads = helper.get_parallel_number(len(connections))
        with FuturesSessionWithRenewal(connection=self.connection, max_workers=threads) as session:

            futures = [
                monitors.delete_database_connection_async(session, self.connection, conn["id"])
                for conn in connections
            ]
            statuses: List[Dict[str, Union[str, int]]] = []
            for f in futures:
                response = f.result()
                statuses.append(
                    {
                        'id': response.url.rsplit("/").pop(-1), 'status': response.status_code
                    }
                )
        return self._prepare_disconnect_by_id_message(statuses=statuses)

    @staticmethod
    def _prepare_disconnect_by_id_message(statuses: List[dict]) -> List[dict]:
        succeeded = []
        failed = []

        for s in statuses:
            status = s['status']
            if status < 400:
                succeeded.append(s['id'])
            else:
                # in most cases there will be status code 403
                failed.append(s['id'])

        if config.verbose:
            if succeeded:
                logger.info(
                    'Database connections with ids listed below were successfully '
                    'disconnected:\n\t' + ',\n\t'.join(succeeded)
                )
            if failed:
                logger.warning(
                    'Database connections with ids listed below were not disconnected:\n\t'
                    + ',\n\t'.join(failed)
                )
        return statuses
