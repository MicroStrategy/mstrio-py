from unittest import TestCase

from mstrio.admin import security_role
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_role import MockRole


class TestSecurityRole(TestCase):
    def setUp(self) -> None:
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        security_role.security = MockRole.mock_security_api()

        security_role.SecurityRole._API_GETTERS = {None: security_role.security.get_security_role}

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')

    def test_init(self):
        r = security_role.SecurityRole(self.connection,
                                       id='73F7482111D3596C60001B8F67019608')
        self.assertEqual(r.id, '73F7482111D3596C60001B8F67019608')
