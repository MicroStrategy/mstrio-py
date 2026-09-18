"""Parallel Flow node specification."""

from threading import TIMEOUT_MAX

from .base import (
    AnyEntry,
    BaseNode,
    ChildScopeDescriptor,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)
from .common import all_keys_present

DEFAULT_PARALLEL_TIMEOUT_SECONDS = 10_800


class ParallelNode(BaseNode):
    type_name = "parallel"
    control_flow = ControlFlowSpec(
        outcomes=("on_success", "on_fail"),
        child_scopes=(
            ChildScopeDescriptor(
                name="branches",
                source_key="branches",
                scope_kind="parallel_branch",
            ),
        ),
    )
    runtime_handler_name = "_run_parallel_node"
    runtime_required_helpers = (
        "FlowExitStep",
        "ParallelExecutionAborted",
        "ParallelExecutionContext",
        "ParallelTimeoutError",
        "PropagatingThread",
        "_current_parallel_context",
        "_join_threads_until",
        "_run_branch",
        "dt",
        "log",
        "operator",
        "time",
    )
    runtime_source_text = r"""
def _run_parallel(graph, node, state):
    log("PARALLEL_PRE", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
    context = ParallelExecutionContext(
        node["timeout_seconds"],
        parent=_current_parallel_context(),
    )
    branches = [
        PropagatingThread(
            target=_run_branch,
            args=(graph, scope_id, context),
            daemon=True,
        )
        for scope_id in node["branches"]
    ]
    [thread.start() for thread in branches]
    for thread in branches:
        thread.join(context.remaining_seconds())

    thread_states = []
    for thread in branches:
        was_alive = thread.is_alive()
        error = thread.join(0)
        finished_at = getattr(thread, "_finished_at", None)
        thread_states.append((was_alive, error, finished_at))

    errors = [error for _, error, _ in thread_states if error is not None]
    timed_out = (
        any(was_alive for was_alive, _, _ in thread_states)
        or any(isinstance(error, ParallelTimeoutError) for error in errors)
        or context.remaining_seconds() <= 0
        or any(
            finished_at is not None and operator.gt(finished_at, context.deadline)
            for _, _, finished_at in thread_states
        )
    )
    unfinished_branches = []
    if timed_out:
        cancellation_threads = context.cancel()
        cancellation_deadline = (
            time.monotonic() + _PARALLEL_CANCELLATION_GRACE_SECONDS
        )
        _join_threads_until(cancellation_threads, cancellation_deadline)
        _join_threads_until(branches, cancellation_deadline)
        unfinished_branches = [thread for thread in branches if thread.is_alive()]

    descendant_aborted = any(
        isinstance(error, ParallelExecutionAborted) for error in errors
    )
    exit_errors = [error for error in errors if isinstance(error, FlowExitStep)]
    if exit_errors:
        raise exit_errors[0]

    if timed_out or errors:
        state.last_script_error = (
            f"Parallel execution exceeded its "
            f"{context.effective_timeout_seconds:g}-second completion timeout."
            if timed_out
            else "Error in at least one of the parallel branches."
        )
        if node["has_conditionals"]:
            log(
                "PARALLEL_COND_F",
                node["unique_id"],
                {
                    "timestamp": str(dt.datetime.now(dt.timezone.utc)),
                    "reason": state.last_script_error,
                },
            )
        if not node["has_on_fail"] or unfinished_branches or descendant_aborted:
            if descendant_aborted:
                raise ParallelExecutionAborted(
                    state.last_script_error,
                    errors,
                )
            if unfinished_branches:
                raise ParallelExecutionAborted(state.last_script_error, errors)
            raise RuntimeError(state.last_script_error, errors)
        return False

    log("PARALLEL_POST", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
    if node["has_on_success"] or node["has_on_fail"]:
        log("PARALLEL_COND_S", node["unique_id"], str(dt.datetime.now(dt.timezone.utc)))
    return True


def _run_parallel_node(graph, node, state):
    success = _run_parallel(graph, node, state)
    return node["on_success" if success else "on_fail"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        if not all_keys_present(entry, ["branches"]) or not isinstance(
            branches := entry["branches"], list
        ):
            raise InvalidInput(f"Parallel Entry has invalid format: {entry}.")

        for branch in branches:
            if not all_keys_present(branch, ["steps"]) or not isinstance(
                branch["steps"], list
            ):
                raise InvalidInput(
                    f"Branch in Parallel Entry has invalid format: {branch}."
                )

        timeout_seconds = entry.get("timeout_seconds", DEFAULT_PARALLEL_TIMEOUT_SECONDS)
        if (
            type(timeout_seconds) is not int
            or timeout_seconds <= 0
            or timeout_seconds > TIMEOUT_MAX
        ):
            raise InvalidInput(
                "Parallel Entry `timeout_seconds` should be a positive integer no "
                f"greater than {TIMEOUT_MAX:g} when provided, is: {timeout_seconds}."
            )

    @classmethod
    def child_scopes(cls, entry: AnyEntry):
        descriptor = cls.control_flow.child_scopes[0]
        return [(descriptor, branch["steps"]) for branch in entry["branches"]]

    @classmethod
    def compile(
        cls, _compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "has_on_success": bool(entry.get("on_success")),
            "has_on_fail": bool(entry.get("on_fail")),
            "has_conditionals": bool(entry.get("on_success") or entry.get("on_fail")),
            "timeout_seconds": entry.get(
                "timeout_seconds", DEFAULT_PARALLEL_TIMEOUT_SECONDS
            ),
        }
