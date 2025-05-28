from mstrio.api import library
from mstrio.connection import Connection
from mstrio.project_objects.dashboard import Dashboard, list_dashboards
from mstrio.project_objects.document import Document, list_documents
from mstrio.utils.helper import get_valid_project_id


class Library:
    def __init__(
        self,
        connection: Connection,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        self.connection = connection
        ids = self.__get_library_ids()
        self.user_id = connection.user_id

        try:
            project_id = get_valid_project_id(
                connection=connection,
                project_id=project_id,
                project_name=project_name,
                with_fallback=not project_name,
            )
        except ValueError:
            self._documents = None
            self._dashboards = None
            self._contents = None
            return

        self._documents = list_documents(self.connection, project_id=project_id, id=ids)
        self._dashboards = list_dashboards(
            self.connection, project_id=project_id, id=ids
        )
        self._contents = self._documents + self._dashboards

    def __get_library_ids(self):
        response = library.get_library(self.connection)
        body = response.json()
        ids = [doc_body['target']['id'] for doc_body in body if 'target' in doc_body]
        return ids

    @property
    def dashboards(self):
        if self.connection.project_id is not None:
            ids = self.__get_library_ids()
            self._dashboards = list_dashboards(self.connection, id=ids)
        return self._dashboards

    @property
    def documents(self):
        if self.connection.project_id is not None:
            ids = self.__get_library_ids()
            self._documents = list_documents(self.connection, id=ids)
        return self._documents

    @property
    def contents(self):
        if self.connection.project_id is not None:
            self._contents = self.dashboards + self.documents
        return self._contents

    def publish(self, contents: "list | Dashboard | Document | str"):
        """Publishes dashboard or document to the authenticated user's library.

        contents: dashboards or documents to be published, can be
            Dashboard/Document class object or ID
        """
        if not isinstance(contents, list):
            contents = [contents]
        for doc in contents:
            doc_id = doc.id if isinstance(doc, Document) else doc
            body = {'id': doc_id, 'recipients': [{'id': self.user_id}]}
            library.publish_document(self.connection, body=body)

    def unpublish(self, contents: "list | Dashboard | Document | str"):
        """Publishes dashboard or document to the authenticated user's library.

        contents: dashboards or documents to be published, can be
            Dashboard/Document class object or ID
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
