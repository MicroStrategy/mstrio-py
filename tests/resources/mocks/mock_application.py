import json
from unittest.mock import Mock
from copy import deepcopy


class MockApplication:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['monitors']['nodes']) as f:
        nodes_data = json.load(f)

    with open(data_paths['monitors']['projects']) as f:
        projects_data = json.load(f)

    with open(data_paths['projects']['projects']) as f:
        projects_projects_data = json.load(f)

    with open(data_paths['monitors']['user_connections']) as f:
        user_connections_data = json.load(f)

    with open(data_paths['monitors']['projects_headers']) as f:
        projects_headers = json.load(f)

    with open(data_paths['projects']['project']) as f:
        project_data = json.load(f)

    with open(data_paths['projects']['settings']) as f:
        project_setting = json.load(f)

    with open(data_paths['projects']['settings_config']) as f:
        project_setting_config = json.load(f)

    with open(data_paths['monitors']['status']) as f:
        status_data = json.load(f)

    with open(data_paths['objects']['get_object_info']) as f:
        object_info_data = json.load(f)

    @classmethod
    def mock_monitors_api(cls):
        def mocked_get_node_info(connection, id=None, node_name=None):
            output = Mock()
            if id:
                temp = deepcopy(cls.nodes_data)
                for app in cls.nodes_data['nodes'][0]['projects']:
                    if app['id'] == id:
                        temp['nodes'][0]['projects'] = [app]
                        output.json.return_value = temp
                        return output

                temp['nodes'] = []
                output.json.return_value = temp

            else:
                output.json.return_value = cls.nodes_data

            return output

        def mocked_get_projects(connection, offset, limit, error_msg):
            response = Mock()
            response.json.return_value = cls.projects_data
            response.headers = cls.projects_headers
            return response

        def mocked_get_projects_async(future_session, connection, offset, limit):
            output = Mock()
            response = Mock()
            response.json.return_value = cls.projects_data
            response.headers = cls.projects_headers
            output.result.return_value = response
            return output

        def mocked_update_node_properties(connection, node, id, body, **kwargs):
            response = Mock(status_code=202)
            response.json.return_value = cls.status_data

            value = body['operationList'][0]['value']
            response.json.return_value['project']['status'] = value

            return response

        def mocked_get_user_connections(connection, node_name, offset, limit, error_msg):
            response = Mock(status_code=200)
            tmp_user_connections_data = deepcopy(cls.user_connections_data)
            total_count = 11

            if (connection.username == 'username2'):
                # delete last element from the list to mocked the deletion of it
                tmp_user_connections_data['userConnections'] = tmp_user_connections_data['userConnections'][:10]
                total_count = 10

            response.json.return_value = tmp_user_connections_data
            response.headers = {'x-mstr-total-count': total_count}
            return response

        def mocked_delete_user_connection(connection, id, error_msg):
            response = Mock(status_code=204)
            return response

        mocked_monitors_api = Mock()
        mocked_monitors_api.get_node_info = mocked_get_node_info
        mocked_monitors_api.get_projects = mocked_get_projects
        mocked_monitors_api.get_projects_async = mocked_get_projects_async
        mocked_monitors_api.update_node_properties = mocked_update_node_properties
        # mocked_monitors_api.update_node_properties.return_value.json.return_value = cls.update_node_data
        mocked_monitors_api.get_user_connections = mocked_get_user_connections
        mocked_monitors_api.delete_user_connection = mocked_delete_user_connection

        return mocked_monitors_api

    @classmethod
    def mock_objects_api(cls):
        def mocked_get_object_info(connection, id, **kwargs):
            output = Mock()
            output.json.return_value = cls.object_info_data
            return output

        mocked_objects_api = Mock()
        mocked_objects_api.get_object_info = mocked_get_object_info

        return mocked_objects_api

    @classmethod
    def mock_project_api(cls):
        with open(cls.data_paths['projects']['projects']) as f:
            cls.projects_projects_data = json.load(f)
        with open(cls.data_paths['projects']['project']) as f:
            cls.project_data = json.load(f)
        with open(cls.data_paths['projects']['settings']) as f:
            cls.project_setting = json.load(f)
        with open(cls.data_paths['projects']['settings_config']) as f:
            cls.project_setting_config = json.load(f)

        def get_project(connection, name, whitelist):
            output = Mock(status_code=201)
            # response.json().get('code')
            output.json.return_value = cls.project_data
            return output

        def get_projects(connection, whitelist):
            output = Mock()
            output.json.return_value = cls.projects_projects_data
            return output

        def get_project_settings(connection, id, whitelist):
            output = Mock()
            output.json.return_value = cls.project_setting
            return output

        def get_project_settings_config(connection, id):
            output = Mock()
            output.json.return_value = cls.project_setting_config
            return output

        def mocked_update_project_settings(connection, id, body):
            mock = Mock(status_code=204)
            return mock

        def create_project(connection, body):
            response = Mock(status_code=201)
            return response

        mocked_project_api = Mock()
        mocked_project_api.get_project = get_project
        mocked_project_api.get_project_settings = get_project_settings
        mocked_project_api.create_project = create_project
        mocked_project_api.get_projects = get_projects
        mocked_project_api.get_project_settings_config = get_project_settings_config
        mocked_project_api.mocked_update_project_settings = mocked_update_project_settings

        return mocked_project_api
