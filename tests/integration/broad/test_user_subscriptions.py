from unittest import TestCase

from mstrio.admin.subscription.content import Content
from mstrio.admin.subscription.subscription import EmailSubscription
from mstrio.admin.user import User

from ..resources import mstr_connect as con
from ..resources.commons import read_configs as rc


class TestUserSubscriptions(TestCase):
    """TC69702"""
    def setUp(self):
        conf_path = rc("production/tests/integration/resources/config_paths.json")
        confs = rc(conf_path["general_configs"])
        url = confs["env_url"]
        usr = confs["username"]
        pwd = confs["password"]
        mode = confs["login_mode"]
        pid = confs["project_id"]
        content_id = confs["sub_test_data"][0]["content_id"]
        content_type = confs["sub_test_data"][0]["content_type"]
        format_type = confs["sub_test_data"][0]["format_type"]
        schedule_ids = confs["schedule_ids"]
        subscription_recipients = confs["sub_recipient_ids"]
        self.connection = con.get_connection(url, usr, pwd, pid, mode)
        try:
            self.user = User(self.connection, confs["username3"])
        except ValueError:
            self.user = User.create(self.connection, confs["username3"], confs["username3"])
        cont = Content(id=content_id,
                       type=content_type,
                       personalization=Content.Properties(
                           format_type=format_type,
                           delimiter=',',
                           compressed=True
                       )
                       )
        self.sub = EmailSubscription.create(
            application_id=self.connection.project_id,
            connection=self.connection,
            name=f'integration_{content_type.lower()}_{content_id}',
            application_name='MicroStrategy Tutorial',
            contents=cont,
            schedules_ids=schedule_ids,
            recipients=subscription_recipients,
            send_now=True,
            email_include_data=False,
            email_subject="integration",
            email_message="TC69703 automated integration test"
        )
        self.address_name = "mail"
        self.address = "test_subs@mstr.com"

    def tearDown(self):
        self.sub.delete(force=True)
        for address in self.user.addresses:
            address_name = address['name']
            self.user.remove_address(name=address_name)
            self.connection.close()

    def test_user_subscriptions(self):
        self.add_address_to_user()
        self.add_user_to_subscription()
        self.remove_user_address()
        self.remove_user_from_subscription()

    def add_address_to_user(self):
        self.assertEqual(len(self.user.addresses), 0)
        self.user.add_address(self.address_name,
                              self.address)
        self.assertEqual(len(self.user.addresses), 1)

    def add_user_to_subscription(self):
        self.assertNotIn(
            self.user.id,
            [user["id"] for user in self.sub.recipients]
        )
        self.sub.add_recipient(recipient_id=self.user.id, recipient_type="USER")
        self.assertIn(self.user.id, [user["id"] for user in self.sub.recipients])

    def remove_user_address(self):
        self.user.remove_address(name=self.address_name)
        self.assertEqual(len(self.user.addresses), 0)

    def remove_user_from_subscription(self):
        self.sub.remove_recipient(self.user.id)
        self.assertNotIn(
            self.user.id,
            [user["id"] for user in self.sub.recipients]
        )
