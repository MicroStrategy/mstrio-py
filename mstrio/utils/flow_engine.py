import datetime as dt
import json
import operator  # noqa: F401
import threading as t
import time
from contextlib import ExitStack
from math import isfinite
from zoneinfo import ZoneInfo

from mstrio import config
from mstrio.connection import Connection, get_connection  # noqa: F401
from mstrio.helpers import try_str_to_num
from mstrio.python_execution import (  # noqa: F401
    ExecutionStatus,
    Script,
    VariableAnswer,
)

config.verbose = False
config.delay_between_polling = 10
glob = {}
_NODE_HANDLERS = {}
log_lock = t.Lock()
_script_stop_lock = t.Lock()
_script_stop_requests = {}
_MISSING = object()
_PARALLEL_CANCELLATION_GRACE_SECONDS = 30


class FlowExitStep(RuntimeError):
    pass


class ParallelTimeoutError(TimeoutError):
    pass


class ParallelExecutionAborted(RuntimeError):
    pass


_CONDITION_FAILURE_PREFIX = "Failed to evaluate the condition"


class ConditionEvaluationError(ValueError):
    def __init__(self, detail):
        self.reason = f"{_CONDITION_FAILURE_PREFIX}: {detail}."
        super().__init__(self.reason)


class ScopeState:
    def __init__(self):
        self.last_script_error = None


def log(key, unique_id, data=None):
    with log_lock:
        if isinstance(data, dict):
            data = json.dumps(data).replace(r"\n", r"\\n")
        txt = f"{key} | {unique_id} | {data or '-'}"
        print(txt)


def _evaluate_condition(condition, unique_id):
    try:
        result = bool(condition())
        reason = "" if result else "Condition evaluated to false."
    except ConditionEvaluationError as error:
        result, reason = False, error.reason
    except Exception:
        result, reason = False, f"{_CONDITION_FAILURE_PREFIX}."

    key = "DECISION_COND_S" if result else "DECISION_COND_F"
    log(
        key,
        unique_id,
        {
            "timestamp": str(dt.datetime.now(dt.timezone.utc)),
            "reason": reason,
        },
    )
    return result


def _parse_numeric_comparison_value(value, side):
    if isinstance(value, str):
        try:
            value = try_str_to_num(value)
        except OverflowError:
            raise ConditionEvaluationError(f"{side} operand is not numeric")
    if type(value) not in (int, float) or (
        type(value) is float and not isfinite(value)
    ):
        raise ConditionEvaluationError(f"{side} operand is not numeric")
    return value


def _string_comparison_value(value, side):
    if value is None or isinstance(value, (list, tuple, set, dict)):
        raise ConditionEvaluationError(f"{side} operand is not scalar")
    return str(value)


def _is_supported_membership_value(value):
    return type(value) in (str, int, float)


def _contains_comparison_value(container, item):
    if not _is_supported_membership_value(item):
        raise ConditionEvaluationError("right operand has unsupported data")

    if isinstance(container, (list, tuple, set)):
        if not all(_is_supported_membership_value(value) for value in container):
            raise ConditionEvaluationError(
                "left operand contains unsupported collection data"
            )
        return item in container

    if isinstance(container, dict):
        raise ConditionEvaluationError("left operand has unsupported data")

    return str(item) in _string_comparison_value(container, "left")


_parallel_thread_state = t.local()


class ParallelExecutionContext:
    def __init__(self, timeout_seconds, parent=None):
        start_time = time.monotonic()
        own_deadline = start_time + timeout_seconds
        self.deadline = (
            min(own_deadline, parent.deadline) if parent is not None else own_deadline
        )
        self.effective_timeout_seconds = round(max(0.0, self.deadline - start_time), 3)
        self.parent = parent
        self.cancelled = t.Event()
        self.active_scripts = {}
        self.cancellation_threads = []
        self._stop_requested_scripts = set()
        self.lock = t.Lock()

    def remaining_seconds(self):
        return max(0.0, self.deadline - time.monotonic())

    def contexts(self):
        context = self
        while context is not None:
            yield context
            context = context.parent

    def register_script(self, script):
        timed_out = False
        for context in self.contexts():
            with context.lock:
                context.active_scripts[id(script)] = script
                timed_out = timed_out or (
                    context.cancelled.is_set() or context.remaining_seconds() <= 0
                )

        if timed_out:
            self.unregister_script(script)
            _request_script_stop(script, self.contexts())
            raise ParallelTimeoutError(
                "Parallel execution exceeded its completion timeout."
            )

    def unregister_script(self, script):
        for context in self.contexts():
            with context.lock:
                context.active_scripts.pop(id(script), None)

    def cancel(self):
        with self.lock:
            if any(
                context.cancelled.is_set()
                for context in self.contexts()
                if context is not self
            ):
                return list(self.cancellation_threads)

            if not self.cancelled.is_set():
                self.cancelled.set()

            if self.cancellation_threads and any(
                thread.is_alive() for thread in self.cancellation_threads
            ):
                return list(self.cancellation_threads)

            scripts = [
                script
                for script in self.active_scripts.values()
                if id(script) not in self._stop_requested_scripts
            ]
            requested_script_ids = {id(script) for script in scripts}
            self._stop_requested_scripts.update(requested_script_ids)
            contexts = tuple(self.contexts())
            for context in contexts:
                if context is self:
                    continue
                with context.lock:
                    context._stop_requested_scripts.update(requested_script_ids)
            self.cancellation_threads = [
                t.Thread(
                    target=_stop_script_execution,
                    args=(script, contexts),
                    daemon=True,
                )
                for script in scripts
            ]
            for thread in self.cancellation_threads:
                thread.start()

            return list(self.cancellation_threads)

    def check_cancelled(self):
        for context in self.contexts():
            if context.cancelled.is_set() or context.remaining_seconds() <= 0:
                context.cancel()
                raise ParallelTimeoutError(
                    "Parallel execution exceeded its completion timeout."
                )


def _stop_script_execution(script, contexts=()):
    script_id = id(script)
    with _script_stop_lock:
        if script_id in _script_stop_requests:
            return
        _script_stop_requests[script_id] = script

    failed = False
    try:
        script.stop_execution()
    except Exception:
        failed = True
    finally:
        with _script_stop_lock:
            _script_stop_requests.pop(script_id, None)
    if failed:
        for context in contexts:
            with context.lock:
                context._stop_requested_scripts.discard(script_id)


def _request_script_stop(script, contexts):
    contexts = tuple(contexts)
    script_id = id(script)
    with ExitStack() as stack:
        for context in contexts:
            stack.enter_context(context.lock)
        if any(script_id in context._stop_requested_scripts for context in contexts):
            return
        for context in contexts:
            context._stop_requested_scripts.add(script_id)
    _stop_script_execution(script, contexts)


def _current_parallel_context():
    return getattr(_parallel_thread_state, "context", None)


def _check_parallel_cancelled():
    if context := _current_parallel_context():
        context.check_cancelled()


def _flow_sleep(duration):
    context = _current_parallel_context()
    if context is None:
        time.sleep(duration)
        return

    context.check_cancelled()
    wait_seconds = min(duration, context.remaining_seconds())
    context.cancelled.wait(wait_seconds)
    context.check_cancelled()


def _wait_for_flow_script(script):
    context = _current_parallel_context()
    if context is None:
        return script.wait_for_execution_finish(pipe_logs=False)

    context.register_script(script)
    try:
        return script.wait_for_execution_finish(pipe_logs=False)
    finally:
        context.unregister_script(script)


def _join_threads_until(threads, deadline):
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))


class PropagatingThread(t.Thread):
    def run(self):
        self._propagated_exception = None
        self._finished_at = None
        try:
            self._target(*self._args, **self._kwargs)
        except Exception as error:
            self._propagated_exception = error
        finally:
            self._finished_at = time.monotonic()

    def join(self, timeout=None):
        super().join(timeout)
        return None if self.is_alive() else self._propagated_exception


def _resolve_step_output(step_id, output):
    script = glob.get(f"_{step_id}", _MISSING)
    if script is _MISSING:
        return _MISSING

    if output == "stdout":
        return script.execution_stdout
    if output == "return":
        return script.execution_result
    return script.execution_pod_executor_message


def _resolve_reference(reference):
    kind = reference[0]
    if kind == "flow_var":
        return reference[1]()
    return _resolve_step_output(reference[1], reference[2])


def _resolve_variable_answer(value):
    kind = value[0]
    if kind == "default":
        return VariableAnswer.KEEP_GLOBAL_DEFAULT
    result = _resolve_reference(value)
    if result is _MISSING:
        raise KeyError(f"Unknown step output reference: {value[1]}")
    return result


def _resolve_variable_with_fallback(value):
    source = _resolve_reference(value[1])
    if source is _MISSING or source is None:
        return _resolve_variable_answer(value[2])
    return source


def _build_variable_answers(variables):
    if not variables:
        return None

    return {
        name: (
            _resolve_variable_with_fallback(value)
            if value[0] == "fallback"
            else _resolve_variable_answer(value)
        )
        for name, value in variables.items()
    }


def _resolve_condition_operand(operand):
    if operand[0] == "constant":
        return operand[1]

    value = _resolve_reference(operand[1])
    if value is _MISSING:
        raise KeyError(operand[1][1])
    return value


def _condition_callable(condition):
    condition_type = condition[0]
    if condition_type == "weekday":
        timezone = condition[2]
        now = (
            dt.datetime.now(ZoneInfo(timezone))
            if timezone
            else dt.datetime.now().astimezone()
        )
        return lambda: now.weekday() in condition[1]

    operator_name, left, right = condition[1], condition[2], condition[3]

    def evaluate_comparison():
        left_value = _resolve_condition_operand(left)
        right_value = _resolve_condition_operand(right)
        parse_numeric = operator_name in {
            "greater_than",
            "greater_than_or_equal",
            "less_than",
            "less_than_or_equal",
        }

        if operator_name in {"begins_with", "ends_with"}:
            left_value = _string_comparison_value(left_value, "left")
            right_value = _string_comparison_value(right_value, "right")
            method = (
                left_value.startswith
                if operator_name == "begins_with"
                else left_value.endswith
            )
            return method(right_value)

        if operator_name == "contains":
            return _contains_comparison_value(left_value, right_value)

        if parse_numeric:
            left_value = _parse_numeric_comparison_value(left_value, "left")
            right_value = _parse_numeric_comparison_value(right_value, "right")

        functions = {
            "equals": operator.eq,
            "not_equals": operator.ne,
            "greater_than": operator.gt,
            "greater_than_or_equal": operator.ge,
            "less_than": operator.lt,
            "less_than_or_equal": operator.le,
        }
        return functions[operator_name](left_value, right_value)

    return evaluate_comparison


def _run_branch(graph, scope_id, context):
    previous_context = _current_parallel_context()
    _parallel_thread_state.context = context
    try:
        _run_scope(graph, graph["scopes"][scope_id]["start"], ScopeState())
    finally:
        _parallel_thread_state.context = previous_context


def _run_scope(graph, program_counter, state):
    while program_counter is not None:
        _check_parallel_cancelled()
        node = graph["nodes"][program_counter]
        try:
            handler = _NODE_HANDLERS[node["kind"]]
        except KeyError:
            raise RuntimeError(f"Unknown compiled Flow node: {node['kind']}.")
        program_counter = handler(graph, node, state)


def _run_flow(graph):
    return _run_scope(
        graph,
        graph["scopes"][graph["root_scope"]]["start"],
        ScopeState(),
    )
