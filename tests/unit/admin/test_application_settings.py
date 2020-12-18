from copy import deepcopy
from unittest import TestCase

import mstrio.utils.settings as base_settings
from mstrio import connection
from mstrio.admin import application
from production.tests.resources.mocks.mock_application import MockApplication
from production.tests.resources.mocks.mock_connection import MockConnection


class TestApplicationSettings(TestCase):
    """Test ApplicationSettings class."""

    def setUp(self):
        self.settings = application.ApplicationSettings(self.connection, self.project_id)

    @classmethod
    def setUpClass(cls):
        cls.project_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        application.projects = MockApplication.mock_project_api()
        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_application_init(self):
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
        settings.maxFTPSubscriptionCount = -1
        self.assertEqual(settings.maxFTPSubscriptionCount.value, -1)
        settings.maxFTPSubscriptionCount = 5
        self.assertEqual(settings.maxFTPSubscriptionCount.value, 5)

        with self.assertRaises(TypeError):
            settings.maxFTPSubscriptionCount = {}
        with self.assertRaises(TypeError):
            settings.maxFTPSubscriptionCount = 'str'
        with self.assertRaises(TypeError):
            settings.maxFTPSubscriptionCount = ['1']
        with self.assertRaises(ValueError):
            settings.maxFTPSubscriptionCount = 1000000
        with self.assertRaises(ValueError):
            settings.maxFTPSubscriptionCount = -10

    def test_validate_setting_values_string(self):
        settings = self.settings
        settings.missingObjectDisplay = 'path'
        self.assertEqual(settings.missingObjectDisplay.value, 'path')

        with self.assertRaises(TypeError):
            settings.missingObjectDisplay = 1
        with self.assertRaises(TypeError):
            settings.missingObjectDisplay = True
        with self.assertRaises(TypeError):
            settings.missingObjectDisplay = {}
        with self.assertRaises(TypeError):
            settings.missingObjectDisplay = ['1']

    def test_validate_setting_values_boolean(self):
        settings = self.settings
        settings.enableEmailDeliveryNotification = True
        self.assertEqual(settings.enableEmailDeliveryNotification.value, True)
        settings.enableEmailDeliveryNotification = False
        self.assertEqual(settings.enableEmailDeliveryNotification.value, False)

        with self.assertRaises(TypeError):
            settings.enableEmailDeliveryNotification = 'str'
        with self.assertRaises(TypeError):
            settings.enableEmailDeliveryNotification = ['1']
        with self.assertRaises(TypeError):
            settings.enableEmailDeliveryNotification = 1

    def test_validate_setting_values_enum(self):
        settings = self.settings
        settings.orderMultiSourceDBI = 0
        self.assertEqual(settings.orderMultiSourceDBI.value, 0)
        settings.orderMultiSourceDBI = 1
        self.assertEqual(settings.orderMultiSourceDBI.value, 1)

        with self.assertRaises(ValueError):
            settings.orderMultiSourceDBI = 4
        with self.assertRaises(TypeError):
            settings.orderMultiSourceDBI = 'str'
        with self.assertRaises(TypeError):
            settings.orderMultiSourceDBI = ['1']
        with self.assertRaises(TypeError):
            settings.orderMultiSourceDBI = True

    def test_validate_setting_values_email(self):
        settings = self.settings
        self.assertIsInstance(settings.emailAddressForMobileDelivery, base_settings.EmailSetting)
        settings.emailAddressForMobileDelivery = 'valid@email.com'
        self.assertEqual(settings.emailAddressForMobileDelivery.value, 'valid@email.com')

        with self.assertRaises(ValueError):
            settings.emailAddressForMobileDelivery = 'not@valid'
        with self.assertRaises(TypeError):
            settings.emailAddressForMobileDelivery = 4

    def test_update_settings(self):
        settings = self.settings
        settings.orderMultiSourceDBI = 0
        settings.enableEmailDeliveryNotification = False
        settings.maxFTPSubscriptionCount = 10
        settings.emailAddressForMobileDelivery = 'valid_2@email.com'
        settings.missingObjectDisplay = 'path'
        before_update = deepcopy(settings)

        self.settings.update()
        self.assertEqual(self.settings.list_properties(), before_update.list_properties())

    # TODO test unit conversion
    # TODO test precondition warning
