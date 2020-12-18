from copy import deepcopy
from unittest import TestCase

import mstrio.utils.settings as base_settings
from mstrio import connection
from mstrio.admin import server
from production.tests.resources.mocks.mock_cluster import MockCluster
from production.tests.resources.mocks.mock_connection import MockConnection


class TestServerSettings(TestCase):
    """Test ServerSettings settings class."""

    def setUp(self):
        server.administration = MockCluster.mock_administration_api()
        self.settings = server.ServerSettings(self.connection)

    @classmethod
    def setUpClass(cls):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_server_init(self):
        settings = self.settings
        self.assertLess(50, len(settings._CONFIG))
        self.assertLess(50, len(settings.__dict__))

    def test_print_object(self):
        self.assertEqual(None, print(self.settings))

    def test_invalid_setting_key(self):
        settings = self.settings
        with self.assertRaises(AttributeError):
            settings.xyz = 1

    def test_validate_setting_values_number(self):
        settings = self.settings
        self.assertIsInstance(settings.maxUserConnectionPerServer, base_settings.NumberSetting)
        settings.maxUserConnectionPerServer = -1
        settings.maxUserConnectionPerServer = 'No Limit'
        self.assertEqual(settings.maxUserConnectionPerServer.value, -1)
        settings.maxUserConnectionPerServer = 5
        self.assertEqual(settings.maxUserConnectionPerServer.value, 5)

        with self.assertRaises(TypeError):
            settings.maxUserConnectionPerServer = {}
        with self.assertRaises(TypeError):
            settings.maxUserConnectionPerServer = 'str'
        with self.assertRaises(TypeError):
            settings.maxUserConnectionPerServer = ['1']
        with self.assertRaises(ValueError):
            settings.maxUserConnectionPerServer = 1000000
        with self.assertRaises(ValueError):
            settings.maxUserConnectionPerServer = -10

    def test_validate_setting_values_string(self):
        settings = self.settings
        self.assertIsInstance(settings.workSetSwapPath, base_settings.StringSetting)
        settings.workSetSwapPath = 'path'
        self.assertEqual(settings.workSetSwapPath.value, 'path')

        with self.assertRaises(TypeError):
            settings.workSetSwapPath = 1
        with self.assertRaises(TypeError):
            settings.workSetSwapPath = True
        with self.assertRaises(TypeError):
            settings.workSetSwapPath = {}
        with self.assertRaises(TypeError):
            settings.workSetSwapPath = ['1']

    def test_validate_setting_values_boolean(self):
        settings = self.settings
        self.assertIsInstance(settings.enableAutoSessionRecovery, base_settings.BoolSetting)
        settings.enableAutoSessionRecovery = True
        self.assertEqual(settings.enableAutoSessionRecovery.value, True)
        settings.enableAutoSessionRecovery = False
        self.assertEqual(settings.enableAutoSessionRecovery.value, False)

        with self.assertRaises(TypeError):
            settings.enableAutoSessionRecovery = 'str'
        with self.assertRaises(TypeError):
            settings.enableAutoSessionRecovery = ['1']
        with self.assertRaises(TypeError):
            settings.enableAutoSessionRecovery = 1

    def test_validate_setting_values_enum(self):
        settings = self.settings
        self.assertIsInstance(settings.hLRepositoryType, base_settings.EnumSetting)
        settings.hLRepositoryType = 2
        settings.hLRepositoryType = 'File Based'
        self.assertEqual(settings.hLRepositoryType.value, 2)
        settings.hLRepositoryType = 1
        self.assertEqual(settings.hLRepositoryType.value, 1)

        with self.assertRaises(ValueError):
            settings.hLRepositoryType = 100
        with self.assertRaises(TypeError):
            settings.hLRepositoryType = 'str'
        with self.assertRaises(TypeError):
            settings.hLRepositoryType = ['1']
        with self.assertRaises(TypeError):
            settings.hLRepositoryType = True

    def test_validate_setting_values_time(self):
        settings = self.settings
        self.assertIsInstance(settings.defaultLicenseComplianceCheckTime, base_settings.TimeSetting)
        settings.defaultLicenseComplianceCheckTime = '23:56:00'
        self.assertEqual(settings.defaultLicenseComplianceCheckTime.value, '23:56:00')
        settings.defaultLicenseComplianceCheckTime = '23:40'
        self.assertEqual(settings.defaultLicenseComplianceCheckTime.value, '23:40')

        with self.assertRaises(TypeError):
            settings.defaultLicenseComplianceCheckTime = 12
        with self.assertRaises(ValueError):
            settings.defaultLicenseComplianceCheckTime = '12'
        with self.assertRaises(ValueError):
            settings.defaultLicenseComplianceCheckTime = '12;23'
        with self.assertRaises(ValueError):
            settings.defaultLicenseComplianceCheckTime = '12:23:65'

    def test_validate_setting_values_deprecated(self):
        settings = self.settings
        self.assertIsInstance(settings.maxContractLimitPercentage, base_settings.DeprecatedSetting)
        with self.assertWarns(DeprecationWarning):
            settings.maxContractLimitPercentage = 2

    def test_update_settings(self):
        settings = self.settings
        settings.maxUserConnectionPerServer = -1
        settings.workSetSwapPath = 'path'
        settings.enableAutoSessionRecovery = True
        settings.hLRepositoryType = 2
        settings.defaultLicenseComplianceCheckTime = '12:34:15'
        before_update = deepcopy(settings)

        self.settings.update()
        self.assertEqual(self.settings.list_properties(), before_update.list_properties())

    # TODO test unit conversion
    # TODO test precondition warning
