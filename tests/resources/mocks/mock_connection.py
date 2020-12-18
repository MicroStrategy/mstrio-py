import json
from unittest.mock import Mock


class MockConnection:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    @classmethod
    def mock_projects_api(cls):
        with open(cls.data_paths['other']['projects']) as f:
            projects_data = json.load(f)

        mocked_projects = Mock()
        mocked_projects.get_projects.return_value.json.return_value = projects_data
        return mocked_projects

    @classmethod
    def mock_authentication_api(cls):
        mocked_authentication = Mock()
        mocked_authentication.login.return_value.ok = True
        mocked_authentication.login.return_value.headers = {'X-MSTR-AuthToken': ''}
        mocked_authentication.login.return_value.cookies = ''

        mocked_authentication.session_renew.return_value.ok = True
        mocked_authentication.session_renew.return_value.headers = {'X-MSTR-AuthToken': ''}
        mocked_authentication.session_renew.return_value.cookies = ''

        mocked_authentication.delegate.return_value.ok = True
        mocked_authentication.delegate.return_value.headers = {'X-MSTR-AuthToken': ''}
        mocked_authentication.delegate.return_value.cookies = ''

        def mocked_get_info_for_authenticated_user(*args, **kwargs):
            response = Mock()
            response.ok = True
            response.headers = {'X-MSTR-AuthToken': ''}
            response.cookies = ''
            response.json.return_value = {'id': '123'}
            return response

        mocked_authentication.get_info_for_authenticated_user = mocked_get_info_for_authenticated_user

        return mocked_authentication

    @classmethod
    def mock_misc_api(cls):
        with open(cls.data_paths["other"]["server_status"]) as f:
            server_status = json.load(f)
        mocked_misc = Mock()
        mocked_misc.server_status.return_value.json.return_value = server_status

        return mocked_misc
