from unittest import TestCase

from mstrio.admin.document import list_documents, Document
from mstrio.admin.user import list_users, User

from production.tests.integration.resources import mstr_connect as con
from production.tests.integration.resources.commons import read_configs


class TestLibraryManagement(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        cls.general_configs = read_configs(cls.config_paths["general_configs"])

        cls.env_url = cls.general_configs["env_url"]
        cls.username = cls.general_configs["username"]
        cls.password = cls.general_configs["password"]
        cls.login_mode = cls.general_configs["login_mode"]
        cls.connection = con.get_connection(
            url=cls.env_url,
            username=cls.username,
            password=cls.password,
            login_mode=cls.login_mode,
            project_id="B7CA92F04B9FAE8D941C3E9B7E0CD754",
        )

    def setUp(self):
        documents = list_documents(self.connection)
        self.document = Document(self.connection, id=documents[0].id)
        self.user = User(connection=self.connection,
                         username=self.username)
        self.document.publish([self.user])

    def test_sharing(self):
        users = list_users(self.connection)
        self.document.unpublish()
        recipients1 = self.document.recipients
        self.assertEqual(len(recipients1), 0)
        self.document.publish(users[:2])
        self.document.fetch()
        recipients2 = self.document.recipients
        self.assertEqual(len(recipients2), 2)
        self.document.unpublish([users[0]])
        self.document.fetch()
        recipients3 = self.document.recipients
        self.assertEqual(len(recipients3), 1)

    def tearDown(self) -> None:
        self.document.unpublish()
        self.document.publish([self.user])

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
