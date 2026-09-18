"""Validation helpers shared by Flow node specifications."""

import re
from math import isfinite
from threading import TIMEOUT_MAX
from typing import Any

from .base import AnyEntry, InvalidInput, ValidationContext

REGEX_PATTERN = r"^[a-zA-Z0-9_]+$"


def all_keys_present(entry: AnyEntry, keys: list[str]) -> bool:
    return isinstance(entry, dict) and all(key in entry for key in keys)


def validate_variable_reference(reference: Any) -> None:
    if not isinstance(reference, str):
        raise InvalidInput(f"Variable source should be a string, is: {reference}.")

    try:
        source, output = reference.split(".", 1)
    except ValueError:
        raise InvalidInput(
            f"Variable source should be in format 'key.ref', is: {reference}."
        )

    is_flow_var = source == "flow_var" and re.fullmatch(REGEX_PATTERN, output)
    is_step_ref = re.fullmatch(REGEX_PATTERN, source) and output in (
        "stdout",
        "return",
        "error",
    )

    if not is_flow_var and not is_step_ref:
        raise InvalidInput(
            "Variable source should be either reference to Flow variable in "
            "format 'flow_var.var_name' or reference to previous step output "
            "in format 'step_id.stdout', 'step_id.return' or 'step_id.error', "
            f"is: {reference}."
        )


def _validate_fallback_reference(fallback: Any) -> None:
    if fallback == "default":
        return

    if not isinstance(fallback, str) or not fallback.startswith("flow_var."):
        raise InvalidInput(
            "Variable fallback should be 'default' or a Flow variable "
            f"reference, is: {fallback}."
        )

    validate_variable_reference(fallback)


def validate_variable_definition(value: Any) -> None:
    if isinstance(value, str):
        if value != "default":
            validate_variable_reference(value)
        return

    if not isinstance(value, dict):
        validate_variable_reference(value)
        return

    if "source" not in value:
        raise InvalidInput(
            "Variable definition should be a reference string or a mapping "
            "with a `source` key."
        )

    source = value["source"]
    validate_variable_reference(source)
    if source.startswith("flow_var."):
        raise InvalidInput("Mapping variable `source` should reference a step output.")

    if "fallback" in value:
        _validate_fallback_reference(value["fallback"])


def validate_object_entry(
    entry: AnyEntry, context: ValidationContext | None = None
) -> bool:
    try:
        valid = isinstance(entry, dict) and bool(
            re.fullmatch(REGEX_PATTERN, entry.get("id", ""))
            and re.fullmatch(REGEX_PATTERN, entry.get("project_id", ""))
        )
    except TypeError:
        return False

    if valid and context is not None:
        context.add_object(entry["id"], entry["project_id"])
    return valid


def normalize_sleep_duration(duration: Any) -> int | float:
    if isinstance(duration, bool):
        raise ValueError()

    try:
        numeric_duration = float(duration)
    except (TypeError, ValueError, OverflowError):
        raise ValueError()

    if (
        not isfinite(numeric_duration)
        or numeric_duration <= 0
        or numeric_duration > TIMEOUT_MAX
    ):
        raise ValueError()
    if isinstance(duration, (int, float)):
        return duration
    return int(numeric_duration) if numeric_duration.is_integer() else numeric_duration
