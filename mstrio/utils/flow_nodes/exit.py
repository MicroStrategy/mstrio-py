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
    runtime_required_helpers = ("FlowExitStep",)
    runtime_source_text = r"""
def _run_exit_node(graph, node, state):
    raise FlowExitStep(node["message"] or state.last_script_error or "UNKNOWN ERROR")
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
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
        }
