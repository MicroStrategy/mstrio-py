from unittest import TestCase

from mstrio import connection
from mstrio.admin import document
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_library import MockLibrary


class TestDocument(TestCase):
    def setUp(self) -> None:
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        from mstrio.utils import entity
        entity.objects = MockLibrary.mock_objects_api()
        entity.Entity._API_GETTERS = {None: entity.objects.get_object_info}

        from mstrio.admin import document
        document.documents = MockLibrary.mock_documents_api()
        document.library = MockLibrary.mock_library_api()
        document.bookmarks = MockLibrary.mock_bookmarks_api()
        document.Document._API_PATCH = [entity.objects.update_object]
        document.list_users = MockLibrary.mock_list_users()

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')
        self.document_id = '123'

    def test_init(self):
        doc = document.Document(self.connection, self.document_id)
        doc.publish('user1')
        doc.unpublish()
        self.assertEqual(doc.id, self.document_id)
        self.assertRaises(Exception, doc.publish, recipients=1)
