import json
from unittest.mock import Mock


class MockDataset:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['objects']['create_search_objects_instance']) as f:
        create_search_objects_instance_data = json.load(f)

    with open(data_paths['objects']['get_objects']) as f:
        get_objects_data = json.load(f)

    with open(data_paths['objects']['update_object']) as f:
        update_object_data = json.load(f)

    with open(data_paths['objects']['get_object_info_dataset_admin']) as f:
        get_object_info_dataset_admin_data = json.load(f)

    @classmethod
    def mock_objects_api(cls):
        def mocked_get_object_info(connection, id, type):
            mocked_response = Mock(status_code=200)
            mocked_response.json.return_value = cls.get_object_info_dataset_admin_data
            return mocked_response

        def mocked_create_search_objects_instance(connection, name, pattern, object_type, error_msg):
            mocked_response = Mock(status_code=200)
            mocked_response.json.return_value = cls.create_search_objects_instance_data
            return mocked_response

        def mocked_get_objects(connection, search_id, offset, limit, error_msg):
            mocked_response = Mock(status_code=200)
            mocked_response.json.return_value = cls.get_objects_data
            mocked_response.headers = {'x-mstr-total-count': 1}
            return mocked_response

        def mocked_update_object(connection, id, body, type):
            mocked_response = Mock(status_code=200)
            mocked_response.json.return_value = cls.update_object_data
            return mocked_response

        mocked_objects = Mock()
        mocked_objects.get_object_info = mocked_get_object_info
        mocked_objects.create_search_objects_instance = mocked_create_search_objects_instance
        mocked_objects.get_objects = mocked_get_objects
        mocked_objects.update_object = mocked_update_object

        return mocked_objects
