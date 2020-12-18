import json
from unittest.mock import Mock


class MockLibrary:
    with open('production/tests/unit/settings/api_response_path.json') as f:
        data_paths = json.load(f)

    with open(data_paths['library']['library']) as f:
        all_library_data = json.load(f)

    with open(data_paths['library']['documents']) as f:
        all_documents_data = json.load(f)

    with open(data_paths['library']['document_info']) as f:
        single_document_data = json.load(f)

    with open(data_paths['library']['document_info_library']) as f:
        library_document_data = json.load(f)

    @classmethod
    def mock_library_api(cls):
        def mocked_get_library(connection):
            response = Mock(status_code=200)
            response.json.return_value = cls.all_library_data
            return response

        def mocked_get_document(connection, **kwargs):
            response = Mock(status_code=200)
            response.json.return_value = cls.library_document_data
            response.headers.get.return_value = 1
            return response

        mocked_library = Mock()
        mocked_library.get_library = mocked_get_library
        mocked_library.get_document = mocked_get_document

        return mocked_library

    @classmethod
    def mock_documents_api(cls):
        def mocked_get_documents(connection, **kwargs):
            response = Mock(status_code=200)
            response.json.return_value = cls.all_documents_data
            response.headers.get.return_value = 1
            return response

        def mocked_get_documents_async(future_session, connection, offset, limit):
            output = Mock()
            response = Mock()
            response.json.return_value = cls.all_documents_data
            output.result.return_value = response
            return output

        def mocked_get_dossiers(connection, **kwargs):
            response = Mock(status_code=200)
            response.json.return_value = cls.all_documents_data
            response.headers.get.return_value = 1
            return response

        def mocked_get_dossiers_async(future_session, connection, offset, limit):
            output = Mock()
            response = Mock()
            response.json.return_value = cls.all_documents_data
            output.result.return_value = response
            return output

        def mocked_create_new_document_instance(**kwargs):
            response = Mock(status_code=200)
            response.json.return_value = {
                'mid': '4321'
            }
            return response

        mocked_documents = Mock()
        mocked_documents.get_documents = mocked_get_documents
        mocked_documents.get_documents_async = mocked_get_documents_async
        mocked_documents.get_dossiers = mocked_get_documents
        mocked_documents.get_dossiers_async = mocked_get_documents_async
        mocked_documents.create_new_document_instance = mocked_create_new_document_instance

        return mocked_documents

    @classmethod
    def mock_objects_api(cls):
        def mocked_get_object_info(connection, **kwargs):
            response = Mock(status_code=200)
            response.ok = True
            response.json.return_value = cls.single_document_data
            return response

        def mocked_update_object(**kwargs):
            response = Mock(status_code=200)
            response.ok = True
            return response

        mocked_objects = Mock()
        mocked_objects.get_object_info = mocked_get_object_info
        mocked_objects.update_object = mocked_update_object

        return mocked_objects

    @classmethod
    def mock_bookmarks_api(cls):
        def mocked_get_bookmarks_from_shortcut(**kwargs):
            response = Mock(status_code=200)
            response.ok = True
            response.json.return_value = [{'id': 'BOOKMARK_ID',
                                           'name': "Bookmark Name"}]
            return response

        def mocked_get_document_shortcut(**kwargs):
            response = Mock(status_code=200)
            response.ok = True
            response.json.return_value = {'id': "SHORTCUTID"}
            return response


        mocked_bookmarks = Mock()
        mocked_bookmarks.get_bookmarks_from_shortcut = mocked_get_bookmarks_from_shortcut
        mocked_bookmarks.get_document_shortcut = mocked_get_document_shortcut
        return mocked_bookmarks

    @classmethod
    def mock_list_users(cls):
        mocked_list_users = Mock()
        mocked_list_users.return_value = ['user1']
        return mocked_list_users


