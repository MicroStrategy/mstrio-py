import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.helpers import VersionException
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity, TenantMixin
from mstrio.utils.enum_helper import AutoName, AutoPascalName, get_enum_val
from mstrio.utils.helper import (
    Dictable,
    delete_none_values,
    filter_params_for_func,
    get_objects_id,
    get_owner_id,
    normalize_enum_list,
)
from mstrio.utils.resolvers import (
    get_project_id_from_params_set,
    get_tenant_id_from_params_set,
)
from mstrio.utils.response_processors import documentation as doc_response_processors
from mstrio.utils.response_processors import (
    documentation_definition as doc_def_response_processors,
)
from mstrio.utils.time_helper import DatetimeFormats
from mstrio.utils.version_helper import is_server_min_version

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server.project import Project
    from mstrio.server.tenant import Tenant
    from mstrio.users_and_groups.user import User

# region Module-level functions


def get_documentations_statuses(
    connection: 'Connection',
    documentations: 'Documentation | str | list[Documentation | str]',
    to_dictionary: bool = False,
) -> 'dict[str, DocumentationStatus] | dict[str, dict]':
    """List statuses for one or more documentation jobs.

    Args:
        connection (Connection): Strategy connection object.
        documentations (Documentation | str | list[Documentation | str]):
            A documentation object, documentation ID, or a list containing
            documentation objects and/or IDs.
        to_dictionary (bool, optional): If `True`, returns dictionaries.
            If `False`, returns `DocumentationStatus` objects.

    Returns:
        A dictionary keyed by documentation ID with values of
        `DocumentationStatus` objects or dictionaries, depending on
        `to_dictionary`.
    """
    doc_list = documentations if isinstance(documentations, list) else [documentations]

    documentation_ids = []
    for doc in doc_list:
        doc_id = get_objects_id(doc, Documentation)
        if doc_id:
            documentation_ids.append(doc_id)

    if not documentation_ids:
        msg = "Please provide at least one valid documentation ID."
        raise ValueError(msg)

    status_dicts = doc_response_processors.get_documentation_status(
        connection=connection,
        documentation_ids=','.join(documentation_ids),
    )

    if to_dictionary:
        return {status['id']: status for status in status_dicts}

    statuses = DocumentationStatus.bulk_from_dict(status_dicts)
    return {status.id: status for status in statuses}


def list_documentations(
    connection: 'Connection',
    definition: 'DocumentationDefinition | str | None' = None,
    name: str | None = None,
    status: 'EnumDocumentationStatus | str | None' = None,
    project: 'Project | str | None' = None,
    project_id: 'str | None' = None,
    project_name: 'str | None' = None,
    limit: int | None = None,
    to_dictionary: bool = False,
) -> 'list[Documentation] | list[dict]':
    """List documentation jobs.

    Args:
        connection (Connection): Strategy connection object.
        definition (DocumentationDefinition | str, optional): Documentation
            definition object or ID used to filter jobs by definition.
        name (str, optional): Documentation name filter.
        status (EnumDocumentationStatus | str, optional): Documentation
            status filter. Accepts `EnumDocumentationStatus` or one of:
            `Running`, `Ready`, `Error`, `Canceled`.
        project (Project | str, optional): Project object, ID, or name used
            to scope results.
        project_id (str, optional): Project ID used to scope results.
        project_name (str, optional): Project name used to scope results.
        limit (int, optional): Maximum number of jobs to return. If `None`,
            all available jobs are returned.
        to_dictionary (bool, optional): If `True`, returns raw dictionaries
            from the API.
            If `False`, returns `Documentation` objects.

    Returns:
        List of `Documentation` objects or list of dictionaries, based on
        `to_dictionary`.
    """

    documentation_definition_id = get_objects_id(definition, DocumentationDefinition)

    status_value = get_enum_val(status, EnumDocumentationStatus)
    proj_id = get_project_id_from_params_set(
        connection,
        project=project,
        project_id=project_id,
        project_name=project_name,
        assert_id_exists=False,
        no_fallback_from_connection=True,
    )

    documentation_dicts = doc_response_processors.get_documentation_list(
        connection=connection,
        documentation_name=name,
        documentation_definition_id=documentation_definition_id,
        project_id=proj_id,
        status=status_value,
        limit=limit,
    )

    if to_dictionary:
        return documentation_dicts

    documentations = Documentation.bulk_from_dict(
        source_list=documentation_dicts,
        connection=connection,
    )
    return documentations


def list_documentation_definitions(
    connection: 'Connection',
    id: str | None = None,
    name: str | None = None,
    sort_by: 'DocDefinitionSortBy | str | None' = None,
    include_embedded: bool | None = None,
    tenant: 'Tenant | str | None' = None,
    tenant_id: str | None = None,
    tenant_name: str | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    owner: 'User | str | None' = None,
    owner_id: str | None = None,
    owner_name: str | None = None,
    date_created: str | None = None,
    last_run: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    to_dictionary: bool = False,
) -> 'list[DocumentationDefinition] | list[dict]':
    """List documentation definitions.

    Args:
        connection (Connection): Strategy connection object.
        id (str, optional): Comma-separated list of definition IDs.
        name (str, optional): Expected definition name filter.
        sort_by (DocDefinitionSortBy | str, optional): Sort by field with
            direction. String values must include a sign prefix where
            `+` means ascending and `-` means descending (for example:
            `+id`, `-name`). Supported fields are
            `id`, `name`, `type`, `projectName`, `ownerName`,
            `dateCreated`, `lastRun`, and `size`.
        include_embedded (bool, optional): Whether to include embedded
            definition details in response.
        tenant (Tenant | str, optional): Tenant object, ID, or name used
            to filter definitions.
        tenant_id (str, optional): Tenant ID used to filter definitions.
        tenant_name (str, optional): Tenant name used to filter
            definitions.
        project (Project | str, optional): Expected project object, ID, or
            name filter.
        project_id (str, optional): Expected project ID filter.
        project_name (str, optional): Expected project name filter.
        owner (User | str, optional): Owner object or ID used to filter
            definitions.
        owner_id (str, optional): Owner ID used to filter definitions.
        owner_name (str, optional): Owner username used to filter
            definitions.
        date_created (str, optional): Date created filter expression.
        last_run (str, optional): Last run filter expression.
        offset (int, optional): Pagination offset.
        limit (int, optional): Expected maximum number of returned
            definitions. If `None`, all available definitions are returned.
        to_dictionary (bool, optional): If `True`, expected to return
            dictionaries.

    Returns:
        A list of `DocumentationDefinition` objects or dictionaries.
    """
    resolved_owner_id = get_owner_id(
        connection=connection,
        owner=owner,
        owner_id=owner_id,
        owner_username=owner_name,
    )
    resolved_tenant_id = get_tenant_id_from_params_set(
        connection,
        tenant=tenant,
        tenant_id=tenant_id,
        tenant_name=tenant_name,
        assert_id_exists=False,
    )
    resolved_project_id = get_project_id_from_params_set(
        connection,
        project=project,
        project_id=project_id,
        project_name=project_name,
        assert_id_exists=False,
        no_fallback_from_connection=True,
    )
    sort_by_value = get_enum_val(sort_by, DocDefinitionSortBy)

    definitions_dicts = doc_def_response_processors.get_documentation_definition_list(
        connection=connection,
        id=id,
        name=name,
        sort_by=sort_by_value,
        include_embedded=include_embedded,
        tenant_id=resolved_tenant_id,
        owner_id=resolved_owner_id,
        project_id=resolved_project_id,
        date_created=date_created,
        last_run=last_run,
        offset=offset,
        limit=limit,
    )

    if to_dictionary:
        return definitions_dicts

    return DocumentationDefinition.bulk_from_dict(
        source_list=definitions_dicts,
        connection=connection,
    )


# endregion

# region Enums


class EnumDocumentationStatus(AutoPascalName):
    """Execution status values for a documentation job.

    Used with `Documentation` and `list_documentations` to filter or
    inspect the current state of a documentation job.
    """

    RUNNING = auto()
    READY = auto()
    ERROR = auto()
    CANCELED = auto()


class DocObjectType(AutoPascalName):
    """Object type filter for documentation content listing.

    Used with `Documentation.list_objects` to narrow results by object
    type. Values correspond to the REST API's `objectType` parameter for
    the documentation objects endpoint.
    """

    # Application Objects
    DASHBOARD = auto()
    DOCUMENT = auto()
    HTML_DOCUMENT = auto()
    HYPERCARD = auto()
    DATA_IMPORT_CUBE = 'MTDICube'
    DATA_MART_REPORT = auto()
    INTELLIGENT_CUBE = auto()
    REPORT = auto()
    CUSTOM_GROUP = auto()
    FILTER = auto()
    AUTO_STYLE = auto()
    BASE_FORMULA = auto()
    CONSOLIDATION = auto()
    DERIVED_ELEMENT = auto()
    DRILL_MAP = auto()
    METRIC = auto()
    SUBTOTAL = auto()
    PREDICTIVE_METRIC = auto()
    PROMPT = auto()
    SEARCH = auto()
    SHORTCUT = auto()
    TEMPLATE = auto()

    # Schema Objects
    ATTRIBUTE = auto()
    FACT = auto()
    FUNCTION = auto()
    HIERARCHY = auto()
    LOGICAL_TABLE = auto()
    METADATA_PARTITION_MAPPING = auto()
    WAREHOUSE_PARTITION_MAPPING = auto()
    SECURITY_FILTER = auto()
    TRANSFORMATION = auto()

    # Folders
    FOLDER = auto()

    # MDX Cube Objects
    MDX_ATTRIBUTE = auto()
    MDX_SYSTEM_HIERARCHY = auto()
    MDX_METRIC = auto()
    MDX_LOGICAL_TABLE = auto()
    MDX_PROMPT = auto()


# endregion

# region Data classes


@dataclass
class DocumentationStatus(Dictable):
    """Draft representation of documentation execution status."""

    _FROM_DICT_MAP = {
        'status': EnumDocumentationStatus,
    }

    id: str | None = None
    progress: int | None = None
    status: EnumDocumentationStatus | None = None
    message: str | None = None
    i_server_error_code: int | None = None


@dataclass
class ResourceFolderReference(Dictable):
    """Draft representation of a resource folder reference."""

    id: str | None = None
    name: str | None = None


@dataclass
class ResourceFolderChildObject(Dictable):
    """Draft representation of a non-folder child object in a resource."""

    id: str | None = None
    name: str | None = None
    type: DocObjectType | None = None
    file_index: str | None = None


@dataclass
class DocumentationObject(Dictable):
    """Draft representation of a documentation object item."""

    _FROM_DICT_MAP = {
        'ancestor_folders': [ResourceFolderReference],
        'creation_time': DatetimeFormats.FULLDATETIME,
        'modification_time': DatetimeFormats.FULLDATETIME,
        'type': DocObjectType,
    }

    id: str | None = None
    name: str | None = None
    owner_id: str | None = None
    owner_name: str | None = None
    location: str | None = None
    ancestor_folders: list[ResourceFolderReference] | None = None
    creation_time: datetime | None = None
    modification_time: datetime | None = None
    description: str | None = None
    type: DocObjectType | None = None


@dataclass
class ResourceFolderChildren(Dictable):
    """Draft representation of children in a resource folder."""

    _FROM_DICT_MAP = {
        'child_folders': [ResourceFolderReference],
        'non_folder_child_objects': [ResourceFolderChildObject],
    }

    child_folders: list[ResourceFolderReference] = field(default_factory=list)
    non_folder_child_objects: list[ResourceFolderChildObject] = field(
        default_factory=list
    )


@dataclass
class ResourceFolderPath(Dictable):
    """Draft representation of folder path metadata in a resource."""

    _FROM_DICT_MAP = {
        'ancestor_folders': [ResourceFolderReference],
        'children': ResourceFolderChildren,
    }

    ancestor_folders: list[ResourceFolderReference] | None = None
    children: ResourceFolderChildren | None = None
    id: str | None = None
    name: str | None = None


@dataclass
class ResourceObject(Dictable):
    """Represents an object entry within a documentation resource folder."""

    _FROM_DICT_MAP = {
        'type': DocObjectType,
    }
    id: str | None = None
    name: str | None = None
    type: DocObjectType | None = None


@dataclass
class ResourceFolder(Dictable):
    """
    Representation of a documentation resource.

    Data tree structure:

    Root: ResourceFolder
      - paths: ResourceFolderPath
          - ancestor_folders: list[ResourceFolderReference]
              Each ancestor folder:
                - id: str
                - name: str
          - children: ResourceFolderChildren
              - child_folders: list[ResourceFolderReference]
                  Each child folder reference:
                    - id: str
                    - name: str
              - non_folder_child_objects: list[ResourceFolderChildObject]
                  Each non-folder child object:
                    - id: str
                    - name: str
                    - type: DocObjectType | None
                    - file_index: str | None
          - id: str
          - name: str

      - objects: list[ResourceObject]
          Each resource object:
            - id: str
            - name: str
            - type: DocObjectType | None
    """

    _FROM_DICT_MAP = {
        'paths': ResourceFolderPath,
        'objects': [ResourceObject],
    }

    paths: ResourceFolderPath | None = None
    objects: list[ResourceObject] | None = None


# endregion

# region Enum and Format definitions


class DocFolderType(AutoPascalName):
    """Folder content scope options for a documentation definition.

    Specifies whether the documentation definition should capture all
    object types or only folder objects.
    """

    ALL = auto()
    FOLDER = auto()


class DocApplicationType(AutoPascalName):
    """Application object types included in a documentation definition.

    Specifies which application-layer Strategy object types (reports,
    dashboards, metrics, etc.) are captured by the documentation
    definition.
    """

    ALL = auto()
    AUTO_STYLE = auto()
    BASE_FORMULA = auto()
    CONSOLIDATION = auto()
    CUSTOM_GROUP = auto()
    DATA_MART_REPORT = auto()
    DASHBOARD = auto()
    DERIVED_ELEMENT = auto()
    DOCUMENT = auto()
    DRILL_MAP = auto()
    FILTER = auto()
    HYPERCARD = auto()
    HTML_DOCUMENT = auto()
    INTELLIGENT_CUBE = auto()
    METRIC = auto()
    DATA_IMPORT_CUBE = 'MTDICube'  # kept for simplicity with WS
    PREDICTIVE_METRIC = auto()
    PROMPT = auto()
    REPORT = auto()
    SEARCH = auto()
    SHORTCUT = auto()
    SUBTOTAL = auto()
    TEMPLATE = auto()


class DocSchemaType(AutoPascalName):
    """Schema object types included in a documentation definition.

    Specifies which schema-layer Strategy object types (attributes,
    facts, hierarchies, etc.) are captured by the documentation
    definition.
    """

    ALL = auto()
    ATTRIBUTE = auto()
    FACT = auto()
    FUNCTION = auto()
    HIERARCHY = auto()
    LOGICAL_TABLE = auto()
    SECURITY_FILTER = auto()
    TRANSFORMATION = auto()
    WAREHOUSE_PARTITION_MAPPING = auto()
    METADATA_PARTITION_MAPPING = auto()


class DocMdxCubeType(AutoPascalName):
    """MDX cube object types included in a documentation definition.

    Specifies which MDX cube-related object types are captured by the
    documentation definition.
    """

    ALL = auto()
    MDX_ATTRIBUTE = auto()
    MDX_SYSTEM_HIERARCHY = auto()
    MDX_METRIC = auto()
    MDX_LOGICAL_TABLE = auto()
    MDX_PROMPT = auto()


class DocBasicProperty(AutoPascalName):
    """Basic object properties captured in a documentation definition.

    Specifies which metadata properties (such as location, owner, and
    timestamps) are included in the documentation output.
    """

    ALL = auto()
    LOCATION = auto()
    DESCRIPTION = auto()
    LONG_DESCRIPTION = auto()
    CREATION_TIME = auto()
    MODIFICATION_TIME = auto()
    OWNER = auto()
    HIDDEN = auto()
    ID = auto()
    VERSION_ID = auto()
    ACCESS_CONTROL = auto()
    INTERNATIONAL_PROPERTIES = 'I18nProperties'


class DocExportFormat(AutoName):
    """Export file formats for a documentation job.

    Used with `Documentation.export_to_file` to specify the output
    format when downloading documentation content.
    """

    CSV = auto()
    JSON = auto()
    EXCEL = auto()


class DocDefinitionSortBy(Enum):
    """Sorting options for listing documentation definitions."""

    ID_ASC = '+id'
    ID_DESC = '-id'
    NAME_ASC = '+name'
    NAME_DESC = '-name'
    TYPE_ASC = '+type'
    TYPE_DESC = '-type'
    PROJECT_NAME_ASC = '+projectName'
    PROJECT_NAME_DESC = '-projectName'
    OWNER_NAME_ASC = '+ownerName'
    OWNER_NAME_DESC = '-ownerName'
    DATE_CREATED_ASC = '+dateCreated'
    DATE_CREATED_DESC = '-dateCreated'
    LAST_RUN_ASC = '+lastRun'
    LAST_RUN_DESC = '-lastRun'
    SIZE_ASC = '+size'
    SIZE_DESC = '-size'


# endregion

# region Documentation class


class Documentation(Entity, DeleteMixin):
    """Represents a Strategy documentation job.

    A documentation job is created by executing a `DocumentationDefinition`
    and captures a snapshot of Strategy metadata at a point in time.

    Attributes:
        id (str): Unique documentation job ID.
        name (str): Name of the documentation job.
        documentation_definition_id (str): ID of the definition used to
            create this job.
        type (int): Object type identifier.
        status (EnumDocumentationStatus): Current job status value.
        message (str): Status message or error detail from the server.
        size (int): Size of the documentation output in bytes.
        project_id (str): ID of the project the job belongs to.
        owner (User): Owner of the documentation job.
        date_created (datetime): Timestamp when the job was created.
    """

    _OBJECT_TYPE = ObjectTypes.DOCUMENT_DEFINITION
    _OBJECT_SUBTYPES = ObjectSubTypes.PROJECT_DOCUMENTATION

    _REST_ATTR_MAP = {
        'document_definition_id': 'documentation_definition_id',
    }

    @staticmethod
    def _user_from_dict(*args, **kwargs):
        # avoids circular imports
        from mstrio.users_and_groups.user import User

        return User.from_dict(*args, **kwargs)

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'date_created': DatetimeFormats.FULLDATETIME,
        'status': EnumDocumentationStatus,
        "owner": _user_from_dict,
    }

    _API_GETTERS = {
        (
            'id',
            'name',
            'documentation_definition_id',
            'type',
            'status',
            'message',
            'size',
            'project_id',
            'owner',
            'date_created',
        ): doc_response_processors.get_documentation,
    }

    _API_DELETE = staticmethod(doc_response_processors.delete_documentation)

    _API_PATCH: dict = {
        ('name',): (doc_response_processors.update_documentation, 'patch'),
    }

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize Documentation object by passing `id` or `name`.

        Args:
            connection (Connection): Strategy connection object.
            id (str, optional): Documentation job ID.
            name (str, optional): Documentation job name. Used to resolve ID
                when `id` is not provided.
        """
        if id is None and name is None:
            raise ValueError("Either 'id' or 'name' must be provided.")

        if id is None:
            from mstrio.utils.resolvers import get_documentation_id_from_params_set

            id = get_documentation_id_from_params_set(
                connection,
                documentation_name=name,
            )

        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        """Initialize documentation-specific attributes from kwargs."""

        super()._init_variables(default_value=default_value, **kwargs)

        self._documentation_definition_id = kwargs.get(
            'documentation_definition_id', default_value
        )
        self._status = kwargs.get('status', default_value)
        self._message = kwargs.get('message', default_value)
        self._size = kwargs.get('size', default_value)
        self._project_id = kwargs.get('project_id', default_value)
        self._tenant_id = kwargs.get('tenant_id', default_value)

    @property
    def documentation_definition_id(self) -> str | None:
        return self._documentation_definition_id

    @property
    def status(self) -> EnumDocumentationStatus | None:
        if self._status is None or self._status is not EnumDocumentationStatus.READY:
            # Refresh status from server if not already loaded or if not ready
            self.fetch('status')
        return self._status

    @property
    def message(self) -> str | None:
        return self._message

    @property
    def size(self) -> int | None:
        return self._size

    @property
    def project_id(self) -> str | None:
        return self._project_id

    def _ensure_tenant_id_loaded(self) -> None:
        """Ensure tenant ID is loaded through documentation definition."""
        if self._tenant_id is not None or self.documentation_definition_id is None:
            return

        definition = DocumentationDefinition(
            connection=self.connection,
            id=self.documentation_definition_id,
        )
        if definition.tenant_id is None:
            definition.fetch('tenant_id')

        self._tenant_id = definition.tenant_id

    @property
    def tenant_id(self) -> str | None:
        """Tenant ID resolved from documentation definition."""
        self._ensure_tenant_id_loaded()
        return self._tenant_id

    @property
    def tenant_name(self) -> str | None:
        """Tenant name resolved from tenant ID."""
        tenant = self.tenant
        return tenant.name if tenant else None

    @property
    def tenant(self) -> 'Tenant | None':
        """Tenant object resolved from tenant ID."""
        self._ensure_tenant_id_loaded()
        if self._tenant_id is None:
            return None

        from mstrio.server.tenant import Tenant

        return Tenant(connection=self.connection, id=self._tenant_id)

    def alter(
        self,
        name: str | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter the documentation job's name.

        Args:
            name (str, optional): New name for the documentation job.
            journal_comment (str, optional): Journal comment for the
                change.
        """
        func = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**func)

    def export_to_file(
        self,
        file_path: str | Path,
        export_format: 'DocExportFormat | str | None' = DocExportFormat.JSON,
        overwrite: bool = False,
    ) -> None:
        """Export documentation to a local file.

        If `file_path` points to a directory, this method uses the exported
        filename returned by the backend and saves it in that directory.

        Args:
            file_path (str | Path): Target file or directory path.
            export_format (DocExportFormat | str, optional): Export format.
                Supported values are `csv`, `json`, and `excel`.
                Defaults to 'json'.
            overwrite (bool, optional): Whether to overwrite an existing
                target file. Defaults to False.
        """
        export_data = doc_response_processors.export_documentation(
            connection=self.connection,
            id=self.id,
            export_format=get_enum_val(export_format, DocExportFormat),
        )

        filename = export_data["filename"]
        file_binary = export_data["file_binary"]

        path = Path(file_path)

        # If file_path is a directory, use its child with the returned filename
        if path.is_dir():
            path = path / filename

        if path.exists() and not overwrite:
            raise FileExistsError(
                f"File '{path}' already exists. " "Set overwrite=True to replace it."
            )

        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_bytes(file_binary)

    def list_objects(
        self,
        doc_object_type: 'DocObjectType | str | None' = None,
        limit: int | None = None,
        to_dictionary: bool = True,
    ) -> 'list[dict] | list[DocumentationObject]':
        """List objects included in this documentation.

        Args:
            doc_object_type (DocObjectType | str, optional):
                Optional filter for documentation object type.
                Must be a value of `DocObjectType`, which is
                distinct from the standard `ObjectTypes` enum.
            limit (int, optional): Maximum number of objects to return.
                If `None`, all available objects are returned.
            to_dictionary (bool, optional): If `True`, returns a list of
                dictionaries with snake_case keys.
                If `False`, returns `DocumentationObject` objects.

        Returns:
            List of dictionaries or list of `DocumentationObject` objects,
            based on `to_dictionary`.
        """
        if not is_server_min_version(self.connection, "11.6.0300"):
            msg = "list_objects requires iServer version 11.6.0300 or later."
            raise VersionException(msg)

        if doc_object_type:
            object_type_filter: str | None = get_enum_val(
                doc_object_type, DocObjectType
            )
        else:
            object_type_filter = None

        object_dicts = doc_response_processors.get_documentation_objects(
            connection=self.connection,
            id=self.id,
            object_type=object_type_filter,
            limit=limit,
        )
        if to_dictionary:
            return object_dicts

        return DocumentationObject.bulk_from_dict(object_dicts)

    def get_resource(
        self,
        resource: 'str | Entity',
        to_dictionary: bool = True,
    ) -> 'dict | ResourceFolder':
        """Get a resource from this documentation.

        Args:
            resource (str | Entity): Resource represented as resource ID or
                an `Entity` object (e.g., `Project`, `Folder`).
            to_dictionary (bool, optional): If `True`, returns dictionary
                data.
                If `False`, returns a `ResourceFolder` object.

        Returns:
            Resource dictionary or `ResourceFolder` object, based on
            `to_dictionary`.
        """

        if not is_server_min_version(self.connection, "11.6.0300"):
            msg = "get_resource requires iServer version 11.6.0300 or later."
            raise VersionException(msg)

        resource_id = get_objects_id(resource, Entity)
        if not resource_id:
            msg = "Please provide a valid resource ID or Entity object."
            raise ValueError(msg)

        resource = doc_response_processors.get_documentation_resource(
            connection=self.connection,
            id=self.id,
            resource_id=resource_id,
        )

        if to_dictionary:
            return resource

        return ResourceFolder.from_dict(resource)

    def get_status(self, to_dictionary: bool = False) -> 'DocumentationStatus | dict':
        """Get current execution status of this documentation.

        Args:
            to_dictionary (bool, optional): If `True`, returns a dictionary.
                If `False`, returns a `DocumentationStatus` object.

        Returns:
            `DocumentationStatus` object or dictionary, based on
            `to_dictionary`.

        Raises:
            ValueError: If status is not yet available on the server.
        """
        statuses = get_documentations_statuses(
            connection=self.connection,
            documentations=self,
            to_dictionary=to_dictionary,
        )

        current_status = statuses.get(self.id)
        if current_status is None:
            msg = (
                f"Status for documentation '{self.id}' was not found yet. "
                "Please try again later."
            )
            raise ValueError(msg)

        if not to_dictionary:
            self._status = current_status.status
            self._message = current_status.message

        return current_status

    def wait_for_execution_finish(
        self,
        interval: int | None = None,
    ) -> 'DocumentationStatus':
        """Wait until documentation execution is completed.

        Args:
            interval (int, optional): Time interval in seconds between polling
                requests for status. If not provided, the value is taken from
                mstrio-py's `config`.

        Returns:
            DocumentationStatus: Final status of the documentation execution.
        """
        current_status = self.get_status()

        while current_status.status == EnumDocumentationStatus.RUNNING:
            time.sleep(interval or config.delay_between_polling)
            current_status = self.get_status()

        if config.verbose:
            if current_status.message:
                log_fn = (
                    logger.warning
                    if current_status.status
                    in (EnumDocumentationStatus.ERROR, EnumDocumentationStatus.CANCELED)
                    else logger.info
                )
                log_fn(f"[Documentation Log]: {current_status.message}")

            logger.info(f"[Documentation Completion -> {current_status.status.value}]")

        return current_status


# endregion

# region DocumentationDefinition class


class DocumentationDefinition(Entity, DeleteMixin, TenantMixin):
    """Represents a Strategy documentation definition.

    A documentation definition specifies the scope and content of a
    documentation job, including which object types, properties, and
    projects are captured.

    Attributes:
        id (str): Unique documentation definition ID.
        name (str): Name of the documentation definition.
        description (str): Description of the documentation definition.
        tenant_id (str): ID of the tenant this definition belongs to.
        hidden_objects (bool): Whether hidden objects are included.
        defaults (bool): Whether default values are included.
        definition (bool): Whether definition data is included.
        advanced_definition (bool): Whether advanced definition data
            is included.
        dependents (bool): Whether dependents are included.
        components (bool): Whether components are included.
        folder (list[DocFolderType]): Folder scope filter values.
        application (list[DocApplicationType]): Application object type
            filter values.
        schema (list[DocSchemaType]): Schema object type filter values.
        mdx_cubes (list[DocMdxCubeType]): MDX cube object type filter
            values.
        basic_properties (list[DocBasicProperty]): Basic property filter
            values.
        project_id (str): ID of the project this definition belongs to.
    """

    _TENANT_ASSIGNMENT_READ_ONLY = True

    _API_GETTERS = {
        (
            'id',
            'name',
            'type',
            'description',
            'date_created',
            'instance',
            'hidden_objects',
            'defaults',
            'definition',
            'advanced_definition',
            'dependents',
            'components',
            'folder',
            'application',
            'schema',
            'mdx_cubes',
            'basic_properties',
            'project_id',
            'tenant_id',
            'owner',
        ): doc_def_response_processors.get_documentation_definition,
    }

    @staticmethod
    def _user_from_dict(*args, **kwargs):
        # avoids circular imports
        from mstrio.users_and_groups.user import User

        return User.from_dict(*args, **kwargs)

    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'date_created': DatetimeFormats.FULLDATETIME,
        'folder': [DocFolderType],
        'application': [DocApplicationType],
        'schema': [DocSchemaType],
        'mdx_cubes': [DocMdxCubeType],
        'basic_properties': [DocBasicProperty],
        'owner': _user_from_dict,
    }

    _API_PATCH: dict = {
        (
            'name',
            'description',
        ): (doc_def_response_processors.update_documentation_definition, 'patch'),
    }

    _API_DELETE = staticmethod(
        doc_def_response_processors.delete_documentation_definition
    )

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize DocumentationDefinition object by passing `id` or `name`.

        Args:
            connection (Connection): Strategy connection object.
            id (str, optional): Documentation definition ID.
            name (str, optional): Documentation definition name. Used to
                resolve ID when `id` is not provided.
        """
        if id is None and name is None:
            raise ValueError("Either 'id' or 'name' must be provided.")

        if id is None:
            from mstrio.utils.resolvers import (
                get_documentation_definition_id_from_params_set,
            )

            id = get_documentation_definition_id_from_params_set(
                connection,
                definition_name=name,
            )

        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        """Initialize documentation definition attributes from kwargs.

        Expects a flat kwargs dict (configuration and objectCategories
        are pre-flattened by the response processor).
        """
        super()._init_variables(default_value=default_value, **kwargs)
        self._hidden_objects = kwargs.get('hidden_objects', default_value)
        self._defaults = kwargs.get('defaults', default_value)
        self._definition = kwargs.get('definition', default_value)
        self._advanced_definition = kwargs.get('advanced_definition', default_value)
        self._dependents = kwargs.get('dependents', default_value)
        self._components = kwargs.get('components', default_value)
        self._folder = kwargs.get('folder', default_value)
        self._application = kwargs.get('application', default_value)
        self._schema = kwargs.get('schema', default_value)
        self._mdx_cubes = kwargs.get('mdx_cubes', default_value)
        self._basic_properties = kwargs.get('basic_properties', default_value)
        self._project_id = kwargs.get('project_id', default_value)
        self._instance = kwargs.get('instance', default_value)

    @property
    def hidden_objects(self) -> bool | None:
        return self._hidden_objects

    @property
    def defaults(self) -> bool | None:
        return self._defaults

    @property
    def definition(self) -> bool | None:
        return self._definition

    @property
    def advanced_definition(self) -> bool | None:
        return self._advanced_definition

    @property
    def dependents(self) -> bool | None:
        return self._dependents

    @property
    def components(self) -> bool | None:
        return self._components

    @property
    def folder(self) -> list[DocFolderType] | None:
        return self._folder

    @property
    def application(self) -> list[DocApplicationType] | None:
        return self._application

    @property
    def schema(self) -> list[DocSchemaType] | None:
        return self._schema

    @property
    def mdx_cubes(self) -> list[DocMdxCubeType] | None:
        return self._mdx_cubes

    @property
    def basic_properties(self) -> list[DocBasicProperty] | None:
        return self._basic_properties

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def instance(self) -> list[str] | None:
        return self._instance

    @property
    def owner(self) -> 'User | None':
        return self._owner

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter documentation definition properties."""
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        self._alter_properties(**properties)

    @staticmethod
    def _normalize_mdx_cubes_for_api(mdx_cubes: list[str] | None) -> list[str] | None:
        """Normalize MDX cube filters for API compatibility.

        TODO: Remove this normalization when the API starts accepting and
        returning `All` for MDX cubes
        """
        if mdx_cubes is None:
            return None

        all_value = DocMdxCubeType.ALL.value
        if all_value not in mdx_cubes:
            return mdx_cubes

        return [
            member.value
            for member in DocMdxCubeType
            if member is not DocMdxCubeType.ALL
        ]

    def execute(self) -> 'Documentation':
        """Execute this documentation definition and return a job.

        This method only triggers the documentation job execution on the
        server. The returned Documentation object is initially created but
        not yet ready for use. To check if the documentation is ready,
        monitor the status until it changes to 'Ready'.

        Warning:
            Documentation execution can be a time-consuming operation and may
            lead to timeout issues, especially for large definitions or
            server-side constraints. If your connection times out before
            execution completes, you can recover the job using the definition
            ID or name with `list_documentations()`.

        Note:
            For long-running executions, use `wait_for_execution_finish()`
            on the returned Documentation object to monitor progress and wait
            until the status becomes 'Ready'.

        Returns:
            Documentation: Newly created documentation job (status may be
                'Running' initially).
        """
        documentation_dict = doc_response_processors.create_documentation(
            connection=self.connection,
            documentation_definition_id=self.id,
        )

        documentation = Documentation.from_dict(
            source=documentation_dict,
            connection=self.connection,
        )

        if config.verbose:
            logger.info(
                "Successfully executed DocumentationDefinition "
                f"'{self.name}' and created Documentation with ID: "
                f"'{documentation.id}'"
            )

        return documentation

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        name: str,
        hidden_objects: bool = True,
        defaults: bool = True,
        definition: bool = True,
        advanced_definition: bool = True,
        dependents: bool = True,
        components: bool = True,
        folder: 'list[DocFolderType | str] | DocFolderType | str | None' = 'All',
        application: (
            'list[DocApplicationType | str] | DocApplicationType | str | None'
        ) = 'All',
        schema: 'list[DocSchemaType | str] | DocSchemaType | str | None' = 'All',
        mdx_cubes: 'list[DocMdxCubeType | str] | DocMdxCubeType | str | None' = 'All',
        basic_properties: (
            'list[DocBasicProperty | str] | DocBasicProperty | str | None'
        ) = 'All',
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> 'DocumentationDefinition':
        """Create a documentation definition.

        Args:
            connection (Connection): Strategy connection object.
            name (str): Name of the documentation definition.
            hidden_objects (bool, optional): Whether to include hidden
                objects. Defaults to `True`.
            defaults (bool, optional): Whether to include default values.
                Defaults to `True`.
            definition (bool, optional): Whether to include definition
                data. Defaults to `True`.
            advanced_definition (bool, optional): Whether to include
                advanced definition data. Defaults to `True`.
            dependents (bool, optional): Whether to include dependents.
                Defaults to `True`.
            components (bool, optional): Whether to include components.
                Defaults to `True`.
            folder (list[DocFolderType | str] | DocFolderType | str,
                optional): Folder scope filter. Defaults to `'All'`.
            application (list[DocApplicationType | str] |
                DocApplicationType | str, optional): Application object
                type filter. Defaults to `'All'`.
            schema (list[DocSchemaType | str] | DocSchemaType | str,
                optional): Schema object type filter. Defaults to `'All'`.
            mdx_cubes (list[DocMdxCubeType | str] | DocMdxCubeType | str,
                optional): MDX cube object type filter. Defaults to
                `'All'`.
            basic_properties (list[DocBasicProperty | str] |
                DocBasicProperty | str, optional): Basic property filter.
                Defaults to `'All'`. `'ID'` field will always be included.
            project (Project | str, optional): Project object, ID, or
                name.
            project_id (str, optional): Project ID.
            project_name (str, optional): Project name.

        Note:
            Passing `None` to any of `folder`, `application`, `schema`,
            `mdx_cubes`, or `basic_properties` means no objects of that
            category will be included in the documentation output.

        Returns:
            DocumentationDefinition: Newly created documentation
                definition object.

        Raises:
            ValueError: If none of `project`, `project_id`, or
                `project_name` is provided.
        """
        if not is_server_min_version(connection, "11.5.1200"):
            msg = "documentation feature requires iServer version 11.5.1200 or later."
            raise VersionException(msg)

        if all(value is None for value in (project, project_id, project_name)):
            msg = "Please provide one of: `project`, `project_id`, or `project_name`."
            raise ValueError(msg)

        folder = normalize_enum_list(folder, DocFolderType)
        application = normalize_enum_list(application, DocApplicationType)
        schema = normalize_enum_list(schema, DocSchemaType)
        mdx_cubes = normalize_enum_list(mdx_cubes, DocMdxCubeType)
        mdx_cubes = cls._normalize_mdx_cubes_for_api(mdx_cubes)
        basic_properties = normalize_enum_list(basic_properties, DocBasicProperty, True)
        if (
            DocBasicProperty.ID.value not in basic_properties
            and DocBasicProperty.ALL.value not in basic_properties
        ):
            # ID needs to be always included
            basic_properties.append(DocBasicProperty.ID.value)
            logger.info(
                "The 'ID' basic property was automatically added to the "
                "documentation definition as it is always required."
            )

        resolved_project_id = get_project_id_from_params_set(
            connection,
            project=project,
            project_id=project_id,
            project_name=project_name,
            no_fallback_from_connection=True,
        )

        body = {
            'name': name,
            'type': 'PROJECT_DOCUMENTATION',
            'hiddenObjects': hidden_objects,
            'defaults': defaults,
            'projectId': resolved_project_id,
            'definition': definition,
            'advancedDefinition': advanced_definition,
            'dependents': dependents,
            'components': components,
            'folder': folder,
            'application': application,
            'schema': schema,
            'mdxCubes': mdx_cubes,
            'basicProperties': basic_properties,
        }
        body = delete_none_values(body, recursion=True)

        definition_id = doc_def_response_processors.create_documentation_definition(
            connection=connection,
            body=body,
        )

        definition = cls(connection=connection, id=definition_id)

        if config.verbose:
            logger.info(
                f"Successfully created DocumentationDefinition named: '{name}' "
                f"with ID: '{definition.id}'"
            )

        return definition


# endregion
