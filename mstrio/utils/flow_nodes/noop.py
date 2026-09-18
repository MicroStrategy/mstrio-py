"""No-op Flow node specification."""

from .base import AnyEntry, BaseNode, CompileContext, ValidationContext


class NoopNode(BaseNode):
    type_name = "noop"
    runtime_handler_name = "_run_noop_node"
    runtime_source_text = r"""
def _run_noop_node(graph, node, state):
    return node["next"]
"""

    @classmethod
    def validate(
        cls,
        _entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        return

    @classmethod
    def compile(
        cls, _compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
        }
