"""Exit Flow node specification."""

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)


class ExitNode(BaseNode):
    type_name = "exit"
    control_flow = ControlFlowSpec(fallthrough=False, terminal=True)
    runtime_handler_name = "_run_exit_node"
    runtime_required_helpers = ("dt", "log")
    runtime_support_source_text = r"""
import sys


class ExitSignal(FlowControlSignal):
    def __init__(self, terminal_status, reason):
        super().__init__(reason)
        self.terminal_status = terminal_status
        self.reason = reason

    def resolve(self):
        stream = sys.stdout if self.terminal_status == "success" else sys.stderr
        print("-" * 80, file=stream)
        print(self.reason, file=stream)
        if self.terminal_status == "success":
            return None
        sys.exit(1)
"""
    runtime_source_text = r"""
def _run_exit_node(graph, node, state):
    reason = node["message"] or state.last_script_error or ""
    log(
        "EXIT_POST",
        node["unique_id"],
        {
            "status": node["terminal_status"],
            "reason": reason,
            "timestamp": str(dt.datetime.now(dt.timezone.utc)),
        },
    )
    raise ExitSignal(node["terminal_status"], reason)
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        if "terminal_status" in entry and entry["terminal_status"] not in (
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
        cls, _compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "message": entry.get("message", ""),
            "terminal_status": entry.get("terminal_status", "fail"),
        }
