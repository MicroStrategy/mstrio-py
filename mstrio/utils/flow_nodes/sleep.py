"""Sleep Flow node specification."""

from .base import AnyEntry, BaseNode, CompileContext, InvalidInput, ValidationContext
from .common import all_keys_present, normalize_sleep_duration


class SleepNode(BaseNode):
    type_name = "sleep"
    runtime_handler_name = "_run_sleep_node"
    runtime_required_helpers = ("_flow_sleep", "dt", "log")
    runtime_source_text = r"""
def _run_sleep_node(graph, node, state):
    log("SLEEP_PRE", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
    _flow_sleep(node["duration"])
    log("SLEEP_POST", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
    return node["next"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        try:
            if not all_keys_present(entry, ["duration"]):
                raise ValueError()
            normalize_sleep_duration(entry["duration"])
        except (ValueError, KeyError):
            raise InvalidInput(f"Sleep Entry has invalid format: {entry}.")

    @classmethod
    def compile(
        cls, _compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "duration": normalize_sleep_duration(entry["duration"]),
        }
