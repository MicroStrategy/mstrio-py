from enum import auto
import logging
from typing import List, Optional, Union

from mstrio.api import schema
from mstrio.connection import Connection
from mstrio.utils.entity import auto_match_args_entity
from mstrio.utils.enum_helper import AutoName, get_enum, get_enum_val
from mstrio.utils.helper import Dictable, exception_handler
from mstrio.utils.time_helper import DatetimeFormats, map_str_to_datetime

logger = logging.getLogger(__name__)


class SchemaLockType(AutoName):
    """Enumeration constants used to specify a type of lock that can be placed
    on schema. Type `UNLOCKED` is used only when displaying status.
    """
    ABSOLUTE_INDIVIDUAL = auto()
    EXCLUSIVE_CONSTITUENT = auto()
    ABSOLUTE_CONSTITUENT = auto()
    UNLOCKED = "none"


class SchemaUpdateType(AutoName):
    """Enumeration constants used to specify type of update for the schema."""
    TABLE_KEY = auto()
    ENTRY_LEVEL = auto()
    LOGICAL_SIZE = auto()
    CLEAR_ELEMENT_CACHE = auto()


class SchemaLockStatus(Dictable):
    """An object that contains all of the information about the lock status of
    the schema. If the schema is not locked then properties of the lock are not
    provided."""
    _DELETE_NONE_VALUES_RECURSION = True

    _FROM_DICT_MAP = {
        'lock_type': SchemaLockType,
        'date_created': DatetimeFormats.YMDHMS,
    }

    def __init__(self, lock_type: Union['SchemaLockType', str], date_created: Optional[str] = None,
                 comment: Optional[str] = None, machine_name: Optional[str] = None,
                 owner_name: Optional[str] = None, owner_id: Optional[str] = None):
        """Initialize schema lock status. When schema is unlocked, only its
        `lock_type` is provided.

        Args:
            lock_type (str, enum): a type of lock status that could be returned
                from the schema. The lock state any of the lock types, but it is
                also possible that the schema is not actually locked. Available
                lock types are:
                - `absolute_individual`: When placed no one, including
                  administrator, can perform changes on the schema objects. The
                  purpose of this lock is to prevent accidental modifications to
                  the schema in a project.
                - `exclusive_constituent`: It is a lock exclusive to the
                  changeset holding the lock; only that changeset can change the
                  schema or its constituents (tables, attributes, etc.).
                - `absolute_constituent`: According to REST API documentation
                  this type is currently not in use.
                - `none`: Schema is unlocked.
                `lock_type` can be provided as string or enum `SchemaLockType`.
            date_created (str, optional): The date/time at which this lock was
                placed on the schema.
            comment (str, optional): Optional comment provided by the user that
                applied the lock. If used, this comment may help to justify why
                the schema was locked.
            machine_name (str, optional): Name of the machine used by the user
                that applied the lock.
            owner_name (str, optional): Name of the owner of the lock.
            owner_id (str, optional): ID of the owner of the lock.

        Raises:
            `TypeError` if `lock_type` is neither a string nor
            a `SchemaLockType`.
            `ValueError` if `lock_type` is specified as a string which is not
            a proper value of enum `SchemaLockType`.
        """

        self.lock_type = get_enum(lock_type, SchemaLockType)
        self.date_created = map_str_to_datetime("date_created", date_created, self._FROM_DICT_MAP)
        self.comment = comment
        self.machine_name = machine_name
        self.owner_name = owner_name
        self.owner_id = owner_id


class SchemaTaskStatus(AutoName):
    """Enumeration constants used to specify status of the task."""
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class SchemaTaskError(Dictable):
    """Representation of properties used to report an error related to schema
    task."""
    _DELETE_NONE_VALUES_RECURSION = True

    def __init__(self, code: str, message: str, additional_properties: Optional[dict] = None):
        """Initialize task error.

        Args:
            code (str): Internal application error code.
            message (str): Description of error.
            additional_properties (dict, optional): Additional information
                related to the error (if any).
        """
        self.code = code
        self.message = message
        self.additional_properties = additional_properties


class SchemaTask(Dictable):
    """Detailed information about a task which is performed on the schema."""
    _DELETE_NONE_VALUES_RECURSION = True

    _FROM_DICT_MAP = {
        'status': SchemaTaskStatus,
        'start_time': DatetimeFormats.FULLDATETIME,
        'end_time': DatetimeFormats.FULLDATETIME,
        'errors': [SchemaTaskError]
    }

    def __init__(
        self,
        id: str,
        status: Union[str, SchemaTaskStatus],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        errors: Optional[List[SchemaTaskError]] = None,
    ):
        """Initialize task.

        Args:
            id (str): Task ID.
            status (str, enum): Task status. Possible values are defined in
                enum `SchemaTaskStatus`.
            start_time: (str, optional): The date/time at which the execution
                of task started.
            end_time (str, optional): The date/time at which the task execution
                completed (or failed). This value is not defined when task is
                still running.
            errors: (list, optional): List of errors if the task execution
                failed. Errors are represented by class `SchemaTaskError`.

        Raises:
            `TypeError` if `status` is neither a string nor
            a `SchemaTaskStatus`.
            `ValueError` if `status` is specified as a string which is not
            a proper value of enum `SchemaTaskStatus`.
        """
        self.id = id
        self.status = get_enum(status, SchemaTaskStatus)
        self.start_time = map_str_to_datetime("start_time", start_time, self._FROM_DICT_MAP)
        self.end_time = map_str_to_datetime("end_time", end_time, self._FROM_DICT_MAP)
        self.errors = errors

    def __repr__(self) -> str:
        param_dict = auto_match_args_entity(self.__init__, self,
                                            exclude=['self', 'start_time', 'end_time',
                                                     'errors'], include_defaults=False)

        params = [f'{param}={repr(value)}' for param, value in param_dict.items()]
        formatted_params = ", ".join(params)

        return f"SchemaTask({formatted_params})"


class SchemaManagement:
    """Representation of schema management object.

    Attributes:
        connection: instance of `Connection` object
        lock_type: type of lock which is placed on the schema
        project_id: ID of project on which schema is managed
        tasks: array with objects of type `SchemaTask`. It represents
            tasks which were created for the current object of
            `SchemaManagement`. They are created when schema is reloaded
            asynchronously.
    """

    def __init__(self, connection: "Connection", project_id: Optional[str] = None):
        """Initialize schema management object for the given project.
        If `project_id` is not specified then, it is taken from `connection`
        object.

        Args:
            connection: MicroStrategy connection object returned by
                `connection.Connection()`.
            project_id (optional, str): ID of project on which schema will be
                managed.

        Raises:
            `AttributeError` when `project_id` is not provided and project is
            not selected in the `connection` object.
        """
        self.connection = connection
        if not project_id:
            connection._validate_project_selected()
            project_id = connection.project_id
        self._project_id = project_id
        self._tasks = None
        self._lock_type = None

    def __repr__(self) -> str:
        param_dict = auto_match_args_entity(self.__init__, self, exclude=['self'],
                                            include_defaults=False)
        params = [
            f"{param}" if
            (param == "connection" and isinstance(value, Connection)) else f'{param}={repr(value)}'
            for param, value in param_dict.items()
        ]
        formatted_params = ', '.join(params)

        return f'SchemaManagement({formatted_params})'

    def get_lock_status(self) -> "SchemaLockStatus":
        """Get the lock status of the schema.

        Returns:
            Lock status of the schema as `SchemaLockStatus` object.
        """
        res = schema.read_lock_status(self.connection, self.project_id).json()
        lock_status = SchemaLockStatus.from_dict(res)
        self._lock_type = lock_status.lock_type
        return lock_status

    def lock(self, lock_type: Union[str, "SchemaLockType"]) -> bool:
        """Lock the schema. After successfully locking the schema its
        `lock_type` property is updated.

        Args:
            lock_type: (string or object): Type of lock which will be placed on
                the schema.

        Returns:
            `True` when schema was successfully locked or schema has already
            been locked. `False` when procedure of locking schema failed.

        Raises:
            `TypeError` if `lock_type` is neither a string nor
            a `SchemaLockType`.
            `ValueError` if `lock_type` is specified as a string which is not
            a proper value of enum `SchemaLockType`.
        """
        lock_type = get_enum_val(lock_type, SchemaLockType)

        if self.lock_type != SchemaLockType.UNLOCKED:
            logger.info('Schema is already locked.')
            return True

        res = schema.lock_schema(self.connection, lock_type, self.project_id)
        if res.ok:
            self.get_lock_status()
            return True
        return False

    def unlock(self) -> bool:
        """Unlock the schema. After successfully unlocking the schema its
        `lock_type` property is updated.

        Returns:
            `True` when schema was successfully unlocked or it has already been
            unlocked. `False` when procedure of unlocking schema failed.
        """

        if self.lock_type == SchemaLockType.UNLOCKED:
            logger.info('Schema is already unlocked.')
            return True

        res = schema.unlock_schema(self.connection, project_id=self.project_id, throw_error=False)
        if res.ok:
            self.get_lock_status()
            return True
        return False

    def reload(self, update_types: Optional[Union[List[Union[str, "SchemaUpdateType"]],
                                                  Union[str, "SchemaUpdateType"]]] = None,
               respond_async: bool = True) -> Optional["SchemaTask"]:
        """Reload (update) the schema. This operation can be performed
        asynchronously. In that case the task is created and it is saved in
        property `tasks` to help tracking its status.

        Args:
            update_types (optional, list or object or string): Field with update
                type(s). Values in this field can be of type `string` or
                `SchemaUpdateType` or be a list of those types. This field can
                contain empty, any of the following options, or all of them:
                - `table_key`: Use this option if you changed the key structure
                  of a table.
                - `entry_level`: Use this option if you changed the level at
                  which a fact is stored.
                - `logical_size`: Use this option to recalculate logical table
                  sizes and override any modifications you made to logical table
                  sizes.
                - `clear_element_cache`: Use this option to clear up the
                  attribute element cache saved on the Intelligence Server.
            respond_async (optional, bool): When `True` reload is performed
                asynchronously. Otherwise it is performed synchronously. Default
                value is `True`.

        Returns:
            When `respond_async` is set to `True` then `SchemaTask` object with
            all details about the task of reloading schema is returned.
            Otherwise `None` is returned.

        Raises:
            `TypeError` if any value in `update_types` is neither a string nor
            a `SchemaUpdateType`.
            `ValueError` if any value in `update_types` is specified as a string
            which is not a proper value of enum `SchemaUpdateType`.
        """
        if not update_types:
            update_types = []
        elif not isinstance(update_types, list):
            update_types = [update_types]
        update_types = [get_enum_val(t, SchemaUpdateType) for t in update_types]

        res = schema.reload_schema(self.connection, self.project_id, update_types, respond_async)
        if res.ok and respond_async:
            return self._save_task(res.json())

    def get_task(self, task_index: int) -> "SchemaTask":
        """Get all details of the task which is stored at a given
        `task_index` in a list from property `tasks`.

        Args:
            task_index (int): Index of the task in the list stored in property
                `tasks`.

        Returns:
            `SchemaTask` object with all details about the task from the given
            index. When index is not proper then `None` is returned and warning
            with explanation message is shown.
        """
        try:
            task_id = self.tasks[task_index].id
        except IndexError:
            msg = (f"Cannot get task with index {task_index} from the list of tasks for this "
                   "schema management object. Check the list using property `tasks`.")
            exception_handler(msg, Warning)
            return

        res = schema.read_task_status(self.connection, task_id, self.project_id)
        return self._save_task(res.json())

    def _save_task(self, task_info: dict) -> 'SchemaTask':
        """Helper method to save the task in property `tasks` based on the
        argument `task_info` provided as a dictionary. When task with the given
        id was in the list before, then it is updated and its index in the list
        is not changed. Otherwise task is appended to the list."""
        task = SchemaTask.from_dict(task_info)
        if self._tasks is None:
            self._tasks = [task]
        else:
            # update task if it is already in the list ; otherwise append it
            try:
                index = [t.id for t in self._tasks].index(task.id)
                self._tasks[index] = task
            except ValueError:
                self._tasks.append(task)
        return task

    @property
    def tasks(self):
        """List with tasks created while running `reload` on the given instance
        of `SchemaManagement`."""
        if self._tasks is None:
            self._tasks = []
        return self._tasks

    @property
    def lock_type(self):
        """Current lock type of the schema."""
        if self._lock_type is None:
            self.get_lock_status()
        return self._lock_type

    @property
    def project_id(self):
        """Id of project which is managed by the `SchemaManagement` object."""
        return self._project_id
