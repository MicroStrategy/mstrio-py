import json
from unittest.mock import Mock
from copy import deepcopy


class MockCluster:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    @classmethod
    def mock_registrations_api(cls):
        with open(cls.data_paths['cluster']['nodes']) as f:
            nodes_data = json.load(f)
        with open(cls.data_paths['cluster']['services']) as f:
            services_data = json.load(f)
        with open(cls.data_paths['cluster']['services_metadata']) as f:
            services_metadata = json.load(f)

        def mocked_get_nodes(connection):
            mocked_nodes = Mock(status_code=200)
            tmp_nodes_data = deepcopy(nodes_data)
            if connection.iserver_version == '11.3.0001':
                tmp_nodes_data[1]['node']['serviceControl'] = False
                tmp_nodes_data[1]['services'] = []
            mocked_nodes.json.return_value = tmp_nodes_data
            return mocked_nodes

        def mocked_get_services(connection):
            mocked_services = Mock(status_code=200)
            mocked_services.json.return_value = services_data
            return mocked_services

        def mocked_get_services_metadata(connection):
            mocked_services_metadata = Mock(status_code=200)
            mocked_services_metadata.json.return_value = services_metadata
            return mocked_services_metadata

        def mocked_start_stop_service(connection, login, password, name, id, address, action, error_msg=None):
            mocked_start_stop = Mock()
            if address == '10.250.145.142':
                status_code = 200
            elif address == '10.250.155.93':
                status_code = 500
            else:
                status_code = 400
            mocked_start_stop.status_code = status_code
            return mocked_start_stop

        mocked_registrations = Mock()
        mocked_registrations.get_nodes = mocked_get_nodes
        mocked_registrations.get_services = mocked_get_services
        mocked_registrations.get_services_metadata = mocked_get_services_metadata
        mocked_registrations.start_stop_service = mocked_start_stop_service

        return mocked_registrations

    @classmethod
    def mock_administration_api(cls):
        with open(cls.data_paths['cluster']['settings']) as f:
            iserver_settings = json.load(f)
        with open(cls.data_paths['cluster']['settings_config']) as f:
            iserver_settings_config = json.load(f)
        with open(cls.data_paths['cluster']['cluster_membership']) as f:
            cluster_membership_data = json.load(f)
        with open(cls.data_paths['cluster']['node_settings']) as f:
            node_settings_data = json.load(f)

        def mocked_get_cluster_membership(connection):
            mocked_cluster_membership = Mock(status_code=200)
            mocked_cluster_membership.json.return_value = cluster_membership_data
            return mocked_cluster_membership

        def mocked_get_iserver_node_settings(connection, node):
            mocked_node_settings = Mock(status_code=200)
            mocked_node_settings.json.return_value = node_settings_data
            return mocked_node_settings

        def mocked_delete_iserver_node_settings(connection, node):
            mocked_res = Mock(status_code=204)
            return mocked_res

        def mocked_get_iserver_settings(connection):
            mock = Mock(status_code=200)
            mock.json.return_value = iserver_settings
            return mock

        def mocked_get_iserver_settings_config(connection):
            mock = Mock(status_code=200)
            mock.json.return_value = iserver_settings_config
            return mock

        def mocked_update_iserver_settings(connection, body):
            mock = Mock(status_code=204)
            return mock

        mocked_administration = Mock()
        mocked_administration.get_cluster_membership = mocked_get_cluster_membership
        mocked_administration.get_iserver_node_settings = mocked_get_iserver_node_settings
        mocked_administration.delete_iserver_node_settings = mocked_delete_iserver_node_settings
        mocked_administration.get_iserver_settings = mocked_get_iserver_settings
        mocked_administration.get_iserver_settings_config = mocked_get_iserver_settings_config
        mocked_administration.mocked_update_iserver_settings = mocked_update_iserver_settings
        return mocked_administration

    @classmethod
    def mock_monitors_api(cls):
        with open(cls.data_paths['monitors']['two_nodes']) as f:
            nodes_data = json.load(f)

        def mocked_get_node_info(connection, id=None, node_name=None):
            output = Mock()
            if id:
                temp = deepcopy(nodes_data)
                for app in nodes_data['nodes'][0]['projects']:
                    if app['id'] == id:
                        temp['nodes'][0]['projects'] = [app]
                        output.json.return_value = temp
                        return output

                temp['nodes'] = []
                output.json.return_value = temp

            else:
                output.json.return_value = nodes_data

            return output

        def mocked_add_node(connection, add_node):
            res = Mock(status_code=200)
            res.json.return_value = {'status': 'running'}
            return res

        def mocked_remove_node(connection, add_node):
            res = Mock(status_code=204)
            return res

        mocked_monitors = Mock()
        mocked_monitors.get_node_info = mocked_get_node_info
        mocked_monitors.add_node = mocked_add_node
        mocked_monitors.remove_node = mocked_remove_node

        return mocked_monitors
