import json
from unittest.mock import Mock


class MockConnection:
    with open('production/tests/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['other']['projects']) as f:
        projects_data = json.load(f)

    @classmethod
    def mock_projects_api(cls):
        mocked_projects = Mock()
        mocked_projects.projects.return_value.json.return_value = cls.projects_data
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

        return mocked_authentication

    @classmethod
    def mock_misc_api(cls):
        mocked_misc = Mock()
        mocked_misc.server_status.return_value.json.return_value = {
            "iServerVersion": '11.2.2.1',
            "webVersion": '11.2.2.1',
        }
        return mocked_misc
