"""Emit standalone Python source for a normalized Flow graph."""

import ast
from functools import partial
from importlib import resources
from textwrap import dedent
from textwrap import indent as _indent_orig
from typing import Any, Callable, Literal

from .flow_graph import FlowVariableExpression
from .flow_nodes.base import BaseNode
from .flow_nodes.common import validate_variable_reference
from .flow_nodes.registry import NODE_SPECS

INDENTATION = " " * 4
FLOW_ENGINE_RESOURCE = resources.files("mstrio.utils").joinpath("flow_engine.py")
GLOBALS = FLOW_ENGINE_RESOURCE.read_text(encoding="utf-8").strip()
AnyEntry = dict[str, Any]

indent_once: Callable[[str], str] = partial(
    _indent_orig, prefix=INDENTATION, predicate=None
)


def _emit_literal(value: Any) -> str:
    if isinstance(value, FlowVariableExpression):
        return f"(lambda: ${value.name})"
    if isinstance(value, dict):
        return (
            "{"
            + ", ".join(
                f"{_emit_literal(key)}: {_emit_literal(item)}"
                for key, item in value.items()
            )
            + "}"
        )
    if isinstance(value, list):
        return "[" + ", ".join(_emit_literal(item) for item in value) + "]"
    if isinstance(value, tuple):
        content = ", ".join(_emit_literal(item) for item in value)
        if len(value) == 1:
            content += ","
        return "(" + content + ")"
    return repr(value)


def merge_code_sections(sections: list[str]) -> str:
    return "\n".join(sections).strip()


def _defined_symbols(source: str) -> set[str]:
    tree = ast.parse(source, filename="<flow-engine>")
    symbols = set()
    for statement in tree.body:
        if isinstance(
            statement,
            (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef),
        ):
            symbols.add(statement.name)
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            symbols.update(
                alias.asname or alias.name.split(".", 1)[0] for alias in statement.names
            )
        elif isinstance(statement, ast.Assign):
            symbols.update(
                target.id
                for target in statement.targets
                if isinstance(target, ast.Name)
            )
        elif isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            symbols.add(statement.target.id)
    return symbols


ENGINE_SYMBOLS = _defined_symbols(GLOBALS)


def _validated_runtime_source(kind: str, node_spec: type[BaseNode]) -> str:
    source = dedent(node_spec.runtime_source()).strip()
    tree = ast.parse(source, filename=f"<{kind}-runtime>")
    function_names = {
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.AsyncFunctionDef, ast.FunctionDef))
    }
    handler_name = node_spec.runtime_handler_name
    if not handler_name or handler_name not in function_names:
        raise RuntimeError(
            f"Runtime source for node type '{kind}' does not define "
            f"'{handler_name}'."
        )

    missing_helpers = set(node_spec.runtime_required_helpers) - (
        ENGINE_SYMBOLS | {"conn", "conn_lock"}
    )
    if missing_helpers:
        missing = ", ".join(sorted(missing_helpers))
        raise RuntimeError(
            f"Runtime source for node type '{kind}' requires unavailable "
            f"engine helpers: {missing}."
        )
    return source


def generate_code_for_connection(
    connection_entry: AnyEntry | Literal["get_connection"],
) -> str:
    if connection_entry == "get_connection":
        return "conn = get_connection(workstationData)\nconn_lock = t.Lock()"

    lines = ["conn = Connection("]
    for key, var_name in connection_entry.items():
        lines.append(indent_once(f"{key}=${var_name.removeprefix('flow_var.')},"))
    lines.append(")")
    lines.append("conn_lock = t.Lock()")
    return "\n".join(lines)


def build_variable_reference(reference: str) -> str:
    validate_variable_reference(reference)
    source, output = reference.split(".", 1)
    if source == "flow_var":
        return f"${output}"

    property_name = {
        "stdout": "execution_stdout",
        "return": "execution_result",
        "error": "execution_pod_executor_message",
    }[output]
    return f"glob['_{source}'].{property_name}"


def _runtime_sections(graph: AnyEntry) -> list[str]:
    node_kinds = {node["kind"] for node in graph["nodes"]}
    sections = []
    handlers = []
    for kind, node_spec in NODE_SPECS.items():
        if kind not in node_kinds:
            continue

        source = _validated_runtime_source(kind, node_spec)
        try:
            ast.parse(source, filename=f"<{kind}-runtime>")
        except SyntaxError as error:
            raise SyntaxError(
                f"Invalid runtime source for node type '{kind}'."
            ) from error

        sections.append(source)
        handlers.append(f"    {kind!r}: {node_spec.runtime_handler_name},")

    sections.append("_NODE_HANDLERS = {\n" + "\n".join(handlers) + "\n}")
    return sections


def emit_flow_code(
    graph: AnyEntry,
    connection_entry: AnyEntry | Literal["get_connection"] | None = None,
    include_globals: bool = True,
) -> str:
    sections = [GLOBALS] if include_globals else []
    if connection_entry is not None:
        sections.append(generate_code_for_connection(connection_entry))

    return merge_code_sections(
        [
            *sections,
            *_runtime_sections(graph),
            f"_FLOW_GRAPH = {_emit_literal(graph)}",
            "_run_flow(_FLOW_GRAPH)",
        ]
    )
