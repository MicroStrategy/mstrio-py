"""Mosaic data-server workspaces, pipelines and pipeline tables.

Note:
    The REST API surface has no collection-GET endpoint for workspaces,
    pipelines or tables, so no `list_*` functions are provided. Obtain
    workspace and pipeline IDs from Studio or from data-model pipeline
    table definitions; nested pipeline definitions are returned inside
    the workspace GET payload.
"""

import logging

from mstrio import config
from mstrio.api import workspaces
from mstrio.connection import Connection
from mstrio.utils.entity import EntityBase
from mstrio.utils.helper import delete_none_values
from mstrio.utils.version_helper import class_version_handler

logger = logging.getLogger(__name__)


@class_version_handler('11.6.0100')
class Workspace(EntityBase):
    """A Mosaic data-server workspace.

    There is no collection-GET endpoint for workspaces, so listing them is
    not supported. Obtain workspace IDs from Studio or from data-model
    pipeline table definitions.

    Attributes:
        id (str): ID of the workspace
        project_id (str): ID of the project the workspace belongs to; if
            None, the project selected on the connection applies
        date_created (str): creation date/time of the workspace
        date_modified (str): last modification date/time of the workspace
        dataset_serve_mode (str): serve mode of the workspace's dataset,
            one of: 'in_memory', 'connect_live', 'off_memory'
        sampling (dict): sampling settings, e.g.
            `{'type': 'first' | 'random', 'rowCount': 1000}`
        dss_host (str): DSS host
        dss_port (int): DSS port
        pipelines (list[Pipeline]): pipelines defined in the workspace
    """

    _API_GETTERS = {
        (
            'id',
            'date_created',
            'date_modified',
            'dataset_serve_mode',
            'sampling',
            'dss_host',
            'dss_port',
            'pipelines',
        ): workspaces.get_workspace
    }

    def __init__(
        self, connection: Connection, id: str, project_id: str | None = None
    ) -> None:
        """Initialize the Workspace object and fetch it from the server.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            id (str): ID of the workspace
            project_id (str, optional): ID of a project; if omitted, the
                project selected on the connection is used
        """
        super().__init__(connection=connection, object_id=id, project_id=project_id)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.project_id = kwargs.get('project_id')
        self.date_created = kwargs.get('date_created', default_value)
        self.date_modified = kwargs.get('date_modified', default_value)
        self.dataset_serve_mode = kwargs.get('dataset_serve_mode', default_value)
        self.sampling = kwargs.get('sampling', default_value)
        self.dss_host = kwargs.get('dss_host', default_value)
        self.dss_port = kwargs.get('dss_port', default_value)
        self._pipelines = kwargs.get('pipelines', default_value)

    @classmethod
    def create(
        cls,
        connection: Connection,
        dataset_serve_mode: str | None = None,
        sampling: dict | None = None,
        pipelines: list[dict] | None = None,
        project_id: str | None = None,
    ) -> 'Workspace':
        """Create a new workspace on the data server.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            dataset_serve_mode (str, optional): serve mode of the workspace's
                dataset, one of: 'in_memory', 'connect_live', 'off_memory'
            sampling (dict, optional): sampling settings, e.g.
                `{'type': 'first' | 'random', 'rowCount': 1000}`
            pipelines (list[dict], optional): pipeline definitions
                (`ms-Pipeline`) to create the workspace with
            project_id (str, optional): ID of a project; if omitted, the
                project selected on the connection is used

        Returns:
            Workspace object with the newly created workspace's definition.
        """
        body = delete_none_values(
            {
                'datasetServeMode': dataset_serve_mode,
                'sampling': sampling,
                'pipelines': pipelines,
            },
            recursion=False,
        )
        response = workspaces.create_workspace(
            connection, body=body, project_id=project_id
        )
        workspace = cls.from_dict(
            source={**response.json(), 'project_id': project_id},
            connection=connection,
        )
        if config.verbose:
            logger.info(f"Successfully created workspace with ID: '{workspace.id}'.")
        return workspace

    def alter(
        self,
        dataset_serve_mode: str | None = None,
        sampling: dict | None = None,
    ) -> None:
        """Alter the workspace's properties.

        Args:
            dataset_serve_mode (str, optional): serve mode of the workspace's
                dataset, one of: 'in_memory', 'connect_live', 'off_memory'
            sampling (dict, optional): sampling settings, e.g.
                `{'type': 'first' | 'random', 'rowCount': 1000}`

        Returns:
            None
        """
        body = delete_none_values(
            {'datasetServeMode': dataset_serve_mode, 'sampling': sampling},
            recursion=False,
        )
        response = workspaces.update_workspace(
            self.connection, self.id, body=body, project_id=self.project_id
        )
        self._set_object_attributes(**response.json())
        if config.verbose:
            logger.info(f"Successfully updated workspace with ID: '{self.id}'.")

    def delete(self, force: bool = False) -> bool:
        """Delete the workspace.

        Args:
            force (bool, optional): if True, no additional prompt will be
                shown before deleting the workspace, defaults to False

        Returns:
            True on success. False otherwise.
        """
        if not force:
            user_input = input(
                f"Are you sure you want to delete Workspace with ID: "
                f"'{self.id}'? [Y/N]: "
            )
            if user_input != 'Y':
                return False
        response = workspaces.delete_workspace(
            self.connection, self.id, project_id=self.project_id
        )
        if response.ok and config.verbose:
            logger.info(f"Successfully deleted Workspace with ID: '{self.id}'.")
        return response.ok

    @property
    def pipelines(self) -> list['Pipeline']:
        """Pipelines defined in the workspace, built from the fetched
        workspace definition."""
        if self._pipelines is None:
            self.fetch()
        return [
            Pipeline.from_dict(
                source={
                    **pipeline,
                    'workspace_id': self.id,
                    'project_id': self.project_id,
                },
                connection=self.connection,
            )
            for pipeline in self._pipelines or []
        ]

    def create_pipeline(
        self,
        name: str | None = None,
        root_table: dict | None = None,
        sql: str | None = None,
        body: dict | None = None,
    ) -> 'Pipeline':
        """Create a new pipeline in the workspace.

        Args:
            name (str, optional): name of the new pipeline (required by the
                server when creating a pipeline with a definition)
            root_table (dict, optional): root table of the pipeline's
                hierarchical table structure (`ms-dataServerRootTable`;
                required by the server when creating a pipeline with
                a definition)
            sql (str, optional): SQL of the pipeline
            body (dict, optional): full JSON-formatted `ms-Pipeline`
                definition; takes precedence over the other arguments.
                If no arguments are provided, an empty pipeline is created.

        Returns:
            Pipeline object with the newly created pipeline's definition.
        """
        if body is None:
            body = delete_none_values(
                {'name': name, 'rootTable': root_table, 'sql': sql},
                recursion=False,
            )
        response = workspaces.create_pipeline(
            self.connection, self.id, body=body, project_id=self.project_id
        )
        pipeline = Pipeline.from_dict(
            source={
                **response.json(),
                'workspace_id': self.id,
                'project_id': self.project_id,
            },
            connection=self.connection,
        )
        if config.verbose:
            logger.info(
                f"Successfully created pipeline with ID: '{pipeline.id}' "
                f"in workspace with ID: '{self.id}'."
            )
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> 'Pipeline':
        """Get a single pipeline of the workspace by its ID.

        Args:
            pipeline_id (str): ID of the pipeline

        Returns:
            Pipeline object fetched from the server.
        """
        return Pipeline(
            connection=self.connection,
            workspace_id=self.id,
            id=pipeline_id,
            project_id=self.project_id,
        )


@class_version_handler('11.6.0100')
class Pipeline(EntityBase):
    """A data processing pipeline within a Mosaic data-server workspace.

    There is no collection-GET endpoint for pipelines, so listing them
    directly is not supported. Use `Workspace.pipelines`, which is built
    from the workspace GET payload, or obtain pipeline IDs from Studio or
    from data-model pipeline table definitions.

    Attributes:
        id (str): ID of the pipeline
        workspace_id (str): ID of the workspace the pipeline belongs to
        project_id (str): ID of the project the pipeline belongs to; if
            None, the project selected on the connection applies
        name (str): name of the pipeline
        sql (str): SQL of the pipeline
        root_table (dict): root table of the pipeline's hierarchical table
            structure (`ms-dataServerRootTable`)
    """

    _API_GETTERS = {('id', 'name', 'sql', 'root_table'): workspaces.get_pipeline}

    def __init__(
        self,
        connection: Connection,
        workspace_id: str,
        id: str,
        project_id: str | None = None,
    ) -> None:
        """Initialize the Pipeline object and fetch it from the server.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            workspace_id (str): ID of the workspace the pipeline belongs to
            id (str): ID of the pipeline
            project_id (str, optional): ID of a project; if omitted, the
                project selected on the connection is used
        """
        super().__init__(
            connection=connection,
            object_id=id,
            workspace_id=workspace_id,
            project_id=project_id,
        )

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.workspace_id = kwargs.get('workspace_id')
        self.project_id = kwargs.get('project_id')
        self.sql = kwargs.get('sql', default_value)
        self.root_table = kwargs.get('root_table', default_value)

    def fetch(self, attr: str | None = None) -> None:
        """Fetch the latest pipeline definition from the server.

        Args:
            attr (str, optional): ignored; present for compatibility with
                the base class. The whole definition is always fetched.

        Returns:
            None
        """
        response = workspaces.get_pipeline(
            self.connection,
            workspace_id=self.workspace_id,
            pipeline_id=self.id,
            project_id=self.project_id,
        )
        self._set_object_attributes(**response.json())
        for key in self._API_GETTERS:
            self._add_to_fetched(key)

    def alter(
        self,
        name: str | None = None,
        root_table: dict | None = None,
        sql: str | None = None,
        body: dict | None = None,
    ) -> None:
        """Alter the pipeline's definition.

        Args:
            name (str, optional): new name of the pipeline
            root_table (dict, optional): new root table of the pipeline's
                hierarchical table structure (`ms-dataServerRootTable`)
            sql (str, optional): new SQL of the pipeline
            body (dict, optional): full JSON-formatted `ms-Pipeline`
                definition update; takes precedence over the other arguments

        Returns:
            None
        """
        if body is None:
            body = delete_none_values(
                {'name': name, 'rootTable': root_table, 'sql': sql},
                recursion=False,
            )
        response = workspaces.update_pipeline(
            self.connection,
            self.workspace_id,
            self.id,
            body=body,
            project_id=self.project_id,
        )
        self._set_object_attributes(**response.json())
        if config.verbose:
            logger.info(f"Successfully updated pipeline with ID: '{self.id}'.")

    def delete(self, force: bool = False) -> bool:
        """Delete the pipeline.

        Args:
            force (bool, optional): if True, no additional prompt will be
                shown before deleting the pipeline, defaults to False

        Returns:
            True on success. False otherwise.
        """
        if not force:
            user_input = input(
                f"Are you sure you want to delete Pipeline with ID: "
                f"'{self.id}'? [Y/N]: "
            )
            if user_input != 'Y':
                return False
        response = workspaces.delete_pipeline(
            self.connection,
            self.workspace_id,
            self.id,
            project_id=self.project_id,
        )
        if response.ok and config.verbose:
            logger.info(f"Successfully deleted Pipeline with ID: '{self.id}'.")
        return response.ok

    def refresh(self) -> None:
        """Refresh the pipeline to update its data and structure.

        Returns:
            None
        """
        workspaces.refresh_pipeline(
            self.connection,
            self.workspace_id,
            self.id,
            project_id=self.project_id,
        )
        if config.verbose:
            logger.info(f"Successfully refreshed pipeline with ID: '{self.id}'.")

    def create_table(self, body: dict | None = None) -> 'PipelineTable':
        """Create a new table in the pipeline.

        Args:
            body (dict): JSON-formatted definition of the new table. The
                server requires a typed table body:
                `ms-dataServerSourceTable` (`'type': 'source'`, with
                `columns`, `importSource`, `filter`, `sampling`) or
                `ms-dataServerWrangleTable` (`'type': 'wrangle'`, with
                `operations`, `columns`, `children`). An empty body `{}`
                fails with `8004d102 InvalidTypeIdException`
                (field-verified).

        Returns:
            PipelineTable object with the newly created table's definition.
        """
        response = workspaces.create_pipeline_table(
            self.connection,
            self.workspace_id,
            self.id,
            body=body,
            project_id=self.project_id,
        )
        table = PipelineTable.from_dict(
            source={
                **response.json(),
                'workspace_id': self.workspace_id,
                'pipeline_id': self.id,
                'project_id': self.project_id,
            },
            connection=self.connection,
        )
        if config.verbose:
            logger.info(
                f"Successfully created table with ID: '{table.id}' "
                f"in pipeline with ID: '{self.id}'."
            )
        return table

    def get_table(
        self,
        table_id: str,
        show_preview_data: bool = False,
        show_raw_data: bool = False,
    ) -> 'PipelineTable':
        """Get a single table of the pipeline by its ID.

        Args:
            table_id (str): ID of the table
            show_preview_data (bool, optional): whether to include preview
                data in the response, defaults to False
            show_raw_data (bool, optional): whether to include raw data in
                the response, defaults to False

        Returns:
            PipelineTable object fetched from the server.
        """
        response = workspaces.get_pipeline_table(
            self.connection,
            self.workspace_id,
            self.id,
            table_id,
            project_id=self.project_id,
            show_preview_data=show_preview_data,
            show_raw_data=show_raw_data,
        )
        return PipelineTable.from_dict(
            source={
                **response.json(),
                'workspace_id': self.workspace_id,
                'pipeline_id': self.id,
                'project_id': self.project_id,
            },
            connection=self.connection,
        )


@class_version_handler('11.6.0100')
class PipelineTable(EntityBase):
    """A table within a Mosaic data-server pipeline.

    A pipeline table is either a source table (`ms-dataServerSourceTable`,
    `table_type` 'source', with `columns`, `original_schema`,
    `import_source`, `filter`, `sampling`, `preview_data`) or a wrangle
    table (`ms-dataServerWrangleTable`, `table_type` 'wrangle', with
    `operations`, `columns`, `children`, `preview_data`). Fetched fields
    are stored generically as object attributes.

    There is no collection-GET endpoint for pipeline tables, so listing
    them directly is not supported. Obtain table IDs from Studio or from
    data-model pipeline table definitions.

    Attributes:
        id (str): ID of the table
        workspace_id (str): ID of the workspace the table belongs to
        pipeline_id (str): ID of the pipeline the table belongs to
        project_id (str): ID of the project the table belongs to; if None,
            the project selected on the connection applies
        table_type (str): type of the table: 'source' or 'wrangle'
            (REST field `type`)
    """

    _REST_ATTR_MAP = {'type': 'table_type'}

    def __init__(
        self,
        connection: Connection,
        workspace_id: str,
        pipeline_id: str,
        id: str,
        project_id: str | None = None,
    ) -> None:
        """Initialize the PipelineTable object and fetch it from the server.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            workspace_id (str): ID of the workspace the table belongs to
            pipeline_id (str): ID of the pipeline the table belongs to
            id (str): ID of the table
            project_id (str, optional): ID of a project; if omitted, the
                project selected on the connection is used
        """
        super().__init__(
            connection=connection,
            object_id=id,
            workspace_id=workspace_id,
            pipeline_id=pipeline_id,
            project_id=project_id,
        )
        if config.fetch_on_init:
            self.fetch()

    def _init_variables(self, default_value=None, **kwargs) -> None:
        kwargs = self._rest_to_python(kwargs)
        super()._init_variables(default_value=default_value, **kwargs)
        self.workspace_id = kwargs.get('workspace_id')
        self.pipeline_id = kwargs.get('pipeline_id')
        self.project_id = kwargs.get('project_id')
        self.table_type = kwargs.get('table_type', default_value)
        handled = {
            'connection',
            'id',
            'name',
            'table_type',
            'workspace_id',
            'pipeline_id',
            'project_id',
        }
        for key, value in kwargs.items():
            if key not in handled and not key.startswith('_'):
                setattr(self, key, value)

    def fetch(
        self, show_preview_data: bool = False, show_raw_data: bool = False
    ) -> None:
        """Fetch the latest table definition from the server.

        Args:
            show_preview_data (bool, optional): whether to include preview
                data in the response, defaults to False
            show_raw_data (bool, optional): whether to include raw data in
                the response, defaults to False

        Returns:
            None
        """
        response = workspaces.get_pipeline_table(
            self.connection,
            workspace_id=self.workspace_id,
            pipeline_id=self.pipeline_id,
            table_id=self.id,
            project_id=self.project_id,
            show_preview_data=show_preview_data,
            show_raw_data=show_raw_data,
        )
        self._set_object_attributes(**response.json())
        self._add_to_fetched('id')

    def alter(self, body: dict) -> None:
        """Alter the table's definition.

        Args:
            body (dict): JSON-formatted table definition update; shape
                depends on the table type: `ms-dataServerSourceTable`
                (`'type': 'source'`) or `ms-dataServerWrangleTable`
                (`'type': 'wrangle'`)

        Returns:
            None
        """
        response = workspaces.update_pipeline_table(
            self.connection,
            self.workspace_id,
            self.pipeline_id,
            self.id,
            body=body,
            project_id=self.project_id,
        )
        self._set_object_attributes(**response.json())
        if config.verbose:
            logger.info(f"Successfully updated table with ID: '{self.id}'.")

    def delete(self, force: bool = False) -> bool:
        """Delete the table.

        Args:
            force (bool, optional): if True, no additional prompt will be
                shown before deleting the table, defaults to False

        Returns:
            True on success. False otherwise.
        """
        if not force:
            user_input = input(
                f"Are you sure you want to delete PipelineTable with ID: "
                f"'{self.id}'? [Y/N]: "
            )
            if user_input != 'Y':
                return False
        response = workspaces.delete_pipeline_table(
            self.connection,
            self.workspace_id,
            self.pipeline_id,
            self.id,
            project_id=self.project_id,
        )
        if response.ok and config.verbose:
            logger.info(f"Successfully deleted PipelineTable with ID: '{self.id}'.")
        return response.ok
