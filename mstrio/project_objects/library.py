import contextlib
from typing import TYPE_CHECKING

from mstrio.api import library
from mstrio.connection import Connection
from mstrio.helpers import VersionException
from mstrio.object_management.library_shortcut import LibraryShortcut
from mstrio.project_objects.agents import Agent, list_agents
from mstrio.project_objects.dashboard import Dashboard, list_dashboards
from mstrio.project_objects.document import Document, list_documents
from mstrio.project_objects.report import Report, list_reports
from mstrio.utils.helper import deprecation_warning
from mstrio.utils.resolvers import get_project_id_from_params_set

if TYPE_CHECKING:
    from mstrio.server.project import Project


class Library:
    """Representation of the state of the authenticated user's Library.
    It contains the references to the documents, dashboards, and reports
    that have been shared to the user's Library.

    Attributes:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`.
        project_id (str): ID of the project that the Library is in.
        user_id (str): ID of the authenticated user.
        documents (list[Document]): List of documents in the Library.
        dashboards (list[Dashboard]): List of dashboards in the Library.
        contents (list[Document | Dashboard]): List of all contents
            (documents and dashboards) in the Library.
    """

    def __init__(
        self,
        connection: Connection,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ):
        """Initialize the Library object.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name
        """
        self.connection = connection
        self.user_id = connection.user_id

        self.project_id = get_project_id_from_params_set(
            connection,
            project,
            project_id,
            project_name,
        )

        # Shortcut data dicts, as they are retrieved from the Library API.
        # They are parsed directly into LibraryShortcut objects. Documents and
        # Dashboards are grouped together in the response, hence the joint dict
        self._doc_dbd_shortcuts_data: list[dict] = []
        self._report_shortcuts_data: list[dict] = []
        self._agent_shortcuts_data: list[dict] = []

        # Cached shortcut IDs for quick to avoid unnecessary retrieval of target
        # objects after the shortcuts list changes
        self._doc_dbd_cached_short_ids: set[str] = set()
        self._report_cached_short_ids: set[str] = set()
        self._agent_cached_short_ids: set[str] = set()

        # The shortcuts themselves and corresponding target objects
        self._documents: list[Document] = []
        self._dashboards: list[Dashboard] = []
        self._reports: list[Report] = []
        self._agents: list[Agent] = []
        self._document_shortcuts: list[LibraryShortcut] = []
        self._dashboard_shortcuts: list[LibraryShortcut] = []
        self._report_shortcuts: list[LibraryShortcut] = []
        self._agent_shortcuts: list[LibraryShortcut] = []

        self.fetch()

    def fetch(self):
        response: dict = library.get_library_v2(self.connection).json()
        self._doc_dbd_shortcuts_data = response.get('documentContents', [])
        self._report_shortcuts_data = response.get('reportContents', [])
        self._agent_shortcuts_data = response.get('aiBotContents', [])

    @staticmethod
    def _get_target_ids(shortcuts_data: list[dict]) -> list[str]:
        """Extracts target IDs from the shortcuts data."""
        return [
            sho.get('target', {}).get('id') for sho in shortcuts_data if 'target' in sho
        ]

    def _set_documents_dashboards(self, short_ids: set[str]):
        doc_ids = self._get_target_ids(self._doc_dbd_shortcuts_data)
        self._documents = list_documents(
            self.connection,
            project_id=self.project_id,
            id=doc_ids,
        )
        self._dashboards = list_dashboards(
            self.connection,
            project_id=self.project_id,
            id=doc_ids,
        )
        self._doc_dbd_cached_short_ids = short_ids

        document_short_ids = [doc.id for doc in self._documents]
        self._document_shortcuts = [
            LibraryShortcut.from_dict(sho, self.connection)
            for sho in self._doc_dbd_shortcuts_data
            if sho.get('target', {}).get('id') in document_short_ids
        ]
        dashboard_short_ids = [dbd.id for dbd in self._dashboards]
        self._dashboard_shortcuts = [
            LibraryShortcut.from_dict(sho, self.connection)
            for sho in self._doc_dbd_shortcuts_data
            if sho.get('target', {}).get('id') in dashboard_short_ids
        ]

    @property
    def documents(self):
        doc_dbd_live_short_ids = {doc['id'] for doc in self._doc_dbd_shortcuts_data}
        if doc_dbd_live_short_ids != self._doc_dbd_cached_short_ids:
            self._set_documents_dashboards(doc_dbd_live_short_ids)
        return self._documents

    @property
    def dashboards(self):
        doc_dbd_live_short_ids = {doc['id'] for doc in self._doc_dbd_shortcuts_data}
        if doc_dbd_live_short_ids != self._doc_dbd_cached_short_ids:
            self._set_documents_dashboards(doc_dbd_live_short_ids)
        return self._dashboards

    @property
    def reports(self):
        report_live_short_ids = {rep['id'] for rep in self._report_shortcuts_data}
        if report_live_short_ids != self._report_cached_short_ids:
            report_ids = self._get_target_ids(self._report_shortcuts_data)
            self._reports = list_reports(
                self.connection,
                project_id=self.project_id,
                id=report_ids,
            )
            self._report_cached_short_ids = report_live_short_ids
            self._report_shortcuts = [
                LibraryShortcut.from_dict(sho, self.connection)
                for sho in self._report_shortcuts_data
            ]
        return self._reports

    @property
    def bots(self):
        deprecation_warning(
            'Library.bots', 'Library.agents', '11.6.1.101', module=False  # NOSONAR
        )
        return self.agents

    @property
    def agents(self):
        agent_live_short_ids = {agent['id'] for agent in self._agent_shortcuts_data}
        if agent_live_short_ids != self._agent_cached_short_ids:
            agent_ids = self._get_target_ids(self._agent_shortcuts_data)
            with contextlib.suppress(VersionException):
                # Leave the agents field empty if no support
                self._agents = list_agents(
                    self.connection,
                    project_id=self.project_id,
                    id=agent_ids,
                )
            self._agent_cached_short_ids = agent_live_short_ids
            self._agent_shortcuts = [
                LibraryShortcut.from_dict(sho, self.connection)
                for sho in self._agent_shortcuts_data
            ]
        return self._agents

    @property
    def contents(self):
        return self.documents + self.dashboards + self.reports + self.agents

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
        """Unpublishes dashboard or document from the authenticated user's
        library.

        contents: dashboards or documents to be published, can be
            Dashboard/Document class object or ID
        """
        if not isinstance(contents, list):
            contents = [contents]
        for doc in contents:
            doc_id = doc.id if isinstance(doc, Document) else doc
            library.unpublish_document_for_user(
                self.connection,
                recipient_id=self.user_id,
                document_id=doc_id,
            )

    def list_library_shortcuts(self) -> list[LibraryShortcut]:
        """List all library shortcuts in the authenticated user's library.

        Returns:
            List of Library items as LibraryShortcut objects.
        """
        self.fetch()
        return [
            LibraryShortcut.from_dict(sho, self.connection)
            for sho in self._doc_dbd_shortcuts_data
            + self._report_shortcuts_data
            + self._agent_shortcuts_data
        ]
