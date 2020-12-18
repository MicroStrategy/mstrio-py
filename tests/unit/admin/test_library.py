from unittest import TestCase

from mstrio import connection, library
from mstrio.admin import document
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_library import MockLibrary


class TestLibrary(TestCase):
    def setUp(self) -> None:
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        from mstrio.utils import entity
        entity.objects = MockLibrary.mock_objects_api()
        entity.Entity._API_GETTERS = {None: entity.objects.get_object_info}

        from mstrio import library
        library.library = MockLibrary.mock_library_api()

        from mstrio.admin import document
        document.documents = MockLibrary.mock_documents_api()

        from mstrio.admin import dossier
        dossier.documents = MockLibrary.mock_documents_api()

        self.connection_no_proj = connection.Connection(base_url='http://mocked.url.com',
                                                        username='username',
                                                        password='password')

        self.connection_tutorial = connection.Connection(base_url='http://mocked.url.com',
                                                         username='username',
                                                         password='password',
                                                         project_name='MicroStrategy Tutorial')

    def test_init(self):
        l = library.Library(self.connection_no_proj)

        self.assertIsNone(l.documents)
        self.assertIsNone(l.dossiers)
        self.assertIsNone(l.contents)

        l = library.Library(self.connection_tutorial)

        self.assertEqual(len(l.documents), 2)
        self.assertEqual(len(l.dossiers), 2)
        self.assertEqual(len(l.contents), 4)
        self.assertIsInstance(l.documents[0], document.Document)
