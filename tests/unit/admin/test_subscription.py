from unittest import TestCase

from mstrio.admin.subscription import subscription
from mstrio.admin.subscription import subscription_manager
from mstrio.admin import application
from mstrio.admin.subscription.subscription import Subscription, EmailSubscription
from mstrio.admin.subscription.subscription_manager import SubscriptionManager
from mstrio.admin.subscription.content import Content
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_subscription import MockSubscription
from production.tests.resources.mocks.mock_application import MockApplication


class TestSubscription(TestCase):

    def setUp(self):
        subscription.subscriptions = MockSubscription.mock_subscriptions_api()
        subscription_manager.subscriptions_ = MockSubscription.mock_subscriptions_api()

    @classmethod
    def setUpClass(cls):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        # application.monitors = MockApplication.mock_monitors_api()
        # application.objects = MockApplication.mock_objects_api()
        application.projects = MockApplication.mock_project_api()

        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')
        cls.sub_id = '9A81FE3F11EB1A9098050080EF05A3D3'
        cls.app_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'
        cls.app_name = 'MicroStrategy Tutorial'
        cls.user1_id = '1EFE801C11EB183CD8DC0080EFA5107E'
        cls.user2_id = 'B259574D11EB190ED8DC0080EF95F180'
        cls.user3_id = 'CCCE414211EB183BD8DC0080EFA51282'
        cls.schedule_id = '7EB853F34A6ED3C3A629A8BBDE3DDD68'
        cls.document_id = '643209B54CC84199C48A238ACB6CB621'

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_init_subscription(self):
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        self.assertIsNotNone(sub)
        self.assertEqual(sub.name, 'subscription test')

    def test_init_subscription_manager(self):
        sub_manager = SubscriptionManager(self.connection, application_id=self.app_id)
        self.assertIsNotNone(sub_manager)

    def test_list_subscriptions(self):
        sub_manager = SubscriptionManager(self.connection, application_id=self.app_id)
        subs_dict = sub_manager.list_subscriptions()
        self.assertGreater(len(subs_dict), 0)
        subs_dict = subscription_manager.list_subscriptions(self.connection, application_id=self.app_id)
        self.assertGreater(len(subs_dict), 0)
        subs = subscription_manager.list_subscriptions(self.connection, application_id=self.app_id, to_dictionary=False)
        self.assertGreater(len(subs), 0)

    def test_delete_subscriptions(self):
        sub_manager = SubscriptionManager(self.connection, application_id=self.app_id)
        to_be_deleted = ['9A81FE3F11EB1A9098050080EF05A3D3']
        is_deleted = sub_manager.delete(to_be_deleted, force=True)
        self.assertTrue(is_deleted)

    def test_execute_subscriptions(self):
        sub_manager = SubscriptionManager(self.connection, application_id=self.app_id)
        to_be_executed = ['9A81FE3F11EB1A9098050080EF05A3D3']
        sub_manager.execute(to_be_executed)

    def test_create_email_subscription(self):
        cont = Content(id=self.document_id,
                       type='DOCUMENT',
                       personalization=Content.Properties.from_dict({'format_type': 'PDF'}))
        sub = EmailSubscription.create(self.connection,
                                       name="subscription test",
                                       application_name=self.app_name,
                                       contents=cont,
                                       schedules_ids=self.schedule_id,
                                       recipients=[self.user1_id, self.user2_id],
                                       send_now=True,
                                       compress=False,
                                       email_subject="Demo Subscription Email",
                                       email_message='This is demo of subscription email')
        self.assertIsNotNone(sub)
        self.assertEqual(sub.name, 'subscription test')

    def test_alter_delivery(self):
        delivery = {
            'mode': 'EMAIL',
            'contactSecurity': True,
            'email': {
                'subject': 'Demo Subscription Email',
                'message': 'This is demo of subscription email',
                'sendContantAs': 'data',
                'overwriteOlderVersion': False
            }
        }
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        sub.alter(delivery=delivery)
        self.assertEqual(sub.delivery['email']['subject'], 'Demo Subscription Email')

    def test_available_recipients(self):
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        available_recipients = sub.available_recipients()
        self.assertIsNotNone(available_recipients)
        self.assertGreater(len(available_recipients), 0)

    def test_list_properties(self):
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        properties = sub.list_properties()
        self.assertIsNotNone(properties)
        self.assertTrue(properties['editable'])

    def test_execute(self):
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        sub.execute()

    def test_delete(self):
        sub = Subscription(connection=self.connection, subscription_id=self.sub_id, application_name=self.app_name)
        sub.delete(force=True)

    def test_add_recipient(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        self.assertEqual(len(sub.recipients), 2)
        sub.add_recipient([self.user3_id])
        self.assertEqual(len(sub.recipients), 3)

    def test_add_recipient_empty(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        error_occured = False
        try:
            sub.add_recipient()
        except ValueError:
            error_occured = True
        self.assertTrue(error_occured)

    def test_add_recipient_two_ways(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        error_occured = False
        try:
            sub.add_recipient(recipients=[self.user1_id], recipient_id=self.user1_id)
        except ValueError:
            error_occured = True
        self.assertTrue(error_occured)

    def test_add_recipient_already_exists(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        self.assertEqual(len(sub.recipients), 2)
        sub.add_recipient(recipients=[{'id': self.user1_id, 'type': 'user'}])
        self.assertEqual(len(sub.recipients), 2)

    def test_remove_recipient(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        self.assertEqual(len(sub.recipients), 2)
        sub.remove_recipient([self.user2_id])
        self.assertEqual(len(sub.recipients), 1)

    def test_remove_when_one_recipients(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        sub.recipients = [{
            "id": "1EFE801C11EB183CD8DC0080EFA5107E",
            "name": "Piotr Czyz",
            "isGroup": False,
            "type": "user",
            "includeType": "TO",
            "childSubscriptionId": "9A84CE8F11EB1A9098050080EF05A3D3"
        }]
        error_occured = False
        try:
            sub.remove_recipient(recipients=[self.user1_id])
        except Exception:
            error_occured = True
        self.assertTrue(error_occured)

    def test_remove_not_existing_recipient(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        self.assertEqual(len(sub.recipients), 2)
        sub.remove_recipient(recipients=['12341234123412341234123412341234'])
        self.assertEqual(len(sub.recipients), 2)

    def test_remove_all_recipients(self):
        sub = Subscription(self.connection, self.sub_id, self.app_id)
        error_occured = False
        try:
            sub.remove_recipient(recipients=[self.user1_id, self.user2_id])
        except Exception:
            error_occured = True
        self.assertTrue(error_occured)

    def test_bursting(self):
        sub_manager = SubscriptionManager(self.connection, application_id=self.app_id)
        content_dict = {'id': '643209B54CC84199C48A238ACB6CB621',
                        'name': 'Cockpit',
                        'type': 'document',
                        'personalization': {'compressed': True,
                                            'formatMode': 'DEFAULT',
                                            'viewMode': 'BOTH',
                                            'formatType': 'PDF'}}
        bursting_attrs = sub_manager.available_bursting_attributes(content_dict)
        self.assertEqual(len(bursting_attrs), 0)
