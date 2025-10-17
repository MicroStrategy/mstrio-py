import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from mstrio.connection import Connection
from mstrio.server import Environment
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, exception_handler
from mstrio.utils.time_helper import DatetimeFormats

logger = logging.getLogger(__name__)


class RequestStatus(AutoName):
    """Status of a request such as import or undo.
    Allowed values are:
    - unknown
    - pending
    - requested
    - rejected
    - approved
    """

    UNKNOWN = auto()
    PENDING = auto()
    REQUESTED = auto()
    REJECTED = auto()
    APPROVED = auto()


class Action(AutoName):
    """The default action used for objects which don't have actions
    explicitly, for example the dependents objects.
    USE_EXISTING: No change is made to the destination object.
    The source object is not copied.
    REPLACE: The destination object is replaced with the source object.
    Note the following:
        • If the conflict type is Exists identically except for path, or
        Exists identically except for Distribution Services objects,
        the  destination object is updated to reflect the path or
        Distribution Services addresses and contacts of the source object.
        • Replace moves the object into the same parent folder as source
        object. If the parent path is the same between source and
        destination but the grandparent path is different, Replace may
        appear to do nothing because Replace puts the object into the same
        parent path.
        • Non-empty folders in the destination location will never have
        the same version ID and modification time as the source, because
        the folder is copied first and the objects are added to it, thus
        changing version ID and modification times during the copy process.
    KEEP_BOTH: No change is made to the destination object. The source
    object is duplicated if destination object doesn't exist. But if the
    destination object exists with the same id and same version, this source
    object is ignored.If the destination object exists with the same id
    and different version, this source object is saved as new object.
    USE_NEWER: If the source object's modification time is more recent than
    the destination object's, the Replace action is used.Otherwise, the Use
    existing action is used.
    USE_OLDER: If the source object's modification time is more recent than
    the destination object's, the Use existing action is used. Otherwise,
    the Replace action is used.
    FORCE_REPLACE: Replace the object in the destination project with the
    version of the object in the update package, even if both versions of
    the object have the same Version ID.
    DELETE: Delete the object from the destination project. The version
    of the object in the update package is not imported into the destination
    project.Warning: If the object in the destination has any used-by
    dependencies when you import the update package, the import will fail.
    """

    USE_EXISTING = auto()
    REPLACE = auto()
    KEEP_BOTH = auto()
    USE_NEWER = auto()
    USE_OLDER = auto()
    FORCE_REPLACE = auto()
    DELETE = auto()


class TranslationAction(AutoName):
    """Translation action for Project Merge Package Settings.
    Allowed values are:
    - not_merged
    - use_existing
    - replace
    - force_replace
    """

    NOT_MERGED = auto()
    USE_EXISTING = auto()
    REPLACE = auto()
    FORCE_REPLACE = auto()


@dataclass
class PackageStorage(Dictable):
    size: int | None = None
    path: str | None = None


@dataclass
class PackageWarning(Dictable):
    message: str | None = None
    iserver_error_code: int | None = None
    banned_object_count: int | None = None


class PackageSettings(Dictable):
    """Object representation of package settings details.

    Attributes:
        default_action(Action): default action for Package
        update_schema(Optional[UpdateSchema]): update_schema for Package
        acl_on_replacing_objects(Optional[AclOnReplacingObjects]):
            ACL setting on replacing objects
        acl_on_new_objects(Optional[AclOnNewObjects]):
            ACL setting on new objects
    """

    class UpdateSchema(AutoName):
        """They allow you to configure the package to automatically perform
        certain schema update functions. These options can be useful if you make
        any changes to schema objects. Use the recalculate table keys and fact
        entry levels if you changed the key structure of a table or if you
        changed the level at which a fact is stored.Use the recalculate table
        logical sizes to override any modifications that you have made to
        logical table sizes. (Logical table sizes affect how the Strategy One
        SQL Engine determines which tables to use in a query.)
        """

        RECAL_TABLE_LOGICAL_SIZE = auto()
        RECAL_TABLE_KEYS_FACT_ENTRY_LEVEL = auto()
        UPDATE_SCHEMA_LOGICAL_INFO = auto()

    class AclOnReplacingObjects(AutoName):
        """If you resolve a conflict with the "Replace" action, and the access
        control lists (ACL) of the objects are different between the two
        projects, you can choose whether to keep the existing ACL in the
        destination project or replace it with the ACL from the source project.
        Note: This is not supported for project security packages.
        """

        USE_EXISTING = auto()
        REPLACE = auto()
        KEEP_BOTH = auto()

    class AclOnNewObjects(AutoName):
        """If you add a new object to the destination project with the
        "Create New" or "Keep Both action", you can choose to have the object
        inherit its ACL from the destination folder instead of keeping its own
        ACL. This is helpful when copying an object into a user's profile
        folder, so that the user can have full control over the object.
        """

        KEEP_ACL_AS_SOURCE_OBJECT = auto()
        INHERIT_ACL_AS_DEST_FOLDER = auto()

    _FROM_DICT_MAP = {
        'default_action': Action,
        'update_schema': [UpdateSchema],
        'acl_on_replacing_objects': AclOnReplacingObjects,
        'acl_on_new_objects': [AclOnNewObjects],
    }

    def __init__(
        self,
        default_action: Action = Action.USE_EXISTING,
        update_schema: UpdateSchema | None = None,
        acl_on_replacing_objects: AclOnReplacingObjects = (
            AclOnReplacingObjects.USE_EXISTING
        ),
        acl_on_new_objects: AclOnNewObjects = AclOnNewObjects.KEEP_ACL_AS_SOURCE_OBJECT,
    ):
        self.default_action = default_action
        self.update_schema = (
            update_schema
            if isinstance(update_schema, list) or not update_schema
            else [update_schema]
        )
        self.acl_on_replacing_objects = acl_on_replacing_objects
        self.acl_on_new_objects = (
            [acl_on_new_objects]
            if isinstance(acl_on_new_objects, PackageSettings.AclOnNewObjects)
            else acl_on_new_objects
        )


class PackageContentInfo(Dictable):
    """Object representation of package content information

    Attributes:
        id(str): object ID
        action(Action): The action to resolve the conflict.
        name(Optional[str]): object name
        version(Optional[str]): object version
        type(Optional[ObjectTypes]): object type
        owner(Optional[Owner]): owner of object
        date_created(Optional[str]): object creation date
        date_modified(Optional[str]): object modification date
        include_dependents(Optional[bool]): whether include the dependents
            for this object or not
        explicit_included(Optional[bool]): whether explicitly included or not
        level(Optional[Level]): level of object
    """

    class Level(AutoName):
        PROJECT_OBJECT = auto()
        CONFIGURATION_OBJECT = auto()
        UNKNOWN = auto()

    class Owner(User):
        """
        This class overrides `from_dict()` and `__init__()` methods as
        PackageContentInfo inherits from `Dictable` and not `EntityBase`.
        Therefore, despite `Owner` being a `User`, `connection` param here is
        optional. If `connection` is specified, `User` constructor will be used
        """

        @classmethod
        def from_dict(
            cls, source: dict[str, any], connection: Optional["Connection"] = None
        ):
            return super().from_dict(source, connection)

        def __init__(self, id: str, connection: Optional["Connection"] = None):
            if connection:
                super().__init__(id, connection)
            else:
                self._id = id

        def _init_variables(self, **kwargs) -> None:
            self._connection = kwargs.get("connection")
            self._id = kwargs.get("id")

    _FROM_DICT_MAP = {
        'type': ObjectTypes,
        'action': Action,
        'level': Level,
        'owner': Owner,
    }

    def __init__(
        self,
        id: str,
        action: Action | str = Action.USE_EXISTING,
        name: str | None = None,
        version: str | None = None,
        type: ObjectTypes | None = None,
        owner: Owner | None = None,
        date_created: str | None = None,
        date_modified: str | None = None,
        include_dependents: bool | None = None,
        explicit_included: bool | None = None,
        level: Level | str | None = None,
    ):
        self.id = id
        self.name = name
        self.version = version
        self.type = type
        self.owner = owner
        self.date_created = date_created
        self.date_modified = date_modified
        self.include_dependents = include_dependents
        self.explicit_included = explicit_included
        try:
            self.level = (
                PackageContentInfo.Level(level) if isinstance(level, str) else level
            )
            self.action = Action(action) if isinstance(action, str) else action
        except ValueError:
            exception_handler(msg="Wrong enum value", exception_type=ValueError)


@dataclass
class ObjectMigrationPackageTocView(Dictable):
    settings: PackageSettings
    content: list[PackageContentInfo] | None = None


@dataclass
class PackageObjectAction(Dictable):
    id: str
    action: Action
    object_type: ObjectTypes | None = None


@dataclass
class PackageObjectTypeAction(Dictable):
    type: ObjectTypes
    action: Action
    sub_type: ObjectSubTypes | None = None


@dataclass
class ProjectMergePackageSettings(Dictable):
    acl_on_replacing_objects: PackageSettings.AclOnReplacingObjects
    acl_on_new_objects: PackageSettings.AclOnNewObjects
    default_action: Action
    validate_dependencies: bool
    translation_action: TranslationAction
    folder_actions: dict | None = None
    object_actions: dict | None = None
    object_type_actions: dict | None = None
    update_schema: PackageSettings.UpdateSchema | None = None


@dataclass
class ProjectMergePackageTocView(Dictable):
    settings: ProjectMergePackageSettings


class PackageConfig(Dictable):
    """Package Update Data Transfer Object

    Attributes:
        settings(PackageSettings): settings details of package
        content(PackageContentInfo, List[PackageContentInfo]): content details
            of package
    """

    _FROM_DICT_MAP = {
        'settings': PackageSettings,
        'content': [PackageContentInfo],
    }

    def __init__(
        self,
        settings: PackageSettings,
        content: list[PackageContentInfo] | PackageContentInfo,
    ):
        self.settings = settings
        self.content = [content] if not isinstance(content, list) else content


class MigrationPurpose(AutoName):
    """Migration purpose.
    Possible values are:
    - object_migration
    - project_merge
    - migration_from_shared_file_store
    """

    OBJECT_MIGRATION = auto()
    PROJECT_MERGE = auto()
    FROM_FILE = 'migration_from_shared_file_store'


class PackageType(Enum):
    """Migration type."""

    OBJECT = 'project'
    ADMINISTRATION = 'configuration'
    PROJECT = 'project_security'


class ImportStatus(AutoName):
    """Status of Migration Import.
    Allowed values are:
    - pending
    - importing
    - imported
    - import_failed
    - undoing
    - undo_success
    - undo_failed
    """

    PENDING = auto()
    IMPORTING = auto()
    IMPORTED = auto()
    IMPORT_FAILED = auto()
    UNDOING = auto()
    UNDO_SUCCESS = auto()
    UNDO_FAILED = auto()


class PackageStatus(AutoName):
    """Status of Migration Package.
    Allowed values are:
    - locked
    - created
    - create_failed
    - creating
    - empty
    - unknown
    """

    LOCKED = auto()
    CREATED = auto()
    CREATE_FAILED = auto()
    CREATING = auto()
    EMPTY = auto()
    UNKNOWN = auto()


class MigratedObjectTypes(AutoName):
    # Per analogous list in Workstation plugin
    DASHBOARD = auto()
    DOCUMENT = auto()
    CARD = auto()
    REPORT = auto()
    DATASET = auto()
    BOT = auto()
    AGENT = "bot"
    ATTRIBUTE = auto()
    BASE_FORMULA = auto()
    CONSOLIDATION = auto()
    CUSTOM_GROUP = auto()
    CONSOLIDATION_ELEMENT = auto()
    COLUMN = auto()
    DRILL_MAP = auto()
    FACT = auto()
    FILTER = auto()
    FUNCTION = auto()
    HIERARCHY = auto()
    METRIC = auto()
    PROMPT = auto()
    SMART_ATTRIBUTE = auto()
    SUBTOTAL = auto()
    AUTO_STYLE = auto()
    EXTERNAL_SHORTCUT = auto()
    SEARCH = auto()
    SECURITY_FILTER = auto()
    SHORTCUT = auto() or 67
    TABLE = auto()
    TEMPLATE = auto()
    TRANSFORMATION = auto()
    SCRIPT = auto()
    USER = auto()
    USER_GROUP = auto()
    DATA_SOURCE = auto()
    SECURITY_ROLE = auto()
    CUSTOM_APPLICATION = auto()
    PALETTE = auto()
    TIMEZONE = auto()
    CALENDAR = auto()
    CONTENT_BUNDLE = auto()
    DEVICE = auto()
    LOCALE = auto()
    SCHEDULE_EVENT = auto()
    SCHEDULE_TRIGGER = auto()
    TRANSMITTER = auto()
    SCRIPT_RUNTIME_ENV = auto()


class PackageCertificationStatus(AutoName):
    UNCERTIFIED = auto()
    REQUESTED = auto()
    CERTIFIED = auto()
    REJECTED = auto()


@dataclass
class PackageCertificationInfo(Dictable):
    _FROM_DICT_MAP = {
        'status': PackageCertificationStatus,
        'operator': User.from_dict,
        'last_updated_date': DatetimeFormats.YMDHMS,
    }
    status: PackageCertificationStatus
    operator: User
    last_updated_date: datetime


class ValidationStatus(AutoName):
    VALIDATING = auto()
    VALIDATED = auto()
    VALIDATION_FAILED = auto()


@dataclass
class Validation(Dictable):
    _FROM_DICT_MAP = {
        'status': ValidationStatus,
        'creation_date': DatetimeFormats.YMDHMS,
        'last_update_date': DatetimeFormats.YMDHMS,
    }
    status: ValidationStatus | None = None
    progress: float | None = None
    message: str | None = None
    creation_date: datetime | None = None
    last_update_date: datetime | None = None


@dataclass
class ImportInfo(Dictable):
    """Python representation of a ImportInfo Migration field.
    Attributes:
        id (str): ID of the import
        creator (dict, optional): Creator data
            id
            name
            full_name (str, optional)
        creation_date (str, optional): Date of creation, in the format
            "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
        last_updated_date (str, optional): Date of last update, in the format
            "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
        environment (dict): Environment data
            id
            name
        status (ImportStatus, optional): Status of the import.
        import_request_status (RequestStatus, optional): Status of the import
            request.
        undo_request_status (RequestStatus, optional): Status of the undo
            request.
        progress (float, optional): Progress of the import.
        message (str, optional): Record information such as the reason of
            import failure
        undo_storage (dict, optional): Storage data for the undo package
            size
            path
        project (dict, optional): Project data
            id
            name
        deleted (bool, optional): Whether the import is deleted
    """

    _FROM_DICT_MAP = {
        'creator': User.from_dict,
        'creation_date': DatetimeFormats.YMDHMS,
        'last_updated_date': DatetimeFormats.YMDHMS,
        'status': ImportStatus,
        'import_request_status': RequestStatus,
        'undo_request_status': RequestStatus,
        'project': Project.from_dict,
        'undo_storage': PackageStorage.from_dict,
    }
    id: str
    environment: Environment | dict
    creator: User | None = None
    creation_date: datetime | None = None
    last_updated_date: datetime | None = None
    status: ImportStatus | None = None
    import_request_status: RequestStatus | None = None
    undo_request_status: RequestStatus | None = None
    progress: float | None = None
    message: str | None = None
    undo_storage: PackageStorage | None = None
    project: Project | None = None
    deleted: bool | None = None


@dataclass
class PackageInfo(Dictable):
    """Python representation of a PackageInfo Migration field.

    Attributes:
        attribute_id: ID of the mapped attribute
        attribute_form_id: ID of the mapped attribute's form
    """

    _FROM_DICT_MAP = {
        'creator': User.from_dict,
        'creation_date': DatetimeFormats.YMDHMS,
        'last_updated_date': DatetimeFormats.YMDHMS,
        'type': PackageType,
        'storage': PackageStorage,
        'project': Project.from_dict,
        'status': PackageStatus,
        'warnings': PackageWarning.bulk_from_dict,
        'purpose': MigrationPurpose,
        'certification': PackageCertificationInfo,
    }
    name: str
    creator: User
    creation_date: datetime
    last_updated_date: datetime
    type: PackageType
    environment: str | None = None
    id: str | None = None
    replicated: bool | None = None
    storage: PackageStorage | None = None
    project: Project | None = None
    status: PackageStatus | None = None
    message: str | None = None
    warnings: list[PackageWarning] | None = None
    progress: float | None = None
    deleted: bool | None = None
    existing: bool | None = None
    toc_view: ProjectMergePackageTocView | ObjectMigrationPackageTocView | None = None
    purpose: MigrationPurpose | None = None
    tree_view: dict | None = None
    certification: PackageCertificationInfo | None = None


OBJECT_MIGRATION_TYPES_MIN_VERSION = {
    MigratedObjectTypes.BOT: '11.3.0760',
    MigratedObjectTypes.AGENT: '11.5.1000',
    MigratedObjectTypes.SMART_ATTRIBUTE: '11.3.0760',
    MigratedObjectTypes.SCRIPT: '11.3.0760',
    MigratedObjectTypes.CALENDAR: '11.3.0760',
    MigratedObjectTypes.CONTENT_BUNDLE: '11.3.0760',
    MigratedObjectTypes.DEVICE: '11.3.0760',
    MigratedObjectTypes.LOCALE: '11.3.0760',
    MigratedObjectTypes.SCHEDULE_EVENT: '11.3.0760',
    MigratedObjectTypes.SCHEDULE_TRIGGER: '11.3.0760',
    MigratedObjectTypes.TRANSMITTER: '11.3.0760',
    MigratedObjectTypes.SCRIPT_RUNTIME_ENV: '11.3.0760',
}
CATALOG_ITEMS = {
    MigratedObjectTypes.DASHBOARD: (ObjectTypes.DOCUMENT_DEFINITION, None),
    MigratedObjectTypes.DOCUMENT: (ObjectTypes.DOCUMENT_DEFINITION, None),
    MigratedObjectTypes.CARD: (
        ObjectTypes.REPORT_DEFINITION,
        ObjectSubTypes.REPORT_HYPER_CARD,
    ),  # Card
    MigratedObjectTypes.REPORT: (
        ObjectTypes.REPORT_DEFINITION,
        [
            ObjectSubTypes.REPORT_GRID,
            ObjectSubTypes.REPORT_GRAPH,
            ObjectSubTypes.REPORT_ENGINE,
            ObjectSubTypes.REPORT_TEXT,
            ObjectSubTypes.REPORT_BASE,
            ObjectSubTypes.REPORT_GRID_AND_GRAPH,
            ObjectSubTypes.REPORT_NON_INTERACTIVE,
            ObjectSubTypes.INCREMENTAL_REFRESH_REPORT,
            ObjectSubTypes.REPORT_TRANSACTION,
            ObjectSubTypes.SUPER_CUBE_IRR,
            ObjectSubTypes.REPORT_DATAMART,
        ],
    ),  # Report
    MigratedObjectTypes.DATASET: (
        ObjectTypes.REPORT_DEFINITION,
        [
            ObjectSubTypes.OLAP_CUBE,
            ObjectSubTypes.SUPER_CUBE,
        ],
    ),  # Dataset
    MigratedObjectTypes.BOT: (
        ObjectTypes.DOCUMENT_DEFINITION,
        ObjectSubTypes.DOCUMENT_BOT,
    ),  # Bot
    MigratedObjectTypes.AGENT: (
        ObjectTypes.DOCUMENT_DEFINITION,
        [
            ObjectSubTypes.DOCUMENT_BOT_2_0,
            ObjectSubTypes.DOCUMENT_BOT_UNIVERSAL,
        ],
    ),  # Agent
    MigratedObjectTypes.ATTRIBUTE: (
        ObjectTypes.ATTRIBUTE,
        [
            ObjectSubTypes.ATTRIBUTE,
            ObjectSubTypes.ATTRIBUTE_ROLE,
            ObjectSubTypes.ATTRIBUTE_TRANSFORMATION,
            ObjectSubTypes.ATTRIBUTE_ABSTRACT,
            ObjectSubTypes.ATTRIBUTE_RECURSIVE,
            ObjectSubTypes.ATTRIBUTE_DERIVED,
        ],
    ),  # Attribute
    MigratedObjectTypes.BASE_FORMULA: (ObjectTypes.AGG_METRIC, None),  # Base Formula
    MigratedObjectTypes.CONSOLIDATION: (
        ObjectTypes.CONSOLIDATION,
        None,
    ),  # Consolidation
    MigratedObjectTypes.CUSTOM_GROUP: (
        ObjectTypes.FILTER,
        ObjectSubTypes.CUSTOM_GROUP,
    ),  # Custom Group
    MigratedObjectTypes.CONSOLIDATION_ELEMENT: (
        ObjectTypes.CONSOLIDATION_ELEMENT,
        None,
    ),  # Consolidation Element
    MigratedObjectTypes.COLUMN: (ObjectTypes.COLUMN, None),  # Column
    MigratedObjectTypes.DRILL_MAP: (ObjectTypes.DRILL_MAP, None),  # Drill Map
    MigratedObjectTypes.FACT: (ObjectTypes.FACT, None),  # Fact
    MigratedObjectTypes.FILTER: (ObjectTypes.FILTER, ObjectSubTypes.FILTER),  # Filter
    MigratedObjectTypes.FUNCTION: (ObjectTypes.FUNCTION, None),  # Function
    MigratedObjectTypes.HIERARCHY: (
        ObjectTypes.DIMENSION,
        [
            ObjectSubTypes.DIMENSION_USER,
            ObjectSubTypes.DIMENSION_ORDERED,
            ObjectSubTypes.DIMENSION_USER_HIERARCHY,
        ],
    ),  # Hierarchy
    MigratedObjectTypes.METRIC: (ObjectTypes.METRIC, ObjectSubTypes.METRIC),  # Metric
    MigratedObjectTypes.PROMPT: (ObjectTypes.PROMPT, None),  # Prompt
    MigratedObjectTypes.SMART_ATTRIBUTE: (
        ObjectTypes.ATTRIBUTE,
        ObjectSubTypes.ATTRIBUTE_SMART,
    ),  # Smart Attribute
    MigratedObjectTypes.SUBTOTAL: (
        ObjectTypes.METRIC,
        [
            ObjectSubTypes.SUBTOTAL_DEFINITION,
            ObjectSubTypes.SYSTEM_SUBTOTAL,
        ],
    ),  # Subtotal
    MigratedObjectTypes.AUTO_STYLE: (ObjectTypes.GRAPH_STYLE, None),  # Auto Style
    MigratedObjectTypes.EXTERNAL_SHORTCUT: (
        ObjectTypes.SHORTCUT,
        None,
    ),  # External Shortcut
    MigratedObjectTypes.SEARCH: (ObjectTypes.SEARCH, None),  # Search
    MigratedObjectTypes.SECURITY_FILTER: (
        ObjectTypes.SECURITY_FILTER,
        None,
    ),  # Security Filter
    MigratedObjectTypes.SHORTCUT: (ObjectTypes.SHORTCUT_TYPE, None),  # Shortcut
    MigratedObjectTypes.TABLE: (ObjectTypes.TABLE, None),  # Table
    MigratedObjectTypes.TEMPLATE: (ObjectTypes.TEMPLATE, None),  # Template
    MigratedObjectTypes.TRANSFORMATION: (
        ObjectTypes.ROLE,
        ObjectSubTypes.ROLE_TRANSFORMATION,
    ),  # Transformation
    MigratedObjectTypes.SCRIPT: (
        ObjectTypes.SCRIPT,
        [
            ObjectSubTypes.SCRIPT,
            ObjectSubTypes.TRANSACTION_SCRIPT,
        ],
    ),  # Script
    MigratedObjectTypes.USER: (ObjectTypes.USER, [ObjectSubTypes.USER]),  # User
    MigratedObjectTypes.USER_GROUP: (
        ObjectTypes.USER,
        [ObjectSubTypes.USER_GROUP],
    ),  # User Group
    MigratedObjectTypes.DATA_SOURCE: (ObjectTypes.DBROLE, None),  # Data Source
    MigratedObjectTypes.SECURITY_ROLE: (
        ObjectTypes.SECURITY_ROLE,
        None,
    ),  # Security Role
    MigratedObjectTypes.CUSTOM_APPLICATION: (
        ObjectTypes.APPLICATION,
        None,
    ),  # Custom Application
    MigratedObjectTypes.PALETTE: (
        ObjectTypes.PALETTE,
        ObjectSubTypes.CUSTOM_PALETTE,
    ),  # Palette
    MigratedObjectTypes.TIMEZONE: (
        ObjectTypes.TIMEZONE,
        [ObjectSubTypes.TIMEZONE_CUSTOM],
    ),  # Timezone
    MigratedObjectTypes.CALENDAR: (
        ObjectTypes.CALENDAR,
        [ObjectSubTypes.CALENDAR_CUSTOM],
    ),  # Calendar
    MigratedObjectTypes.CONTENT_BUNDLE: (
        ObjectTypes.CONTENT_BUNDLE,
        None,
    ),  # Content Bundle
    MigratedObjectTypes.DEVICE: (
        ObjectTypes.SUBSCRIPTION_DEVICE,
        None,
    ),  # Device
    MigratedObjectTypes.LOCALE: (ObjectTypes.LOCALE, None),  # Locale
    MigratedObjectTypes.SCHEDULE_EVENT: (
        ObjectTypes.SCHEDULE_EVENT,
        None,
    ),  # Schedule Event
    MigratedObjectTypes.SCHEDULE_TRIGGER: (
        ObjectTypes.SCHEDULE_TRIGGER,
        None,
    ),  # Schedule Trigger
    MigratedObjectTypes.TRANSMITTER: (
        ObjectTypes.SUBSCRIPTION_TRANSMITTER,
        None,
    ),  # Transmitter
    MigratedObjectTypes.SCRIPT_RUNTIME_ENV: (
        ObjectTypes.RUNTIME,
        None,
    ),  # Script Runtime Environment
}
OBJECT_MIGRATION_TYPES_OBJECT = {
    MigratedObjectTypes.DASHBOARD,
    MigratedObjectTypes.DOCUMENT,
    MigratedObjectTypes.CARD,
    MigratedObjectTypes.REPORT,
    MigratedObjectTypes.DATASET,
    MigratedObjectTypes.BOT,
    MigratedObjectTypes.AGENT,
    MigratedObjectTypes.ATTRIBUTE,
    MigratedObjectTypes.BASE_FORMULA,
    MigratedObjectTypes.CONSOLIDATION,
    MigratedObjectTypes.CUSTOM_GROUP,
    MigratedObjectTypes.CONSOLIDATION_ELEMENT,
    MigratedObjectTypes.COLUMN,
    MigratedObjectTypes.DRILL_MAP,
    MigratedObjectTypes.FACT,
    MigratedObjectTypes.FILTER,
    MigratedObjectTypes.FUNCTION,
    MigratedObjectTypes.HIERARCHY,
    MigratedObjectTypes.METRIC,
    MigratedObjectTypes.PROMPT,
    MigratedObjectTypes.SMART_ATTRIBUTE,
    MigratedObjectTypes.SUBTOTAL,
    MigratedObjectTypes.AUTO_STYLE,
    MigratedObjectTypes.EXTERNAL_SHORTCUT,
    MigratedObjectTypes.SEARCH,
    MigratedObjectTypes.SECURITY_FILTER,
    MigratedObjectTypes.SHORTCUT,
    MigratedObjectTypes.TABLE,
    MigratedObjectTypes.TEMPLATE,
    MigratedObjectTypes.TRANSFORMATION,
    MigratedObjectTypes.SCRIPT,
}
OBJECT_MIGRATION_TYPES_ADMINISTRATION = {
    MigratedObjectTypes.USER,
    MigratedObjectTypes.USER_GROUP,
    MigratedObjectTypes.DATA_SOURCE,
    MigratedObjectTypes.SECURITY_ROLE,
    MigratedObjectTypes.CUSTOM_APPLICATION,
    MigratedObjectTypes.PALETTE,
    MigratedObjectTypes.TIMEZONE,
    MigratedObjectTypes.CALENDAR,
    MigratedObjectTypes.CONTENT_BUNDLE,
    MigratedObjectTypes.DEVICE,
    MigratedObjectTypes.LOCALE,
    MigratedObjectTypes.SCHEDULE_EVENT,
    MigratedObjectTypes.SCHEDULE_TRIGGER,
    MigratedObjectTypes.TRANSMITTER,
    MigratedObjectTypes.SCRIPT_RUNTIME_ENV,
}
