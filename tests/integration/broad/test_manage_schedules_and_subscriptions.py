from unittest import TestCase
from mstrio.admin.application import Environment
from mstrio.admin.subscription.subscription import Subscription, EmailSubscription
from mstrio.admin.subscription.subscription_manager import SubscriptionManager, list_subscriptions
from mstrio.admin.subscription.delivery import Delivery, ZipSettings
from mstrio.admin.subscription.content import Content
from mstrio.admin.schedule import Schedule, ScheduleManager
from mstrio.utils.entity import ObjectTypes

from ..resources import mstr_connect as con
from ..resources.commons import read_configs
class TestManageSchedulesSubscriptions(TestCase):
    """TC69703"""
    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        self.env_url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.schedule_ids = general_configs["schedule_ids"]
        self.subscription_recipients = general_configs["sub_recipient_ids"]
        self.test_data = general_configs["sub_test_data"]
        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id="B7CA92F04B9FAE8D941C3E9B7E0CD754",
        )
        self.sm = ScheduleManager(self.connection)
        self.created_subscriptions = []

    def test_subscription_creation(self):
        for data in self.test_data:
            with self.subTest(data=data):
                self.create_subscription(content_type=data["content_type"],
                                         content_id=data["content_id"],
                                         format_type=data["format_type"])
                self.execute_subscription()
                self.list_all_subscriptions_within_a_project()
                self.list_all_subscriptions_for_all_projects()
                self.list_properties_for_subscription()
                self.list_schedules()
                self.get_properties_for_a_schedule()

    def create_subscription(self, content_type=None, content_id=None,
                            format_type=None):
        self.old_subs = list_subscriptions(
            connection=self.connection,
            application_id=self.connection.project_id
        )
        cont = Content(id=content_id,
                       type=content_type,
                       personalization=Content.Properties(
                           format_type=format_type,
                           delimiter=',',
                           compressed=True
                       )
                       )
        self.subscription = EmailSubscription.create(
            application_id=self.connection.project_id,
            connection=self.connection,
            name=f'integration_{content_type.lower()}_{content_id}',
            application_name='MicroStrategy Tutorial',
            contents=cont,
            schedules_ids=self.schedule_ids,
            recipients=self.subscription_recipients,
            send_now=True,
            email_include_data=False,
            email_subject="integration",
            email_message="TC69703 automated integration test"
        )
        self.created_subscriptions.append(self.subscription)
        self.new_subs = list_subscriptions(
            connection=self.connection,
            application_id=self.connection.project_id
        )
        self.new_subs = [s["id"] for s in self.new_subs]
        self.assertIsInstance(self.subscription, Subscription)
        self.assertNotIn(self.subscription, self.old_subs)
        self.assertIn(self.subscription.id, self.new_subs)

    def execute_subscription(self):
        self.subscription.execute()

    def list_all_subscriptions_within_a_project(self):
        self.project_subs = list_subscriptions(
            connection=self.connection,
            application_id=self.connection.project_id,
            to_dictionary=False
        )
        for sub in self.project_subs:
            with self.subTest(sub=sub):
                self.assertIsInstance(sub, Subscription)

        self.project_subs = list_subscriptions(
            connection=self.connection,
            application_id=self.connection.project_id,
            to_dictionary=True
        )
        for sub in self.project_subs:
            with self.subTest(sub=sub):
                self.assertIsInstance(sub, dict)

    def list_all_subscriptions_for_all_projects(self):
        subs = []
        env = Environment(self.connection)
        for app in env.list_applications():
            subs.extend(list_subscriptions(connection=self.connection,
                                           application_id=app.id,
                                           to_dictionary=False))
        for sub in subs:
            with self.subTest(sub=sub):
                self.assertIsInstance(sub, Subscription)
        self.assertGreaterEqual(len(subs), len(self.project_subs))

    def list_properties_for_subscription(self):
        subscription_properties = self.subscription.list_properties()
        self.assertGreater(len(subscription_properties), 0)

    def list_schedules(self):
        schedules = self.sm.list_schedules()
        for schedule in schedules:
            with self.subTest(schedule=schedule):
                self.assertIsInstance(schedule, dict)

    def get_properties_for_a_schedule(self):
        sch = Schedule(self.connection, self.schedule_ids[0])
        schedule_properties = sch.list_properties()
        self.assertGreater(len(schedule_properties), 0)

    def delete_created_subscription(self):
        self.subscription.delete(force=True)

    def tearDown(self) -> None:
        self.delete_created_subscription()
