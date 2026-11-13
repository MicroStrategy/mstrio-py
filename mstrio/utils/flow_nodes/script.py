"""Script Flow node specification."""

import re

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    MappingEmitter,
    ValidationContext,
)
from .common import (
    CURRENT_PROJECT_ID_VARIABLE,
    REGEX_PATTERN,
    all_keys_present,
    validate_object_entry,
    validate_variable_definition,
)


class ScriptNode(BaseNode):
    type_name = "script"
    control_flow = ControlFlowSpec(outcomes=("on_success", "on_fail"))
    runtime_handler_name = "_run_script_node"
    runtime_required_helpers = (
        "ExecutionStatus",
        "Script",
        "_build_variable_answers",
        "_get_script_exit_code",
        "_wait_for_flow_script",
        "dt",
        "glob",
        "log",
    )
    runtime_source_text = r"""
def _run_script(node, state):
    script_data = node["script"]
    step_id = script_data["step_id"]
    with (
        conn_lock,  # noqa: F821
        conn.temporary_project_change(script_data["project_id"]),  # noqa: F821
    ):
        log("SCRIPT_PRE", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
        script = Script(conn, id=script_data["id"])  # noqa: F821
        glob[f"_{step_id}"] = script

    script.execute(
        block_until_done=False,
        variables_answers=_build_variable_answers(script_data["variables"], script),
    )
    result = _wait_for_flow_script(script)
    log(
        "SCRIPT_POST",
        node["unique_id"],
        {
            "status": script.execution_status.value,
            "stdout": script.execution_stdout,
            "stderr": script.execution_stderr,
            "output": script.execution_result,
            "message": script.execution_pod_executor_message,
            "exit_code": _get_script_exit_code(script),
            "timestamp": str(dt.datetime.now(dt.timezone.utc)),
        },
    )
    state.last_script_error = (
        (
            f"Script '{script.name}', ID '{script.id}' "
            f"Project '{script.project_id}', failed with error:\n"
            f"{script.execution_pod_executor_message}"
        )
        if script.execution_pod_executor_message
        else None
    )
    return not ExecutionStatus.is_error(result)


def _run_unconfigured_script(node, state):
    message = "This step needs manual configuration before it can run."
    timestamp = str(dt.datetime.now(dt.timezone.utc))
    log("SCRIPT_PRE", node["unique_id"], timestamp)
    log(
        "SCRIPT_POST",
        node["unique_id"],
        {
            "status": ExecutionStatus.ERROR.value,
            "stdout": "",
            "stderr": message,
            "output": None,
            "message": message,
            "exit_code": 1,
            "timestamp": timestamp,
        },
    )
    state.last_script_error = message
    return False


def _run_script_node(graph, node, state):
    unconfigured = node.get("requires_configuration", False)
    success = (
        _run_unconfigured_script(node, state)
        if unconfigured
        else _run_script(node, state)
    )
    if node["has_conditionals"]:
        log(
            "SCRIPT_COND_S" if success else "SCRIPT_COND_F",
            node["unique_id"],
            str(dt.datetime.now(dt.timezone.utc)),
        )
    fails_run = unconfigured or node.get("fail_on_unhandled_error")
    if not success and fails_run and not node["has_on_fail"]:
        raise RuntimeError(state.last_script_error or "A Flow step failed.")
    return node["on_success" if success else "on_fail"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        context: ValidationContext,
    ) -> None:
        for field in ("fail_on_unhandled_error", "requires_configuration"):
            if field in entry and type(entry[field]) is not bool:
                raise InvalidInput(f"Script Entry `{field}` should be a boolean.")
        if entry.get("requires_configuration"):
            # An unconfigured step never runs, so its object is no dependency.
            if "object" in entry and not validate_object_entry(entry["object"]):
                raise InvalidInput(f"Script Entry has invalid format: {entry}.")
        elif not all_keys_present(entry, ["object"]) or not validate_object_entry(
            entry["object"], context
        ):
            raise InvalidInput(f"Script Entry has invalid format: {entry}.")

        if "step_id" in entry and (
            not isinstance(entry["step_id"], str)
            or entry["step_id"] == "flow_var"
            or not re.fullmatch(REGEX_PATTERN, entry["step_id"])
        ):
            raise InvalidInput(
                f"If provided, `step_id` should match pattern `{REGEX_PATTERN}` and "
                'not be equal to "flow_var", '
                f"is: {entry['step_id']}."
            )

        if "variables" in entry:
            variables = entry["variables"]
            if not isinstance(variables, dict):
                raise InvalidInput(
                    f"`variables` key should contain a dictionary if provided, is: "
                    f"{variables}."
                )
            for variable in variables.values():
                validate_variable_definition(variable)

    @classmethod
    def compile(
        cls, compiler: CompileContext, node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        script_object = entry.get("object") or {}
        node = {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "has_on_success": bool(entry.get("on_success")),
            "has_on_fail": bool(entry.get("on_fail")),
            "has_conditionals": bool(entry.get("on_success") or entry.get("on_fail")),
            "script": {
                "id": script_object.get("id"),
                "project_id": script_object.get("project_id"),
                "step_id": compiler.get_step_id(entry, node_id),
                "variables": {
                    name: compiler.compile_variable(value)
                    for name, value in entry.get("variables", {}).items()
                },
            },
        }
        if entry.get("fail_on_unhandled_error"):
            node["fail_on_unhandled_error"] = True
        if entry.get("requires_configuration"):
            node["requires_configuration"] = True
        return node

    @classmethod
    def emit(cls, node: AnyEntry, emit_mapping: MappingEmitter) -> str:
        script = node["script"]
        if script["project_id"] != CURRENT_PROJECT_ID_VARIABLE:
            return super().emit(node, emit_mapping)

        return emit_mapping(
            node,
            {
                "script": emit_mapping(
                    script, {"project_id": CURRENT_PROJECT_ID_VARIABLE}
                )
            },
        )
