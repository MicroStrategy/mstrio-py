import datetime as dt
import logging
import time
from copy import copy
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Literal, overload

from mstrio import config
from mstrio.distribution_services import Schedule
from mstrio.distribution_services.schedule.schedule_time import UnixTimeZone
from mstrio.python_execution.script import (
    Script,
    ScriptError,
    ScriptExecutionError,
    ScriptSetupError,
    VariablesAnswers,
)
from mstrio.server.node import Node
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import EntityBase
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable, _prepare_objects, delete_none_values
from mstrio.utils.resolvers import validate_content_key_in_filters
from mstrio.utils.response_processors import tasks as tasks_processor
from mstrio.utils.time_helper import DatetimeFormats, map_str_to_datetime

if TYPE_CHECKING:
    from mstrio.connection import Connection


logger = logging.getLogger(__name__)


# region Helpers


# TODO: Inherit from `IntEnum` with Python 3.11
class ActiveState(Enum):
    INACTIVE = 0
    ACTIVE = 1
    UNKNOWN = 2

    def __int__(self):
        return self.value

    def __eq__(self, value):
        try:
            return int(self) == int(value) or super().__eq__(value)
        except (TypeError, ValueError):
            return super().__eq__(value)


class _TaskType(AutoName):
    INVALID = auto()
    WORKFLOW = auto()
    SCRIPT = auto()


@dataclass(frozen=True)
class LastRunData(Dictable):
    """Data class representing the last run information of a Planned Task."""

    class TaskRunStatus(AutoName):
        RESERVE = auto()
        RUNNING = auto()
        FAILED = auto()
        SUCCESS = auto()
        TIMEOUT = auto()

    status: TaskRunStatus
    time_triggered: dt.datetime | str
    trigger_user: 'User'
    message: str | None = None
    time_finished: dt.datetime | str | None = None
    node: 'Node | str | None' = None

    @staticmethod
    def _node_from_name(name: str | None, conn: 'Connection') -> 'Node | str | None':
        try:
            return conn.environment.list_nodes(node_name=name)[0]
        except Exception:
            return name

    _FROM_DICT_MAP = {
        "status": TaskRunStatus,
        "trigger_user": User.from_dict,
        "node": _node_from_name,
        "time_triggered": DatetimeFormats.FULLDATETIME,
        "time_finished": DatetimeFormats.FULLDATETIME,
    }
    _ALLOW_NONE_ATTRIBUTES = ["message", "time_finished"]

    @classmethod
    def _preparsed_from_dict(
        cls, source: dict | None, connection: 'Connection'
    ) -> 'LastRunData | None':
        if source is None:
            return None

        result = copy(source)
        result["trigger_user"] = {
            "id": result.pop("trigger_user_id", None),
            "username": result.pop("trigger_user_name", None),
        }

        return cls.from_dict(result, connection)


# endregion


# region Implementation


def list_tasks(
    connection: 'Connection',
    schedule: 'Schedule | str | None' = None,
    limit: int | None = None,
    to_dictionary: bool = False,
    **filters,
) -> 'list[dict] | list[Task]':
    """Get a list of Planned Tasks.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        schedule (Schedule | str | None, optional): Schedule object, ID or name
            to filter tasks by.
        limit (int, optional): Maximum number of tasks to return.
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns Task objects.
        **filters: Available filter parameters: ['id', 'type', 'active', 'name',
            'date_created', 'date_modified', 'script'].

    Returns:
        list[dict] | list[Task]: List of tasks as dicts or as
            Task objects.
    """

    if "script" in filters:
        filters["content"] = filters.pop("script")

    validate_content_key_in_filters(filters)

    tasks_data = tasks_processor.list_tasks(
        connection=connection,
        schedule_id=(
            Schedule._get_id_from_any_param(value=schedule, connection=connection)
            if schedule is not None
            else None
        ),
        limit=limit,
    )
    tasks_data = _prepare_objects(tasks_data, filters=filters)

    if to_dictionary:
        return tasks_data

    return [Task.from_dict(task, connection) for task in tasks_data]


class Task(EntityBase):
    """
    Class representing a Planned Task entity in Strategy.

    A Planned Task is a scheduled execution of a Script within a specific
    Schedule.
    """

    _OBJECT_TYPE = None
    _API_GETTERS = {
        # explicitly no `**EntityBase._API_GETTERS`
        (
            "id",
            "name",
            "task_type",
            "active",
            "schedule",
            "executor",
            "content",
            "date_created",
            "date_modified",
            "expiration",
            "expiration_time_zone",
            "last_run",
        ): tasks_processor.get_task_info_and_last_status,
    }
    _API_GETTERS_KEEP_PRIVATE = EntityBase._API_GETTERS_KEEP_PRIVATE | {"task_type"}
    _REST_ATTR_MAP = {
        **EntityBase._REST_ATTR_MAP,
        "executor": "owner",
        "content": "script",
        "type": "task_type",
    }

    @staticmethod
    def _parse_expiration_time_zone(
        source: str | None, connection: 'Connection | None' = None
    ) -> 'UnixTimeZone | str | None':
        if source is None:
            return None

        try:
            return UnixTimeZone(source)
        except (TypeError, ValueError):
            return source

    _FROM_DICT_MAP = {
        # explicitly no `**EntityBase._API_GETTERS`
        "owner": User.from_dict,
        "active": ActiveState,
        "task_type": _TaskType,
        "schedule": Schedule.from_dict,
        "script": Script.from_dict,  # TODO: validate after Flow module
        "date_created": DatetimeFormats.FULLDATETIME,
        "date_modified": DatetimeFormats.FULLDATETIME,
        "expiration": DatetimeFormats.DATE,
        "expiration_time_zone": _parse_expiration_time_zone,
        "last_run": LastRunData._preparsed_from_dict,
    }
    _UNWRAP_ATTR = {
        **EntityBase._UNWRAP_ATTR,
        "script": {"variables": "variables_answers"},
    }
    _EXCLUDE_WHEN_LISTING = EntityBase._EXCLUDE_WHEN_LISTING + [
        "type",
        "task_type",
        "last_run",
    ]
    _ALLOW_NONE_ATTRIBUTES = EntityBase._ALLOW_NONE_ATTRIBUTES + [
        "variables_answers",
        "expiration",
        "expiration_time_zone",
    ]
    _API_PATCH = {
        # explicitly no `**EntityBase._API_PATCH`
        (
            "id",
            "name",
            "task_type",
            "active",
            "schedule",
            "executor",
            "content",
            "expiration",
            "expiration_time_zone",
        ): (tasks_processor.alter_task, 'partial_put'),
    }
    _PATCH_PATH_TYPES = {
        **EntityBase._PATCH_PATH_TYPES,
        "id": str,
        "name": str,
        "task_type": Literal["script"],
        "active": int,
        "expiration": str | None,
        "expiration_time_zone": str | None,
        "last_run": None,
    }

    def __init__(
        self,
        connection: 'Connection',
        schedule: 'Schedule | str | None' = None,  # can be class, id or name
        id: str | None = None,
        name: str | None = None,
    ):
        """Initialize a Task object.

        Note:
            Planned Task is directly coupled with the Schedule so it can be
            uniquely identified only with a reference to such. When not
            provided, all of the schedules will be searched for the Task
            existence.

            Also, `connection` needs to have selected a Project where the
            Task is stored.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`.
            schedule (Schedule | str, optional): Schedule object, ID or name.
            id (str, optional): ID of the task.
            name (str, optional): Name of the task.
        """

        connection._validate_project_selected()

        if not schedule:
            kwargs = {
                "name": name,
                "id": id,
            }
            opts = list_tasks(
                connection=connection,
                **delete_none_values(kwargs, recursion=False),
                to_dictionary=True,
            )

            if len(opts) != 1:
                raise ValueError(
                    f"Cannot uniquely identify Task: ID '{id or '<undefined>'}', "
                    f"name '{name or '<undefined>'}', without explicitly providing a "
                    "schedule."
                )

            id = opts[0]["id"]
            schedule = opts[0]["schedule"]["id"]

        if not id:
            if not name:
                raise ValueError(
                    "Please specify either 'id' or 'name' parameter in the constructor."
                )

            opts = list_tasks(
                connection=connection,
                schedule=schedule,
                name=name,
                to_dictionary=True,
            )

            if len(opts) != 1:
                raise ValueError(
                    f"Cannot uniquely identify {self.__class__.__name__} based on "
                    f"schedule '{schedule or '<undefined>'}' and name '{name}'. "
                    f"Found {len(opts)} hits. Please provide ID instead."
                )

            id = opts[0]["id"]

        schedule_id = Schedule._get_id_from_any_param(
            value=schedule, connection=connection
        )

        super().__init__(
            connection=connection,
            object_id=id,
            project_id=connection.project_id,
            schedule_id=schedule_id,
        )

    def __init_subset(self, default_value=None, **kwargs) -> None:
        """Subset of `_init_variables` after pythonifying REST response,
        including only the following:
            - "active"
            - "expiration"
            - "expiration_time_zone"

        Created to handle multiple ways for alter in different methods.
        """

        # handling for first pass or via `to_dict`
        if not hasattr(self, "_active"):
            self._active = None

        if not hasattr(self, "_expiration"):
            self._expiration = None

        if not hasattr(self, "_expiration_time_zone"):
            self._expiration_time_zone = None

        # actual application
        if "active" in kwargs:
            self._active: 'ActiveState | None' = (
                ActiveState(kwargs.get('active'))
                if "active" in kwargs
                else default_value
            )

        if "expiration" in kwargs:
            self._expiration: dt.date | None = (
                map_str_to_datetime(
                    "expiration", kwargs.get("expiration"), self._FROM_DICT_MAP
                ).date()
                if kwargs.get("expiration")
                else default_value
            )

        if "expiration_time_zone" in kwargs:
            etz = kwargs.get("expiration_time_zone", default_value)
            try:
                self._expiration_time_zone: 'UnixTimeZone | str | None' = (
                    UnixTimeZone(etz) if etz is not default_value else default_value
                )
            except (TypeError, ValueError):
                self._expiration_time_zone = etz

    def _init_variables(self, default_value=None, **kwargs) -> None:
        # first, rename raw names into expected names (not un-REST'ified yet)
        for key, alt_key in self._REST_ATTR_MAP.items():
            if key in kwargs:
                kwargs[alt_key] = kwargs.pop(key)

        super()._init_variables(default_value, **kwargs)
        self._task_type: '_TaskType | None' = (
            _TaskType(kwargs.get('task_type'))
            if "task_type" in kwargs
            else default_value
        )
        self._schedule_id = kwargs.get(
            "schedule_id", kwargs.get("schedule", {}).get("id", default_value)
        )
        self._schedule: 'Schedule | None' = (
            Schedule.from_dict(kwargs.get("schedule"), self._connection)
            if "schedule" in kwargs
            else default_value
        )

        # There are 3 possibilities for where the info about
        # Task's Variable Answers can be:
        # - in `variables_answers` prop -> if exists, we're done
        # - in `script.variables` nested prop -> but only if it is "raw" API res
        # otherwise -> leave `None` to refresh it from API next time
        candidate = kwargs.get("variables_answers")
        if candidate is None:
            candidate = kwargs.get("script", {}).get("variables", [])
            if not all(set(c.keys()) == {"id", "value", "type"} for c in candidate):
                candidate = None

        self._variables_answers: VariablesAnswers = candidate

        try:
            self._script: 'Script | None' = (
                Script.from_dict(kwargs.get("script"), self._connection)
                if "script" in kwargs
                else default_value
            )
        except AttributeError as err:
            if "NoneType" in str(err):
                self._script = None
                logger.warning(
                    f"Script for Task '{self.name}' with ID '{self.id}' does not exist "
                    "or cannot be accessed. Initializing Task without Script data."
                )
            else:
                raise

        self._owner: 'User | None' = (
            User.from_dict(kwargs.get("owner"), self._connection)
            if "owner" in kwargs
            else default_value
        )
        self._date_created: dt.datetime | None = (
            map_str_to_datetime(
                "date_created", kwargs.get("date_created"), self._FROM_DICT_MAP
            )
            if kwargs.get("date_created")
            else default_value
        )
        self._date_modified: dt.datetime | None = (
            map_str_to_datetime(
                "date_modified", kwargs.get("date_modified"), self._FROM_DICT_MAP
            )
            if kwargs.get("date_modified")
            else default_value
        )

        self.__init_subset(default_value=default_value, **kwargs)

        self._last_run: 'LastRunData | None' = default_value
        if lr := kwargs.get("last_run"):
            self._last_run = LastRunData._preparsed_from_dict(lr, self.connection)

        if not hasattr(self, "_project_id"):
            self._project_id: str = self._connection.project_id

    def _set_object_attributes(self, **kwargs) -> None:
        cached_project_id = getattr(self, "_project_id", None)
        super()._set_object_attributes(**kwargs)

        if self._project_id is None:
            self._project_id = (
                cached_project_id
                if cached_project_id is not None
                else self._connection.project_id
            )

    def is_active(self) -> bool:
        """Returns True if the task is active, False otherwise."""
        return self.active is ActiveState.ACTIVE

    def _validate_expiration_data_alter_payload(
        self,
        expiration: dt.date | str | None = None,
        expiration_time_zone: UnixTimeZone | str | None = None,
        remove_expiration_data: bool = False,
    ) -> tuple[dt.date | str | None, UnixTimeZone | str | None]:
        if remove_expiration_data and (expiration or expiration_time_zone):
            raise ValueError(
                "Request can either set `expiration` or `expiration_time_zone` or "
                "remove it via `remove_expiration_data=True`, not both."
            )

        if remove_expiration_data:
            return (None, None)

        if expiration and not expiration_time_zone:
            return (expiration, self.expiration_time_zone or UnixTimeZone.GMT)

        if not expiration and expiration_time_zone:
            return (self.expiration, expiration_time_zone)

        return (expiration, expiration_time_zone)

    def alter(
        self,
        name: str | None = None,
        schedule: 'Schedule | str | None' = None,
        active: 'ActiveState | int | bool | None' = None,
        script: 'Script | str | None' = None,
        variables_answers: 'VariablesAnswers | None' = None,
        expiration: dt.date | str | None = None,
        expiration_time_zone: UnixTimeZone | str | None = None,
        remove_expiration_data: bool = False,
    ) -> None:
        """Alter the properties of the task.

        Args:
            name (str | None, optional): New name for the task.
            schedule (Schedule | str | None, optional): New schedule for the
                task. Can be a Schedule object or its ID or name.
            active (ActiveState | int | bool | None, optional): New active state
                for the task.
            script (Script | str | None, optional): New script for the task.
                Can be a Script object or its ID or name.
            variables_answers (VariablesAnswers | None, optional): New variables
                answers for the script.
            expiration (date | str | None, optional): New
                expiration date for the task.
            expiration_time_zone (UnixTimeZone | str | None, optional): New time
                zone for the expiration date.
            remove_expiration_data (bool, optional): If True, removes the
                expiration date and time zone from the task. Defaults to False.

        Raises:
            ValueError: If both expiration data and `remove_expiration_data` are
                provided.
        """

        expiration, expiration_time_zone = self._validate_expiration_data_alter_payload(
            expiration, expiration_time_zone, remove_expiration_data
        )

        script_id, answers = self._get_script_id_and_validated_raw_vars_answers(
            self.connection,
            script=script or self.script,
            variables_answers=(
                variables_answers
                if variables_answers is not None
                else self.variables_answers
            ),
        )

        exp, exp_tz = self._get_raw_expiration_data_if_applicable(
            expiration, expiration_time_zone
        )

        params = {
            "id": self.id,
            "schedule": {
                "id": (
                    Schedule._get_id_from_any_param(schedule, self.connection)
                    if schedule
                    else self.schedule_id
                ),
            },
            "schedule_id": self.schedule_id,
            "name": name or self.name,
            "active": int(active) if active is not None else self.active.value,
            "script": {
                "object_id": script_id,
                "variables": answers or [],
            },
            "expiration": exp,
            "expiration_time_zone": exp_tz,
        }
        params = delete_none_values(params, recursion=False)

        if remove_expiration_data:
            params.update(
                {
                    "expiration": None,
                    "expiration_time_zone": None,
                }
            )

        self._alter_properties(**params)
        self._schedule_id = self.schedule.id  # override cache

        if isinstance(self._expiration, dt.datetime):
            self._expiration = self._expiration.date()

    def activate(
        self,
        expiration: dt.date | str | None = None,
        expiration_time_zone: UnixTimeZone | str | None = None,
        remove_expiration_data: bool = False,
    ) -> None:
        """Activate the task.

        Note:
            Optionally, you can set an expiration date and time zone for the
            task at the same time.

        Args:
            expiration (date | str | None, optional): Expiration
                date for the task.
            expiration_time_zone (UnixTimeZone | str | None, optional): Time
                zone for the expiration date.
            remove_expiration_data (bool, optional): If True, removes the
                expiration date and time zone from the task. Defaults to False.

        Raises:
            ValueError: If both expiration data and `remove_expiration_data` are
                provided.
        """

        expiration, expiration_time_zone = self._validate_expiration_data_alter_payload(
            expiration, expiration_time_zone, remove_expiration_data
        )

        exp, exp_tz = self._get_raw_expiration_data_if_applicable(
            expiration, expiration_time_zone
        )

        if remove_expiration_data:
            body = {
                "expiration": None,
                "expirationTimeZone": None,
            }
        else:
            if not exp and not exp_tz:
                body = None
            else:
                body = {
                    "expiration": exp,
                    "expirationTimeZone": exp_tz,
                }

        res = self._auto_match_params_then_call(
            tasks_processor.activate_task, body=body
        )
        self.__init_subset(**self._rest_to_python(res))

        if config.verbose:
            logger.info(
                f"Successfully activated Planned Task '{self.name}' with ID: {self.id}"
            )

    def deactivate(self) -> None:
        """Deactivate the task."""
        success = self._auto_match_params_then_call(tasks_processor.deactivate_task)
        if success:
            self._active = ActiveState.INACTIVE

            if config.verbose:
                logger.info(
                    f"Successfully deactivated Planned Task '{self.name}' with "
                    f"ID: {self.id}"
                )

    @overload
    def execute(
        self,
        block_until_done: Literal[True] = True,
        raise_on_execution_failure: bool = False,
    ) -> 'LastRunData': ...

    @overload
    def execute(
        self,
        block_until_done: Literal[False] = False,
    ) -> None: ...

    def execute(
        self,
        block_until_done: bool = False,
        raise_on_execution_failure: bool = False,
    ) -> 'LastRunData | None':
        """Execute the task.

        Args:
            block_until_done (bool, optional): If True, waits for the task's
                execution to finish before returning. Defaults to False.
            raise_on_execution_failure (bool, optional): If True, raises an
                exception if the task's execution fails. Defaults to False.
                Ignored if `block_until_done` is False.

        Returns:
            LastRunData | None: The last run data of the task if
                `block_until_done` is True, otherwise None.

        Raises:
            ScriptSetupError: If the task is already being executed.
            ScriptExecutionError: If there is an unexpected error while
                executing the task.
        """

        self.fetch("last_run")
        if self.last_run and self.last_run.status == LastRunData.TaskRunStatus.RUNNING:
            raise ScriptSetupError(f"Task '{self.name}' is already being executed.")

        success = self._auto_match_params_then_call(tasks_processor.trigger_task)

        if not success:
            raise ScriptExecutionError(f"Failed to execute Task '{self.name}'.")

        self.fetch("last_run")

        if block_until_done:
            ret = self.wait_for_execution_finish()

            if ret.status != LastRunData.TaskRunStatus.SUCCESS:
                msg = (
                    f"Task '{self.name}' Script's execution failed with the following "
                    f"message:\n{self.last_run.message}"
                )

                if raise_on_execution_failure:
                    raise ScriptExecutionError(msg)

                if config.verbose:
                    logger.info(msg)

            elif config.verbose:
                logger.info(f"Task '{self.name}' Script's execution was successful.")

            return ret

    def wait_for_execution_finish(
        self,
        interval: int | None = None,
    ) -> 'LastRunData':
        """Wait for the task's execution to finish.

        Args:
            interval (int | None, optional): Time in seconds to wait between
                polling the task's status. Defaults to None, which uses the
                global configuration delay.

        Returns:
            LastRunData: The last run data of the task.

        Raises:
            ScriptSetupError: If the task has not been executed yet.
            ScriptExecutionError: If there is an unexpected error while
                fetching the last run status.
        """

        self.fetch("last_run")
        if (
            not self.last_run
            or self.last_run.status != LastRunData.TaskRunStatus.RUNNING
        ):
            raise ScriptSetupError(f"Task '{self.name}' is not executed yet.")

        while (
            self.last_run and self.last_run.status == LastRunData.TaskRunStatus.RUNNING
        ):
            time.sleep(interval or config.delay_between_polling)
            self.fetch("last_run")

        if not self.last_run:
            raise ScriptExecutionError(
                "Something unexpected happened and it is impossible to read last run "
                f"status of Task '{self.name}'."
            )

        return self.last_run

    def delete(self, force: bool = False) -> bool:
        """Delete the task.

        Args:
            force (bool, optional): If True, deletes the task without asking for
                confirmation. Defaults to False.

        Returns:
            bool: True if the task was deleted, False otherwise.
        """

        question = (
            f"Are you sure you want to delete a Planned Task named '{self.name}' "
            f"with ID '{self.id}' within a {self.schedule}? [Y/N]"
        )

        if not force and input(question) != "Y":
            return False

        res = self._auto_match_params_then_call(tasks_processor.delete_task)

        if config.verbose and res:
            logger.info(
                f"Successfully deleted Planned Task '{self.name}' with ID: {self.id}"
            )

        return res

    @property
    def schedule(self) -> 'Schedule':
        return self._schedule

    @property
    def schedule_id(self) -> str:
        return self.schedule.id

    @property
    def script(self) -> 'Script':
        return self._script

    @property
    def variables_answers(self) -> 'VariablesAnswers':
        return self._variables_answers

    @property
    def owner(self) -> 'User':
        return self._owner

    @property
    def date_created(self) -> dt.datetime:
        return self._date_created

    @property
    def date_modified(self) -> dt.datetime:
        return self._date_modified

    @property
    def active(self) -> 'ActiveState':
        return self._active

    @property
    def expiration(self) -> dt.date | None:
        return self._expiration

    @property
    def expiration_time_zone(self) -> 'UnixTimeZone | str | None':
        return self._expiration_time_zone

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def last_run(self) -> 'LastRunData | None':
        return self._last_run

    @classmethod
    def _get_script_id_and_validated_raw_vars_answers(
        cls,
        connection: 'Connection',
        script: 'Script | str',
        variables_answers: 'VariablesAnswers | None',
    ) -> tuple[str, list[dict]]:
        """Convert `script` and `variables_answers` to raw values for REST API.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`.
            script (Script | str): Script object, ID or name.
            variables_answers (VariablesAnswers | None): Variables answers to be
                used when executing the script.

        Returns:
            tuple[str, list[dict]]: A tuple containing the script ID and a list
                of variables answers as dictionaries.

        Raises:
            ValueError: If either `script` or `variables_answers` parameter is
                invalid.
            ScriptSetupError: If any of the variables with prompts are not
                answered.
        """

        connection._validate_project_selected()

        with config.temp_verbose_disable():
            script_instance = (
                script
                if isinstance(script, Script)
                else Script(
                    connection, id=Script._get_id_from_any_param(script, connection)
                )
            )

        try:
            variables, _ = (
                script_instance._script_content._convert_variables_and_answers_to_lists(
                    script_instance.get_variables(),
                    variables_answers or [],
                    None,
                )
            )
            # FYI: will raise if any of the variables
            # with prompts are not answered
            [v.validate_whether_answered() for v in variables]

        except ScriptError as err:
            raise ValueError(
                "Either `script` or `variables_answers` parameter is invalid. "
                "See traceback for more details."
            ) from err

        return (
            script_instance.id,
            [v.get_answer_as_dict() for v in variables if v.prompt],
        )

    @classmethod
    def _get_raw_expiration_data_if_applicable(
        cls,
        expiration: dt.date | str | None,
        expiration_time_zone: 'UnixTimeZone | str | None',
    ) -> tuple[str | None, str | None]:
        """Convert `expiration` and `expiration_time_zone` to raw values for
        REST API, allowing `None`.
        """
        return (
            (
                expiration.strftime(DatetimeFormats.DATE.value)
                if isinstance(expiration, dt.date)
                else expiration
            ),
            (
                expiration_time_zone.value
                if isinstance(expiration_time_zone, UnixTimeZone)
                else expiration_time_zone
            ),
        )

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        name: str,
        schedule: 'Schedule | str',
        script: 'Script | str',
        variables_answers: 'VariablesAnswers | None' = None,
        active: 'ActiveState | int | bool' = True,
        expiration: dt.date | str | None = None,
        expiration_time_zone: 'UnixTimeZone | str | None' = None,
        execute_on_creation: bool = False,
    ) -> 'Task':
        """Create a new Task object.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`.
            name (str): Name of the task.
            schedule (Schedule | str): Schedule object, ID or name.
            script (Script | str): Script object, ID or name.
            variables_answers (VariablesAnswers | None, optional): Variables
                answers to be used when executing the script. Defaults to None,
                meaning none of the prompts in the Script are prompted or there
                is no Variables used. Can be either a list of `VariableAnswer`
                class instances, `FlagKeepDefaultAnswer` flags or a dict with
                shape: `{"variable-id-or-name": "answer-value", ...}`.
            active (ActiveState | int | bool, optional): Whether the task is
                active. Defaults to True.
            expiration (date | str | None, optional): Expiration date
                of the task. Defaults to None.
            expiration_time_zone (UnixTimeZone | str | None, optional): Timezone
                for the expiration date. Defaults to None.
            execute_on_creation (bool, optional): If True, the task will be
                executed immediately after creation. Defaults to False.

        Returns:
            Task: The created Task object.
        """

        script_id, answers = cls._get_script_id_and_validated_raw_vars_answers(
            connection, script=script, variables_answers=variables_answers
        )

        exp, exp_tz = cls._get_raw_expiration_data_if_applicable(
            expiration, expiration_time_zone
        )

        data = tasks_processor.create_task(
            connection=connection,
            name=name,
            type=_TaskType.SCRIPT.value,
            schedule_id=Schedule._get_id_from_any_param(schedule, connection),
            script_id=script_id,
            variables_answers=answers,
            active=int(active),
            expiration=exp,
            expiration_time_zone=(
                (exp_tz or UnixTimeZone.GMT.value) if exp else exp_tz
            ),
        )

        ret = cls.from_dict(data, connection)

        if execute_on_creation:
            ret.execute()

        return ret

    def __str__(self) -> str:
        start = super().__str__()
        return f"{start} and schedule ID: '{self.schedule_id}'"

    def __repr__(self) -> str:
        schedule_id = repr(self.schedule_id)
        name = repr(self.name)
        id = repr(self.id)
        return (
            f"{self.__class__.__name__}"
            f"(connection, id={id}, name={name}, schedule={schedule_id})"
        )


# endregion
