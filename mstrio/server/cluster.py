import getpass
from typing import Dict, List, Optional, TYPE_CHECKING, Union

import numpy as np
import pandas as pd

from mstrio.api import administration, monitors, registrations
import mstrio.config as config
import mstrio.utils.helper as helper

if TYPE_CHECKING:
    from mstrio.server.application import Application
    from mstrio.connection import Connection


class Cluster:
    """Manage, list nodes (servers) on a cluster.

    Manage Services on nodes. Manage node settings. Load and Unload
    applications. A "service" is a product developed by MicroStrategy or
    a third-party product distributed by MicroStrategy i.e.
    "MicroStrategy Intelligence Server" or "Apache ZooKeeper".
    """

    def __init__(self, connection: "Connection"):
        """Initialize Cluster object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
        """
        self.connection = connection

    def list_nodes(self, application_id: str = None, node_name: str = None) -> List[dict]:
        """Return a list of nodes and their properties within the cluster.

        Optionally filter by `application_id` or `node_name`.

        Args:
            application_id: ID of application
            node_name: Name of node
        """
        response = monitors.get_node_info(self.connection, application_id, node_name).json()
        return response['nodes']

    def list_services(self, group_by: str = 'nodes') -> List:
        """List services in the cluster grouped by nodes or services.

        When `group_by` is set to `nodes` then in the list for each node there
        is given a list of services which are available within. When `group_by`
        is set to `services` then in the list for each services there is given a
        list of nodes on which current service is available.

        Args:
            group_by: determine by what the list will be grouped. Either
                `group_by` or `services`.
        Returns:
            list of nodes with services in case of `group_by` set to `nodes` or
            list of services with nodes in case of `group_by` set to `services`.
        Raise:
            ValueError if `group_by` is neither equal to `nodes` nor `services`.
        """
        if group_by == 'nodes':
            return registrations.get_nodes(connection=self.connection).json()
        elif group_by == 'services':
            return registrations.get_services(connection=self.connection).json()
        else:
            raise ValueError(
                "When listing services it is possible to group them only be `nodes` or `services`")

    def nodes_topology(self) -> pd.DataFrame:
        """View node topology in a cluster as Pandas DataFrame with following
        columns:
            - displayName -> it shows the name with which service is displayed
                in Workstation;
            - id -> name of the service within nodes;
            - for each node in the cluster there is given a column which name is
                name of a node and its content is information with the status of
                the given service in this node. Available values of status are:
                'Running' (additionally marked with green color), 'Stopped'
                (additionally marked with red color), 'Not Available (when
                service is not available in the node);

        Returns:
            DataFrame with topology of nodes.
        """
        nodes = self.list_services(group_by='nodes')
        metadata = registrations.get_services_metadata(connection=self.connection).json()
        service_type = pd.DataFrame(metadata["serviceTypes"])[['displayName', 'name']]

        for node in nodes:
            node_name = node['node']['node']
            if node['services']:
                node_service = pd.DataFrame(node['services'])[['id', 'status']]
                node_service['status'] = node_service['status'].map(
                    lambda x: 'Running' if x == "PASSING" else 'Stopped')
                tp = service_type.join(
                    node_service.set_index('id'),
                    on='name',
                    how='inner',
                )[['status']]
                # add column with statuses in current node
                service_type[node_name] = tp['status']
            else:
                # add an empty column in case of no services for the given node
                service_type[node_name] = np.nan

            service_type[node_name] = service_type[node_name].fillna('Not Available')

        service_type = service_type.rename(columns={'name': 'id'}, inplace=False)
        service_type = service_type.style.applymap(Cluster._show_color)
        return service_type

    def services_topology(self) -> pd.DataFrame:
        """Prepare topology of services in a cluster as DataFrame. This
        DataFrame has given columns:
            - service -> name of the service;
            - node -> name on which service appears (each service can appear in
                more than one service and then name of the service is provided
                only once for the group of nodes in which it appears);
            - status -> status which a given service has on a given node.
                Available values of statuses are: 'Running' (additionally marked
                with green color), 'Stopped' (additionally marked with red
                color), 'Not Available (when service is not available in the
                node)

        Returns:
            DataFrame with topology of services.
        """
        services = self.list_services(group_by='services')
        services_topology = [{
            "service": s['service'],
            "nodes": [{
                "node": n['node'],
                "status": n['status']
            } for n in s['nodes']]
        } for s in services]

        tmp = []
        for s in services_topology:
            for n in s['nodes']:
                n['service'] = s['service']
                tmp.append(n)

        tmp_df = pd.DataFrame(tmp)[['service', 'node', 'status']]
        tmp_df['status'] = tmp_df['status'].map(lambda x: 'Running'
                                                if x == "PASSING" else 'Stopped')
        tmp_df = tmp_df.set_index('service', append=True).swaplevel(0, 1)
        tmp_df = tmp_df.style.applymap(Cluster._show_color, subset='status')
        return tmp_df

    def add_node(self, name: str) -> None:
        """Add server (node) to the cluster.

        Args:
            name: name of node to be added
        """
        monitors.add_node(self.connection, name)
        if config.verbose:
            print("{} added to cluster.".format(name))

    def remove_node(self, name: str) -> None:
        """Remove server (node) from the cluster.

        Args:
            name: name of node to be removed
        """
        monitors.remove_node(self.connection, name)
        if config.verbose:
            print("{} removed from cluster.".format(name))

    def set_primary_node(self, name: str) -> None:
        """Set default/primary server (node) for the cluster.

        Args:
            name: name of the node which will be set as default for this cluster
        """
        body = {"defaultHostname": name}
        res = administration.update_iserver_configuration_settings(connection=self.connection,
                                                                   body=body)
        if res.ok and config.verbose:
            print("Primary node of the cluster was set to {}.".format(name))

    def check_dependency(self, service: str) -> List[str]:
        """Check all dependencies for the given service.

        Raises:
            ValueError: If incorrect service name is provided.
        """
        if not hasattr(self, '_metadata'):
            self._metadata = registrations.get_services_metadata(connection=self.connection).json()
        service_id_map = {
            service['typeId']: service['name'] for service in self._metadata['serviceTypes']
        }
        available_services = list(service_id_map.values())

        def get_dependencies_recursively(service_name: str):
            service = helper.filter_list_of_dicts(self._metadata['serviceTypes'],
                                                  name=service_name)
            if service:
                service = service[0]
                dependencies_set = {
                    name for id, name in service_id_map.items() if id in service['dependsOn']
                }

                if dependencies_set:
                    for srv in dependencies_set:
                        dependencies_set.update(get_dependencies_recursively(srv))
                    return dependencies_set
                else:
                    return {}
            else:
                raise ValueError((f"Service {service_name} is incorrect. Please choose one of: "
                                  f"{available_services}"))

        return list(get_dependencies_recursively(service))

    def start(self, service: 'str', nodes: List['str'], login=None, passwd=None):
        """Start up a service on selected nodes.

        Args:
            service: name of the service which will be started
            nodes: list of names of nodes on which service will be started
            login: login for SSH operation. If not provided, the user will be
                prompted.
            passwd: password for SSH operation. If not provided, the user will
                be prompted.
        Raises:
            ValueError: If incorrect node/service name is provided
        """
        self._control_service('START', service, nodes, login, passwd)

    def stop(self, service: 'str', nodes: List['str'], login=None, passwd=None, force=False):
        """Stop a service on selected nodes. Provided service and node names
        are checked for correctness.

        Args:
            service: name of the service which will be started
            nodes: list of names of nodes on which service will be started
            login: login for SSH operation. If not provided, the user will be
                prompted.
            passwd: password for SSH operation. If not provided, the user will
                be prompted.
            force: if True, no additional prompt will be showed before
        Raises:
            ValueError: If incorrect node/service name is provided
        """
        self._control_service('STOP', service, nodes, login, passwd, force)

    def _control_service(self, action: str, service: 'str', nodes: List['str'], login=None,
                         passwd=None, force=False):
        # validate inputs
        self._check_nodes(nodes)
        service_list = self.list_services(group_by='services')
        self._check_service(service, service_list)

        # ask for confirmation when stopping MicroStrategy-Intelligence-Server
        if action == 'STOP':
            if not force and service == 'MicroStrategy-Intelligence-Server':
                print(("Stopping the Intelligence Server can affect all the users' sessions, "
                       "including this current session."))
                if input("Are you sure you want to proceed? [Y/N]:") != 'Y':
                    return
        if action == 'START':
            self._check_dependencies(service, service_list)
        # get credentials for operation on service
        if not login or not passwd:
            print("Provide credentials for SSH operation.")
        if not login:
            login = input("username: ")
        if not passwd:
            passwd = getpass.getpass("password: ")
        wrong = []
        good = []
        # try to start each node; in case of error, execution is not terminated
        for node_name in nodes:
            info = Cluster._get_node_info(node_name, service, service_list)
            if not info:
                wrong.append(node_name)
                continue
            result = registrations.start_stop_service(
                connection=self.connection,
                login=login,
                password=passwd,
                name=service,
                id=info['id'],
                address=info['address'],
                action=action,
            ).ok
            if not result:
                wrong.append(node_name)
            else:
                good.append(node_name)
        self._show_start_stop_msg(service, wrong, good, action)

    def list_node_settings(self, node: str) -> Dict:
        """List server (nodes) settings.

        Args:
            node: name of node which settings will be listed

        Returns:
            dictionary with the settings of node returned from I-Server.
        """
        response = administration.get_iserver_node_settings(self.connection, node)
        return response.json()

    def update_node_settings(self, node: str, load_balance_factor: int, initial_pool_size: int,
                             max_pool_size: int) -> None:
        """Update I-Server configuration settings for a given server node
        within a cluster.

        Args:
            load_balance_factor: This setting becomes relevant in an environment
                that has a MicroStrategy Intelligence Server cluster. By
                default, the load balance factor is 1. The value can be
                increased on more powerful servers in a cluster to provide an
                appropriate balance. A larger load balance factor means the
                current server consumes a greater load in the server cluster in
                which it resides.
            initial_pool_size: Initial number of connections available.
            max_pool_size: Maximum number of connections available.
        """
        helper.validate_param_value("load_balance_factor", load_balance_factor, int, 100, 1)
        helper.validate_param_value("initial_pool_size", initial_pool_size, int, 1024, 1)
        helper.validate_param_value("max_pool_size", max_pool_size, int, 1024, 1)

        body = {
            "loadBalanceFactor": load_balance_factor,
            "initialPoolSize": initial_pool_size,
            "maxPoolSize": max_pool_size
        }
        response = administration.update_iserver_node_settings(self.connection, body, node)
        if config.verbose and response.ok:
            print(f"Intelligence Server configuration updated for {node}")

    def reset_node_settings(self, node: str) -> None:
        """Remove I-Server configuration settings for given node within a
        cluster. Default values will be applied after execution of this method.

        Args:
            node: name of the node for which default settings will be applied.
        """
        administration.delete_iserver_node_settings(self.connection, node)

    def list_applications(self, to_dictionary: bool = False, limit: int = None,
                          **filters) -> List["Application"]:
        """Return list of application objects or if `to_dictionary=True`
        application dicts. Optionally filter the Applications by specifying the
        `filters` keyword arguments.

        Args:
            to_dictionary: If True returns list of application dicts
            limit: limit the number of elements returned. If `None`, all objects
                are returned.
            **filters: Available filter parameters: ['name', 'id',
                'description', 'date_created', 'date_modified', 'owner']
        """
        from mstrio.server.environment import Environment
        env = Environment(connection=self.connection)
        return env.list_applications(to_dictionary=to_dictionary, limit=limit, **filters)

    def load_application(self, application_name: str, on_nodes: Union[str,
                                                                      List[str]] = None) -> None:
        """Request to load the application onto the chosen cluster nodes. If
        nodes are not specified, the application will be loaded on all nodes.

        Args:
            application_name: name of application which will be loaded
            on_nodes: name of node or nodes, if not passed, application will be
                loaded on all of the nodes
        """
        from mstrio.server.application import Application
        app = Application._list_applications(self.connection, name=application_name)[0]
        app.load(on_nodes=on_nodes)

    def unload_application(self, application_name: str, on_nodes: Union[str,
                                                                        List[str]] = None) -> None:
        """Request to unload the application from the chosen cluster nodes. If
        nodes are not specified, the application will be unloaded on all nodes.
        The unload action cannot be performed until all jobs and connections
        for application are completed. Once these processes have finished,
        pending application will be automatically unloaded.

        Args:
            application_name: name of application which will be unloaded
            on_nodes: name of node or nodes, if not passed, application will be
                unloaded on all of the nodes
        """
        from mstrio.server.application import Application
        app = Application._list_applications(self.connection, name=application_name)[0]
        app.unload(on_nodes=on_nodes)

    def _show_start_stop_msg(self, service_name, wrong, good, action):
        """Prepare message to show after action of stopping or starting a
        service with the information on which node the actions were good (done
        correctly) and on which were wrong (response status was not ok).
        """
        action_msg = 'started' if action == 'START' else 'stopped' if action == 'STOP' else ''
        if action_msg == '':
            return
        if len(wrong) > 0:
            nodes_msg = ', '.join(wrong)
            print(f'Service {service_name} was not {action_msg} for node(s) {nodes_msg}.')
        if len(good) > 0:
            action_msg = 'start' if action == 'START' else 'stop'
            nodes_msg = ','.join(good)
            print(f'Request to {action_msg} {service_name} was sent for node(s) {nodes_msg}.')

    def _check_service(self, service_name: 'str', service_list: List[Dict]) -> None:
        """Checks if the name of the given service is one of the names of
        existing services.

        Raises:
            ValueError: If name is incorrect.
        """
        valid_service_names = [service['service'] for service in service_list]

        if service_name not in valid_service_names:
            raise ValueError(
                f"Service {service_name} is incorrect. Please choose one of: {valid_service_names}"
            )

    def _check_dependencies(self, service_name: 'str', service_list: List[Dict]):
        """Check if service depends on other services.

        Warns if any one of the dependencies is not running.
        """
        dependencies = self.check_dependency(service_name)
        dependencies = [
            service for service in dependencies
            if not Cluster._check_service_running(service_name, service_list)
        ]

        if dependencies:
            helper.exception_handler(
                f"Service {service_name} depends on services {dependencies} to run correctly.",
                Warning)

    def _check_nodes(self, node_names: List['str']) -> None:
        """Checks if the names of the given nodes are within names of existing
        nodes. Checks if the node is running.

        Raises:
            ValueError: If name is incorrect.
        """
        all_nodes = self.list_nodes()
        all_node_names = [node['name'] for node in all_nodes]
        active_nodes = [
            node['name'] for node in filter(lambda node: node['status'] == 'running', all_nodes)
        ]

        for node_name in node_names:
            if node_name not in all_node_names:
                raise ValueError(
                    f"Node '{node_name}' is incorrect. Please choose one of: {all_node_names}")
            elif node_name not in active_nodes:
                raise ValueError(f"Node '{node_name}' is stopped. Try starting it first.")
            else:
                continue

    @staticmethod
    def _check_service_running(service_name: str, service_list: List[Dict],
                               node_name: str = None) -> bool:
        """Return True if service is running on any node available.

        If `node_name` is provided, the service status will be given for
        the selected node.
        """
        nodes_info = helper.filter_list_of_dicts(service_list, service=service_name)[0]['nodes']
        if node_name:
            node_info = helper.filter_list_of_dicts(nodes_info, node=node_name)[0]
            if node_info['status'] == 'PASSING':
                return True
            else:
                return False
        else:
            return bool([True for node in nodes_info if node['status'] == 'PASSING'])

    @staticmethod
    def _get_node_info(node_name: str, service_name: str, service_list: List[Dict]) -> Dict:
        nodes_info = helper.filter_list_of_dicts(service_list, service=service_name)[0]['nodes']
        node_info = helper.filter_list_of_dicts(nodes_info, node=node_name)
        if not node_info:
            helper.exception_handler(f"Service {service_name} is not available on {node_name}",
                                     exception_type=Warning)
            return None
        else:
            node_info = node_info[0]

        if node_info.get('serviceControl') is False:
            helper.exception_handler(f"Service {service_name} cannot be controlled on {node_name}",
                                     exception_type=Warning)
            return None
        else:
            return node_info

    @staticmethod
    def _show_color(val: str) -> str:
        """Prepare color in which values of columns in DataFrames for
        topologies are shown."""
        color = 'Green' if val == 'Running' else '#b22222' if val == 'Stopped' else 'Black'
        return 'color: %s' % color

    @property
    def default_node(self) -> Optional[str]:
        """Return name of default node for this cluster."""

        for n in self.list_nodes():
            if n.get('default', 'False') is True:
                return n.get('name')
        return None
