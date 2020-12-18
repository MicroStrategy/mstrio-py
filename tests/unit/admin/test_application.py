from unittest import TestCase
from mstrio.admin import application
from mstrio import connection
from mstrio.utils import entity
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_entity import MockEntity
from production.tests.resources.mocks.mock_application import MockApplication

import os
import pandas as pd


class TestApplication(TestCase):

    def setUp(self):
        # to make sure that mocks' data is set before every test
        application.monitors = MockApplication.mock_monitors_api()
        application.objects = MockApplication.mock_objects_api()
        application.projects = MockApplication.mock_project_api()
        application.Application._API_GETTERS = {None: application.objects.get_object_info,
                                                'status': application.projects.get_project,
                                                'nodes': application.monitors.get_node_info
                                                }
        self.app = application.Application(self.connection, "BestApp")

    @classmethod
    def setUpClass(cls):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        entity.objects = MockEntity.mock_objects()

        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_init(self):
        a = self.app
        self.assertIsInstance(a.name, str)
        self.assertEqual(a.id, '62B6829211EAC6B0A1260080EFC54260')
        self.assertIsInstance(a.owner, dict)
        self.assertEqual(len(a.acl), 5)

    def test_create(self):
        e = application.Environment(self.connection)
        a = e.create_application("Test_App", "this is test app", force=True)
        self.assertIsInstance(a.name, str)
        self.assertEqual(a.id, '62B6829211EAC6B0A1260080EFC54260')
        self.assertIsInstance(a.owner, dict)
        self.assertEqual(len(a.acl), 5)

    def test_is_loaded(self):
        e = application.Environment(self.connection)
        e.list_applications()
        is_loaded = e.is_loaded(
            application_id="62B6829211EAC6B0A1260080EFC54260",
            application_name="BestApp"
        )
        self.assertTrue(is_loaded)

        is_loaded = e.is_loaded(
            application_id="1537259811EA9E7A0A5B0080EF15ED24",
            application_name="Project3"
        )
        self.assertFalse(is_loaded)

        is_loaded = e.is_loaded(
            application_id="a",
            application_name="a"
        )
        self.assertFalse(is_loaded)

    def test_applications(self):
        e = application.Environment(self.connection)
        applications = e.list_applications()
        self.assertIsInstance(applications, list)
        apps = applications
        self.assertEqual(apps[0].name, "BestApp")

    def test_raw_applications(self):
        e = application.Environment(self.connection)
        applications = e.list_applications(to_dictionary=True)
        self.assertIsInstance(applications, list)
        apps = applications
        self.assertEqual(apps[0]['id'], "62B6829211EAC6B0A1260080EFC54260")

        loaded_applications = e.list_applications(to_dictionary=True)
        self.assertIsInstance(applications, list)
        apps = loaded_applications
        self.assertEqual(apps[0]['id'], "62B6829211EAC6B0A1260080EFC54260")

    def test_nodes(self):
        e = application.Environment(self.connection)
        nodes = e.list_nodes()
        self.assertIsInstance(nodes, list)
        self.assertIsInstance(nodes[0], dict)
        self.assertEqual(nodes[0].get('name'), 'env-214578laiouse1')
        self.assertEqual(nodes[0].get('port'), 34952)

    def test_to_csv(self):
        a = self.app
        settings = a.settings
        settings.to_csv(name='tmp_csv.csv')
        f = open('tmp_csv.csv', 'r')
        file_content = f.read()
        self.assertGreater(len(file_content), 0)
        os.remove('tmp_csv.csv')

    def test_to_json(self):
        a = self.app
        settings = a.settings
        settings.to_json(name='tmp_json.json')
        f = open('tmp_json.json', 'r')
        file_content = f.read()
        f.close()
        self.assertGreater(len(file_content), 0)
        os.remove('tmp_json.json')

    def test_to_pickle(self):
        a = self.app
        settings = a.settings
        settings.to_pickle(name='tmp_pickle.pickle')
        f = open('tmp_pickle.pickle', 'rb')
        file_content = f.read()
        f.close()
        self.assertGreater(len(file_content), 0)
        os.remove('tmp_pickle.pickle')

    def help_import_from(self, file_name, file_type):
        a = self.app
        settings_dict = a.settings.list_properties()

        self.assertEqual(a.settings.maxReportResultRowCount.value, 32000)
        a.settings.maxReportResultRowCount = 33000

        if file_type == 'csv':
            a.settings.to_csv(name=file_name)
        elif file_type == 'json':
            a.settings.to_json(name=file_name)
        elif file_type == 'pickle':
            a.settings.to_pickle(name=file_name)

        a.settings.import_from(file=file_name)

        for setting1, setting2 in zip(a.settings.list_properties().items(), settings_dict.items()):
            with self.subTest():
                if setting1[0] == 'maxReportResultRowCount':
                    self.assertEqual(setting1[1], 33000)
                else:
                    self.assertEqual(setting1, setting2)
        os.remove(file_name)

    def test_import_from_pickle2(self):
        self.help_import_from(file_name='tmp_pickle2.pickle', file_type='pickle')

    def test_import_from_csv2(self):
        self.help_import_from(file_name='tmp_csv2.csv', file_type='csv')

    def test_import_from_json2(self):
        self.help_import_from(file_name='tmp_json2.json', file_type='json')

    def test_settings(self):
        a = self.app
        settings = a.settings
        self.assertIsInstance(settings, object)
        self.assertLess(100, len(settings.list_properties()))

    def test_load(self):
        a = application.Application(self.connection, "BestApp6")
        a.load()
        self.assertEqual(a.nodes[0]['projects'][0]['status'], 'loaded')

    def test_unload(self):
        a = application.Application(self.connection, "BestApp6")
        a.unload()
        self.assertEqual(a.nodes[0]['projects'][0]['status'], 'unloaded')

    def test_idle(self):
        a = application.Application(self.connection, "BestApp6")
        a.idle()
        self.assertEqual(a.nodes[0]['projects'][0]['status'], 'request_idle')

    def test_resume(self):
        a = application.Application(self.connection, "BestApp6")
        a.resume()
        self.assertEqual(a.nodes[0]['projects'][0]['status'], 'loaded')

    def test_properties(self):
        a = application.Application(self.connection, "BestApp6")
        self.assertIsInstance(a.to_dataframe(), pd.DataFrame)
        self.assertIsInstance(a.list_properties(), dict)
        self.assertIsInstance(a.settings.to_dataframe(), pd.DataFrame)
        self.assertIsInstance(a.settings.list_properties(), dict)
        self.assertIsInstance(a.settings.setting_types, pd.DataFrame)
