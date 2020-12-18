import json
from unittest.mock import Mock
from copy import deepcopy


class MockUser:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['user']['info']) as f:
        info_data = json.load(f)

    with open(data_paths['user']['create']) as f:
        create_data = json.load(f)

    with open(data_paths['user']['all_users']) as f:
        all_users_data = json.load(f)

    with open(data_paths['user']['new_address']) as f:
        new_address_data = json.load(f)

    with open(data_paths['user']['add_memberships']) as f:
        add_memberships = json.load(f)

    with open(data_paths['user']['remove_memberships']) as f:
        remove_memberships = json.load(f)

    with open(data_paths['user']['privileges']) as f:
        privileges_data = json.load(f)

    @classmethod
    def mock_users_api(cls):
        def mocked_get_user_info(connection, id, *args, **kwargs):
            mocked_user_info = Mock()
            mocked_user_info.json.return_value = cls.info_data
            return mocked_user_info

        def mocked_change_password(connection, body):
            output = Mock()
            if body['newPassword'] is None:
                output.status_code = 400
            if body['oldPassword'] is None:
                output.status_code = 400
            if body['username'] is None:
                output.status_code = 400
            else:
                output.status_code = 204
            return output

        def mocked_get_users_info(connection, name_begins, *args, **kwargs):
            response = Mock()
            response.json.return_value = cls.all_users_data
            response.status_code = 200
            response.headers = {'x-mstr-total-count': 2}
            return response

        def mocked_get_users_info_async(connection, name_begins, *args, **kwargs):
            output = Mock()
            response = Mock()
            response.json.return_value = cls.all_users_data
            response.status_code = 200
            output.result.return_value = response
            response.headers = {'x-mstr-total-count': 2}
            return output

        def mocked_delete_user(connection, id):
            response = Mock(status_code=204)
            return response

        def mocked_create_address(connection, id, body):
            response = Mock(status_code=200)
            response.json.return_value = cls.new_address_data
            return response

        def mocked_update_user_info(connection, id, body):
            response = Mock(status_code=200)
            op = body['operationList'][0]['op']
            if op == 'add':
                response.json.return_value = cls.add_memberships
            elif op == 'remove':
                objects_list = body['operationList'][0]['value']
                tmp_remove_memberships = deepcopy(cls.remove_memberships)
                if (len(objects_list) == 2):
                    tmp_remove_memberships['memberships'] = []
                response.json.return_value = tmp_remove_memberships

            return response

        def mocked_get_user_privileges(connection, id, project_id):
            user_id1 = '6DA105CF11EAD31783510080EF65A0DF'

            response = Mock(status_code=200)
            tmp_return_value = deepcopy(cls.privileges_data)
            if id != user_id1:
                tmp_return_value['privileges'] = []

            response.json.return_value = tmp_return_value
            return response

        mocked_users = Mock()
        mocked_users.get_user_info = mocked_get_user_info

        mocked_users.create_user = Mock()
        mocked_users.create_user.return_value.json.return_value = cls.create_data

        mocked_users.update_acl = Mock()
        mocked_users.update_acl.return_value = None

        mocked_users.change_password = mocked_change_password

        mocked_users.get_users_info = mocked_get_users_info

        mocked_users.get_users_info_async = mocked_get_users_info_async

        mocked_users.delete_user = mocked_delete_user

        mocked_users.create_address = mocked_create_address

        mocked_users.update_user_info = mocked_update_user_info

        mocked_users.get_user_privileges = mocked_get_user_privileges
        
        return mocked_users

    @classmethod
    def mock_objects_api(cls):
        def mocked_get_object_info(connection, id, type):
            response = Mock(status_code=200)
            response.json.return_value = {}
            return response
        
        mocked_objects = Mock()
        mocked_objects.get_object_info = mocked_get_object_info
        return mocked_objects
