from enum import auto
import logging
from time import sleep
from typing import Any, Dict, List, Optional, Union

from mstrio import config
from mstrio.api import migration
from mstrio.connection import Connection
from mstrio.types import ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils import helper
from mstrio.utils.entity import DeleteMixin, EntityBase
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, exception_handler
from mstrio.utils.wip import module_wip, WipLevels

module_wip(globals(), level=WipLevels.PREVIEW)

logger = logging.getLogger(__name__)

TIMEOUT = 60
TIMEOUT_INCREMENT = 0.25


class PackageSettings(Dictable):
    """Object representation of package settings details.

    Attributes:
        default_action(DefaultAction): default action for Package
        update_schema(Optional[UpdateSchema]): update_schema for Package
        acl_on_replacing_objects(Optional[AclOnReplacingObjects]):
            ACL setting on replacing objects
        acl_on_new_objects(Optional[AclOnNewObjects]):
            ACL setting on new objects
    """
    _DELETE_NONE_VALUES_RECURSION = True

    class UpdateSchema(AutoName):
        """They allow you to configure the package to automatically perform
        certain schema update functions. These options can be useful if you make
        any changes to schema objects. Use the recalculate table keys and fact
        entry levels if you changed the key structure of a table or if you
        changed the level at which a fact is stored.Use the recalculate table
        logical sizes to override any modifications that you have made to
        logical table sizes. (Logical table sizes affect how the MicroStrategy
        SQL Engine determines which tables to use in a query.)
        """
        RECAL_TABLE_LOGICAL_SIZE = auto()
        RECAL_TABLE_KEYS_FACT_ENTRY_LEVEL = auto()

    class AclOnReplacingObjects(AutoName):
        """If you resolve a conflict with the "Replace" action, and the access
        control lists (ACL) of the objects are different between the two
        projects, you can choose whether to keep the existing ACL in the
        destination project or replace it with the ACL from the source project.
        Note: This is not supported for project security packages.
        """
        USE_EXISTING = auto()
        REPLACE = auto()

    class AclOnNewObjects(AutoName):
        """If you add a new object to the destination project with the
        "Create New" or "Keep Both action", you can choose to have the object
        inherit its ACL from the destination folder instead of keeping its own
        ACL. This is helpful when copying an object into a user's profile
        folder, so that the user can have full control over the object.
        """
        KEEP_ACL_AS_SOURCE_OBJECT = auto()
        INHERIT_ACL_AS_DEST_FOLDER = auto()

    class DefaultAction(AutoName):
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
        FORCE_KEEP_BOTH: No change is made to the destination object. The source
        object is always saved as a new object.
        """
        USE_EXISTING = auto()
        REPLACE = auto()
        KEEP_BOTH = auto()
        USE_NEWER = auto()
        USE_OLDER = auto()
        FORCE_REPLACE = auto()
        DELETE = auto()
        FORCE_KEEP_BOTH = auto()

    _FROM_DICT_MAP = {
        'default_action': DefaultAction,
        'update_schema': [UpdateSchema],
        'acl_on_replacing_objects': AclOnReplacingObjects,
        'acl_on_new_objects': [AclOnNewObjects]
    }

    def __init__(self, default_action: DefaultAction = DefaultAction.USE_EXISTING,
                 update_schema: Optional[UpdateSchema] = None,
                 acl_on_replacing_objects: Optional[AclOnReplacingObjects] = None,
                 acl_on_new_objects: Optional[AclOnNewObjects] = None):
        self.default_action = default_action
        self.update_schema = update_schema if isinstance(update_schema, list) else [update_schema]
        self.acl_on_replacing_objects = acl_on_replacing_objects
        self.acl_on_new_objects = acl_on_new_objects if isinstance(acl_on_new_objects,
                                                                   list) else [acl_on_new_objects]


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
    _DELETE_NONE_VALUES_RECURSION = True

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
        FORCE_KEEP_BOTH: No change is made to the destination object. The source
        object is always saved as a new object.
        """
        USE_EXISTING = auto()
        REPLACE = auto()
        KEEP_BOTH = auto()
        USE_NEWER = auto()
        USE_OLDER = auto()
        FORCE_REPLACE = auto()
        DELETE = auto()
        FORCE_KEEP_BOTH = auto()

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
        _DELETE_NONE_VALUES_RECURSION = True

        @classmethod
        def from_dict(cls, source: Dict[str, Any], connection: Optional["Connection"] = None):
            return super().from_dict(source, connection)

        def __init__(self, id: str, connection: Optional["Connection"] = None):
            if connection:
                super().__init__(id, connection)
            else:
                self._id = id

    _FROM_DICT_MAP = {'type': ObjectTypes, 'action': Action, 'level': Level, 'owner': Owner}

    def __init__(self, id: str, action: Union[Action, str] = Action.USE_EXISTING,
                 name: Optional[str] = None, version: Optional[str] = None,
                 type: Optional[ObjectTypes] = None, owner: Optional[Owner] = None,
                 date_created: Optional[str] = None, date_modified: Optional[str] = None,
                 include_dependents: Optional[bool] = None,
                 explicit_included: Optional[bool] = None, level: Optional[Union[Level,
                                                                                 str]] = None):
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
            self.level = PackageContentInfo.Level(level) if isinstance(level, str) else level
            self.action = PackageContentInfo.Action(action) if isinstance(action, str) else action
        except ValueError:
            exception_handler(msg="Wrong enum value", exception_type=ValueError)


class PackageConfig(Dictable):
    """Package Update Data Transfer Object

    Attributes:
        type(PackageUpdateType): type of package update
        settings(PackageSettings): settings details of package
        content(PackageContentInfo, List[PackageContentInfo]): content details
            of package
    """
    _DELETE_NONE_VALUES_RECURSION = True

    class PackageUpdateType(AutoName):
        """ Package update type:
        PROJECT: For user’s input, only accept non configuration object. But
            the actual package contains all kinds of objects, including
            configuration objects.
        CONFIGURATION: Only contains configuration objects. 12 types in total,
            including “Database connection“, “Transmitter“, “Database Instance“,
            “Database login“, “DBMS“, “Device“, “Event“, ”Language”, “Schedule“,
            ”Security Role”,”User”, “User group“.
        PROJECT_SECURITY: Only contains user objects.
        """
        PROJECT = auto()
        PROJECT_SECURITY = auto()
        CONFIGURATION = auto()

    _FROM_DICT_MAP = {
        'type': PackageUpdateType,
        'settings': PackageSettings,
        'content': [PackageContentInfo]
    }

    def __init__(self, type: PackageUpdateType, settings: PackageSettings,
                 content: Union[List[PackageContentInfo], PackageContentInfo]):
        self.type = type
        self.settings = settings
        self.content = [content] if not isinstance(content, list) else content


class Package(EntityBase, DeleteMixin):
    """Object representation of MicroStrategy Package object.

    Attributes:
        connection(Connection): a MicroStrategy connection object
        id(str): package ID
        status(str): status of a package
        settings(PackageSettings): settings details of package
        content(PackageContentInfo): content details of package
    """
    _DELETE_NONE_VALUES_RECURSION = True

    _API_GETTERS = {("id", "status", "settings", "content"): migration.get_package_holder}
    _API_DELETE = staticmethod(migration.delete_package_holder)

    _FROM_DICT_MAP = {
        'settings': PackageSettings.from_dict,
        'content': [PackageContentInfo.from_dict],
    }

    def __init__(self, connection: Connection, id: str) -> None:
        """Initialize PackageImport object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`
            id: ID of package import process
        """
        if id is None:
            exception_handler("Please provide actual value for id argument, other than None.",
                              exception_type=ValueError)

        super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        self.settings = None
        self.content = None

        super()._init_variables(**kwargs)
        self.status = kwargs.get("status")
        self.project_id = kwargs.get("project_id")

    @classmethod
    def create(cls, connection: Connection, progress_bar: bool = False):
        response = migration.create_package_holder(connection).json()
        if config.verbose and not progress_bar:
            logger.info(f"Created package with ID: '{response.get('id')}'")
        return cls.from_dict(source=response, connection=connection)

    def update_config(self, package_config: PackageConfig):
        body = package_config.to_dict()
        body = helper.delete_none_values(body, recursion=True)
        body = helper.snake_to_camel(body)
        migration.update_package_holder(self.connection, body, self.id).json()

        total_time = 0
        # Wait until update ready
        while True:
            response = migration.get_package_holder(self.connection, self.id,
                                                    show_content=False).json()
            if response.get('status') == 'ready':
                break
            sleep(TIMEOUT_INCREMENT)
            total_time += TIMEOUT_INCREMENT

            if total_time > TIMEOUT:
                logger.warning('Time out on updating package')
                return False

        self.fetch()
        return True

    def upload_package_binary(self, package_binary: bytes, progress_bar: bool = False):
        response = migration.upload_package(self.connection, self.id, package_binary).json()
        self.status = response.get('status')
        if config.verbose and not progress_bar:
            logger.info(
                f"Uploaded package binary to package holder with ID: '{response.get('id')}'")

    def download_package_binary(self, progress_bar: bool = False) -> bytes:
        response = migration.download_package(self.connection, self.id)
        if config.verbose and not progress_bar:
            logger.info(f"Downloaded binary of a package with ID: '{self.id}'")
        return response.content


class PackageImport(EntityBase, DeleteMixin):
    """Object representation of MicroStrategy PackageImportProcess object.

    Attributes:
        connection(Connection): A MicroStrategy connection object
        id(str): PackageImport ID
        status(str): status of an import
        undo_package_created(bool): if the undo package have been created
        progress(int): progress of package import process
    """
    _DELETE_NONE_VALUES_RECURSION = True

    _API_GETTERS = {("id", "status", "undo_package_created", "progress"): migration.get_import}
    _API_DELETE = staticmethod(migration.delete_import)
    _progress_bar = True

    def __init__(self, connection: Connection, id: str) -> None:
        """Initialize PackageImport object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            id: ID of package import process
        """
        if id is None:
            exception_handler("Please provide actual value for id argument, other than None.",
                              exception_type=ValueError)

        super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.undo_package_created = kwargs.get("undo_package_created")
        self.status = kwargs.get("status")
        self.progress = kwargs.get("progress")

    @classmethod
    def create(cls, connection: Connection, package_id: str, generate_undo: bool,
               progress_bar=False):
        response = migration.create_import(connection, package_id,
                                           generate_undo=generate_undo).json()

        total_time = 0
        # Wait until update ready
        while True:
            response = migration.get_import(connection, response.get('id')).json()
            if response.get('status') == 'imported':
                break
            sleep(TIMEOUT_INCREMENT)
            total_time += TIMEOUT_INCREMENT

            if total_time > TIMEOUT:
                logger.warning('Time out on creating import')
                return False

        if config.verbose and not progress_bar:
            logger.info(f"Created package import process with ID: '{response.get('id')}'")
        return cls.from_dict(source=response, connection=connection)

    def download_undo_binary(self, progress_bar=False):
        total_time = 0
        # Wait until update ready
        while True:
            response = migration.get_import(self.connection, self.id).json()
            if response.get('undoPackageCreated') is True:
                break
            sleep(TIMEOUT_INCREMENT)
            total_time += TIMEOUT_INCREMENT

            if total_time > TIMEOUT:
                logger.warning('Time out on downloading undo binary')
                return False

        response = migration.create_undo(self.connection, self.id)
        if config.verbose and not progress_bar:
            logger.info(f"Downloaded undo package binary for import process with ID: '{self.id}'")
        return response.content
