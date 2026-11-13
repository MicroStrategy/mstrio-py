"""Exit Flow node specification."""

from mstrio.utils.exit_code import validate_exit_code

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)
from .common import validate_variable_reference


class ExitNode(BaseNode):
    type_name = "exit"
    control_flow = ControlFlowSpec(fallthrough=False, terminal=True)
    runtime_handler_name = "_run_exit_node"
    runtime_required_helpers = (
        "_MISSING",
        "_resolve_reference",
        "dt",
        "log",
        "validate_exit_code",
    )
    runtime_support_source_text = r"""
import sys


class ExitSignal(FlowControlSignal):
    def __init__(self, exit_code, reason):
        super().__init__(reason)
        self.exit_code = exit_code
        self.terminal_status = "success" if exit_code == 0 else "fail"
        self.reason = reason

    def resolve(self):
        stream = sys.stdout if self.terminal_status == "success" else sys.stderr
        print("-" * 80, file=stream)
        print(self.reason, file=stream)
        if self.terminal_status == "success":
            return None
        sys.exit(self.exit_code)
"""
    runtime_source_text = r"""
def _run_exit_node(graph, node, state):
    exit_code = node["exit_code"]
    source = node.get("exit_code_source")
    if source is not None:
        try:
            exit_code = _resolve_reference(exit_code)
            if exit_code is _MISSING:
                raise ValueError(f"Exit code reference '{source}' is unavailable.")
        except (KeyError, NameError, ValueError) as error:
            raise ValueError(
                f"Exit node '{node['unique_id']}' has an invalid `exit_code` "
                f"from {source!r}: {error}"
            ) from error

    exit_code_error = None
    try:
        exit_code = validate_exit_code(exit_code)
    except ValueError as error:
        if source is None:
            raise
        exit_code_error = f"Invalid exit code from {source!r}: {error}"
        exit_code = 1

    terminal_status = "success" if exit_code == 0 else "fail"
    reason = node["message"] or state.last_script_error or ""
    data = {
        "status": terminal_status,
        "exit_code": exit_code,
        "reason": reason,
        "timestamp": str(dt.datetime.now(dt.timezone.utc)),
    }
    if exit_code_error is not None:
        data["exit_code_error"] = exit_code_error
    log("EXIT_POST", node["unique_id"], data)
    raise ExitSignal(exit_code, reason)
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        if "exit_code" in entry:
            value = entry["exit_code"]
            if isinstance(value, str):
                validate_variable_reference(value)
            else:
                try:
                    validate_exit_code(value)
                except ValueError as error:
                    raise InvalidInput(f"Exit Entry `exit_code`: {error}") from error
        elif "terminal_status" in entry and entry["terminal_status"] not in (
            "success",
            "fail",
        ):
            raise InvalidInput(
                "Exit Entry `terminal_status` should be either 'success' or 'fail'."
            )

        if "message" in entry:
            if not isinstance(entry["message"], str):
                raise InvalidInput("Exit Entry `message` should be a string.")
            return

        previous_step_provides_error = (
            previous_entry
            and previous_entry["type"] in ("script", "parallel")
            and "on_fail" in previous_entry
            and previous_entry["on_fail"]
            and previous_entry["on_fail"][0] is entry
        )
        if not previous_step_provides_error:
            raise InvalidInput(
                "Exit Entry without custom message can only be used directly "
                "in a Script or Parallel Entry `on_fail` conditional."
            )

    @classmethod
    def compile(
        cls, compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        exit_code = entry.get(
            "exit_code", 0 if entry.get("terminal_status") == "success" else 1
        )
        node = {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "message": entry.get("message", ""),
            "exit_code": exit_code,
        }
        if isinstance(exit_code, str):
            node["exit_code"] = compiler.compile_variable(exit_code)
            node["exit_code_source"] = exit_code
        return node
