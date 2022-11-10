from typing import List, TYPE_CHECKING, Union, Optional

from mstrio.api import library
from mstrio.project_objects.document import Document, list_documents
from mstrio.project_objects.dossier import list_dossiers
from mstrio.utils.helper import get_valid_project_id
from mstrio.connection import Connection

if TYPE_CHECKING:
    from mstrio.project_objects.dossier import Dossier


class Library:

    def __init__(
        self,
        connection: Connection,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        self.connection = connection
        ids = self.__get_library_ids()
        self.user_id = connection.user_id

        try:
            project_id = get_valid_project_id(
                connection=connection,
                project_id=project_id,
                project_name=project_name,
                with_fallback=False if project_name else True,
            )
        except ValueError:
            self._documents = None
            self._dossiers = None
            self._contents = None
            return

        self._documents = list_documents(self.connection, project_id=project_id, id=ids)
        self._dossiers = list_dossiers(self.connection, project_id=project_id, id=ids)
        self._contents = self._documents + self._dossiers

    def __get_library_ids(self):
        response = library.get_library(self.connection)
        body = response.json()
        ids = [doc_body['target']['id'] for doc_body in body if 'target' in doc_body]
        return ids

    @property
    def dossiers(self):
        if self.connection.project_id is not None:
            ids = self.__get_library_ids()
            self._dossiers = list_dossiers(self.connection, id=ids)
        return self._dossiers

    @property
    def documents(self):
        if self.connection.project_id is not None:
            ids = self.__get_library_ids()
            self._documents = list_documents(self.connection, id=ids)
        return self._documents

    @property
    def contents(self):
        if self.connection.project_id is not None:
            self._contents = self.dossiers + self.documents
        return self._contents

    def publish(self, contents: Union[List, "Document", "Dossier", str]):
        """Publishes dossier or document to the authenticated user's library.

        contents: dossiers or documents to be published, can be Dossier/Document
            class object or ID
        """
        if not isinstance(contents, list):
            contents = [contents]
        for doc in contents:
            doc_id = doc.id if isinstance(doc, Document) else doc
            body = {'id': doc_id, 'recipients': [{'id': self.user_id}]}
            library.publish_document(self.connection, body=body)

    def unpublish(self, contents: Union[List, "Document", "Dossier", str]):
        """Publishes dossier or document to the authenticated user's library.

        contents: dossiers or documents to be published, can be Dossier/Document
            class object or ID
        """
        if not isinstance(contents, list):
            contents = [contents]
        for doc in contents:
            doc_id = doc.id if isinstance(doc, Document) else doc
            library.unpublish_document_for_user(
                self.connection,
                user_id=self.user_id,
                document_id=doc_id,
            )
