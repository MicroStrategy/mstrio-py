from enum import auto, Enum
import logging
from pathlib import Path
from typing import Callable, List, Optional, Union

from mstrio import config
from mstrio.api.exceptions import VersionException
from mstrio.connection import Connection
from mstrio.object_management.migration.package import Package, PackageConfig, PackageImport
from mstrio.utils.helper import Dictable, exception_handler
from mstrio.utils.progress_bar_mixin import ProgressBarMixin
from mstrio.utils.wip import module_wip, WipLevels

module_wip(globals(), level=WipLevels.PREVIEW)

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    NOT_STARTED = auto()
    STARTED = auto()
    CREATING_PACKAGE = auto()
    CREATING_PACKAGE_FAILED = auto()
    CREATING_PACKAGE_COMPLETED = auto()
    MIGRATION_IN_PROGRESS = auto()
    MIGRATION_FAILED = auto()
    MIGRATION_COMPLETED = auto()
    UNDO_STARTED = auto()
    UNDO_FAILED = auto()
    UNDO_COMPLETED = auto()


class Migration(Dictable, ProgressBarMixin):
    """A class encapsulating migration process from env A to env B.

    Raises VersionException if either of environments are running IServer
    version lower than 11.3.0200

    Raises AttributeError if parent directory of specified `save_path` is
    non-existent or points to another kind of file.

    Attributes:
        configuration(PackageConfig): a configuration of the migration
        save_path(str): a full path used when saving import package to a
        file. It is also used for saving undo package with the addition of
        `_undo` suffix. By default, uses ~cwd/migration.mmp and
        ~cwd/migration_undo.mmp.
        source_connection(Connection): A MicroStrategy connection object
          to the source env,
        target_connection(Connection): A MicroStrategy connection object
          to the target env,
        name(str): Name of the migration. Used for identification purposes for
            the convenience of the user,
        package(Package): a package that is migrated,
        package_import(PackageImport): a package import process object,
        package_binary(Binary): actual data that is migrated
        status(MigrationStatus): current status of migration,
        create_undo(bool): should a undo package be made
        undo_package(Binary): undo package binary for this import process.
          if `create_undo` is False, it is equal to None.

    Additional args:
        custom_package_path(str): a full path to an already existing .mpp file.
            This argument overrides `save_path`. Creating a `Migration` object
            with only `source_connection`, `target_connection` and
            `custom_package_path` allows for an easier export to the target by
            running `migrate_package()` on that `Migration` instance (instead of
            performing full migration with an import from the source first.
            See demos and examples for details.)."""
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, save_path: Optional[str] = f"{Path.cwd()}/migration.mmp",
                 source_connection: Optional[Connection] = None,
                 configuration: Optional[PackageConfig] = None,
                 target_connection: Optional[Connection] = None,
                 custom_package_path: Optional[str] = None, name: Optional[str] = None,
                 create_undo: bool = True):
        if not self._validate_envs_version(source_connection, target_connection):
            exception_handler(
                msg=("Environments must run IServer version 11.3.0200 or newer. "
                     "Please update your environments to use this feature."),
                exception_type=VersionException)
        self.name = name
        self.source_connection = source_connection
        self.target_connection = target_connection
        self.configuration = configuration
        self.create_undo = create_undo
        self._status = MigrationStatus.NOT_STARTED

        self._check_file_path(save_path, "save_path")
        self.save_path = save_path

        self._package = None
        self._package_import = None
        self._undo_binary = None

        if custom_package_path and self._check_file_path(custom_package_path,
                                                         "custom_package_path"):
            self.save_path = custom_package_path
            filename, file_extension = self._decompose_file_path(custom_package_path)
            with open(f"{filename}{file_extension}", "rb") as f:
                self._package_binary = f.read()
        else:
            self._package_binary = None

    @staticmethod
    def _validate_envs_version(source_connection: Connection,
                               target_connection: Connection) -> bool:
        return ((source_connection is None or source_connection._iserver_version >= '11.3.0200')
                and (target_connection is None
                     or target_connection._iserver_version >= '11.3.0200'))

    @staticmethod
    def _decompose_file_path(file_path: str) -> tuple:
        file_path = Path(file_path)
        filename, file_extension = file_path.parent / file_path.stem, file_path.suffix
        if file_extension == '':
            return filename, '.mmp'
        return filename, file_extension

    @staticmethod
    def _check_file_path(file_path: str, var_name: str):
        file_path = Path(file_path)

        if file_path.parent.is_dir() and not file_path.is_dir():
            return True
        else:
            exception_handler(
                msg=f"Invalid save path. Parent directory specified in `{var_name}` is incorrect.",
                exception_type=AttributeError)

    def perform_full_migration(self) -> bool:
        """Perform 'create_package()' and 'migrate_package()' using
        configuration provided when creating `Migration` object.
        """
        if not isinstance(self.source_connection, Connection) or self.source_connection is None:
            exception_handler(
                msg=("Migration object missing `source_connection`. "
                     "`perform_full_migration()` unavailable."), exception_type=AttributeError)
        if not isinstance(self.target_connection, Connection) or self.target_connection is None:
            exception_handler(
                msg=("Migration object missing `target_connection`. "
                     "`perform_full_migration()` unavailable."), exception_type=AttributeError)

        self._display_progress_bar(desc='Migration status: ', unit='Migration', total=4,
                                   bar_format='{desc} |{bar:50}| {percentage:3.0f}%')

        if not self.create_package():
            return False

        if not self.migrate_package():
            return False

        self._close_progress_bar()
        return True

    def create_package(self) -> bool:
        """Performs import of the object described in the migration
        configuration from the source environment and save it in a file
        at location specified in `save_path` parameter.

        Raises AttributeError if `source_connection` is not specified.

        Raises FileExistsError if a package or undo package with the same name
        already exist at`save_path` location. """
        if not isinstance(self.source_connection, Connection) or self.source_connection is None:
            exception_handler(
                msg=("Migration object does not have `source_connection`. Import unavailable."),
                exception_type=AttributeError)

        filename, file_extension = self._decompose_file_path(self.save_path)
        """File existence checked here instead of using "xb" mode in context
        manager to avoid creation of package if it should not be saved"""
        if Path(f"{filename}{file_extension}").exists() or Path(
                f"{filename}_undo{file_extension}").exists():
            exception_handler(
                msg=("Migration file / undo package with this name already exists."
                     "Please use other location / filename in `save_path` parameter."),
                exception_type=FileExistsError)

        self.__private_status = MigrationStatus.CREATING_PACKAGE
        self._create_package_holder(self.source_connection)
        if not self._update_package_holder():
            self.__private_status = MigrationStatus.CREATING_PACKAGE_FAILED
            return False

        self._download_package_binary()
        self._delete_package_holder()
        self._save_package_binary_locally(filename, file_extension, self.package_binary)

        self.__private_status = MigrationStatus.CREATING_PACKAGE_COMPLETED
        return True

    def migrate_package(self, custom_package_path: Optional[str] = None, is_undo=False) -> bool:
        """Performs migration of already created package to the target
        environment. Import package will be loaded from `custom_package_path`.
        If `custom_package_path` not provided, the object previously acquired
        with the `create_package()` will be used.
        If `create_undo` parameter is set to True, package needed for undo
        process will be downloaded.

        Raises AttributeError if `target_connection` is not specified.
        """

        if not isinstance(self.target_connection, Connection) or self.target_connection is None:
            exception_handler(
                msg=("Migration object does not have `target_connection`. "
                     "Export unavailable."), exception_type=AttributeError)

        if custom_package_path and self._check_file_path(custom_package_path,
                                                         "custom_package_path"):
            self.save_path = custom_package_path
            filename, file_extension = self._decompose_file_path(custom_package_path)
            with open(f"{filename}{file_extension}", "rb") as f:
                return self._migrate_package(f.read(), is_undo=is_undo)
        return self._migrate_package(self._package_binary, custom_package_path=custom_package_path,
                                     is_undo=is_undo)

    def _migrate_package(self, binary: bytes, is_undo: bool = False,
                         custom_package_path: Optional[str] = None) -> bool:
        if binary is None:
            exception_handler(
                msg=("Import package is None. Run `create_package()` first, "
                     "or specify `custom_package_path`."), exception_type=AttributeError)

        self.__private_status = MigrationStatus.MIGRATION_IN_PROGRESS
        self._create_package_holder(self.target_connection)
        self._upload_package_binary(binary)
        if not self._create_import(self.target_connection):
            self.__private_status = MigrationStatus.MIGRATION_FAILED
            return False

        if not is_undo and self.create_undo:
            self._download_undo_binary()
            file_path = custom_package_path if custom_package_path else self.save_path
            filename, file_extension = self._decompose_file_path(file_path)
            self._save_package_binary_locally(filename=f"{filename}_undo",
                                              file_extension=file_extension,
                                              _bytes=self.undo_binary)

        self._delete_package_holder()
        self._delete_import()

        self.__private_status = MigrationStatus.MIGRATION_COMPLETED
        return True

    def undo_migration(self):
        """Revert the migration using the package downloaded during
        `migrate_package()` or `perform_full_migration()`.

        Raises AttributeError if `undo_binary` is None.
        """
        self.__private_status = MigrationStatus.UNDO_STARTED
        if self.undo_binary:
            self._migrate_package(self._undo_binary, True)
        else:
            self.__private_status = MigrationStatus.UNDO_FAILED
            msg = ('`undo_binary` is None. Perform migration with `create_undo`'
                   ' parameter set to True')
            exception_handler(msg, exception_type=AttributeError)
        self.__private_status = MigrationStatus.UNDO_COMPLETED

    def _create_package_holder(self, conn: Connection):
        self._package = Package.create(conn, progress_bar=self._progress_bar is not None)

    def _update_package_holder(self):
        return self._package.update_config(self.configuration)

    def _download_package_binary(self):
        self._package_binary = self._package.download_package_binary(
            progress_bar=self._progress_bar is not None)

    def _upload_package_binary(self, binary: bytes):
        self._package.upload_package_binary(binary, progress_bar=self._progress_bar is not None)

    def _delete_package_holder(self):
        self._package.delete(force=True)
        self._package = None

    def _create_import(self, conn: Connection) -> bool:
        self._package_import = PackageImport.create(conn, self.package.id, self.create_undo,
                                                    progress_bar=self._progress_bar is not None)
        if self._package_import is False:
            return False
        return True

    def _delete_import(self):
        self._package_import.delete(force=True)
        self._package_import = None

    def _download_undo_binary(self):
        self._undo_binary = self._package_import.download_undo_binary(
            progress_bar=self._progress_bar is not None)

    def _save_package_binary_locally(self, filename: str, file_extension: str, _bytes: bytes):
        with open(f"{filename}{file_extension}", "wb") as f:
            f.write(_bytes)
        logger.info(f'Package / package undo binary created at:{filename}{file_extension}')

    @property
    def package(self):
        return self._package

    @property
    def package_binary(self):
        return self._package_binary

    @property
    def package_import(self):
        return self._package_import

    @property
    def undo_binary(self):
        return self._undo_binary

    @property
    def status(self):
        return self._status

    @property
    def __private_status(self):
        return self._status

    @__private_status.setter
    def __private_status(self, var: MigrationStatus):
        self._update_progress_bar_if_needed(new_description=f'[{self.name}] Status: {var.name}')
        self._status = var


def bulk_full_migration(migrations: Union[Migration, List[Migration]], verbose: bool = False):
    """Run `perform_full_migration()` for each of the migrations provided.
    Args:
        migrations: migrations to be executed
        verbose: if True, information about each step will be printed
    """
    __run_func_for_all_migrations(Migration.perform_full_migration, migrations, verbose)


def bulk_migrate_package(migrations: Union[Migration, List[Migration]], verbose: bool = False):
    """Run `migrate_package()` for each of the migrations provided.
    Args:
        migrations: migrations to be executed
        verbose: if True, information about each step will be printed
    """
    __run_func_for_all_migrations(Migration.migrate_package, migrations, verbose)


def __run_func_for_all_migrations(func: Callable, migrations: Union[Migration, List[Migration]],
                                  verbose: bool = False, *args, **kwargs):
    if type(migrations) is Migration:
        migrations = [migrations]
    original_verbose = config.verbose
    config.verbose = verbose
    for migration in migrations:
        func(migration, *args, **kwargs)
    config.verbose = original_verbose
