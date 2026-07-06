import copy
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import data_models
from mstrio.connection import Connection
from mstrio.helpers import MstrException, MstrTimeoutError
from mstrio.modeling.data_model.data_model_attribute import (
    DataModelAttribute,
    list_data_model_attributes,
)
from mstrio.modeling.data_model.data_model_metric import (
    DataModelFactMetric,
    DataModelMetric,
    list_data_model_fact_metrics,
    list_data_model_metrics,
)
from mstrio.modeling.data_model.data_model_security_filter import (
    DataModelSecurityFilter,
    list_data_model_security_filters,
)
from mstrio.modeling.data_model.data_model_table import (
    DataModelTable,
    list_data_model_tables,
)
from mstrio.modeling.data_model.helpers import (
    DataModelFolder,
    DataModelLink,
    DataModelPublishStatus,
    DataServeMode,
    ExternalDataModel,
    RefreshPolicy,
    unpack_information_dict,
)
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchPattern
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.api_helpers import changeset_manager
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import get_enum_val
from mstrio.utils.helper import (
    Dictable,
    delete_none_values,
    find_object_with_name,
    get_objects_id,
    get_response_json,
)
from mstrio.utils.resolvers import (
    FolderPathType,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.server.project import Project

logger = logging.getLogger(__name__)


@method_version_handler('11.6.0100')
def list_data_models(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    folder: 'Folder | str | FolderPathType | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: FolderPathType | None = None,
    **filters,
) -> list['DataModel'] | list[dict]:
    """Get a list of Mosaic data models.

    Note:
        Data models share the metadata subtype 779 (`report_emma_cube`) with
        classic EMMA super cubes; Mosaic data models are the Modeling-Service
        view of these objects, so classic super cubes may appear in the
        results as well.

    Args:
        connection (Connection): Strategy One connection object returned
            by `connection.Connection()`
        name (str, optional): value the search pattern is set to, which will
            be applied to the names of data models being searched
        to_dictionary (bool, optional): if True, return data models as
            a list of dicts
        limit (int, optional): limit the number of elements returned. If None
            all objects are returned.
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        folder (Folder | str | FolderPathType, optional): Folder object or ID
            or name or path specifying the folder to search in
        folder_id (str, optional): ID of a folder
        folder_name (str, optional): Name of a folder
        folder_path (FolderPathType, optional): Path of the folder. It can be
            a string with "/" as path separator
            (e.g. "folder/subfolder1/subfolder2") or a tuple or list of path
            parts (e.g. `("folder", "subfolder1", "subfolder2")`).
        **filters: Available filter parameters: `id`, `name`, `description`,
            `date_created`, `date_modified`, `version`, `owner`, `acg`,
            `subtype`, `ext_type`

    Returns:
        A list of DataModel objects or dictionaries representing them.
    """
    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )
    validate_owner_key_in_filters(filters)
    objects_ = full_search(
        connection,
        object_types=ObjectSubTypes.SUPER_CUBE,
        project=proj_id,
        name=name,
        pattern=search_pattern,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects_
    return [
        DataModel.from_dict(source=obj_, connection=connection, with_missing_value=True)
        for obj_ in objects_
    ]


@class_version_handler('11.6.0100')
class DataModel(Entity, CopyMixin, MoveMixin, DeleteMixin):
    """Python representation of a Mosaic Data Model object.

    Data model definitions are managed through the changeset-scoped
    Modeling-Service endpoints (`/api/model/dataModels/...`), while
    publishing, attribute elements and security-filter members use the
    runtime endpoints (`/api/dataModels/...`). A 404 on one path shape
    usually means the other shape was intended.

    Attributes:
        id: data model's ID
        name: data model's name
        description: data model's description
        sub_type: string literal used to identify the type of a metadata
            object
        data_serve_mode: mode in which the data model serves data,
            DataServeMode enum
        schema_folder_id: the schema folder ID where data model objects are
            stored
        type: object type, ObjectTypes enum
        subtype: object subtype, ObjectSubTypes enum
        date_created: creation time, DateTime object
        date_modified: last modification time, DateTime object
        owner: User object that is the owner
        acg: access rights
        acl: object access control list
        hidden: specifies whether the object is hidden
    """

    _OBJECT_TYPE = ObjectTypes.REPORT_DEFINITION
    _OBJECT_SUBTYPES = [ObjectSubTypes.SUPER_CUBE]
    _API_GETTERS = {
        (
            'id',
            'sub_type',
            'name',
            'description',
            'data_serve_mode',
            'schema_folder_id',
            'enable_wrangle_recommendations',
            'enable_auto_hierarchy_relationships',
            'sampling',
            'partition',
            'auto_join',
        ): data_models.get_data_model,
        (
            'abbreviation',
            'type',
            'subtype',
            'ext_type',
            'date_created',
            'date_modified',
            'version',
            'owner',
            'icon_path',
            'view_media',
            'ancestors',
            'certified_info',
            'acg',
            'acl',
            'target_info',
            'hidden',
            'comments',
        ): objects_processors.get_info,
    }
    _API_PATCH = {
        (
            'name',
            'description',
            'data_serve_mode',
            'destination_folder_id',
        ): (data_models.update_data_model, 'partial_put'),
        (
            'comments',
            'owner',
            'hidden',
            'folder_id',
        ): (objects_processors.update, 'partial_put'),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'data_serve_mode': DataServeMode,
    }

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize DataModel object by passing `id` or `name`.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            id (str, optional): ID of the data model
            name (str, optional): name of the data model

        Note:
            Parameter `name` is not used when fetching. If only `name`
            parameter is provided, `id` will be found automatically if such
            object exists.

        Raises:
            ValueError: if both `id` and `name` are not provided or if
                DataModel with the given `name` doesn't exist.
        """
        if id is None:
            if name is None:
                raise ValueError("Please specify either 'name' or 'id'.")
            data_model = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=list_data_models,
                search_pattern=SearchPattern.EXACTLY,
            )
            id = data_model['id']
        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self._sub_type = kwargs.get('sub_type', default_value)
        data_serve_mode = kwargs.get('data_serve_mode')
        self._data_serve_mode = (
            DataServeMode(data_serve_mode)
            if isinstance(data_serve_mode, str)
            else data_serve_mode
        ) or default_value
        self._schema_folder_id = kwargs.get('schema_folder_id', default_value)
        self._enable_wrangle_recommendations = kwargs.get(
            'enable_wrangle_recommendations', default_value
        )
        self._enable_auto_hierarchy_relationships = kwargs.get(
            'enable_auto_hierarchy_relationships', default_value
        )
        self._sampling = kwargs.get('sampling', default_value)
        self._partition = kwargs.get('partition', default_value)
        self._auto_join = kwargs.get('auto_join', default_value)

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        destination_folder: Folder | str,
        data_serve_mode: DataServeMode | str = DataServeMode.CONNECT_LIVE,
        description: str | None = None,
        tables: list[dict] | None = None,
        attributes: list[dict] | None = None,
    ) -> 'DataModel':
        """Create a new Mosaic data model.

        Note:
            Servers enforce a minimum committable model (field-verified):
            the creation changeset must contain at least one table (error
            8004e46f otherwise), every table must end up with at least one
            attribute or metric (error 8004e42f), and every attribute must
            carry `displays` (error 8004cf06). Provide `tables` and
            `attributes` together so the whole minimum shape is committed
            in one changeset.

        Args:
            connection (Connection): Strategy One connection object returned
                by `connection.Connection()`
            name (str): name of the data model
            destination_folder (Folder | str): Folder object or folder ID
                where the data model will be created
            data_serve_mode (DataServeMode | str, optional): mode in which
                the data model serves data, defaults to
                `DataServeMode.CONNECT_LIVE`
            description (str, optional): description of the data model
            tables (list[dict], optional): definitions of logical tables to
                add to the data model inside the same (creation) changeset;
                each entry is an `ms-DataModelTableAdd` dict (`name`,
                `physicalTable`, `refreshPolicy`, ...)
            attributes (list[dict], optional): attribute definitions created
                inside the same changeset, after the tables. Each entry is an
                attribute body (`information`, `forms`, `keyForm`, `displays`,
                `attributeLookupTable`, ...). Anywhere the body references a
                logical table — `lookupTable`, `attributeLookupTable` or an
                entry of a form expression's `tables` list — the name of a
                table created in this call may be passed as a plain string
                (or as a ref dict without `objectId`); it is resolved to the
                new table's reference automatically.

        Returns:
            DataModel object.
        """
        folder_id = get_objects_id(destination_folder, Folder)
        body = {
            'name': name,
            'description': description,
            'destinationFolderId': folder_id,
            'dataServeMode': get_enum_val(data_serve_mode, DataServeMode),
        }
        body = delete_none_values(body, recursion=False)
        if tables is not None:
            with changeset_manager(connection, body=body) as changeset_id:
                response = data_models.create_data_model(
                    connection, body=body, changeset_id=changeset_id
                ).json()
                new_id = response.get('id')
                table_refs = {}
                for table_body in tables:
                    created = data_models.create_data_model_table(
                        connection, new_id, table_body, changeset_id=changeset_id
                    ).json()
                    table_id = created.get('id') or created.get('information', {}).get(
                        'objectId'
                    )
                    table_name = created.get('name') or created.get(
                        'information', {}
                    ).get('name')
                    ref = {
                        'objectId': table_id,
                        'subType': 'logical_table',
                        'name': table_name,
                    }
                    table_refs[table_name] = ref
                    if table_body.get('name'):
                        table_refs[table_body['name']] = ref
                for attribute_body in attributes or []:
                    data_models.create_data_model_attribute(
                        connection,
                        new_id,
                        cls._resolve_table_refs(attribute_body, table_refs),
                        changeset_id=changeset_id,
                    )
            if config.verbose:
                logger.info(
                    f"Successfully created data model named: '{name}' with ID: '"
                    f"{new_id}'"
                )
            return cls(connection, id=new_id)
        response = data_models.create_data_model(connection, body=body).json()
        if config.verbose:
            logger.info(
                f"Successfully created data model named: '{name}' with ID: '"
                f"{response.get('id')}'"
            )
        return cls.from_dict(source=response, connection=connection)

    @classmethod
    def _resolve_table_refs(cls, attribute_body: dict, table_refs: dict) -> dict:
        """Replace by-name logical-table references in an attribute body with
        the full references of tables created in the same changeset.

        A reference is resolved when it is a plain string naming a created
        table, or a dict without an 'objectId' whose 'name' matches one.
        """

        def resolve(node):
            if isinstance(node, str) and node in table_refs:
                return table_refs[node]
            if isinstance(node, dict):
                if not node.get('objectId') and node.get('name') in table_refs:
                    return table_refs[node['name']]
                return node
            return node

        body = copy.deepcopy(attribute_body)
        for key in ('attributeLookupTable',):
            if key in body:
                body[key] = resolve(body[key])
        for form in body.get('forms', []):
            if 'lookupTable' in form:
                form['lookupTable'] = resolve(form['lookupTable'])
            for expression in form.get('expressions', []):
                if 'tables' in expression:
                    expression['tables'] = [
                        resolve(table) for table in expression['tables']
                    ]
        return body

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        data_serve_mode: DataServeMode | str | None = None,
        comments: str | None = None,
        owner: str | User | None = None,
    ) -> None:
        """Alter the data model's properties.

        Args:
            name (str, optional): new name of the data model
            description (str, optional): new description of the data model
            data_serve_mode (DataServeMode | str, optional): new data serve
                mode
            comments (str, optional): long description of the data model
            owner (str | User, optional): new owner of the data model
        """
        if isinstance(owner, User):
            owner = owner.id
        if data_serve_mode is not None:
            data_serve_mode = get_enum_val(data_serve_mode, DataServeMode)
        properties = {
            'name': name,
            'description': description,
            'data_serve_mode': data_serve_mode,
            'comments': comments,
            'owner': owner,
        }
        self._alter_properties(**delete_none_values(properties, recursion=False))

    def save_as(
        self, name: str, destination_folder: Folder | str | None = None
    ) -> 'DataModel':
        """Save a copy of the data model under a new name.

        Args:
            name (str): name of the new data model
            destination_folder (Folder | str, optional): Folder object or
                folder ID where the copy will be saved

        Returns:
            DataModel object representing the newly created copy.
        """
        body = {'name': name}
        if destination_folder:
            body['destinationFolderId'] = get_objects_id(destination_folder, Folder)
        response = data_models.save_data_model_as(
            self.connection, id=self.id, body=body
        )
        data = response.json()
        new_id = (
            data.get('objectId') or data.get('id') if isinstance(data, dict) else data
        )
        if config.verbose:
            logger.info(
                f"Successfully saved data model as: '{name}' with ID: '" f"{new_id}'"
            )
        return DataModel(connection=self.connection, id=new_id)

    def to_yaml(self, path: str | Path | None = None) -> str:
        """Export the data model definition to YAML.

        Args:
            path (str | Path, optional): if provided, the YAML text is also
                written to this file

        Returns:
            The YAML definition of the data model as a string.
        """
        response = data_models.export_data_model(self.connection, id=self.id)
        text = response.text
        if path:
            Path(path).write_text(text, encoding='utf-8')
            if config.verbose:
                logger.info(
                    f"Successfully exported data model with ID: '{self.id}' "
                    f"to '{path}'."
                )
        return text

    def restore_from_yaml(self, file: str | Path | bytes) -> bool:
        """Restore the data model definition from a YAML export.

        Args:
            file (str | Path | bytes): path to a YAML file, or the YAML
                content itself as bytes

        Returns:
            True on success. False otherwise.
        """
        if isinstance(file, bytes):
            data, file_name = file, 'data_model.yaml'
        else:
            path = Path(file)
            data, file_name = path.read_bytes(), path.name
        response = data_models.restore_data_model(
            self.connection, id=self.id, file=data, file_name=file_name
        )
        if response.ok:
            if config.verbose:
                logger.info(
                    f"Successfully restored data model with ID: '{self.id}' "
                    f"from '{file_name}'."
                )
            self.fetch()
        return response.ok

    # Publishing

    def create_instance(self, show_invalid_cache_table_ids: bool = False) -> str:
        """Create a new data model instance used for publishing.

        Note:
            The endpoint returns 204 with NO body; the new instance ID is
            returned only in the `X-MSTR-DataModelInstanceId` response
            header. Instance IDs expire after roughly 2 minutes (a 404
            ERR004 on `get_publish_status` means the instance must be minted
            again).

        Args:
            show_invalid_cache_table_ids (bool, optional): whether to report
                invalid cache table IDs

        Returns:
            ID of the created instance (str).
        """
        response = data_models.create_data_model_instance(
            self.connection,
            id=self.id,
            show_invalid_cache_table_ids=show_invalid_cache_table_ids,
        )
        return response.headers['X-MSTR-DataModelInstanceId']

    def delete_instance(self, instance_id: str) -> bool:
        """Delete a data model instance.

        Args:
            instance_id (str): ID of the instance to delete

        Returns:
            True on success. False otherwise.
        """
        response = data_models.delete_data_model_instance(
            self.connection, id=self.id, instance_id=instance_id
        )
        return response.ok

    def get_publish_status(self, instance_id: str) -> DataModelPublishStatus:
        """Get the publish status of a data model instance.

        Args:
            instance_id (str): ID of the instance returned by
                `create_instance()` / `publish(await_completion=False)`

        Returns:
            DataModelPublishStatus object. Publishing succeeded only when
            the top-level `status` is 0 and every table's status is
            `loaded`.
        """
        response = data_models.get_publish_status(
            self.connection, id=self.id, instance_id=instance_id
        )
        return DataModelPublishStatus.from_dict(response.json())

    def publish(
        self,
        refresh_policy: RefreshPolicy | str = RefreshPolicy.REPLACE,
        tables: list['str | DataModelTable'] | None = None,
        await_completion: bool = True,
        timeout: int = 600,
        polling_interval: int = 5,
    ) -> DataModelPublishStatus | str:
        """Publish the data model (create instance, trigger publish, poll).

        Note (field-verified behavior):
            - The publish POST returns 204 and is FIRE-AND-FORGET - never
              report success without polling `get_publish_status`.
            - Every logical table must be listed in the refresh settings;
              an empty table list returns 400 "tableRefreshSettings cannot
              be null". When `tables` is None all tables are enumerated
              automatically.
            - Instance IDs expire after ~2 minutes; a 404 ERR004 on the
              status poll means a new instance must be minted and publish
              re-triggered.
            - A top-level status of `-2147212544` indicates a tenant-side
              QueryEngine stall - do NOT retry in a loop; fall back to the
              `connect_live` data serve mode instead.
            - Publish silently no-ops when physical-table columns carry
              warehouse-catalog sentinel dataTypes (precision -1 / scale
              -MIN_INT).
            - The per-instance status can remain `1` (queued/running) even
              after the cube has finished loading — notably when a second
              publish is triggered while one is already running. On a
              timeout (`MstrTimeoutError`), cross-check the authoritative
              cube state via `mstrio.api.cubes.status` (the
              'X-MSTR-CubeStatus' response header) before re-publishing.
            - `connect_live` data models have no publish workflow — the
              server rejects the publish trigger with ERR006.

        Args:
            refresh_policy (RefreshPolicy | str, optional): refresh policy
                applied to all tables, defaults to `RefreshPolicy.REPLACE`
            tables (list, optional): list of `DataModelTable` objects or
                table IDs to publish; if None, ALL tables of the data model
                are published
            await_completion (bool, optional): if True (default), poll the
                publish status until success, error or timeout
            timeout (int, optional): maximum seconds to wait, default 600
            polling_interval (int, optional): seconds between status polls,
                default 5

        Returns:
            DataModelPublishStatus on success when `await_completion` is
            True; the instance ID (str) when `await_completion` is False.

        Raises:
            MstrException: on publish error or timeout.
        """
        policy = get_enum_val(refresh_policy, RefreshPolicy)
        instance_id = self.create_instance()
        if tables is None:
            table_ids = [
                unpack_information_dict(table).get('id')
                for table in data_models.list_data_model_tables(
                    self.connection, id=self.id
                )
                .json()
                .get('tables', [])
            ]
        else:
            table_ids = [
                table.id if isinstance(table, DataModelTable) else table
                for table in tables
            ]
        body = {
            'tables': [
                {'id': table_id, 'refreshPolicy': policy} for table_id in table_ids
            ]
        }
        data_models.publish_data_model(
            self.connection, id=self.id, instance_id=instance_id, body=body
        )
        if not await_completion:
            return instance_id
        start = time.time()
        while True:
            status = self.get_publish_status(instance_id)
            if status.status == 0:
                if config.verbose:
                    logger.info(
                        f"Successfully published data model with ID: '" f"{self.id}'."
                    )
                return status
            failed_tables = [
                table for table in (status.tables or []) if table.status == 'error'
            ]
            if (status.status is not None and status.status < 0) or failed_tables:
                raise MstrException(
                    {
                        'code': status.status,
                        'message': (
                            f"Error publishing data model with ID: '{self.id}'. "
                            f"Status: {status.to_dict()}"
                        ),
                    }
                )
            if time.time() - start > timeout:
                raise MstrTimeoutError(
                    {
                        'message': (
                            f"Timeout ({timeout}s) while publishing data model "
                            f"with ID: '{self.id}'. "
                            f"Last status: {status.to_dict()}"
                        )
                    }
                )
            time.sleep(polling_interval)

    def get_hierarchy(self) -> dict:
        """Get the system hierarchy of the data model.

        Returns:
            Dictionary with the hierarchy definition
            (`ms-DataModelHierarchy` schema).
        """
        return data_models.get_data_model_hierarchy(self.connection, id=self.id).json()

    # Folders

    def list_folders(
        self,
        offset: int | None = None,
        limit: int | None = None,
        to_dictionary: bool = False,
    ) -> list[DataModelFolder] | list[dict]:
        """List folders of the data model.

        Args:
            offset (int, optional): starting point within the collection
            limit (int, optional): limit the number of elements returned
            to_dictionary (bool, optional): if True, return folders as
                a list of dicts

        Returns:
            A list of DataModelFolder objects or dictionaries representing
            them.
        """
        folders = (
            data_models.list_data_model_folders(
                self.connection, id=self.id, offset=offset, limit=limit
            )
            .json()
            .get('folders', [])
        )
        if to_dictionary:
            return folders
        return [DataModelFolder.from_dict(folder) for folder in folders]

    def create_folder(
        self, name: str, destination_folder_id: str | None = None
    ) -> DataModelFolder:
        """Create a new folder inside the data model.

        Args:
            name (str): name of the folder
            destination_folder_id (str, optional): ID of the parent folder
                inside the data model

        Returns:
            DataModelFolder object.
        """
        information = delete_none_values(
            {'name': name, 'destinationFolderId': destination_folder_id},
            recursion=False,
        )
        response = data_models.create_data_model_folder(
            self.connection, id=self.id, body={'information': information}
        )
        if config.verbose:
            logger.info(
                f"Successfully created folder named: '{name}' in data model "
                f"with ID: '{self.id}'."
            )
        return DataModelFolder.from_dict(get_response_json(response))

    def get_folder(self, folder_id: str) -> DataModelFolder:
        """Get a folder of the data model.

        Args:
            folder_id (str): ID of the folder

        Returns:
            DataModelFolder object.
        """
        response = data_models.get_data_model_folder(
            self.connection, id=self.id, folder_id=folder_id
        )
        return DataModelFolder.from_dict(response.json())

    def alter_folder(
        self,
        folder_id: str,
        name: str | None = None,
        destination_folder_id: str | None = None,
    ) -> DataModelFolder:
        """Alter a folder of the data model (rename or move).

        Args:
            folder_id (str): ID of the folder to alter
            name (str, optional): new name of the folder
            destination_folder_id (str, optional): ID of the new parent
                folder

        Returns:
            DataModelFolder object after the update.
        """
        information = delete_none_values(
            {'name': name, 'destinationFolderId': destination_folder_id},
            recursion=False,
        )
        response = data_models.update_data_model_folder(
            self.connection,
            id=self.id,
            folder_id=folder_id,
            body={'information': information},
        )
        return DataModelFolder.from_dict(get_response_json(response))

    def delete_folder(self, folder_id: str) -> bool:
        """Delete a folder of the data model.

        Args:
            folder_id (str): ID of the folder to delete

        Returns:
            True on success. False otherwise.
        """
        response = data_models.delete_data_model_folder(
            self.connection, id=self.id, folder_id=folder_id
        )
        if response.ok and config.verbose:
            logger.info(
                f"Successfully deleted folder with ID: '{folder_id}' from "
                f"data model with ID: '{self.id}'."
            )
        return response.ok

    # Links

    def list_links(
        self,
        offset: int | None = None,
        limit: int | None = None,
        to_dictionary: bool = False,
    ) -> list[DataModelLink] | list[dict]:
        """List links of the data model.

        Args:
            offset (int, optional): starting point within the collection
            limit (int, optional): limit the number of elements returned
            to_dictionary (bool, optional): if True, return links as a list
                of dicts

        Returns:
            A list of DataModelLink objects or dictionaries representing
            them.
        """
        links = (
            data_models.list_data_model_links(
                self.connection, id=self.id, offset=offset, limit=limit
            )
            .json()
            .get('links', [])
        )
        if to_dictionary:
            return links
        return [DataModelLink.from_dict(link) for link in links]

    def create_link(self, link: dict | DataModelLink) -> DataModelLink:
        """Create a new link in the data model.

        Args:
            link (dict | DataModelLink): link definition
                (`ms-DataModelLink` schema)

        Returns:
            DataModelLink object.
        """
        body = link.to_dict() if isinstance(link, DataModelLink) else link
        response = data_models.create_data_model_link(
            self.connection, id=self.id, body=body
        )
        if config.verbose:
            logger.info(
                f"Successfully created link in data model with ID: '" f"{self.id}'."
            )
        return DataModelLink.from_dict(get_response_json(response))

    def update_links(self, links: list[dict | DataModelLink]) -> list[DataModelLink]:
        """Update the links of the data model.

        Note:
            The underlying endpoint is a PUT which REPLACES ALL links of the
            data model. Omitting existing links DELETES them. Always read
            the current list with `list_links()`, modify it and send the
            full list back.

        Args:
            links (list): full list of link definitions (dicts or
                `DataModelLink` objects)

        Returns:
            A list of DataModelLink objects after the update.
        """
        body = {
            'links': [
                link.to_dict() if isinstance(link, Dictable) else link for link in links
            ]
        }
        response = data_models.update_data_model_links(
            self.connection, id=self.id, body=body
        )
        return [
            DataModelLink.from_dict(link)
            for link in get_response_json(response).get('links', [])
        ]

    # External data models

    def list_external_data_models(
        self, to_dictionary: bool = False
    ) -> list[ExternalDataModel] | list[dict]:
        """List external data models referenced by the data model.

        Args:
            to_dictionary (bool, optional): if True, return external data
                models as a list of dicts

        Returns:
            A list of ExternalDataModel objects or dictionaries representing
            them.
        """
        external = (
            data_models.list_external_data_models(self.connection, id=self.id)
            .json()
            .get('externalDataModels', [])
        )
        if to_dictionary:
            return external
        return [ExternalDataModel.from_dict(edm) for edm in external]

    def add_external_data_model(
        self,
        base_data_model: 'DataModel | str | dict',
        alias: str | None = None,
        objects: list | None = None,
    ) -> ExternalDataModel:
        """Reference another data model as an external data model.

        Args:
            base_data_model (DataModel | str | dict): the base data model as
                an object, its ID, or a full `ms-ObjectInfoReference` dict
            alias (str, optional): alias of the external data model
            objects (list, optional): external data model units
                (`ms-ExternalDataModelUnit` schema)

        Returns:
            ExternalDataModel object.
        """
        if isinstance(base_data_model, dict):
            base_reference = base_data_model
        else:
            base_id = (
                base_data_model.id
                if isinstance(base_data_model, DataModel)
                else base_data_model
            )
            base_reference = {
                'objectId': base_id,
                'subType': 'report_emma_cube',
            }
        body = delete_none_values(
            {
                'baseDataModel': base_reference,
                'alias': alias,
                'objects': objects,
            },
            recursion=False,
        )
        response = data_models.create_external_data_model(
            self.connection, id=self.id, body=body
        )
        if config.verbose:
            logger.info(
                f"Successfully added external data model to data model with "
                f"ID: '{self.id}'."
            )
        return ExternalDataModel.from_dict(get_response_json(response))

    def remove_external_data_model(self, external_data_model_id: str) -> bool:
        """Remove an external data model reference.

        Args:
            external_data_model_id (str): ID of the external data model

        Returns:
            True on success. False otherwise.
        """
        response = data_models.delete_external_data_model(
            self.connection,
            id=self.id,
            external_data_model_id=external_data_model_id,
        )
        if response.ok and config.verbose:
            logger.info(
                f"Successfully removed external data model with ID: '"
                f"{external_data_model_id}' from data model with ID: '"
                f"{self.id}'."
            )
        return response.ok

    def alter_external_data_model(
        self, external_data_model_id: str, body: dict
    ) -> ExternalDataModel:
        """Alter an external data model reference (partial update).

        Args:
            external_data_model_id (str): ID of the external data model
            body (dict): changes to apply (`ms-ExternalDataModel` schema)

        Returns:
            ExternalDataModel object after the update.
        """
        response = data_models.update_external_data_model(
            self.connection,
            id=self.id,
            external_data_model_id=external_data_model_id,
            body=body,
        )
        return ExternalDataModel.from_dict(get_response_json(response))

    def alter_external_data_model_object(
        self, external_data_model_id: str, object_id: str, body: dict
    ) -> dict:
        """Alter a single object of an external data model reference.

        Args:
            external_data_model_id (str): ID of the external data model
            object_id (str): ID of the object to alter
            body (dict): changes to apply (`ms-ExternalDataModelUnit` schema)

        Returns:
            Dictionary with the updated object definition.
        """
        response = data_models.update_external_data_model_object(
            self.connection,
            id=self.id,
            external_data_model_id=external_data_model_id,
            object_id=object_id,
            body=body,
        )
        return get_response_json(response)

    def refresh_external_data_models(self) -> dict:
        """Refresh all external data model references of the data model.

        Returns:
            Dictionary with the refreshed external data models and any
            invalid links or objects.
        """
        response = data_models.refresh_external_data_models(self.connection, id=self.id)
        return get_response_json(response)

    # Object governance (ACLs and translations)

    def get_object_acl(self, object_id: str, sub_type: str) -> dict:
        """Get the ACL of an object living inside the data model.

        Note:
            The endpoint returns a 500 error when `sub_type` is missing and
            silently returns a consistent-but-wrong facet when the subtype
            is wrong - always pass the object's true subtype (e.g.
            'attribute', 'metric', 'fact_metric', 'logical_table',
            'md_security_filter').

        Args:
            object_id (str): ID of the object inside the data model
            sub_type (str): subtype of the object

        Returns:
            Dictionary with the object's ACL definition.
        """
        return data_models.get_data_model_object_acl(
            self.connection, id=self.id, object_id=object_id, sub_type=sub_type
        ).json()

    def update_object_acl(self, object_id: str, sub_type: str, acl: dict) -> dict:
        """Update the ACL of an object living inside the data model.

        Note:
            The update is a WHOLESALE REPLACEMENT: trustees omitted from
            `acl` lose their entries. The rights mask `255` is the server's
            magic "Full Control" value (do not decompose it from flag
            names). A wrong `sub_type` silently patches the wrong facet.

        Args:
            object_id (str): ID of the object inside the data model
            sub_type (str): subtype of the object
            acl (dict): mapping of trustee ID to rights definition, e.g.
                `{'<trusteeId>': {'granted': 255, 'denied': 0,
                'subType': 'user', 'inheritable': True}}`. May also be
                passed already wrapped as `{'acl': {...}}`.

        Returns:
            Dictionary with the updated ACL definition.
        """
        body = acl if 'acl' in acl else {'acl': acl}
        return data_models.update_data_model_object_acl(
            self.connection,
            id=self.id,
            object_id=object_id,
            sub_type=sub_type,
            body=body,
        ).json()

    def get_object_translations(self, object_id: str, sub_type: str) -> dict:
        """Get the translations of an object living inside the data model.

        Args:
            object_id (str): ID of the object inside the data model
            sub_type (str): subtype of the object

        Returns:
            Dictionary with the object's translations.
        """
        return data_models.get_data_model_object_translations(
            self.connection, id=self.id, object_id=object_id, sub_type=sub_type
        ).json()

    def update_object_translations(
        self, object_id: str, sub_type: str, translations: dict
    ) -> dict:
        """Update the translations of an object living inside the data model.

        Args:
            object_id (str): ID of the object inside the data model
            sub_type (str): subtype of the object
            translations (dict): translations definition to send

        Returns:
            Dictionary with the updated translations.
        """
        return data_models.update_data_model_object_translations(
            self.connection,
            id=self.id,
            object_id=object_id,
            sub_type=sub_type,
            body=translations,
        ).json()

    # Security filters (runtime collection)

    def list_active_security_filters(
        self,
        offset: int | None = None,
        limit: int | None = None,
        to_dictionary: bool = False,
    ) -> list[DataModelSecurityFilter] | list[dict]:
        """List active security filters of the data model (runtime
        endpoint).

        Args:
            offset (int, optional): starting point within the collection
            limit (int, optional): limit the number of elements returned
            to_dictionary (bool, optional): if True, return security filters
                as a list of dicts

        Returns:
            A list of DataModelSecurityFilter objects or dictionaries
            representing them.
        """
        security_filters = (
            data_models.list_active_security_filters(
                self.connection, id=self.id, offset=offset, limit=limit
            )
            .json()
            .get('securityFilters', [])
        )
        if to_dictionary:
            return security_filters
        return [
            DataModelSecurityFilter.from_dict(
                source={**sf, 'data_model_id': self.id},
                connection=self.connection,
            )
            for sf in security_filters
        ]

    # Component listing conveniences

    def list_tables(
        self, to_dictionary: bool = False, **kwargs
    ) -> list[DataModelTable] | list[dict]:
        """List tables of the data model. See
        `mstrio.modeling.data_model.list_data_model_tables` for the full
        parameter list."""
        return list_data_model_tables(
            self.connection, data_model=self.id, to_dictionary=to_dictionary, **kwargs
        )

    def list_attributes(
        self, to_dictionary: bool = False, **kwargs
    ) -> list[DataModelAttribute] | list[dict]:
        """List attributes of the data model. See
        `mstrio.modeling.data_model.list_data_model_attributes` for the full
        parameter list."""
        return list_data_model_attributes(
            self.connection, data_model=self.id, to_dictionary=to_dictionary, **kwargs
        )

    def list_metrics(
        self, to_dictionary: bool = False, **kwargs
    ) -> list[DataModelMetric] | list[dict]:
        """List metrics of the data model. See
        `mstrio.modeling.data_model.list_data_model_metrics` for the full
        parameter list."""
        return list_data_model_metrics(
            self.connection, data_model=self.id, to_dictionary=to_dictionary, **kwargs
        )

    def list_fact_metrics(
        self, to_dictionary: bool = False, **kwargs
    ) -> list[DataModelFactMetric] | list[dict]:
        """List fact metrics of the data model. See
        `mstrio.modeling.data_model.list_data_model_fact_metrics` for the
        full parameter list."""
        return list_data_model_fact_metrics(
            self.connection, data_model=self.id, to_dictionary=to_dictionary, **kwargs
        )

    def list_security_filters(
        self, to_dictionary: bool = False, **kwargs
    ) -> list[DataModelSecurityFilter] | list[dict]:
        """List security filters of the data model (Modeling-Service
        collection). See
        `mstrio.modeling.data_model.list_data_model_security_filters` for
        the full parameter list."""
        return list_data_model_security_filters(
            self.connection, data_model=self.id, to_dictionary=to_dictionary, **kwargs
        )

    # Properties

    @property
    def sub_type(self) -> str | None:
        """String literal identifying the metadata subtype of the object."""
        return self._sub_type

    @property
    def data_serve_mode(self) -> DataServeMode | None:
        """Mode in which the data model serves data."""
        return self._data_serve_mode

    @property
    def schema_folder_id(self) -> str | None:
        """The schema folder ID where data model objects are stored."""
        return self._schema_folder_id

    @property
    def enable_wrangle_recommendations(self) -> bool | None:
        """Whether wrangle recommendations are enabled."""
        return self._enable_wrangle_recommendations

    @property
    def enable_auto_hierarchy_relationships(self) -> bool | None:
        """Whether automatic hierarchy relationships are enabled."""
        return self._enable_auto_hierarchy_relationships

    @property
    def sampling(self) -> dict | None:
        """Sampling settings of the data model."""
        return self._sampling

    @property
    def partition(self) -> dict | None:
        """Partition settings of the data model."""
        return self._partition

    @property
    def auto_join(self) -> bool | None:
        """Whether tables without user-defined relationships are joined
        automatically using common attributes."""
        return self._auto_join
