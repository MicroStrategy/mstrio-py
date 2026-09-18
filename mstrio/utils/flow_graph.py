"""Compilation of validated Flow steps into a normalized graph."""

from dataclasses import dataclass
from typing import Any

from .flow_nodes.base import AnyEntry, EntrySteps, InvalidInput
from .flow_nodes.registry import get_node_spec


class FlowVariableExpression:
    """Deferred expression for a Flow variable in generated source."""

    def __init__(self, name: str):
        self.name = name


@dataclass(frozen=True)
class NormalizedEdge:
    """Typed edge in the normalized execution graph."""

    source_id: int
    kind: str
    target_id: int


@dataclass(frozen=True)
class NormalizedNode:
    """Typed normalized node with its graph edges."""

    node_id: int
    scope_id: int
    data: AnyEntry
    edges: tuple[NormalizedEdge, ...]

    def as_dict(self) -> AnyEntry:
        return dict(self.data)


def _describe_node(node: NormalizedNode) -> str:
    kind = node.data.get("kind")
    unique_id = node.data.get("unique_id")
    if isinstance(kind, str) and isinstance(unique_id, str):
        return f"{kind} node '{unique_id}'"
    if isinstance(kind, str):
        return f"{kind} node (internal ID {node.node_id})"
    return f"node (internal ID {node.node_id})"


@dataclass(frozen=True)
class NormalizedScope:
    """Typed execution scope and its source-order node list."""

    scope_id: int
    start: int | None
    node_ids: tuple[int, ...]

    def as_dict(self) -> AnyEntry:
        return {"start": self.start, "nodes": list(self.node_ids)}


@dataclass(frozen=True)
class NormalizedGraph:
    """Private typed IR used between graph compilation and source emission."""

    root_scope: int
    scopes: tuple[NormalizedScope, ...]
    nodes: tuple[NormalizedNode, ...]

    @classmethod
    def from_working_data(
        cls,
        root_scope: int,
        scopes: list[AnyEntry],
        nodes: list[AnyEntry],
        node_scopes: dict[int, int],
    ) -> "NormalizedGraph":
        normalized_scopes = tuple(
            NormalizedScope(
                scope_id=scope_id,
                start=scope["start"],
                node_ids=tuple(scope["_nodes"]),
            )
            for scope_id, scope in enumerate(scopes)
        )
        normalized_nodes = tuple(
            NormalizedNode(
                node_id=node_id,
                scope_id=node_scopes[node_id],
                data=dict(node),
                edges=tuple(
                    NormalizedEdge(node_id, key, node[key])
                    for key in _edge_keys(node)
                    if node.get(key) is not None
                ),
            )
            for node_id, node in enumerate(nodes)
        )
        return cls(root_scope, normalized_scopes, normalized_nodes)

    def validate(self) -> None:
        scope_ids = {scope.scope_id for scope in self.scopes}
        node_ids = {node.node_id for node in self.nodes}
        if self.root_scope not in scope_ids:
            raise InvalidInput("Compiled Flow has no valid root execution scope.")
        if scope_ids != set(range(len(self.scopes))):
            raise InvalidInput(
                "Compiled Flow execution scopes have invalid internal identifiers."
            )
        if node_ids != set(range(len(self.nodes))):
            raise InvalidInput("Compiled Flow nodes have invalid internal identifiers.")

        listed_nodes = [node_id for scope in self.scopes for node_id in scope.node_ids]
        if set(listed_nodes) != node_ids or len(listed_nodes) != len(node_ids):
            raise InvalidInput(
                "Compiled Flow nodes must belong to exactly one execution scope."
            )

        node_by_id = {node.node_id: node for node in self.nodes}
        scope_by_id = {scope.scope_id: scope for scope in self.scopes}
        for scope in self.scopes:
            expected_start = scope.node_ids[0] if scope.node_ids else None
            if scope.start != expected_start:
                raise InvalidInput(
                    "An execution scope does not start with its first declared node."
                )

        child_scope_owners: dict[int, tuple[int, str]] = {}
        for node in self.nodes:
            if node.scope_id not in scope_by_id:
                raise InvalidInput(
                    f"{_describe_node(node)} refers to a missing execution scope."
                )
            if node.node_id not in scope_by_id[node.scope_id].node_ids:
                raise InvalidInput(
                    f"{_describe_node(node)} is assigned to an execution scope "
                    "that does not contain it."
                )

            kind = node.data.get("kind")
            if not isinstance(kind, str):
                raise InvalidInput(f"{_describe_node(node)} has an invalid node type.")
            spec = get_node_spec(kind)
            control_flow = spec.control_flow
            if control_flow.fallthrough and "next" not in node.data:
                raise InvalidInput(
                    f"{_describe_node(node)} is missing its sequential continuation."
                )
            missing_outcomes = [
                outcome for outcome in control_flow.outcomes if outcome not in node.data
            ]
            if missing_outcomes:
                raise InvalidInput(
                    f"{_describe_node(node)} is missing outcomes: "
                    f"{', '.join(missing_outcomes)}."
                )
            if control_flow.reference_target and not any(
                edge.kind == "target" for edge in node.edges
            ):
                raise InvalidInput(f"{_describe_node(node)} has no target.")
            if control_flow.terminal and any(
                edge.kind == "next" for edge in node.edges
            ):
                raise InvalidInput(
                    f"Terminal node {_describe_node(node)} has a sequential "
                    "continuation."
                )

            expected_edges = tuple(
                NormalizedEdge(node.node_id, key, node.data[key])
                for key in _edge_keys(node.data)
                if node.data.get(key) is not None
            )
            if node.edges != expected_edges:
                raise InvalidInput(
                    f"{_describe_node(node)} has inconsistent transition metadata."
                )

            for edge in node.edges:
                if type(edge.target_id) is not int:
                    raise InvalidInput(
                        f"{_describe_node(node)} has an invalid "
                        f"'{edge.kind}' transition."
                    )
                if edge.target_id not in node_by_id:
                    raise InvalidInput(
                        f"{_describe_node(node)} points to a missing "
                        f"'{edge.kind}' target node."
                    )
                if node_by_id[edge.target_id].scope_id != node.scope_id:
                    raise InvalidInput(
                        f"{_describe_node(node)} cannot transition via "
                        f"'{edge.kind}' to "
                        f"{_describe_node(node_by_id[edge.target_id])} "
                        "(cross-scope edge)."
                    )

            for descriptor in control_flow.child_scopes:
                child_scope_ids = node.data.get(descriptor.name)
                if not isinstance(child_scope_ids, list) or not all(
                    type(scope_id) is int and scope_id in scope_by_id
                    for scope_id in child_scope_ids
                ):
                    raise InvalidInput(
                        f"{_describe_node(node)} has invalid child execution "
                        f"scopes for '{descriptor.name}'."
                    )
                if len(set(child_scope_ids)) != len(child_scope_ids):
                    raise InvalidInput(
                        f"{_describe_node(node)} declares the child execution "
                        f"scope '{descriptor.name}' more than once."
                    )
                for child_scope_id in child_scope_ids:
                    if child_scope_id == node.scope_id:
                        raise InvalidInput(
                            f"{_describe_node(node)} cannot contain itself as "
                            f"a child execution scope ('{descriptor.name}')."
                        )
                    if child_scope_id == self.root_scope:
                        raise InvalidInput(
                            f"{_describe_node(node)} cannot own the root "
                            "execution scope."
                        )
                    owner = child_scope_owners.setdefault(
                        child_scope_id,
                        (node.node_id, descriptor.name),
                    )
                    if owner != (node.node_id, descriptor.name):
                        owner_node = node_by_id[owner[0]]
                        raise InvalidInput(
                            f"{_describe_node(node)} cannot reuse a child "
                            f"execution scope already owned by "
                            f"{_describe_node(owner_node)}."
                        )

        if set(child_scope_owners) != scope_ids - {self.root_scope}:
            raise InvalidInput(
                "Every nested execution scope must be owned by exactly one "
                "Flow node."
            )
        parent_scopes = {
            child_scope_id: node_by_id[owner[0]].scope_id
            for child_scope_id, owner in child_scope_owners.items()
        }
        for scope_id in scope_ids - {self.root_scope}:
            visited_scopes = set()
            current_scope_id = scope_id
            while current_scope_id != self.root_scope:
                if current_scope_id in visited_scopes:
                    raise InvalidInput(
                        "Nested execution scopes must form a hierarchy rooted "
                        "in the root execution scope."
                    )
                visited_scopes.add(current_scope_id)
                current_scope_id = parent_scopes[current_scope_id]

    def as_dict(self) -> AnyEntry:
        return {
            "root_scope": self.root_scope,
            "scopes": [scope.as_dict() for scope in self.scopes],
            "nodes": [node.as_dict() for node in self.nodes],
        }


class FlowCompiler:
    """Compile YAML steps into deterministic nodes and execution scopes."""

    def __init__(self, steps: EntrySteps):
        self.steps = steps
        self.nodes: list[AnyEntry] = []
        self.scopes: list[AnyEntry] = []
        self._node_scopes: dict[int, int] = {}
        self._global_unique_ids: dict[str, list[int]] = {}
        self._explicit_step_ids = self._collect_explicit_step_ids(steps)

    def compile(self) -> AnyEntry:
        root_scope = self._collect_scope(self.steps)
        for scope in self.scopes:
            self._connect_list(scope["_root_list"], None)
        self._resolve_references()
        self._validate_cycles()

        graph = NormalizedGraph.from_working_data(
            root_scope,
            self.scopes,
            self.nodes,
            self._node_scopes,
        )
        graph.validate()
        return graph.as_dict()

    def _collect_explicit_step_ids(self, steps: EntrySteps) -> set[str]:
        step_ids = set()
        for step in steps:
            if step["type"] == "script" and "step_id" in step:
                step_ids.add(step["step_id"])
            node_spec = get_node_spec(step["type"])
            for _, outcome_steps in node_spec.outcome_step_lists(step):
                step_ids.update(self._collect_explicit_step_ids(outcome_steps))
            for _, child_steps in node_spec.child_scopes(step):
                step_ids.update(self._collect_explicit_step_ids(child_steps))
        return step_ids

    def _collect_scope(self, steps: EntrySteps) -> int:
        scope_id = len(self.scopes)
        scope = {
            "_root_list": None,
            "_unique_ids": {},
            "_nodes": [],
            "start": None,
        }
        self.scopes.append(scope)
        scope["_root_list"] = self._collect_list(scope_id, steps)
        scope["start"] = (
            scope["_root_list"]["nodes"][0] if scope["_root_list"]["nodes"] else None
        )
        return scope_id

    def _collect_list(self, scope_id: int, steps: EntrySteps) -> AnyEntry:
        scope = self.scopes[scope_id]
        node_ids = []
        for step in steps:
            node_id = len(self.nodes)
            node_spec = get_node_spec(step["type"])
            node = node_spec.compile(self, node_id, step)
            node_ids.append(node_id)
            self.nodes.append(node)
            scope["_nodes"].append(node_id)
            self._node_scopes[node_id] = scope_id
            scope["_unique_ids"].setdefault(step["unique_id"], []).append(node_id)
            self._global_unique_ids.setdefault(step["unique_id"], []).append(node_id)

            for outcome, outcome_steps in node_spec.outcome_step_lists(step):
                node[f"_{outcome}_list"] = self._collect_list(scope_id, outcome_steps)

            child_scope_ids: dict[str, list[int]] = {}
            for descriptor, child_steps in node_spec.child_scopes(step):
                if not descriptor.name or not descriptor.source_key:
                    raise RuntimeError(
                        f"Node type '{node_spec.type_name}' has an invalid "
                        "child-scope descriptor."
                    )
                if descriptor.name in node:
                    raise RuntimeError(
                        f"Node type '{node_spec.type_name}' reuses child-scope "
                        f"name '{descriptor.name}' in its payload."
                    )
                child_scope_ids.setdefault(descriptor.name, []).append(
                    self._collect_scope(child_steps)
                )
            node.update(child_scope_ids)
        return {"nodes": node_ids}

    def get_step_id(self, step: AnyEntry, node_id: int) -> str:
        if "step_id" in step:
            return step["step_id"]

        candidate = f"__flow_auto_{node_id}"
        while candidate in self._explicit_step_ids:
            candidate += "_"
        return candidate

    @staticmethod
    def compile_reference(reference: str) -> tuple[Any, ...]:
        source, output = reference.split(".", 1)
        if source == "flow_var":
            return ("flow_var", FlowVariableExpression(output))
        return ("step", source, output)

    def compile_variable(self, value: Any) -> tuple[Any, ...]:
        if isinstance(value, str):
            if value == "default":
                return ("default",)
            return self.compile_reference(value)

        source = self.compile_reference(value["source"])
        fallback = self.compile_fallback(value.get("fallback", "default"))
        return ("fallback", source, fallback)

    def compile_fallback(self, fallback: str) -> tuple[Any, ...]:
        if fallback == "default":
            return ("default",)
        return self.compile_reference(fallback)

    def compile_condition(self, condition: AnyEntry) -> tuple[Any, ...]:
        if condition["type"] == "weekday":
            return (
                "weekday",
                condition["value"],
                condition.get("timezone"),
            )

        return (
            "comparison",
            condition["operator"],
            self.compile_operand(condition["left"]),
            self.compile_operand(condition["right"]),
        )

    def compile_operand(self, operand: AnyEntry) -> tuple[Any, ...]:
        if operand["type"] == "constant":
            return ("constant", operand["value"])
        return ("reference", self.compile_reference(operand["name"]))

    def _connect_list(self, step_list: AnyEntry, continuation: int | None) -> None:
        node_ids = step_list["nodes"]
        for index, node_id in enumerate(node_ids):
            node = self.nodes[node_id]
            next_node = (
                node_ids[index + 1] if index + 1 < len(node_ids) else continuation
            )
            control_flow = get_node_spec(node["kind"]).control_flow
            if control_flow.fallthrough:
                node["next"] = next_node

            node_continuation = next_node
            for outcome in control_flow.outcomes:
                branch_list = node.pop(f"_{outcome}_list", None)
                if branch_list is None:
                    node[outcome] = node_continuation
                    continue

                node[outcome] = (
                    branch_list["nodes"][0]
                    if branch_list["nodes"]
                    else node_continuation
                )
                self._connect_list(branch_list, node_continuation)

    def _resolve_references(self) -> None:
        for node_id, node in enumerate(self.nodes):
            if not get_node_spec(node["kind"]).control_flow.reference_target:
                continue

            scope = self.scopes[self._node_scopes[node_id]]
            local_matches = scope["_unique_ids"].get(node["target_unique_id"], [])
            if len(local_matches) == 1:
                node["target"] = local_matches[0]
                node.pop("target_unique_id")
                continue
            if len(local_matches) > 1:
                raise InvalidInput(
                    f"Ref target '{node['target_unique_id']}' is ambiguous "
                    "within its execution scope."
                )

            if node["target_unique_id"] in self._global_unique_ids:
                raise InvalidInput(
                    f"Ref target '{node['target_unique_id']}' crosses an "
                    "execution-scope boundary."
                )
            raise InvalidInput(
                f"Ref target '{node['target_unique_id']}' does not exist "
                "within its execution scope."
            )

    def _validate_cycles(self) -> None:
        for scope in self.scopes:
            node_ids = set(scope["_nodes"])
            components = _strongly_connected_components(
                node_ids,
                self.nodes,
            )
            for component in components:
                is_cycle = len(component) > 1 or any(
                    target in component
                    for node_id in component
                    for target in _node_targets(self.nodes[node_id])
                )
                if is_cycle and not any(
                    self.nodes[node_id]["kind"] in ("script", "sleep", "parallel")
                    for node_id in component
                ):
                    raise InvalidInput(
                        "Flow contains a cyclic component with no script, "
                        "sleep, or parallel step."
                    )


def _node_targets(node: AnyEntry) -> list[int]:
    edge_keys = _edge_keys(node)
    return [target for key in edge_keys if (target := node.get(key)) is not None]


def _edge_keys(node: AnyEntry) -> tuple[str, ...]:
    control_flow = get_node_spec(node["kind"]).control_flow
    keys = ("next",) if control_flow.fallthrough else ()
    keys += control_flow.outcomes
    if control_flow.reference_target:
        keys += ("target",)
    return keys


def _strongly_connected_components(
    node_ids: set[int], nodes: list[AnyEntry]
) -> list[set[int]]:
    adjacency = {
        node_id: [
            target for target in _node_targets(nodes[node_id]) if target in node_ids
        ]
        for node_id in node_ids
    }
    reverse_adjacency = {node_id: [] for node_id in node_ids}
    for node_id, targets in adjacency.items():
        for target in targets:
            reverse_adjacency[target].append(node_id)

    visited = set()
    finish_order = []
    for start in sorted(node_ids):
        if start in visited:
            continue
        visited.add(start)
        stack = [(start, 0)]
        while stack:
            node_id, target_index = stack[-1]
            targets = adjacency[node_id]
            if target_index == len(targets):
                stack.pop()
                finish_order.append(node_id)
                continue

            target = targets[target_index]
            stack[-1] = (node_id, target_index + 1)
            if target not in visited:
                visited.add(target)
                stack.append((target, 0))

    components = []
    assigned = set()
    for start in reversed(finish_order):
        if start in assigned:
            continue
        component = set()
        stack = [start]
        assigned.add(start)
        while stack:
            node_id = stack.pop()
            component.add(node_id)
            for source in reverse_adjacency[node_id]:
                if source not in assigned:
                    assigned.add(source)
                    stack.append(source)
        components.append(component)
    return components


def compile_flow_graph(steps: EntrySteps) -> AnyEntry:
    """Compile validated Flow steps into a normalized execution graph."""
    return FlowCompiler(steps).compile()
