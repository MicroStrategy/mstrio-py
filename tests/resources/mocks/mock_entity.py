import json
from unittest.mock import Mock
from copy import deepcopy


class MockEntity:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['monitors']['nodes']) as f:
        nodes_data = json.load(f)

    with open(data_paths['monitors']['projects']) as f:
        projects_data = json.load(f)

    with open(data_paths['monitors']['projects_headers']) as f:
        projects_headers = json.load(f)

    @classmethod
    def mock_objects(cls):
        mocked_objects = Mock()
        return mocked_objects

    @classmethod
    def mock_monitors_api(cls):
        def mocked_get_node_info(connection, id, node_name):
            output = Mock()
            if id:
                temp = deepcopy(cls.nodes_data)
                for app in cls.nodes_data['nodes'][0]['projects']:
                    if app['id'] == id:
                        temp['nodes'][0]['projects'] = [app]
                        output.json.return_value = temp
                        return output
                    
                temp['nodes'][0]['projects'] = []
                output.json.return_value = temp
    
            else:
                output.json.return_value = cls.nodes_data

            return output

        def mocked_get_projects(connection, offset, limit, error_msg):
            output = Mock()
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

        mocked_monitors_api = Mock()

        mocked_monitors_api.get_node_info = mocked_get_node_info
        mocked_monitors_api.get_projects = mocked_get_projects
        mocked_monitors_api.get_projects_async = mocked_get_projects_async
        # mocked_monitors_api.update_node_properties.return_value.json.return_value = cls.update_node_data
        return mocked_monitors_api
