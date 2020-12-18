import json
from unittest.mock import Mock


class MockRole:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['security']['info']) as f:
        info_data = json.load(f)

    with open(data_paths['security']['create']) as f:
        create_data = json.load(f)

    with open(data_paths['security']['grant_role_to']) as f:
        grant_role_to_data = json.load(f)

    with open(data_paths['security']['revoke_role_from']) as f:
        revoke_role_from_data = json.load(f)

    @classmethod
    def mock_security_api(cls):
        def mocked_get_security_role(connection, id, error_msg=None, *args, **kwargs):
            mocked_security_role = Mock()
            mocked_security_role.json.return_value = cls.grant_role_to_data
            return mocked_security_role

        def mocked_update_security_role(connection, id, body):
            response = Mock(status_code=200)
            tmp_return_value = None
            op = body['operationList'][0]['op']
            if op == 'add':
                tmp_return_value = cls.grant_role_to_data
            if op == 'remove':
                tmp_return_value = cls.revoke_role_from_data
            response.json.return_value = tmp_return_value
            return response

        mocked_security = Mock()

        mocked_security.get_security_role = mocked_get_security_role

        create_response = Mock()
        create_response.json.return_value = cls.create_data
        mocked_security.create_security_role.return_value = create_response

        mocked_security.update_security_role = mocked_update_security_role

        return mocked_security
