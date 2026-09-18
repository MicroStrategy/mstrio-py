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
