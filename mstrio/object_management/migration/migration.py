import logging
import os
from collections.abc import Callable
from datetime import datetime
from hashlib import sha256

from mstrio import config
from mstrio.api import migration as migration_api
from mstrio.connection import Connection
from mstrio.object_management import Object, SearchObject
from mstrio.object_management.migration.package import (
    CATALOG_ITEMS,
    OBJECT_MIGRATION_TYPES_ADMINISTRATION,
    OBJECT_MIGRATION_TYPES_MIN_VERSION,
    OBJECT_MIGRATION_TYPES_OBJECT,
    Action,
    ImportInfo,
    ImportStatus,
    MigratedObjectTypes,
    MigrationPurpose,
    PackageCertificationStatus,
    PackageConfig,
    PackageContentInfo,
    PackageInfo,
    PackageSettings,
    PackageStatus,
    PackageType,
    ProjectMergePackageSettings,
    ProjectMergePackageTocView,
    RequestStatus,
    Validation,
)
from mstrio.server import Environment
from mstrio.server.project import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups import User
from mstrio.utils.entity import DeleteMixin, EntityBase
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import camel_to_snake
from mstrio.utils.progress_bar_mixin import ProgressBarMixin
from mstrio.utils.resolvers import get_project_id_from_params_set
from mstrio.utils.response_processors import migrations
from mstrio.utils.time_helper import datetime_to_str
from mstrio.utils.version_helper import (
    class_version_handler,
    is_server_min_version,
    method_version_handler,
)

logger = logging.getLogger(__name__)


def list_migration_possible_content(
    connection: Connection, package_type: PackageType
) -> list[ObjectTypes | ObjectSubTypes]:
    """List possible content for migration process based on the package type and
    environment version.

    Args:
        connection (Connection): A Strategy One connection object
        package_type (PackageType): Type of the package

    Returns:
        Set of MigratedObjectTypes"""
    if package_type == PackageType.ADMINISTRATION:
        available_per_package_type = OBJECT_MIGRATION_TYPES_ADMINISTRATION
    elif package_type == PackageType.OBJECT:
        available_per_package_type = OBJECT_MIGRATION_TYPES_OBJECT
    else:
        available_per_package_type = set(MigratedObjectTypes)
    unavailable_per_version = {
        object_type
        for object_type, version in OBJECT_MIGRATION_TYPES_MIN_VERSION.items()
        if not is_server_min_version(connection, version)
    }
    available_migrated_types = available_per_package_type - unavailable_per_version
    types_to_search: list[ObjectTypes | ObjectSubTypes] = []
    for mig_object_type in available_migrated_types:
        obj_type, obj_subtype = CATALOG_ITEMS[mig_object_type]
        if isinstance(obj_subtype, list):
            types_to_search.extend(obj_subtype)
        elif obj_subtype is not None:
            types_to_search.append(obj_subtype)
        else:
            types_to_search.append(obj_type)

    return types_to_search


@method_version_handler(version='11.3.10')
def list_migrations(
    connection: Connection,
    name: str | None = None,
    migration_purpose: MigrationPurpose | str | None = None,
    package_status: PackageStatus | str | None = None,
    import_status: ImportStatus | str | None = None,
    limit: int | None = None,
    to_dictionary: bool = False,
) -> list["Migration"] | list[dict]:
    """Get list of Migration objects.
    Optionally use `to_dictionary` to choose output format.

    Args:
        connection (Connection): A Strategy One connection object
        name (str, optional): characters that the Migration name must contain
        migration_purpose (MigrationPurpose, str, optional): purpose of the
            migration can be either 'object_migration', 'project_merge' or
            'migration_from_shared_file_store'. If None returns migration of all
            purposes
        package_status (PackageStatus, str, optional): status of the migration
            package
        import_status (ImportStatus, str, optional): status of the Migration
            import process
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned
        to_dictionary (bool, optional): If True returns dict, by default (False)
            returns Metric objects

    Returns:
        List of Migration objects or list of dictionaries
    """
    if migration_purpose:
        objects_ = _list_migrations(
            connection, migration_purpose=migration_purpose, limit=limit
        )
    else:
        all_purposes = ','.join([purpose.value for purpose in MigrationPurpose])
        objects_ = _list_migrations(
            connection,
            migration_purpose=all_purposes,
            limit=limit,
        )

    for obj in objects_:
        obj['name'] = obj['packageInfo']['name']

    if name:
        objects_ = list(filter(lambda x: name in x['name'], objects_))
    if package_status:
        package_status = get_enum_val(package_status, PackageStatus)
        objects_ = list(
            filter(lambda x: package_status == x['packageInfo']['status'], objects_)
        )
    if import_status:
        import_status = get_enum_val(import_status, ImportStatus)
        objects_ = list(
            filter(lambda x: import_status == x['importInfo']['status'], objects_)
        )
    if to_dictionary:
        return objects_
    else:
        return [
            Migration.from_dict(source=obj, connection=connection) for obj in objects_
        ]


def _list_migrations(
    connection: Connection,
    migration_purpose: (
        MigrationPurpose | list[MigrationPurpose] | str | list[str] | None
    ) = None,
    limit: int | None = None,
) -> list[dict]:
    max_call_limit = 1000
    if isinstance(migration_purpose, MigrationPurpose):
        migration_purpose = migration_purpose.value
    if limit is not None and limit <= max_call_limit:
        resp = migration_api.list_migrations(
            connection, limit=limit, migration_type=migration_purpose
        )
        objects_ = resp.json().get('data')
    else:
        resp = migration_api.list_migrations(
            connection, limit=1000, migration_type=migration_purpose
        )
        total_objects = resp.json().get('total')
        if total_objects > max_call_limit:
            objects_ = resp.json().get('data')
            while len(objects_) < total_objects:
                resp = migration_api.list_migrations(
                    connection,
                    limit=1000,
                    offset=len(objects_),
                    migration_type=migration_purpose,
                )
                objects_ += resp.json().get('data')
        else:
            objects_ = resp.json().get('data')
    return objects_


@class_version_handler(version='11.3.10')
class Migration(EntityBase, ProgressBarMixin, DeleteMixin):
    """A class encapsulating migration process from env A to env B.

    Raises VersionException if either of environments are running IServer
    version lower than 11.3.10

    Attributes:
        id(str): ID of the migration
        name(str): Name of the migration
        type(str): MSTR type of the migration object. Returns either
            NOT_SUPPORTED or None
        connection(Connection): A Strategy One connection object
        import_info(ImportInfo): Information about the import process
        package_info(PackageInfo): Information about the package configuration
            and status
        validation(Validation): Information about the validation process
        version(str): Version of the migration API
    """

    _API_GETTERS: dict[str | tuple, Callable] = {
        (
            'id',
            'name',
            'import_info',
            'package_info',
            'validation',
            'version',
        ): migrations.get,
    }
    _API_DELETE = staticmethod(migration_api.delete_migration)

    _FROM_DICT_MAP = {
        'import_info': ImportInfo.from_dict,
        'package_info': PackageInfo.from_dict,
        'validation': Validation.from_dict,
    }

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize migration object by its identifier.

        Args:
            connection: Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): identifier of a pre-existing migration.
                Defaults to None.
            name (str, optional): name of a pre-existing migration.
                Defaults to None.
        """
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            migrations = list_migrations(connection=connection, name=name)
            if migrations:
                number_of_objects = len(migrations)
                if number_of_objects > 1:
                    raise ValueError(
                        f"There are {number_of_objects} {type(self).__name__}"
                        " objects with this name. Please initialize with ID."
                    )

                id = migrations[0].to_dict()[  # NOSONAR - shadowing `id` in fn scope
                    'id'
                ]
            else:
                raise ValueError(
                    f"There is no {type(self).__name__} with the given name: '{name}'"
                )
        super().__init__(connection, id)

    def _init_variables(self, **kwargs) -> None:
        super()._init_variables(**kwargs)
        self.version = kwargs.get('version')
        self._import_info = kwargs.get('importInfo')
        self._package_info = kwargs.get('packageInfo')
        self._validation = kwargs.get('validation')

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        body: dict,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> 'Migration':
        """Create a totally new migration object.

        Note:
            Project parameters are obsolete when `body` package info is a
            `PackageType.ADMINISTRATION` type.

        Args:
            connection (Connection): A Strategy One connection object
            body (dict): a json body with migration details
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            A new Migration object
        """

        if body['packageInfo']['type'] == PackageType.ADMINISTRATION.value:
            response = migration_api.create_new_migration(
                connection=connection,
                body=body,
                prefer='respond-async',
            )
        else:
            proj_id = get_project_id_from_params_set(
                connection,
                project,
                project_id,
                project_name,
            )
            response = migration_api.create_new_migration(
                connection=connection,
                body=body,
                prefer='respond-async',
                project_id=proj_id,
            )

        response_data = response.json()

        if config.verbose:
            logger.info(
                "Successfully started creation of migration object with ID:"
                f" '{response_data.get('id')}'"
            )

        return cls.from_dict(
            source=camel_to_snake(response_data), connection=connection
        )

    @classmethod
    def create_object_migration(
        cls,
        connection: 'Connection',
        toc_view: dict | PackageConfig,
        tree_view: str | None = None,
        name: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> 'Migration':
        """
        Create a new migration for object migration purpose.

        Args:
            connection (Connection): A Strategy One connection object.
            toc_view (dict, PackageConfig): A dictionary representing the TOC
                view or a PackageConfig object.
            tree_view (str, optional): A string representing the tree view.
            name (str, optional): Name of the migration. Used for identification
                purposes for the convenience of the user. If None default name
                will be generated.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            A new Migration object.
        """
        if isinstance(toc_view, PackageConfig):
            toc_view = toc_view.to_dict()
        tree_view = tree_view or {}
        base_body = Migration._get_body_for_create(
            connection, toc_view, tree_view, name
        )
        base_body['packageInfo']['type'] = PackageType.OBJECT.value
        return cls.create(connection, base_body, project, project_id, project_name)

    @classmethod
    def create_admin_migration(
        cls,
        connection: 'Connection',
        toc_view: dict | PackageConfig,
        tree_view: str | None = None,
        name: str | None = None,
    ) -> 'Migration':
        """
        Create a new migration for administration migration purpose.

        Args:
            connection (Connection): A Strategy One connection object.
            toc_view (dict, PackageConfig): A dictionary representing the TOC
                view or a PackageConfig object.
            tree_view (str): A string representing the tree view.
            name (str, optional): Name of the migration. Used for identification
                purposes for the convenience of the user. If None default name
                will be generated.

        Returns:
            A new Migration object.
        """
        if isinstance(toc_view, PackageConfig):
            toc_view = toc_view.to_dict()
        tree_view = tree_view or {}
        base_body = Migration._get_body_for_create(
            connection, toc_view, tree_view, name
        )
        base_body['packageInfo']['type'] = PackageType.ADMINISTRATION.value
        return cls.create(connection, base_body)

    @classmethod
    def create_project_merge_migration(
        cls,
        connection: 'Connection',
        toc_view: dict | ProjectMergePackageSettings | ProjectMergePackageTocView,
        tree_view: str | None = None,
        name: str | None = None,
        project: 'Project | str | None' = None,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> 'Migration':
        """
        Create a new migration for project merge migration purpose.

        Args:
            connection (Connection): A Strategy One connection object.
            toc_view (dict): A dictionary representing the TOC view or a
                ProjectMergePackageSettings | ProjectMergePackageTocView object.
            tree_view (str): A string representing the tree view.
            name (str, optional): Name of the migration. Used for identification
                purposes for the convenience of the user. If None default name
                will be generated.
            project (Project | str, optional): Project object or ID or name
                specifying the project. May be used instead of `project_id` or
                `project_name`.
            project_id (str, optional): Project ID
            project_name (str, optional): Project name

        Returns:
            A new Migration object.
        """

        if isinstance(toc_view, ProjectMergePackageSettings):
            toc_view = ProjectMergePackageTocView(toc_view).to_dict()
        if isinstance(toc_view, ProjectMergePackageTocView):
            toc_view = toc_view.to_dict()
            toc_view['settings']['aclOnNewObjects'] = [
                toc_view['settings']['aclOnNewObjects']
            ]
        tree_view = tree_view or {}
        base_body = Migration._get_body_for_create(
            connection, toc_view, tree_view, name
        )
        base_body['packageInfo']['type'] = PackageType.OBJECT.value
        base_body['packageInfo']['purpose'] = MigrationPurpose.PROJECT_MERGE.value
        return cls.create(connection, base_body, project, project_id, project_name)

    def reuse(
        self,
        target_env: Connection | Environment,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
    ) -> 'Migration':
        """
        Reuse an already migrated package to create a new one with the same
        properties, and then migrate it to a different environment or
        the same one.

        Args:
            target_env (Connection, Environment): Target environment to migrate
                reused package to.
            target_project (Project | str, optional): Project object or ID or
                name specifying the project. May be used instead of
                `target_project_id` or `target_project_name`.
            target_project_id (str, optional): Project ID
            target_project_name (str, optional): Project name

        Returns:
            A new Migration object based on the reused package.
        """
        target_id = Migration._get_env_id(target_env)
        body = {"importInfo": {"environment": {'id': target_id, 'name': target_id}}}

        if self._package_info.type == PackageType.OBJECT:
            if isinstance(target_env, Environment):
                target_env = target_env.connection
            target_proj_id = get_project_id_from_params_set(
                target_env,
                target_project,
                target_project_id,
                target_project_name,
            )
            target_proj_name = Project(target_env, id=target_proj_id).name
            body['importInfo']['project'] = {
                'id': target_proj_id,
                'name': target_proj_name,
            }

        response_data = migration_api.create_new_migration(
            connection=self.connection, package_id=self._package_info.id, body=body
        ).json()
        mig_dict = migration_api.get_migration(
            self.connection, response_data['id'], show_content='all'
        ).json()
        mig_dict['packageInfo']['replicated'] = True
        migration_api.start_migration(
            target_env,
            prefer='respond-async',
            migration_id=response_data['id'],
            body=mig_dict,
            generate_undo=True,
            project_id=target_project_id,
        ).json()
        if config.verbose:
            logger.info(
                "Successfully reused existing migration object and created new "
                "one with ID:"
                f" '{response_data.get('id')}'"
                " that was already migrated."
            )
        return Migration(connection=self.connection, id=response_data.get('id'))

    @classmethod
    def _upload_binary(
        cls,
        connection: Connection,
        name: str,
        package_type: PackageType | str,
        migration_purpose: MigrationPurpose | str,
        file: bytes,
    ):
        """
        "packageType": str
            ("project", "project_security", "configuration"),
        "packagePurpose": str
            ("object_migration", "project_merge", "migration_group",
            "migration_group_child", "migration_from_shared_file_store")
        """

        package_type = get_enum_val(package_type, PackageType)
        migration_purpose = get_enum_val(migration_purpose, MigrationPurpose)

        conn: Connection = connection
        body = {
            "name": name,
            "extension": "mmp",
            "type": "migrations.packages",
            "size": len(file),
            "sha256": sha256(file).hexdigest(),
            "environment": {
                "id": conn.base_url,
                "name": conn.base_url,
            },
            "extraInfo": {
                "packageType": package_type,
                "packagePurpose": migration_purpose,
            },
        }
        response = migration_api.storage_service_create_file_metadata(connection, body)
        if response.ok:
            cls._file_id = response.json()["id"]
        return migration_api.storage_service_upload_file_binary(
            connection, cls._file_id, file
        )

    @classmethod
    def migrate_from_file(
        cls,
        connection: 'Connection',
        file_path: str,
        package_type: PackageType | str,
        name: str | None = None,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
    ) -> 'Migration':
        """
        Create a new migration object from an existing package file.
        Project information is required in case of object migration.

        Args:
            connection (Connection): A Strategy One connection object.
            file_path (str): A full path to the package file.
            package_type (PackageType | str): Type of the package.
            name (str, optional): Name of the migration. Used for identification
                purposes for the convenience of the user. Defaults to None.
            target_project (Project | str, optional): Project object or ID or
                name specifying the project. May be used instead of
                `target_project_id` or `target_project_name`.
            target_project_id (str, optional): Project ID
            target_project_name (str, optional): Project name

        Returns:
            Migration: A new Migration object.
        """
        target_proj_id = get_project_id_from_params_set(
            connection,
            target_project,
            target_project_id,
            target_project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        package_type = get_enum_val(package_type, PackageType)
        with open(file_path, mode='rb') as file:  # b is important -> binary
            file_content = file.read()

        resp = cls._upload_binary(
            connection=connection,
            name=name,
            package_type=package_type,
            migration_purpose=MigrationPurpose.FROM_FILE,
            file=file_content,
        )
        file_id = resp.json()["id"]
        env_id = Migration._check_slash_in_id(connection.base_url)
        body = {
            "packageInfo": {
                "storage": {
                    "sharedFileStore": {
                        "files": {
                            "id": file_id,
                        }
                    }
                },
                "purpose": MigrationPurpose.FROM_FILE.value,
            },
            "importInfo": {
                "environment": {
                    "id": env_id,
                    "name": env_id,
                }
            },
        }

        if target_proj_id:
            target_proj_name = Project(connection, id=target_proj_id).name

            body['importInfo']['project'] = {
                'id': target_proj_id,
                'name': target_proj_name,
            }
            body['packageInfo']['project'] = {
                'id': target_proj_id,
                'name': target_proj_name,
            }

        response_data = migration_api.create_new_migration(
            connection=connection,
            body=body,
            prefer='respond-async',
            project_id=target_proj_id,
        )
        mig_id = response_data.json().get('id')
        logger.info(f"Successfully started migration from file with ID: '{mig_id}'.")
        return cls.from_dict(
            source=camel_to_snake(response_data.json()), connection=connection
        )

    def get_migration_content(self) -> dict:
        "Get full body of the migration object"
        mig_content = migration_api.get_migration(
            connection=self.connection,
            migration_id=self.id,
            show_content='all',
        ).json()
        return mig_content

    def trigger_validation(
        self,
        target_env: Connection | Environment,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
    ) -> None:
        """Trigger a validate process to migrate the package from the source
        environment to the destination environment according to the action
        defined, without committing any changes to the metadata.
        This API can only be called by administrator when package is created.

        Note:
            Project parameters are obsolete if no project-level objects are
            migrated.

        Args:
            target_env (Connection, Environment): Destination environment
                to validate the package.
            target_project (Project | str, optional): Project object or ID or
                name specifying the project. May be used instead of
                `target_project_id` or `target_project_name`.
            target_project_id (str, optional): Project ID
            target_project_name (str, optional): Project name

        """

        if isinstance(target_env, Environment):
            target_env = target_env.connection

        target_proj_id = get_project_id_from_params_set(
            target_env,
            target_project,
            target_project_id,
            target_project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        target_id = Migration._get_env_id(target_env)
        body = {
            'id': self.id,
            'packageInfo': self._package_info.to_dict(),
            'importInfo': {
                'id': self.import_info.id,
                'environment': {
                    'id': target_id,
                    'name': target_id,
                },
            },
        }

        if target_proj_id:
            body['importInfo']['project'] = {
                'id': target_proj_id,
                'name': Project(target_env, id=target_proj_id).name,
            }

        migration_api.update_migration(
            connection=self.connection, migration_id=self.id, body=body
        )
        fetched_body = migration_api.get_migration(
            connection=self.connection, migration_id=self.id, show_content='all'
        ).json()
        migration_api.trigger_migration_package_validation(
            connection=target_env,
            id=self.id,
            body=fetched_body,
            project_id=target_proj_id,
        )
        status_change = {"validation": {"status": "validating"}}
        migration_api.update_migration(
            connection=self.connection, migration_id=self.id, body=status_change
        )

        if config.verbose:
            logger.info(
                f"Successfully triggered validation process for migration "
                f"with ID: '{self.id}'"
            )

    def certify(
        self,
        status: PackageCertificationStatus | str | None = None,
        creator: User | None = None,
        last_updated_date: datetime | None = None,
        auto_sync: bool | None = None,
    ) -> None:
        """Update a migration's package certification status or trigger a
        process to synchronize the status.

        Notes:
            If argument 'auto_sync' is True, the migration's package
            certification status is synchronized with shared environment via
            storage service.
            Otherwise, the package certification status is updated with the
            definition of 'status', 'creator' and 'last_updated_date'.

        Args:
            status (PackageCertificationStatus, str, optional):
                Package certification status. Optional only if auto_sync is
                set to True.
            creator (User, optional): Creator of this file. Optional only if
                auto_sync is set to True.
            last_updated_date (datetime, optional): The last updated date of the
                certification operation. Optional only if auto_sync is set
                to True.
            auto_sync (bool, optional): If True, the migration's package
                certification status is synchronized with shared environment
                via storage service.
        """

        if all(arg is None for arg in [status, creator, last_updated_date, auto_sync]):
            raise ValueError(
                "Please provide required argument: 'auto_sync' or "
                "arguments: 'status', 'creator' and 'last_updated_date'"
            )

        body = (
            {
                'status': get_enum_val(status, PackageCertificationStatus),
                'operator': {
                    'id': creator.id,
                    'name': creator.name,
                    'fullName': creator.full_name,
                },
                'lastUpdatedDate': datetime_to_str(
                    last_updated_date, '%Y-%m-%dT%H:%M:%S.%f%z'
                ),
            }
            if not auto_sync
            else None
        )
        migration_api.certify_migration_package(
            connection=self.connection,
            id=self.id,
            body=body,
            auto_sync=auto_sync,
        )
        if config.verbose:
            logger.info(
                f"Successfully changed migration status with ID: '{self.id}' "
                f"to status: '{status}'"
            )

    def delete(self, force: bool = False) -> bool:
        """Deletes the Migration.

        Args:
            force: If True, no additional prompt will be shown before deleting
                Migration.

        Returns:
            True for success. False otherwise.
        """
        if self._package_info.purpose == MigrationPurpose.FROM_FILE:
            file_path = self._package_info.storage.path
            storage_files = migration_api.list_storage_files(
                self.connection, file_type='migrations.packages'
            ).json()['data']
            filtered_files = list(
                filter(lambda x: x['path'] == file_path, storage_files)
            )
            if len(filtered_files) > 0:
                migration_api.delete_file_binary(
                    self.connection, filtered_files[0]['id']
                )
        self.package_id = self._package_info.id
        delete_response = super().delete(force=force)
        if not delete_response:
            logger.info(f"Migration with ID: '{self.id}' is already deleted.")
            delete_response = True
        return delete_response

    def download_package(self, save_path: str | None = None) -> dict:
        """Download the package binary to the specified location.

        Args:
            save_path: a full path where the package binary will be saved.
            if None, the package will be saved in the current working directory.

        Returns:
            Dictionary with the filepath and file binary.
        """
        if not save_path:
            save_path = os.getcwd()
        response = migration_api.download_migration_package(
            connection=self.connection, package_id=self.package_info.id
        )
        if response.ok:
            filename = response.headers['Content-Disposition'].split('filename=')[1]
            with open(filename, "wb") as f:
                f.write(response.content)
            filepath = os.path.join(save_path, filename)
            logger.info(f"Package binary saved to: {filepath}")
            return {"filepath": filepath, "file_binary": response.content}

    @classmethod
    def from_dict(
        cls,
        source: dict,
        connection: 'Connection | None' = None,
        to_snake_case: bool = True,
    ):
        """Initialize Migration object from dictionary."""
        data = camel_to_snake(source) if to_snake_case else source.copy()
        return super().from_dict(data, connection, to_snake_case)

    def reverse(
        self,
        target_env: Environment | Connection,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
    ) -> None:
        """Reverse the migration process by importing the undo package.

        Note:
            Project parameters are obsolete if no project-level objects were
            migrated.

        Args:
            target_env (Environment, Connection): Destination environment to
                reverse the migration.
            target_project (Project | str, optional): Project object or ID or
                name specifying the project. May be used instead of
                `target_project_id` or `target_project_name`.
            target_project_id (str, optional): Project ID
            target_project_name (str, optional): Project name
        """
        if isinstance(target_env, Environment):
            target_env = target_env.connection

        target_proj_id = get_project_id_from_params_set(
            target_env,
            target_project,
            target_project_id,
            target_project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        migration_api.update_migration(
            connection=target_env,
            migration_id=self.id,
            body={'importInfo': {'undoRequestStatus': 'requested'}},
            prefer='respond-async',
            project_id=target_proj_id,
        )
        migration_api.update_migration(
            connection=target_env,
            migration_id=self.id,
            body={'importInfo': {'undoRequestStatus': 'approved'}},
            prefer='respond-async',
            project_id=target_proj_id,
        )
        if config.verbose:
            logger.info(f"Successfully reversed migration with ID: '{self.id}'")

    def migrate(
        self,
        target_env: Connection | Environment,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
        generate_undo: bool = True,
    ):
        """Migrate the package to the target environment.
        Project information is required in case of object migration.

        Args:
            target_env (Connection, Environment): Destination environment
                to migrate the package.
            target_project (Project | str, optional): Project object or ID or
                name specifying the project. May be used instead of
                `target_project_id` or `target_project_name`.
            target_project_id (str, optional): Project ID
            target_project_name (str, optional): Project name
            generate_undo (bool, optional): Specify weather to generate an undo
                package or not. True by default.
        """

        if isinstance(target_env, Environment):
            target_env = target_env.connection

        target_proj_id = get_project_id_from_params_set(
            target_env,
            target_project,
            target_project_id,
            target_project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        target_id = Migration._get_env_id(target_env)
        body = {
            "importInfo": {
                "environment": {'id': target_id, 'name': target_id},
                "importRequestStatus": RequestStatus.REQUESTED.value,
            },
        }
        if target_proj_id:
            body['importInfo']['project'] = {
                'id': target_proj_id,
                'name': Project(target_env, id=target_proj_id).name,
            }

        migration_api.update_migration(
            connection=self.connection, migration_id=self.id, body=body
        )
        body['importInfo']['importRequestStatus'] = RequestStatus.APPROVED.value
        migration_api.update_migration(
            connection=self.connection, migration_id=self.id, body=body
        )
        fetched_body = migration_api.get_migration(
            connection=self.connection, migration_id=self.id, show_content='all'
        ).json()
        fetched_body['packageInfo']['replicated'] = True
        response = migration_api.start_migration(
            connection=target_env,
            migration_id=self.id,
            prefer='respond-async',
            generate_undo=generate_undo,
            body=fetched_body,
            project_id=target_proj_id,
        )

        if response.ok and config.verbose:
            logger.info(
                f"Successfully migrated migration '{self.name}' with ID: '{self.id}'"
            )

    def alter_migration_info(
        self,
        name: str | None = None,
        target_env: Connection | Environment | str = None,
        target_project: 'Project | str | None' = None,
        target_project_id: str | None = None,
        target_project_name: str | None = None,
    ) -> None:
        """Alter the migration object info.

        Args:
            name (str, optional): The name of the migration object.
            target_env (Connection | Environment | str, optional): The target
                environment for the migration. It can be a Connection object, an
                Environment object, or a string representing the environment
                    base url.
            target_project (Project | str, optional): The target project for the
                migration. It can be a Project object or a string representing
                the project ID.

        """
        if isinstance(target_env, Environment):
            target_env = target_env.connection

        target_proj_id = get_project_id_from_params_set(
            target_env if isinstance(target_env, Connection) else None,
            target_project,
            target_project_id,
            target_project_name,
            assert_id_exists=False,
            no_fallback_from_connection=True,
        )

        if target_proj_id and isinstance(target_env, Connection):
            target_proj_id = Project(target_env, id=target_proj_id)

        request_body = self._build_body_to_alter_migration_info(
            name=name, target_env=target_env, target_project=target_proj_id
        )
        response = migration_api.update_migration(
            connection=self.connection, migration_id=self.id, body=request_body
        )
        if response.ok and config.verbose:
            logger.info(f"Successfully altered migration object with ID: '{self.id}'")

    @staticmethod
    def _build_body_to_alter_migration_info(
        name: str | None = None,
        target_env: Connection | Environment | str = None,
        target_project: 'Project | str | None' = None,
    ) -> dict:
        request_body = {}
        if name:
            request_body['packageInfo'] = {"name": name}
        if target_env:
            target_id = Migration._get_env_id(target_env)
            request_body['importInfo'] = {
                "environment": {'id': target_id, 'name': target_id}
            }
        if target_project:
            if isinstance(target_project, Project):
                target_project_id = target_project.id
                target_project_name = target_project.name
                request_body['importInfo'] = {
                    "project": {
                        'id': target_project_id,
                        'name': target_project_name,
                    }
                }
            else:
                request_body['importInfo'] = {
                    "project": {
                        'id': target_project,
                    }
                }
        return request_body

    @staticmethod
    def _check_slash_in_id(env_id: str) -> str:
        return env_id if env_id.endswith('/') else f"{env_id}/"

    @staticmethod
    def _get_env_id(env: Connection | Environment | str) -> str:
        if isinstance(env, Connection):
            base_url = env.base_url
        elif isinstance(env, Environment):
            base_url = env.connection.base_url
        else:
            base_url = env

        return Migration._check_slash_in_id(base_url)

    @staticmethod
    def _get_body_for_create(
        connection: 'Connection',
        toc_view: dict,
        tree_view: str,
        name: str | None = None,
    ) -> dict:
        if not name:
            name = Migration._get_new_migration_name()
        env_id = Migration._check_slash_in_id(connection.base_url)
        body = {
            "packageInfo": {
                "name": name,
                "environment": {
                    "id": env_id,
                    "name": env_id,
                },
                "tocView": toc_view,
                "treeView": tree_view,
            },
            "importInfo": {},
        }
        return body

    @staticmethod
    def _get_new_migration_name() -> str:
        return (
            f"New Migration Package {datetime.now().strftime('%m-%d-%Y %I:%M:%S %p')}"
        )

    @staticmethod
    def build_package_config(
        connection: Connection,
        content: list[Object | dict] | SearchObject,
        package_settings: PackageSettings,
        object_action_map: list[tuple] | None = None,
        object_dependents_map: list[tuple] | None = None,
        default_action: Action | None = None,
        default_dependents: bool = False,
    ) -> PackageConfig:
        """
        Build administration or object migration package definition based on the
            provided content.

        Args:
            connection (Connection): A Strategy One connection object.
            content (list[Object | dict] | SearchObject): List of objects to
                migrate or a SearchObject instance.
            package_settings (PackageSettings): Package settings information.
            object_action_map (list[tuple], optional): List of tuples where the
                first element is the object type and the second element is the
                action to perform. If None, default_action will be used.
            object_dependents_map (list[tuple], optional): List of tuples where
                the first element is the object type and the second element is
                the include_dependents flag. If None, default_dependents will be
                used.
            default_action (Action, optional): Default action to apply to the
                list of migration objects passed with the `content` field. When
                an object in the content has the `include_dependents` flag set
                to True, then it's dependents action will be taken from
                `package_settings` field.
                If not provided, the `default_action` from `package_settings`
                will be used.
            default_dependents (bool, optional): Default value for
                include_dependents flag. Defaults to False.

        Returns:
            PackageConfig: A new PackageConfig object.
        """
        default_action = default_action or package_settings.default_action
        content_list = []
        if isinstance(content, SearchObject):
            content = content.run()
        for obj in content:
            if isinstance(obj, dict):
                obj = Object.from_dict(source=obj, connection=connection)
            if object_action_map:
                action = next(
                    (
                        action
                        for obj_type, action in object_action_map
                        if obj.type == obj_type
                    ),
                    default_action,
                )
            else:
                action = default_action
            if object_dependents_map:
                dependents = next(
                    (
                        dependents
                        for obj_type, dependents in object_dependents_map
                        if obj.type == obj_type
                    ),
                    default_dependents,
                )
            else:
                dependents = default_dependents
            content_list.append(
                PackageContentInfo(
                    id=obj.id,
                    type=obj.type,
                    action=action,
                    include_dependents=dependents,
                )
            )
        return PackageConfig(package_settings, content_list)

    @property
    def package_info(self) -> 'PackageInfo':
        return self._package_info

    @property
    def import_info(self) -> 'ImportInfo':
        return self._import_info

    @property
    def validation(self) -> 'Validation':
        self.fetch()
        return self._validation
