"""Script Flow node specification."""

import re

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)
from .common import (
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
        variables_answers=_build_variable_answers(script_data["variables"]),
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


def _run_script_node(graph, node, state):
    success = _run_script(node, state)
    if node["has_conditionals"]:
        log(
            "SCRIPT_COND_S" if success else "SCRIPT_COND_F",
            node["unique_id"],
            str(dt.datetime.now(dt.timezone.utc)),
        )
    return node["on_success" if success else "on_fail"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        context: ValidationContext,
    ) -> None:
        if not all_keys_present(entry, ["object"]) or not validate_object_entry(
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
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "has_on_success": bool(entry.get("on_success")),
            "has_on_fail": bool(entry.get("on_fail")),
            "has_conditionals": bool(entry.get("on_success") or entry.get("on_fail")),
            "script": {
                "id": entry["object"]["id"],
                "project_id": entry["object"]["project_id"],
                "step_id": compiler.get_step_id(entry, node_id),
                "variables": {
                    name: compiler.compile_variable(value)
                    for name, value in entry.get("variables", {}).items()
                },
            },
        }
