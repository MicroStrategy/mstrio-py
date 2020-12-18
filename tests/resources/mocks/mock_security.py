import json
from unittest.mock import Mock


class MockSecurity:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['security']['privileges']) as f:
        all_privileges_data = json.load(f)

    @classmethod
    def mock_security_api(cls):
        def mocked_get_privileges(connection):
            response = Mock(status_code=200)
            response.json.return_value = cls.all_privileges_data
            return response

        mocked_security = Mock()
        mocked_security.get_privileges = mocked_get_privileges

        return mocked_security
