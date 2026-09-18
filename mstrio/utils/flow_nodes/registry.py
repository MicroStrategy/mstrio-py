"""Built-in Flow node registry."""

from typing import Any

from .base import BaseNode, InvalidInput
from .decision import DecisionNode
from .exit import ExitNode
from .noop import NoopNode
from .parallel import ParallelNode
from .ref import RefNode
from .script import ScriptNode
from .sleep import SleepNode

_BUILTIN_NODE_SPECS = (
    ScriptNode,
    SleepNode,
    ParallelNode,
    NoopNode,
    DecisionNode,
    ExitNode,
    RefNode,
)


def _build_registry(
    node_specs: tuple[type[BaseNode], ...],
) -> dict[str, type[BaseNode]]:
    registry: dict[str, type[BaseNode]] = {}
    for node_spec in node_specs:
        if node_spec.type_name in registry:
            raise RuntimeError(f"Duplicate Flow node type: '{node_spec.type_name}'.")
        registry[node_spec.type_name] = node_spec
    return registry


NODE_SPECS = _build_registry(_BUILTIN_NODE_SPECS)


def get_node_spec(type_name: Any) -> type[BaseNode]:
    if not isinstance(type_name, str):
        raise InvalidInput(f"Unknown type of step: {type_name!r}.")

    try:
        return NODE_SPECS[type_name]
    except KeyError:
        raise InvalidInput(f"Unknown type of step: '{type_name}'.")
