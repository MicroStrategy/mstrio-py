"""Reference Flow node specification."""

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)


class RefNode(BaseNode):
    type_name = "ref"
    control_flow = ControlFlowSpec(
        fallthrough=False,
        terminal=True,
        reference_target=True,
    )
    runtime_handler_name = "_run_ref_node"
    runtime_source_text = r"""
def _run_ref_node(graph, node, state):
    return node["target"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        if not isinstance(entry.get("target"), str):
            raise InvalidInput("Ref Entry `target` should be a string.")

    @classmethod
    def compile(
        cls, _compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "target_unique_id": entry["target"],
        }
