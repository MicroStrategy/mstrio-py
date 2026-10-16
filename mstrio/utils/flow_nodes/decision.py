"""Decision Flow node specification."""

from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mstrio.helpers import try_str_to_num

from .base import (
    AnyEntry,
    BaseNode,
    CompileContext,
    ControlFlowSpec,
    InvalidInput,
    ValidationContext,
)
from .common import validate_variable_reference

COMPARISON_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "begins_with",
    "ends_with",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
}
ORDERING_COMPARISON_OPERATORS = {
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
}


def parse_numeric_comparison_constant(value: Any, side: str) -> int | float:
    if isinstance(value, str):
        try:
            value = try_str_to_num(value)
        except OverflowError:
            # Let the validation below report the value as non-numeric.
            pass

    if type(value) is int or (type(value) is float and isfinite(value)):
        return value

    raise InvalidInput(
        "Comparison Condition ordering operator requires numeric constant "
        f"`{side}`, is: {value!r}."
    )


def validate_comparison_operand_entry(entry: Any, side: str) -> None:
    if not isinstance(entry, dict) or "type" not in entry:
        raise InvalidInput(f"Comparison Condition `{side}` should be a typed operand.")

    match entry["type"]:
        case "variable":
            if "name" not in entry:
                raise InvalidInput(
                    f"Comparison Condition variable `{side}` should contain `name`."
                )
            validate_variable_reference(entry["name"])
        case "constant":
            if "value" not in entry:
                raise InvalidInput(
                    f"Comparison Condition constant `{side}` should contain `value`."
                )

            value = entry["value"]
            is_valid_number = type(value) in (int, float) and (
                type(value) is int or isfinite(value)
            )
            if not isinstance(value, str) and not is_valid_number:
                raise InvalidInput(
                    "Comparison Condition constants should be strings or finite "
                    f"numbers, is: {value}."
                )

            if isinstance(value, str) and any(char in value for char in ">~"):
                raise InvalidInput(
                    "Comparison Condition string constants cannot contain "
                    "characters '>' or '~'."
                )
        case other:
            raise InvalidInput(
                f"Unsupported Comparison Condition operand type: '{other}'."
            )


def validate_weekday_condition_entry(entry: Any) -> None:
    values = entry.get("value")
    if (
        not isinstance(values, list)
        or not values
        or any(type(value) is not int or value not in range(7) for value in values)
    ):
        raise InvalidInput(
            "Weekday Condition `value` should be a non-empty list of integers "
            "between 0 and 6."
        )

    if "timezone" not in entry:
        return

    timezone = entry["timezone"]
    if not isinstance(timezone, str):
        raise InvalidInput("Weekday Condition `timezone` should be an IANA string.")
    try:
        ZoneInfo(timezone)
    except (OSError, ValueError, ZoneInfoNotFoundError):
        raise InvalidInput(f"Weekday Condition has invalid IANA timezone: {timezone}.")


def validate_comparison_condition_entry(entry: Any) -> None:
    if not all(key in entry for key in ("operator", "left", "right")):
        raise InvalidInput(
            "Comparison Condition should contain `operator`, `left` and `right`."
        )

    operator = entry["operator"]
    if not isinstance(operator, str) or operator not in COMPARISON_OPERATORS:
        raise InvalidInput(f"Unsupported Comparison Condition operator: '{operator}'.")

    validate_comparison_operand_entry(entry["left"], "left")
    validate_comparison_operand_entry(entry["right"], "right")

    if operator in ORDERING_COMPARISON_OPERATORS:
        for side in ("left", "right"):
            operand = entry[side]
            if operand["type"] == "constant":
                parse_numeric_comparison_constant(operand["value"], side)


def validate_condition_entry(entry: Any) -> None:
    if not isinstance(entry, dict) or "type" not in entry:
        raise InvalidInput("Decision Entry `condition` should be a typed dictionary.")

    match entry["type"]:
        case "weekday":
            validate_weekday_condition_entry(entry)
        case "comparison":
            validate_comparison_condition_entry(entry)
        case other:
            raise InvalidInput(f"Unsupported Decision Condition type: '{other}'.")


class DecisionNode(BaseNode):
    type_name = "decision"
    control_flow = ControlFlowSpec(outcomes=("on_success", "on_fail"))
    runtime_handler_name = "_run_decision_node"
    runtime_support_source_text = r"""
import datetime as dt
import operator
from math import isfinite
from zoneinfo import ZoneInfo

from mstrio.helpers import try_str_to_num


_CONDITION_FAILURE_PREFIX = "Failed to evaluate the condition"


class ConditionEvaluationError(ValueError):
    def __init__(self, detail):
        self.reason = f"{_CONDITION_FAILURE_PREFIX}: {detail}."
        super().__init__(self.reason)


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
"""
    runtime_required_helpers = ("_condition_callable", "_evaluate_condition")
    runtime_source_text = r"""
def _run_decision_node(graph, node, state):
    success = _evaluate_condition(
        _condition_callable(node["condition"]),
        node["unique_id"],
    )
    return node["on_success" if success else "on_fail"]
"""

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        _previous_entry: AnyEntry | None,
        _context: ValidationContext,
    ) -> None:
        if "condition" not in entry:
            raise InvalidInput("Decision Entry should contain `condition`.")
        validate_condition_entry(entry["condition"])

    @classmethod
    def compile(
        cls, compiler: CompileContext, _node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        return {
            "kind": cls.type_name,
            "unique_id": entry["unique_id"],
            "next": None,
            "condition": compiler.compile_condition(entry["condition"]),
        }
