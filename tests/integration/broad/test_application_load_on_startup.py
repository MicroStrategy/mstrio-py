from unittest import TestCase

from mstrio.admin.application import Environment

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestApplicationLoadOnStartup(TestCase):
    """Test if server startup applications as per settings."""
    # NOTE optimally test on multi-node environment

    @classmethod
    def setUpClass(cls):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])

        cls.env_url = general_configs["env_url"]
        cls.username = general_configs["username"]
        cls.password = general_configs["password"]
        cls.login_mode = general_configs["login_mode"]
        cls.project_id = general_configs["project_id"]
        cls.connection = con.get_connection(
            url=cls.env_url,
            username=cls.username,
            password=cls.password,
            login_mode=cls.login_mode,
            project_id=None,
        )
        cls.env = Environment(cls.connection)
        cls.nodes = cls.env.list_nodes()
        cls.all_node_names = [node['name'] for node in cls.nodes]
        cls.application = cls.env.list_loaded_applications()[0]

    @classmethod
    def tearDownClass(cls):
        cls.application.register(on_nodes=None)
        cls.connection.close()

    def tearDown(self):
        # reset the startup settings for each test
        self.application.unregister(on_nodes=None)

    def test_clear_startup_nodes_for_app(self):
        """Clear the current application startup settings.

        Application will not load on startup.
        """
        self.application.unregister(on_nodes=None)
        self.assertEqual(self.application.load_on_startup, [])

    def test_retrieve_app_startup_settings(self):
        """Get information about current startup settings per application."""
        self.initial_startup_settings = self.application.load_on_startup
        self.assertIsInstance(self.initial_startup_settings, list)

    def test_add_application_to_startup(self):
        """Modify application startup settings."""
        self.application.register(on_nodes=self.all_node_names)
        self.assertEqual(self.application.load_on_startup, self.all_node_names)

    def test_delete_application_from_startup(self):
        """Remove application from one node startup."""
        one_node = self.all_node_names[0]
        remaining_nodes = self.all_node_names[1:]
        self.application.register(on_nodes=self.all_node_names)
        self.application.unregister(on_nodes=one_node)
        self.assertEqual(self.application.load_on_startup, remaining_nodes)

    def test_register_all_nodes(self):
        """Remove application from one node startup."""
        self.application.register(on_nodes=None)
        self.assertEqual(self.application.load_on_startup, self.all_node_names)
