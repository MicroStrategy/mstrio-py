import ast
import contextlib
import json
import logging
import re
import time
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from inspect import isfunction
from operator import xor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypeVar, overload

from mstrio import config
from mstrio.helpers import is_valid_datetime, try_str_to_num
from mstrio.object_management.folder import Folder
from mstrio.object_management.search_enums import SearchDomain, SearchPattern
from mstrio.object_management.search_operations import full_search
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.certified_info import CertifiedInfo
from mstrio.utils.encoder import Encoder
from mstrio.utils.entity import (
    CertifyMixin,
    ChangeJournalMixin,
    CopyMixin,
    DeleteMixin,
    Entity,
    MoveMixin,
)
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable, delete_none_values
from mstrio.utils.resolvers import (
    get_folder_id_from_params_set,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import scripts as scripts_processor

if TYPE_CHECKING:
    from mstrio.connection import Connection
    from mstrio.server.project import Project


logger = logging.getLogger(__name__)


# Sync below with any `isinstance` checks done in this module
_VariableValueRaw: TypeAlias = str | int | float | datetime | date
VariableValue: TypeAlias = _VariableValueRaw | list[_VariableValueRaw]
CodeResult: TypeAlias = str | int | float | datetime | None
VariablesAnswers: TypeAlias = (
    list['VariableAnswer | FlagKeepDefaultAnswer | AnswerForCallback']
    # FYI: dict shape {"id-or-name-of-variable": "some-value", ...}
    | dict[str, 'VariableValue | FlagKeepDefaultAnswer']
)
AnswerForCallback: TypeAlias = Callable[[list['Variable']], None]
FlagKeepDefaultAnswer: TypeAlias = (
    type['VariableAnswer.KEEP_PERSONAL_DEFAULT']
    | type['VariableAnswer.KEEP_GLOBAL_DEFAULT']
)


# --- Exceptions ---
class ScriptError(Exception):
    """Base Exception class for other exceptions in Scripts module.

    Created for ease of catching all errors from this module, regardless of
    subtype. All other Exceptions in this module will inherit from it.
    """


class ScriptExecutionError(ScriptError):
    """Exception raised when a script execution fails."""


class ScriptEnvironmentError(ScriptExecutionError):
    """Exception raised when there is an environment-related error during
    script execution.
    """


class ScriptSetupError(ScriptError):
    """Exception raised when a script is not properly set up for execution
    or saving.
    """


# --- END: Exceptions ---


# --- Enums ---
class ExecutionStatus(Enum):
    INITIATED = 0
    RUNNING = 1
    PARTIALLY_READY = 2
    READY = 3  # This and all below are considered "done"
    ERROR = 4
    EXPIRED = 5
    CANCELLED = 6

    @classmethod
    def is_done(cls, value: 'ExecutionStatus | int') -> bool:
        return get_enum_val(value, ExecutionStatus) >= ExecutionStatus.READY.value

    @classmethod
    def is_error(cls, value: 'ExecutionStatus | int') -> bool:
        return get_enum_val(value, ExecutionStatus) >= ExecutionStatus.ERROR.value


class ScriptType(Enum):
    RESERVED = "reserved"
    PYTHON = "python"
    JUPYTER_NOTEBOOK = 'jupyterNotebook'


class ScriptUsageType(Enum):
    STANDARD = 'commandManager'
    DATASOURCE = 'dataSource'
    TRANSACTION = 'transaction'
    # script-as-metric related types below
    SIMPLE_FUNCTION = 'pythonSimpleFunction'
    AGGREGATION_FUNCTION = 'pythonAggFunction'
    AGGREGATION_FUNCTION_NO_SORT = 'pythonNoSortAggFunction'
    RELATIVE_FUNCTION = 'pythonRelativeFunction'
    RELATIVE_FUNCTION_NO_SORT = 'pythonNoSortRelativeFunction'


class ScriptResultType(AutoName):
    """Type of Script's output"""

    NUMERICAL = auto()
    TEXT = auto()
    DATE = auto()
    RESERVED = auto()
    UNKNOWN = auto()


class VariableType(Enum):
    RESERVED = 0x00
    TEXT = 0x01
    NUMERICAL = 0x02
    DATE = 0x03
    SECRET = 0x04
    DATETIME = 0x05
    SYSTEM_PROMPT = 0x100A  # 4106
    TXN_ROW_PROVENANCE = 0x8001  # 32769


# --- END: Enums ---


# --- Configs & Behavior Customization ---
@dataclass
class _VariableAnswerConfig:
    INTERACTIVE_KEEP_PERSONAL_DEFAULT: str = '...'
    INTERACTIVE_KEEP_GLOBAL_DEFAULT: str = '^'


VariableAnswerConfig = _VariableAnswerConfig()
# --- END: Configs & Behavior Customization ---


def list_scripts(
    connection: 'Connection',
    name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> 'list[dict] | list[Script]':
    """Get a list of scripts.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        name (str, optional): Name or part of the name of the Script.
        search_pattern (SearchPattern | int, optional): Search pattern for
            finding the Script by name. Defaults to
            `SearchPattern.CONTAINS`.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        to_dictionary (bool, optional): If True returns dicts, by default
            (False) returns Script objects
        limit (integer, optional): limit the number of elements returned. If
            None all object are returned.
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['id', 'description, 'owner',
            'date_created', 'date_modified', 'version', 'acg']

    Returns:
        List of scripts as dicts or as Script objects.
    """

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )
    validate_owner_key_in_filters(filters)

    with connection.temporary_project_change(project=proj_id):
        return full_search(
            connection=connection,
            project=proj_id,
            object_types=ObjectTypes.SCRIPT,
            name=name,
            pattern=search_pattern,
            domain=SearchDomain.PROJECT,
            to_dictionary=to_dictionary,
            limit=limit,
            root=folder,
            root_id=folder_id,
            root_name=folder_name,
            root_path=folder_path,
            **filters,
        )


class Code:
    """Class representing Python code to be run in server-side execution
    engine of Strategy.

    Note:
        To retrieve code-as-text from an instance of Code class, just use
        `.as_text` property or stringify the `Code` instance with `str`:
        ```
        >>> code = Code(conn, "print('Hello World')")
        >>> txt = str(code)
        >>> txt2 = code.as_text  # both equal "print('Hello World')"
        ```
    """

    _evaluation_id: str | None = None
    _run_details: dict = {}
    _source_script: 'Script | None' = None
    __validation_error: Exception | None = None

    def __init__(
        self,
        connection: 'Connection',
        code: 'Code | str',
        validate_code: bool = False,
    ) -> None:
        """Initialize Python Code as string or from another Code class instance.

        Args:
            code (Code | str): Other Code class instance or code as a string
                (either already base64-encoded or original)
            validate_code (bool, optional): Whether to validate the code
                syntax upon creation. Defaults to False. (This is a pre-run
                validation only and does not guarantee no Runtime Errors.)
        """

        self._connection = connection

        if isinstance(code, Code):
            code = code._code.decoded_text

        if not code or not isinstance(code, str):
            raise ScriptSetupError(
                "Cannot obtain string version of provided `code` parameter or "
                "the `code` is empty."
            )

        self._code = (
            Encoder(encoded_text=code)
            if Encoder.is_encoded(code)
            else Encoder(decoded_text=code)
        )

        if validate_code:
            self._validate()

    def _validate(self) -> None:
        if not self.is_valid():
            raise ScriptSetupError(
                f"Invalid Code: {str(self)}"
            ) from self.__validation_error

    def _convert_variables_and_answers_to_lists(
        self,
        variables: 'list[Variable | dict] | None',
        answers: VariablesAnswers | None,
        variables_factory: type['Variable'] | None,
    ) -> tuple[list['Variable'], list['VariableAnswer']]:
        """Parses Variables versus their answers to return all variables and
        their answers in common format -> as lists.

        - Variables as a list of `Variable` instances
        - Answers as a list of `VariableAnswer` instances

        Returns:
            `tuple(variables, answers)`
        """

        # FYI: Either explicitly provided factory...
        # OR factory calculated from variables if it's unique for all...
        # OR Standard Script one
        Factory = variables_factory or (  # NOSONAR # (name format)
            options.pop()
            if variables
            and len(
                options := {type(var) for var in variables if isinstance(var, Variable)}
            )
            == 1
            else VariableStandardScript
        )

        variables = variables or []
        answers = answers or []

        if not all(isinstance(var, (dict, Factory)) for var in variables):
            raise ScriptSetupError(
                "Variables have incorrect shape. All of them need to be either "
                "a dictionary of data or an instance of provided factory class "
                f"'{Factory.__name__}'."
            )

        # TODO: create helper method for this "Object | dict -> Object" logic
        variables: list[Variable] = [
            Factory.from_dict(v) if isinstance(v, dict) else v for v in variables
        ]

        if isinstance(answers, dict):
            # convert complex dict to `VariableAnswer` class instances
            try:
                answers = [
                    Factory.get_variable_by_identifier(variables, key).answer(answer)
                    for key, answer in answers.items()
                ]
            except (KeyError, AttributeError):
                raise ScriptSetupError(
                    "Some provided answers refer to non-existent Variables."
                )

        variables = variables.copy()
        answers = answers.copy()

        # calculate answers if done via `VariableAnswer.For(...)...` callback
        for i, answer in enumerate(answers):
            if isfunction(answer) and getattr(answer, '_is_internal_mstrio', None):
                answers[i] = answer(variables)

        return (variables, answers)

    @overload
    def execute(
        self,
        runtime_id: str | None = None,
        variables: 'list[Variable | dict] | None' = None,
        answers: VariablesAnswers | None = None,
        block_until_done: Literal[True] = True,
        pipe_logs: bool = False,
        raise_on_execution_failure: bool = False,
        allow_interactive_answering: bool = False,
        variables_factory: type['Variable'] = None,
    ) -> ExecutionStatus: ...

    @overload
    def execute(
        self,
        runtime_id: str | None = None,
        variables: 'list[Variable | dict] | None' = None,
        answers: VariablesAnswers | None = None,
        block_until_done: Literal[False] = False,
        allow_interactive_answering: bool = False,
        variables_factory: type['Variable'] = None,
    ) -> None: ...

    def execute(
        self,
        # TODO: extend with proper resolver during Module for Runtimes FE dev
        runtime_id: str | None = None,
        variables: 'list[Variable | dict] | None' = None,
        answers: VariablesAnswers | None = None,
        block_until_done: bool = True,
        pipe_logs: bool = False,
        raise_on_execution_failure: bool = False,
        allow_interactive_answering: bool = False,
        # FYI: `None` represents `VariableStandardScript`
        variables_factory: type['Variable'] = None,
    ) -> 'ExecutionStatus | None':
        """Start Code execution.

        Args:
            runtime_id (str, optional): ID of the Script runtime. If nothing is
                provided, defaults to Default Runtime.
            variables (list[_Variable | dict], optional): List of Variables to
                be used during Code execution.
            answers (VariablesAnswers, optional): Answers to prompted Variables.
                Can be either a list of `VariableAnswer` class instances,
                `FlagKeepDefaultAnswer` flags or a dict with shape:
                `{"variable-id-or-name": "answer-value", ...}`.
            block_until_done (bool, optional): Whether to block the execution
                until it is done. Defaults to True.
            pipe_logs (bool, optional): Whether to pipe the execution logs
                to the logger while waiting for the execution to finish. Valid
                only if `block_until_done` is set. Defaults to False.
            raise_on_execution_failure (bool, optional): Whether to raise an
                exception if the execution fails. Valid only if
                `block_until_done` is set. Defaults to False.
            allow_interactive_answering (bool, optional): Whether to allow
                interactive answering of Variables if not all are answered.
                Defaults to False.
            variables_factory (type[Variable], optional): Factory class to use
                for creating Variable instances. Defaults to
                `VariableStandardScript`.

        Returns:
            ExecutionStatus: if `block_until_done` is set to True.
            Nothing otherwise.
        """

        if self._evaluation_id:
            raise ScriptExecutionError(
                "The code is already running. Make sure you wait for its "
                "finalization before trying to run it again or create a new "
                "instance of Script or Code class to run it independently."
            )

        variables, answers = self._convert_variables_and_answers_to_lists(
            variables=variables,
            answers=answers,
            variables_factory=variables_factory,
        )

        if allow_interactive_answering:
            if self._connection.is_run_in_workstation():
                raise ScriptEnvironmentError(
                    "Cannot allow interactive Variables answering in a script "
                    "run in Workstation."
                )

            left_to_consider = tuple(v for v in variables if not v.is_answered())

            if left_to_consider:
                logger.info(
                    f"(Write `{VariableAnswerConfig.INTERACTIVE_KEEP_PERSONAL_DEFAULT}`"
                    " to keep personal default answer or "
                    f"`{VariableAnswerConfig.INTERACTIVE_KEEP_GLOBAL_DEFAULT}` to "
                    "keep global default answer)"
                )

            for var_to_answer in left_to_consider:
                user_input = input(f"Answer to Variable '{var_to_answer.name}': ")

                match user_input:
                    case VariableAnswerConfig.INTERACTIVE_KEEP_GLOBAL_DEFAULT:
                        user_input = VariableAnswer.KEEP_GLOBAL_DEFAULT
                    case VariableAnswerConfig.INTERACTIVE_KEEP_PERSONAL_DEFAULT:
                        user_input = VariableAnswer.KEEP_PERSONAL_DEFAULT
                    case _:
                        if var_to_answer.type == VariableType.NUMERICAL:
                            with contextlib.suppress(ValueError):
                                # keep as string if not a valid float,
                                # `answer` will handle errors
                                user_input = float(user_input)

                var_to_answer.answer(user_input)

        # FYI: raises at Variable that is not properly answered
        [v.validate_whether_answered() for v in variables]

        if not block_until_done and (raise_on_execution_failure or pipe_logs):
            logger.warning(
                "`raise_on_execution_failure` or `pipe_logs` flags will be ignored as "
                "`block_until_done` is not set, therefore the Code will "
                "run in the background, independently."
            )

        if self._source_script:
            self._evaluation_id = scripts_processor.start_run(
                connection=self._source_script.connection,
                script_id=self._source_script.id,
                variables_data=[v.get_answer_as_dict() for v in variables if v.prompt],
            )
        else:
            self._evaluation_id = scripts_processor.start_run(
                connection=self._connection,
                encoded_code=self._code.encoded_text,
                runtime_id=runtime_id,
                variables_data=[
                    v.get_answer_as_dict_for_non_script_run() for v in variables
                ],
            )

        if not self._evaluation_id:
            raise ScriptEnvironmentError("Evaluation ID was not received.")

        if block_until_done:
            ret = self.wait_for_execution_finish(pipe_logs=pipe_logs)

            if raise_on_execution_failure and ExecutionStatus.is_error(ret):
                msg_prefix = (
                    (
                        f"Execution of Script {self._source_script.name} with "
                        f"ID '{self._source_script.id}'"
                    )
                    if self._source_script
                    else "Code execution"
                )

                raise ScriptExecutionError(
                    f"{msg_prefix} failed. Details: {str(self._run_details)}"
                )

            return ret

    def stop_execution(self) -> None:
        """Stops the code execution."""

        if not self._evaluation_id:
            raise ScriptSetupError(
                "Code execution cannot be stopped as it is not running."
            )

        scripts_processor.stop_run(self._connection, self._evaluation_id)
        self.get_execution_details()
        self._evaluation_id = None

    def get_current_execution_status(self) -> ExecutionStatus | None:
        """Retrieve current status of the code execution.

        Returns:
            ExecutionStatus: Current status of the code execution, or None if
                the code is not currently running.
        """

        if not self._evaluation_id:
            return None

        raw_status = self.get_execution_details().get('status')
        return ExecutionStatus(raw_status) if raw_status is not None else None

    def wait_for_execution_finish(
        self, pipe_logs: bool = False, interval: int | None = None
    ) -> ExecutionStatus:
        """Wait until the code execution is finished.

        Args:
            pipe_logs (bool, optional): Whether to pipe the execution logs of
                the Code to the console of this requester script. Defaults to
                False.
            interval (int, optional): Time interval in seconds between polling
                requests for status. If not provided, the value is taken from
                mstrio-py's `config`.

        Returns:
            ExecutionStatus: Final status of the code execution.
        """

        if not self._evaluation_id:
            self.get_execution_details()  # FYI: will throw

        try:
            while not ExecutionStatus.is_done(self.get_current_execution_status()):
                time.sleep(interval or config.delay_between_polling)

        except BaseException as err:
            # At this point the code run on I-Server pod and this requester
            # script should be synchronized. If something happens with this
            # script, we should do something similar to the code run on
            # I-Server as well
            with contextlib.suppress(Exception):
                self.stop_execution()

            raise err

        finally:
            if pipe_logs:
                prefix = "Script" if self._source_script else "Code"

                if self.stdout:
                    logger.info(f"[{prefix} Log]: {self.stdout}")

                if self.stderr:
                    logger.warning(f"[{prefix} Error Log]: {self.stderr}")

                logger.info(f"[{prefix} Completion -> {self.status}]")

        self._evaluation_id = None

        return self.status

    def get_execution_details(self) -> dict:
        """Retrieve details about the current code execution.

        Returns:
            dict: Details about the current code execution.
        """

        if not self._evaluation_id:
            raise ScriptSetupError(
                "Cannot retrieve execution information for non-running code."
            )

        self._run_details = scripts_processor.get_run_result(
            self._connection, self._evaluation_id
        )

        return self._run_details

    def is_valid(self) -> bool:
        """Check whether the code syntax is valid.

        Note:
            This is a pre-run validation only and does not guarantee no
            Runtime Errors.

        Returns:
            bool: True if the code syntax is valid, including Strategy-specific
                extensions, like Variables. False otherwise.
        """

        code = str(self)

        try:
            if "$" in code:
                if re.match(r'\$[a-zA-Z0-9_]+\s*=[^=]', code):
                    # assignment to variable
                    raise SyntaxError(
                        # FYI: content based on what I-Server raises
                        "Strategy Variable cannot be assigned to in Python Code. "
                        "Did you mean to use `==` instead of `=`?"
                    )

                # replace all Variables with a placeholder that is a valid
                # Python constant to check if in that form the code is valid
                code = "__mstrio_vars__ = None\n" + re.sub(
                    r'\$[a-zA-Z0-9_]+', '__mstrio_vars__', code
                )

            compile(
                code,
                "<string>",
                'exec',
                flags=ast.PyCF_TYPE_COMMENTS,
                dont_inherit=True,
                optimize=0,
            )

            return True
        except (SyntaxError, TypeError) as err:
            self.__validation_error = err
            return False

    @property
    def status(self) -> ExecutionStatus | None:
        """Status from last made current execution status request."""

        raw_value = self._run_details.get('status')
        return ExecutionStatus(raw_value) if raw_value is not None else None

    @property
    def stdout(self) -> str:
        """STDOUT from last made current execution status request."""

        return self._run_details.get('results', {}).get('stdout', '').strip()

    @property
    def stderr(self) -> str:
        """STDERR from last made current execution status request."""

        return self._run_details.get('results', {}).get('stderr', '').strip()

    @property
    def executor_message(self) -> str | None:
        """Message from Python Executor (if any) in last made current execution
        status request.

        Usually populated with error details when Code failed during runtime.
        """

        return self._run_details.get('message')

    @property
    def result(self) -> CodeResult:
        """Returned Value from last made current execution status request."""

        ret = json.loads(self._run_details.get('results', {}).get('output', 'null'))

        if self._source_script and ret is not None:
            if self._source_script.script_result_type == ScriptResultType.DATE:
                ret = datetime.fromisoformat(ret)
            elif self._source_script.script_result_type == ScriptResultType.NUMERICAL:
                ret = try_str_to_num(ret)

        return ret

    @property
    def as_text(self) -> str:
        return self._code.decoded_text

    def __str__(self):
        return self.as_text

    def __repr__(self):
        LEN_LIMIT = 70
        code = str(self)
        code = code.replace("\n", "\\n")[:LEN_LIMIT] + (
            '' if len(code) <= LEN_LIMIT else '...'
        )
        return f"Code<\"{code}\">"

    @classmethod
    def get_from_file(
        cls,
        connection: 'Connection',
        path: 'Path | str',
        validate_code: bool = False,
    ) -> 'Code':
        """Create Code instance from contents of a local file.

        Note:
            Does not validate whether the path is correct, accessible or
            existing, so re-raises any OS-specific errors.

        Args:
            connection (Connection): Strategy One connection object returned by
                `connection.Connection()`.
            path (Path | str): Path to a file on your local drive containing
                the code.
                Example: `C:\\Program Files\\My Scripts\\some_script.py`
            validate_code (bool, optional): Whether to validate the code
                syntax upon creation. Defaults to False. (This is a pre-run
                validation only and does not guarantee no Runtime Errors.)

        Returns:
            Code: Created Code instance.
        """

        with open(Path(path)) as file:
            return cls(
                connection=connection,
                code=file.read(),
                validate_code=validate_code,
            )


class Script(
    Entity, DeleteMixin, MoveMixin, CopyMixin, CertifyMixin, ChangeJournalMixin
):
    """
    Class representing a Script object in Strategy.
    """

    _OBJECT_TYPE = ObjectTypes.SCRIPT
    _API_GETTERS = {
        **Entity._API_GETTERS,
        (
            "script_content",
            "script_result_type",
            "script_runtime_id",
            "script_type",
            # "script_usage_type",  # FYI: this is calculated from `subtype`
            "source",
            "variables",
        ): scripts_processor.get_info_data,
    }
    _API_GETTERS_KEEP_PRIVATE = {"variables", "script_content"}
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        "subtype": ObjectSubTypes,
        'certified_info': CertifiedInfo.from_dict,
        "owner": User.from_dict,
        "script_content": lambda source, connection: Code(connection, code=source),
        "script_result_type": ScriptResultType,
        "script_type": ScriptType,
        "script_usage_type": ScriptUsageType,
    }
    _API_PATCH = {
        **Entity._API_PATCH,
        (
            "name",
            "description",
            "folder_id",
            "script_type",
            "script_content",
            "script_runtime_id",
            "variables",
            "script_result_type",
        ): (scripts_processor.update_script, 'partial_put'),
    }

    _history_last_entry: dict = {}
    _variables_personal_answers: dict | None = None

    def __init__(
        self,
        connection: 'Connection',
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize Script object by passing in either its ID or name.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`.
            id (str, optional): ID of the Script.
            name (str, optional): Name of the Script.
        """

        connection._validate_project_selected()

        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'id' or 'name' parameter in the constructor."
                )

            opts = list_scripts(
                connection,
                project=connection.project_id,
                name=name,
                search_pattern=SearchPattern.EXACTLY,
            )

            if len(opts) != 1:
                raise ValueError(
                    f"Cannot uniquely identify Script with name '{name}'. "
                    f"Found {len(opts)} Scripts with this name. "
                    "Please provide ID instead."
                )

            id = opts[0].id

        super().__init__(connection, object_id=id)
        self.fetch()
        self._script_content._source_script = self

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self._source: dict | None = kwargs.get('source', default_value)
        self._variables = (
            tuple(kwargs.get('variables')) if kwargs.get('variables') else default_value
        )
        self._script_content: Code = (
            Code(self._connection, kwargs.get('script_content'))
            if kwargs.get('script_content')
            else default_value
        )
        self._script_content._source_script = self
        self._script_type: ScriptType = (
            ScriptType(kwargs.get('script_type'))
            if kwargs.get('script_type')
            else default_value
        )
        self._script_runtime_id: str | None = kwargs.get(
            'script_runtime_id', default_value
        )
        self._script_result_type: ScriptResultType = (
            ScriptResultType(kwargs.get('script_result_type'))
            if kwargs.get('script_result_type')
            else default_value
        )

    @overload
    def execute(
        self,
        block_until_done: Literal[True] = True,
        pipe_logs: bool = False,
        raise_on_execution_failure: bool = False,
        variables_answers: VariablesAnswers | None = None,
        save_answers_as_personal: bool = False,
        allow_interactive_answering: bool = False,
    ) -> ExecutionStatus: ...

    @overload
    def execute(
        self,
        block_until_done: Literal[False] = False,
        variables_answers: VariablesAnswers | None = None,
        save_answers_as_personal: bool = False,
        allow_interactive_answering: bool = False,
    ) -> None: ...

    def execute(
        self,
        block_until_done: bool = True,
        pipe_logs: bool = False,
        raise_on_execution_failure: bool = False,
        variables_answers: VariablesAnswers | None = None,
        save_answers_as_personal: bool = False,
        allow_interactive_answering: bool = False,
    ) -> ExecutionStatus | None:
        """Start Script execution.

        Args:
            block_until_done (bool, optional): Whether to block the execution
                until it is done. Defaults to True.
            pipe_logs (bool, optional): Whether to pipe the execution logs
                to the logger while waiting for the execution to finish. Valid
                only if `block_until_done` is set. Defaults to False.
            raise_on_execution_failure (bool, optional): Whether to raise an
                exception if the execution fails. Valid only if
                `block_until_done` is set. Defaults to False.
            allow_interactive_answering (bool, optional): Whether to allow
                interactive answering of Variables if not all are answered.
                Defaults to False.

        Returns:
            ExecutionStatus: if `block_until_done` is set to True.
            Nothing otherwise.
        """

        variables = list(self.get_variables())

        if save_answers_as_personal:
            self.save_personal_variable_answers(variables_answers)

        return self._script_content.execute(
            variables=variables,
            answers=variables_answers,
            block_until_done=block_until_done,
            pipe_logs=pipe_logs,
            raise_on_execution_failure=raise_on_execution_failure,
            allow_interactive_answering=allow_interactive_answering,
        )

    def stop_execution(self) -> None:
        """Stops the Script execution."""

        return self._script_content.stop_execution()

    def get_execution_status(self) -> ExecutionStatus | None:
        """Retrieve current status of the Script execution.

        Returns:
            ExecutionStatus: Current status of the Script execution, or None if
                the Script is not currently running.
        """

        return self._script_content.get_current_execution_status()

    def wait_for_execution_finish(
        self, pipe_logs: bool = False, interval: int | None = None
    ) -> ExecutionStatus:
        """Wait until the Script execution is finished.

        Args:
            pipe_logs (bool, optional): Whether to pipe the execution logs of
                the Script to the console of this requester script. Defaults to
                False.
            interval (int, optional): Time interval in seconds between polling
                requests for status. If not provided, the value is taken from
                mstrio-py's `config`.

        Returns:
            ExecutionStatus: Final status of the Script execution.
        """

        return self._script_content.wait_for_execution_finish(
            pipe_logs=pipe_logs, interval=interval
        )

    def get_execution_details(self) -> dict:
        """Retrieve details about the Script current execution.

        Note:
            This property reads from Current Execution, hence refer to last run
            of the Script done by you specifically.

        Returns:
            dict: Details about the Script current execution.
        """

        return self._script_content.get_execution_details()

    def get_last_run_details(self) -> dict:
        """Gets the details about the last run of the Script, if any, including
        execution time, status and logs of the run.

        Note:
            This property reads from Run History, hence refer to last run of the
            Script overall, not necessarily your last run of this Script.

        Returns:
            dict: Dictionary with data about the last run of the Script,
                or empty dictionary if there is no history.
        """

        if self._script_content._evaluation_id:
            logger.info(
                "Script seems to be currently running so the data gathered may "
                "refer to a previous run, not current one."
            )

        self._history_last_entry = (
            scripts_processor.get_history(self.connection, self.id) or {}
        )

        return self._history_last_entry

    def _get_variable_factory(self) -> type['Variable']:
        match get_enum_val(
            self.script_usage_type, ScriptUsageType, throw_on_unknown=False
        ):
            case ScriptUsageType.DATASOURCE.value:
                return VariableDatasourceScript
            case ScriptUsageType.TRANSACTION.value:
                return VariableTransactionScript
            # TODO: add metric type when its Feature is ready
            case ScriptUsageType.STANDARD.value:
                return VariableStandardScript
            case _:
                raise ScriptSetupError(
                    "Unknown or unsupported Script Usage Type "
                    f"'{self.script_usage_type}'."
                )

    def _get_variables_personal_answers(self) -> dict[str, 'VariableAnswer']:
        if self._variables_personal_answers is None:
            try:
                self._variables_personal_answers = (
                    scripts_processor.get_variables_personal_answers(
                        self.connection, self.id
                    )
                )
            except (KeyError, ValueError):
                logger.warning(
                    "Getting Personal Default Answers for Variables failed. "
                    "Assuming none were set."
                )
                self._variables_personal_answers = {}

        return self._variables_personal_answers

    def get_variables(self) -> tuple['Variable']:
        """Get Variables saved in metadata of the Script.

        Returns:
            tuple[Variable]: Tuple of Variables associated with the Script.
        """

        Factory = self._get_variable_factory()

        # FYI: This is fine to recreate every time as usually there will be
        # around maybe 5 Variables. Even in edge cases there should be no more
        # than around 15. But even if there's 100, this is performant enough.
        variables = (
            tuple(
                (
                    # This keeps Variables types in sync with Script Usage Type.
                    # Below logic basically represents the following:
                    # 1. if an instance of exactly `Factory` class, keep it
                    # 2. build `Factory` class from...
                    #    a) if raw dict, from it directly
                    #    b) if an instance of other `Variable`, from its data
                    v
                    if isinstance(v, Factory)
                    else Factory.from_dict(
                        source=(
                            v.to_dict(skip_private_keys=True)
                            if isinstance(v, Variable)
                            else v
                        ),
                        connection=self._connection,
                    )
                )
                for v in self._variables
            )
            if self._variables
            else ()
        )

        for v in variables:
            v._source_script = self
            v._answer = None

        return variables

    def save_personal_variable_answers(
        self,
        answers: VariablesAnswers,
    ) -> None:
        """Save provided answers as personal default answers for Variables
        on the Script.

        Note:
            If some prompted Variables are not answered, current global default
            value for them will be used as your personal default. This is due to
            the REST API call requiring all prompted Variables to be provided
            at once.

        Args:
            answers (VariablesAnswers): Answers to be saved as personal
                default answers for Variables on the Script.
        """

        if not answers:
            raise ScriptSetupError("No answers were provided to be saved.")

        variables, answers = (
            self._script_content._convert_variables_and_answers_to_lists(
                variables=self.get_variables(),
                answers=answers,
                variables_factory=self._get_variable_factory(),
            )
        )

        if not all(
            isinstance(a, VariableAnswer) and a.is_valid() and a.source_variable.id
            for a in answers
        ):
            raise ScriptSetupError(
                "Some Variables or Variable answers provided to be saved as personal "
                "defaults are not valid. All provided answers need to be a valid "
                "Variable value for existing Variables and cannot be a flag to keep "
                "some default value."
            )

        answers = [a.to_dict() for a in answers]

        # FYI: API requires for all prompted variables to be provided in
        # payload. Below logic simulates not requiring that: by providing
        # global defaults if a variable is not answered.
        for var in (v for v in variables if v.prompt and not v.is_answered()):
            var.answer(keep_global_default=True)
            answers.append(var.get_answer_as_dict())

        scripts_processor.save_variables_personal_answers(
            self.connection,
            script_id=self.id,
            answers=answers,
        )

        # clear previous cache
        self._variables_personal_answers = None

    def add_variables(
        self,
        *data: 'Variable | dict',
    ) -> None:
        """Add Variables to the Script.

        Note:
            This method makes sure that provided data for new Variables is
            correct and valid before applying changes. If valid, saves to both
            metadata and locally.

        Args:
            *data (Variable | dict): Collected arbitrary amount of entries. For
                each Variable, an entry is either a Variable-class-based
                class instance or a dict with data to create a new Variable.

        Example:
        ```
            >>> script.add_variables(
            ...     {
            ...         "name": "var1",
            ...         "type": VariableType.TEXT,
            ...     },
            ...     VariableStandardScript(
            ...         name="var2",
            ...         type=VariableType.NUMERICAL,
            ...         prompt=True,
            ...     ),
            ... )
        ```
        """

        Factory = self._get_variable_factory()
        all_vars = self.get_variables()
        current_names = [v.name for v in all_vars]

        for v in data:
            if isinstance(v, dict):
                v = Factory.from_dict(v, self._connection)

            if not isinstance(v, Factory):
                raise ScriptSetupError(
                    f"Variable '{str(v)}' is not in valid shape. Make sure for "
                    "each new variable you provide a dict of valid data or "
                    f"instance of class {Factory.__name__}."
                )

            if v.name in current_names:
                raise ScriptSetupError(
                    f"Variable with name '{v.name}' already exists on {self}. Use "
                    "`Script.alter_variables(...)` method to edit an existing Variable."
                )

            current_names.append(v.name)

        self.alter(variables=list(all_vars) + list(data))

    def alter_variables(
        self,
        changes: dict[str, 'Variable | dict'] = None,  # FYI: `None` represent `{}`
    ) -> None:
        """Alter existing Variables on the Script.

        Note:
            This method makes sure that provided data for Variables to be
            altered is correct and valid before applying changes. If valid,
            saves to both metadata and locally.

        Args:
            changes (dict[str, Variable | dict]): Dictionary where keys are
                names or IDs of existing Variables to be altered, and values
                are either Variable-class-based class instances with new data
                or dicts with new data for the Variables.

        Example:
        ```
            >>> script.alter_variables({
            ...     "var1": {
            ...         "name": "new_variable_name",
            ...         "type": VariableType.TEXT,
            ...     },
            ...     "var2": VariableStandardScript(
            ...         name="another_new_name",
            ...         type=VariableType.NUMERICAL,
            ...         prompt=True,
            ...     ),
            ... })
        ```
        """

        # FYI: we allow not providing any changes if there were some changes
        # done locally to the existing Variables. Then, call to this method
        # just applies them to metadata
        changes = changes or {}

        Factory = self._get_variable_factory()
        all_vars = list(self.get_variables())
        current_names = [v.name for v in all_vars]

        for var_id_or_name, new_data in changes.items():
            target_var = Factory.get_variable_by_identifier(all_vars, var_id_or_name)

            if not target_var:
                raise ScriptSetupError(
                    f"Variable with identifier '{var_id_or_name}' does not exist on "
                    f"{self}. Cannot alter non-existing Variable."
                )

            if isinstance(new_data, Variable) and not isinstance(new_data, Factory):
                raise ScriptSetupError(
                    f"New data for Variable '{var_id_or_name}' is not in valid shape. "
                    "Make sure you provide either a dict of valid data or an instance "
                    f"of class {Factory.__name__}"
                )

            new_name = Variable._get_attr_from_variable(new_data, 'name')
            if new_name and new_name != target_var.name and new_name in current_names:
                raise ScriptSetupError(
                    f"Variable with name '{new_name}' already exists on {self}. "
                    "Cannot change to a name that is already in use by another "
                    "Variable."
                )

            current_names.append(new_name)

            idx = next(
                i
                for i, v in enumerate(all_vars)
                if v.name == var_id_or_name or v.id == var_id_or_name
            )
            all_vars[idx] = Factory.from_dict(
                {
                    **target_var.to_dict(),
                    **(new_data if isinstance(new_data, dict) else new_data.to_dict()),
                },
                self._connection,
            )

        self.alter(variables=all_vars)

    def delete_variables(
        self,
        *data: 'Variable | str',
    ) -> None:
        """Delete Variables from the Script.

        Note:
            This method makes sure that provided data for Variables to be
            deleted is correct and valid before applying changes. If valid,
            saves to both metadata and locally.

        Args:
            *data (Variable | str): Collected arbitrary amount of entries. For
                each Variable to be deleted, an entry is either a
                Variable-class-based class instance or the name/ID of the
                Variable as a string.

        Example:
        ```
            >>> script.delete_variables(
            ...     "var1",
            ...     VariableStandardScript(
            ...         name="var2",
            ...     ),
            ... )
        ```
        """

        if not all(isinstance(entry, (str, Variable)) for entry in data):
            raise ScriptSetupError(
                "At least one of provided arguments is not a valid type. "
                "All provided arguments must be either string representing name or ID "
                "of a Variable or Variable-based-class instance."
            )

        vars_for_remove = [
            entry.name if isinstance(entry, Variable) else entry for entry in data
        ]
        all_vars = self.get_variables()

        if not all(
            bool(Variable.get_variable_by_identifier(all_vars, var))
            for var in vars_for_remove
        ):
            raise ScriptSetupError(
                "At least one of provided arguments targets non-existing Variable. "
                "Please validate that you try to delete only existing Variables."
            )

        self.alter(
            variables=[
                v
                for v in all_vars
                if v.name not in vars_for_remove and v.id not in vars_for_remove
            ]
        )

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        code: Code | str | None = None,
        validate_code: bool = False,
        # TODO: improve with resolver during Module for Runtimes dev
        runtime_id: str | None = None,
        variables: 'list[Variable | dict] | None' = None,
        script_type: ScriptType | str | None = None,
        script_result_type: ScriptResultType | str | None = None,
    ) -> None:
        """Alter Script's properties.

        Note:
            Script Usage Type cannot be changed in an existing Script. One needs
            to create a new Script to "change" the Usage type.

        Args:
            name (str, optional): New name of the Script.
            description (str, optional): New description of the Script.
            code (Code | str, optional): New code for the Script, either as
                Code class instance or as string (either already
                base64-encoded or original).
            validate_code (bool, optional): Whether to validate the code
                syntax before alteration. Defaults to False. Is ignored if code
                is not modified. (This is a pre-run validation only and does
                not guarantee no Runtime Errors.)
            runtime_id (str, optional): ID of the Script runtime.
            variables (list[Variable | dict], optional): List of Variables to
                be set for the Script.
            script_type (ScriptType | str, optional): Type of the Script.
            script_result_type (ScriptResultType | str, optional): Result type
                of the Script.
        """

        if code is not None:
            code = Code(self.connection, code, validate_code=validate_code)

        params = {
            'name': name,
            'description': description,
            'script_content': code._code.encoded_text if code else None,
            'script_runtime_id': runtime_id,
            'variables': (
                [v.to_dict() if isinstance(v, Variable) else v for v in variables]
                if variables is not None
                else None
            ),
            'script_type': get_enum_val(script_type, ScriptType),
            'script_result_type': get_enum_val(script_result_type, ScriptResultType),
        }
        expects_empty_vars = params.get("variables") == []
        params = delete_none_values(params, recursion=False)

        if expects_empty_vars:
            params["variables"] = []
            self._variables = None

        self._alter_properties(**params)

        if variables is not None:
            # remove cache if we are updating variables
            self._variables_personal_answers = None

    def _alter_properties(self, **properties):
        if new_fid := properties.get('folder_id'):
            self._folder_id = new_fid

        # FYI: REST requires some params in alter ALWAYS, even if not changed
        properties['name'] = properties.get('name', self.name)
        properties['folder_id'] = properties.get('folder_id', self.folder_id)

        return super()._alter_properties(**properties)

    def list_properties(self, excluded_properties=None):
        ret = super().list_properties(excluded_properties)

        if not excluded_properties or 'variables' not in excluded_properties:
            ret['variables'] = self.get_variables() or ()
            #                                       <>
            #                                      \__/

        return ret

    def to_dict(self, camel_case=True):  # NOSONAR # (missing params)
        ret = super().to_dict(camel_case=camel_case, skip_private_keys=True)

        content_key = 'scriptContent' if camel_case else 'script_content'
        ret[content_key] = str(ret.get(content_key, ''))

        if "variables" in ret:
            Factory = self._get_variable_factory()
            ret["variables"] = [
                # FYI: REST have some "shallow"-ly calculated defaults
                # in metadata. This parsing removes invalid edge cases
                Factory.from_dict(v, self.connection).to_dict()
                for v in ret["variables"]
            ]

        return ret

    @property
    def source(self) -> dict:
        return self._source

    @property
    def code(self) -> str:
        return str(self._script_content)

    @property
    def script_type(self) -> ScriptType:
        return self._script_type

    @property
    def script_runtime_id(self) -> str | None:
        return self._script_runtime_id

    # TODO: deliver this prop during Runtimes Module dev
    # @property
    # def script_runtime_details(self):
    #     pass

    @property
    def script_usage_type(self) -> ScriptUsageType:
        match self.subtype:
            case ObjectSubTypes.DATASOURCE_SCRIPT:
                return ScriptUsageType.DATASOURCE
            case ObjectSubTypes.TRANSACTION_SCRIPT:
                return ScriptUsageType.TRANSACTION
            case ObjectSubTypes.SCRIPT | ObjectSubTypes.COMMAND_MANAGER_SCRIPT:
                return ScriptUsageType.STANDARD
            # TODO: add metric types when their Feature is done
            case ObjectSubTypes.JUPYTER_NOTEBOOK_SCRIPT:
                raise ScriptSetupError(
                    "Script of type Jupyter Notebook is not supported."
                )
            case _:
                raise ScriptSetupError(
                    f'Unrecognized or unsupported Script Subtype: {self.subtype}'
                )

    @property
    def script_result_type(self) -> ScriptResultType:
        return self._script_result_type or ScriptResultType.UNKNOWN

    @property
    def last_execution_time(self) -> datetime | None:
        """Execution time as `datetime` object. `None` only if the Script was
        never run on server-side.

        Note:
            This property reads from Run History, hence refer to last run of the
            Script overall, not necessarily your last run of this Script.
        """

        value = self._history_last_entry.get('executionTime')
        return datetime.fromisoformat(value) if value else None

    @property
    def last_run_status(self) -> str | None:
        """Status of the last run of the Script (whether successful or not).
        `None` only if the Script was never run on server-side.

        Note:
            This property reads from Run History, hence refer to last run of the
            Script overall, not necessarily your last run of this Script.
        """

        return self._history_last_entry.get('lastStatus')

    @property
    def last_run_logs(self) -> str | None:
        """Logs from the last run of the Script. `None` only if the Script was
        never run on server-side.

        Note:
            This property reads from Run History, hence all log levels (stdout
            and stderr) are merged into one string and refer to last run of the
            Script overall, not necessarily your last run of this Script.
        """

        return self._history_last_entry.get('log')

    @property
    def execution_status(self) -> ExecutionStatus | None:
        """Status from last made current execution status request."""

        return self._script_content.status

    @property
    def execution_stdout(self) -> str:
        """STDOUT from last made current execution status request."""

        return self._script_content.stdout

    @property
    def execution_stderr(self) -> str:
        """STDERR from last made current execution status request."""

        return self._script_content.stderr

    @property
    def execution_pod_executor_message(self) -> str | None:
        """Message from Python Executor (if any) in last made current execution
        status request.

        Usually populated with error details when Code in Script failed during
        runtime.
        """

        return self._script_content.executor_message

    @property
    def execution_result(self) -> CodeResult:
        """Returned Value from last made current execution status request."""

        return self._script_content.result

    @classmethod
    def create(
        cls,
        connection: 'Connection',
        name: str,
        # TODO: improve with resolver during Module for Runtimes dev
        runtime_id: str,
        code: Code | str,
        destination_folder: 'Folder | tuple[str] | list[str] | str | None' = None,
        destination_folder_path: tuple[str] | list[str] | str | None = None,
        description: str | None = None,
        variables: 'list[Variable | dict] | None' = None,
        script_type: ScriptType | str = ScriptType.PYTHON,
        script_usage_type: ScriptUsageType | str = ScriptUsageType.STANDARD,
        script_result_type: ScriptResultType | str | None = None,
        validate_code: bool = False,
    ) -> 'Script':
        """Create a new Script in Strategy.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`.
            name (str): Name of the Script.
            runtime_id (str): ID of the Script runtime.
            code (Code | str): Code class instance or code as a string, either
                base64-encoded or not
            destination_folder (Folder | tuple | list | str, optional): Folder
                object or ID or name or path specifying the folder where to
                create object.
            destination_folder_path (str, optional): Path of the folder.
                The path has to be provided in the following format:
                    /MicroStrategy Tutorial/Public Objects/Python Scripts
            description (str, optional): Description of the Script.
            variables (list[Variable | dict], optional): List of Variables'
                definitions (as raw dicts or as Variable class instances) to be
                saved in metadata of the Script.
            script_type (ScriptType | str, optional): Type of the Script.
                Defaults to ScriptType.PYTHON.
            script_usage_type (ScriptUsageType | str, optional): Usage type of
                the Script. Defaults to ScriptUsageType.STANDARD.
            script_result_type (ScriptResultType | str, optional): Result type
                of the Script. Defaults to None.
            validate_code (bool, optional): Whether to validate the code
                syntax before Script creation. Defaults to False. (This is a
                pre-run validation only and does not guarantee no Runtime
                Errors.)

        Returns:
            Script: Created Script class instance object.
        """

        connection._validate_project_selected()
        dest_id = get_folder_id_from_params_set(
            connection,
            connection.project_id,
            folder=destination_folder,
            folder_path=destination_folder_path,
        )

        new_obj_id = scripts_processor.create_script(
            connection=connection,
            name=name,
            runtime_id=runtime_id,
            encoded_code=Code(
                connection, code, validate_code=validate_code
            )._code.encoded_text,
            script_type=get_enum_val(script_type, ScriptType),
            folder_id=dest_id,
            description=description,
            variables=(
                [v.to_dict() if isinstance(v, Variable) else v for v in variables]
                if variables
                else None
            ),
            script_usage_type=get_enum_val(script_usage_type, ScriptUsageType),
            script_result_type=get_enum_val(script_result_type, ScriptResultType),
        )

        return Script(connection=connection, id=new_obj_id)


# --- Variables ---
_SYSTEM_PROMPTS_FOLDER_ID = "19BD7AE596A740C19341A88803DB87C2"


class SystemPrompt(Entity):
    """Simple representation of a System Prompt object."""

    _OBJECT_TYPE = ObjectTypes.PROMPT

    def __init__(self, connection: 'Connection', id: str):
        super().__init__(connection, object_id=id)

    @staticmethod
    def get_all(conn: 'Connection') -> list['SystemPrompt']:
        """Get all System Prompts available in the System Prompts Folder."""

        with config.temp_verbose_disable():
            return [
                SystemPrompt.from_dict(x, conn)
                for x in Folder(conn, id=_SYSTEM_PROMPTS_FOLDER_ID).get_contents(
                    to_dictionary=True
                )
            ]

    @staticmethod
    def get_by_name(conn: 'Connection', name: str) -> 'SystemPrompt':
        """Get System Prompt by its name."""

        try:
            return next(sp for sp in SystemPrompt.get_all(conn) if sp.name == name)
        except StopIteration:
            raise ScriptEnvironmentError(
                f"System Prompt with name '{name}' does not exist or "
                "cannot be accessed."
            )


class Variable(Dictable):
    """Script or Code Variable representation.

    Base Variable shape from which script-type-specific Variables inherit.
    """

    _FROM_DICT_MAP = {
        "type": VariableType,
        "object_ref": SystemPrompt.from_dict,
    }

    # descriptors
    name: str
    id: str | None = None
    type: 'VariableType | int' = VariableType.TEXT
    desc: str | None = None
    # shape (based on script type: which props are set may differ)
    multiple: bool | None = None
    prompt: bool | None = None
    transaction_column: bool | None = None
    nullable: bool | None = None
    required: bool | None = None
    editable: bool | None = None
    # actual answering and value
    value: VariableValue | None = None
    object_ref: 'SystemPrompt | dict | None' = None
    secret_value_input: bool | None = None

    _answer: 'VariableAnswer | FlagKeepDefaultAnswer | None' = None
    _source_script: 'Script | None' = None

    def __post_init__(self) -> None:
        """Post-calculation done after dataclass init.

        Note:
            Make sure to `super()`-call this in override methods.
        """
        # post-calculations
        # (required due to "shallow" REST defaults not covering edge cases)
        if self.transaction_column:
            if self.editable is None:
                self.editable = True

            # Falsy but not a list - reset to `None`
            if not self.value and not isinstance(self.value, list):
                self.value = None
        else:
            self.required = None
            self.nullable = None
            self.editable = None

        # validation
        if self.multiple:
            assert (self.value is None and self.prompt) or isinstance(
                self.value, list
            ), "When Variable is set to Multiple, its Value needs to be a list."
        else:
            assert (self.value is None and self.prompt) or not isinstance(
                self.value, list
            ), "When Variable is not set to Multiple, its Value cannot to be a list."

        is_multiple = self.multiple is True
        is_non_multi_type = self.type in [
            VariableType.DATE,
            VariableType.DATETIME,
            VariableType.SECRET,
            VariableType.SYSTEM_PROMPT,
        ]
        assert not (is_multiple and is_non_multi_type), (
            "Variables of type Date, Datetime, Secret or System Prompt cannot "
            "be set to Multiple."
        )

        if self.value is not None:
            assert VariableAnswer.is_of_valid_type(self, self.value), (
                "Value of the Variable is invalid. It does not correspond to "
                "the Variable's type properly."
            )

        assert self.type != VariableType.SYSTEM_PROMPT or (
            self.object_ref and not self.prompt
        ), (
            "System Prompt variable requires declared System Prompt to refer to "
            "and cannot be prompted."
        )

    def is_answered(self) -> bool:
        """Check whether the Variable has a valid answer.

        Returns:
            bool: True if the Variable is properly answered, False otherwise.
        """

        try:
            self.validate_whether_answered()
        except ScriptSetupError:
            return False
        return True

    def validate_whether_answered(self) -> None:
        """Validate whether the Variable is properly answered.
        Raises `ScriptSetupError` otherwise, with reasons.

        Raises:
            ScriptSetupError: When the Variable is not properly answered.
        """

        if not self.prompt:
            if self._answer:
                logger.warning(
                    f"Variable '{self.name}' is answered even though is not prompted. "
                    "Ignoring the invalid answer..."
                )
                self._answer = None

            if not VariableAnswer.is_of_valid_type(self, self.value):
                raise ScriptSetupError(
                    f"Variable '{self.name}' is not prompted and has invalid "
                    "or empty default value. Either make it prompted or set a "
                    "valid default value."
                )

            return

        if VariableAnswer.is_keep_default_flag(self._answer):
            value = (
                self.value
                if self._answer is VariableAnswer.KEEP_GLOBAL_DEFAULT
                else self.personal_default_answer
            )

            if (
                self.type != VariableType.SECRET
                and not VariableAnswer.is_of_valid_type(self, value)
            ):
                raise ScriptSetupError(
                    f"Variable '{self.name}' do not have a valid default value to "
                    "keep. Either make it prompted or set a valid default value."
                )

            return

        if not self._answer:
            raise ScriptSetupError(
                f"Variable '{self.name}' is prompted but not answered."
            )

        if not self._answer.is_valid():
            raise ScriptSetupError(
                f"Variable '{self.name}' has incorrect answer. Check whether types "
                "of Variable and its Answer match and whether the value is valid."
            )

    def answer(
        self,
        value: 'VariableValue | FlagKeepDefaultAnswer | None' = None,
        keep_personal_default: bool = False,
        keep_global_default: bool = False,
    ) -> 'VariableAnswer | FlagKeepDefaultAnswer':
        """Answer the Variable with the provided value (or a
        `FlagKeepDefaultAnswer` flag).

        Args:
            value (VariableValue | FlagKeepDefaultAnswer): Value to answer the
                Variable with or a flag to keep default value from a Variable.
                Optional only if `keep_default` flag is provided.
            keep_personal_default (bool): Whether to keep the personal default
                value from Variable as its answer. Defaults to False. If set to
                True, `value` parameter cannot be provided.
            keep_global_default (bool): Whether to keep the global default
                value from Variable as its answer. Defaults to False. If set to
                True, `value` parameter cannot be provided.

        Returns:
            VariableAnswer: Created answer for the Variable or a
                `FlagKeepDefaultAnswer` flag.
        """

        if keep_personal_default and keep_global_default:
            raise ScriptSetupError(
                "Cannot keep both personal and global default answer at the same time."
            )

        if not xor(value is not None, keep_personal_default or keep_global_default):
            raise ScriptSetupError(
                "Variable can either be answered with `value` or marked as "
                "`keep_<...>_default` but not both nor neither."
            )

        if keep_personal_default or value is VariableAnswer.KEEP_PERSONAL_DEFAULT:
            self._answer = VariableAnswer.KEEP_PERSONAL_DEFAULT
        elif keep_global_default or value is VariableAnswer.KEEP_GLOBAL_DEFAULT:
            self._answer = VariableAnswer.KEEP_GLOBAL_DEFAULT
        else:
            self._answer = VariableAnswer(self, value)

        self.validate_whether_answered()  # this will validate answer's structure
        return self._answer

    def get_answer_as_dict(self) -> dict:
        """Generate `to_dict` representation for REST execution request for
        Script class, where Script exists and have Variables definition stored
        in its metadata and we just need to provide actual answers.

        Note:
            This method assumes validation of the answer was already done.

        Returns:
            dict: Dictionary representation of the Variable's Answer.
        """

        if self._answer and not VariableAnswer.is_keep_default_flag(self._answer):
            return self._answer.to_dict()

        if self.type == VariableType.SECRET:
            # For SECRET we cannot gather true values from REST, so we need to
            # send empty value with a payload representing "use what you have
            # already in metadata"
            return VariableAnswer(self, value='', secret_value_input=False).to_dict()

        value = (
            self.value
            if self._answer is not VariableAnswer.KEEP_PERSONAL_DEFAULT
            else self.personal_default_answer
        )
        return VariableAnswer(self, value).to_dict()

    def get_answer_as_dict_for_non_script_run(self) -> dict:
        """Generate `to_dict` representation for REST execution request for
        Code class, where Script does not exist and full variable representation
        is required, non-prompted.

        It basically merges Variable definition and its Answer into one dict.

        Note:
            This method assumes validation of the answer was already done.

        Returns:
            dict: Dictionary representation of the Variable for non-Script run.
        """

        ret = self.to_dict(skip_private_keys=True)
        ret.update(self.get_answer_as_dict())
        ret['prompt'] = False
        ret['value'] = str(ret['value'])
        return ret

    @property
    def personal_default_answer(self) -> 'VariableValue':
        script = self._source_script
        vid = self.id

        if not vid or not script:
            raise ScriptSetupError(
                "Cannot gather or save personal answer to a Variable that is not "
                "saved in Script metadata on I-Server."
            )

        return script._get_variables_personal_answers().get(
            vid,
            # fall-back to global default if no personal answer was saved
            self.value,
        )

    @classmethod
    def from_dict(cls, *args, **kwargs):
        ret = super().from_dict(*args, **kwargs)
        if isinstance(cls, Variable):
            cls.__post_init__()  # NOSONAR
        return ret

    # TODO: consider improving typehint to all iterables, here and where
    # applicable after 3.10 is dropped (generics with params added in 3.11)
    @classmethod
    def get_variable_by_identifier(
        cls, variables: 'list[TVar]', id_or_name: str
    ) -> 'TVar | None':
        """Find Variable in the provided list by its ID or name.

        Args:
            variables (list[Variable | dict]): List of Variables to
                search in.
            id_or_name (str): ID or name of the Variable to find.

        Returns:
            Variable | dict | None: Found Variable or None if not found.
        """

        return next(
            (
                v
                for v in variables
                if (
                    Variable._get_attr_from_variable(v, 'id') == id_or_name
                    or Variable._get_attr_from_variable(v, 'name') == id_or_name
                )
            ),
            None,
        )

    @staticmethod
    def _get_attr_from_variable(variable: 'TVar', attr: str):
        if isinstance(variable, Variable):
            return getattr(variable, attr, None)

        if isinstance(variable, dict):
            return variable.get(attr)

        raise TypeError("Variable is neither Variable-class-based nor dict.")


TVar = TypeVar("TVar", Variable, dict)


@dataclass
class VariableStandardScript(Variable):
    """Simple representation of a Variable for Standard Scripts.

    Attributes:
        name: Variable name
        id: Variable ID
        type: Variable type
        desc: Variable description
        multiple: Whether the variable is a list of values
        prompt: Whether the variable prompts the user for input to be answered
        value: Variable default value, if any
        object_ref: For System Prompt variable, the System Prompt object
            referenced

    """

    name: str
    id: str | None = None
    type: 'VariableType | int' = VariableType.TEXT
    desc: str | None = None
    multiple: bool | None = False
    prompt: bool | None = True
    value: VariableValue | None = None
    object_ref: 'SystemPrompt | dict | None' = None

    def __post_init__(self) -> None:
        super().__post_init__()

        assert self.type != VariableType.TXN_ROW_PROVENANCE, (
            "For Standard Script, variable cannot be of type "
            "Transaction Provenance Column"
        )
        assert (
            isinstance(self.value, (str, int, float, date, datetime))
            # warning does not mention that secret will not be received from API
            # but it's by design
            or (self.id and self.type == VariableType.SECRET)
            or self.prompt
            or (self.object_ref and self.type == VariableType.SYSTEM_PROMPT)
        ), (
            "For Standard Script, variable needs to either have a value, "
            "be prompted or be a set System Prompt."
        )


@dataclass
class VariableDatasourceScript(Variable):
    """Simple representation of a Variable for Datasource Scripts.

    Attributes:
        name: Variable name
        id: Variable ID
        type: Variable type
        desc: Variable description
        multiple: Whether the variable is a list of values
        value: Variable default value, if any
    """

    name: str
    id: str | None = None
    type: 'VariableType | int' = VariableType.TEXT
    desc: str | None = None
    multiple: bool | None = False
    value: VariableValue | None = None

    def __post_init__(self):
        super().__post_init__()

        assert self.type not in [
            VariableType.TXN_ROW_PROVENANCE,
        ], (
            "For Datasource Script, variable cannot be of type "
            "Transaction Provenance Column"
        )


@dataclass
class VariableTransactionScript(Variable):
    """Simple representation of a Variable for Dashboard Transaction Scripts.

    Attributes:
        name: Variable name
        id: Variable ID
        type: Variable type
        desc: Variable description
        multiple: Whether the variable is a list of values
        prompt: Whether the variable prompts the user for input to be answered
        object_ref: For System Prompt variable, the System Prompt object
            referenced
        transaction_column: Whether the variable represents transaction column
        nullable: Whether the `transaction_column` variable can contain
            null values
        required: Whether the `transaction_column` variable is required to be
            answered in transaction dashboard
        editable: Whether the value of `transaction_column` variable in the
            transaction dashboard can be edited (or only added or removed)
    """

    name: str
    id: str | None = None
    type: 'VariableType | int' = VariableType.TEXT
    desc: str | None = None
    multiple: bool | None = False
    value: VariableValue | None = None
    prompt: bool | None = False
    object_ref: 'SystemPrompt | dict | None' = None
    transaction_column: bool | None = None
    nullable: bool | None = None
    required: bool | None = None
    editable: bool | None = None

    def __post_init__(self):
        super().__post_init__()

        if self.nullable or self.required or self.editable:
            assert self.transaction_column, (
                "Nullable, Required or Editable properties of a variable refer "
                "only to Transaction Column variable"
            )

        assert self.type != VariableType.TXN_ROW_PROVENANCE or (
            self.transaction_column
            and self.required
            and self.nullable is False
            and self.editable is False
        ), (
            "Transaction provenance Column variable needs to be explicitly set to "
            "Required and not Nullable and not Editable"
        )

        if self.transaction_column:
            assert self.value is None, "Transaction variable cannot have set value"
            assert (
                self.multiple and self.prompt
            ), "Transaction variable needs to be set to Multiple and Prompt"
            assert not (
                self.required and self.nullable
            ), "Required variable value cannot also be Nullable"
        else:
            assert (
                not self.prompt
            ), "For Transaction Script, non-transaction variables cannot be prompted"


# TODO: Finish and validate when the BHMO-105 Feature is released
# @dataclass
# class VariableMetricScript(Variable):
#     pass


@dataclass
class VariableAnswer(Variable):
    source_variable: 'Variable'
    value: VariableValue
    secret_value_input: bool = True

    def __post_init__(self):
        # FYI: explicitly not doing `super().__post_init__()`

        assert self.source_variable, "Cannot answer non-existent Variable"
        self.source_variable._answer = self

    def is_valid(self) -> bool:
        """Check whether the answer value is valid for the source variable.

        Returns:
            bool: True if the answer value is valid for the source variable.
        """

        is_non_prompted = self.source_variable.type in [
            VariableType.SYSTEM_PROMPT,
            VariableType.TXN_ROW_PROVENANCE,
        ]

        return not is_non_prompted and VariableAnswer.is_of_valid_type(
            self.source_variable, self.value
        )

    def to_dict(self, camel_case: bool = True):
        ret = super().to_dict(
            camel_case=camel_case,
            whitelist_keys=['value', 'secret_value_input'],
            skip_private_keys=True,
        )
        if vid := self.source_variable.id:
            ret['id'] = vid
        return ret

    @classmethod
    def is_of_valid_type(
        cls, source_variable: 'Variable', answer_value: VariableValue
    ) -> bool:
        """Check whether the provided answer value is of valid type for the
        source variable.

        Args:
            source_variable (Variable): Source Variable to check against.
            answer_value (VariableValue): Answer value to check.

        Returns:
            bool: True if the provided answer value is of valid type for the
                source variable.
        """

        if source_variable.multiple:
            if not isinstance(answer_value, (list, tuple)):
                return False

            mocked_var = deepcopy(source_variable)
            mocked_var.multiple = False

            return all(
                VariableAnswer.is_of_valid_type(mocked_var, value)
                for value in answer_value
            )

        is_number = source_variable.type == VariableType.NUMERICAL
        is_date = source_variable.type in [
            VariableType.DATE,
            VariableType.DATETIME,
        ]

        is_valid_number = is_number and isinstance(answer_value, (int, float))
        is_valid_date = is_date and is_valid_datetime(answer_value)
        is_valid_other = not is_date and not is_number and isinstance(answer_value, str)

        return is_valid_number or is_valid_date or is_valid_other

    @staticmethod
    def is_keep_default_flag(flag: Any) -> bool:
        return flag in [
            VariableAnswer.KEEP_GLOBAL_DEFAULT,
            VariableAnswer.KEEP_PERSONAL_DEFAULT,
        ]

    @staticmethod
    @property
    def KEEP_PERSONAL_DEFAULT() -> object:
        """Flag representing intention to keep personal-saved-default value of
        a Variable as an answer to the prompt-for-answer, instead of explicitly
        providing the answer.

        If no personal answer was saved, uses `KEEP_GLOBAL_DEFAULT` flag
        behavior instead.
        """
        # instance of singleton "nothing" to be compared via `is`
        return object()

    @staticmethod
    @property
    def KEEP_GLOBAL_DEFAULT() -> object:
        """Flag representing intention to keep global default value of a
        Variable as an answer to the prompt-for-answer, instead of explicitly
        providing the answer (even ignoring personal-saved-answer if it was
        set).

        Note:
            For `VariableType.SECRET` always defaults to `KEEP_PERSONAL_DEFAULT`
            if one is set.
        """
        # instance of singleton "nothing" to be compared via `is`
        return object()

    class For:
        """Helper method which exists solely to simplify answering prompted
        Variables in bulk.

        This allows to be used within `answers` params in `execute` methods in
        `Code` or `Script` to be provided as follows:

        ```
        >>> ...
        >>> answers=[
        >>>     VariableAnswer.For('var1').should_be('my-value'),
        >>>     VariableAnswer.For('var2').should_be_global_default,
        >>>     VariableAnswer.For('var3').should_be_personal_default,
        >>>     ...
        >>> ]
        >>> ...
        ```
        """

        def __init__(self, id_or_name: str):
            self.__id_or_name = id_or_name

        def should_be(self, value: 'VariableAnswer') -> 'AnswerForCallback':

            def __callback(
                variables: list['Variable'],
            ) -> 'VariableAnswer | FlagKeepDefaultAnswer':
                var = Variable.get_variable_by_identifier(variables, self.__id_or_name)

                if not var:
                    raise ScriptSetupError(
                        f"Variable with name or id '{self.__id_or_name}' does not "
                        "exist in available Variables collection."
                    )

                return var.answer(value)

            __callback._is_internal_mstrio = True

            return __callback

        @property
        def should_be_personal_default(self) -> 'AnswerForCallback':
            """Flag the Variable to keep personal default answer. If no such
            answer was saved, falls back to global default.
            """
            return self.should_be(VariableAnswer.KEEP_PERSONAL_DEFAULT)

        @property
        def should_be_global_default(self) -> 'AnswerForCallback':
            """Flag the Variable to keep global default answer.

            Note:
                For `VariableType.SECRET` always defaults to
                `should_be_personal_default` if one is set.
            """
            return self.should_be(VariableAnswer.KEEP_GLOBAL_DEFAULT)


# --- END: Variables ---
