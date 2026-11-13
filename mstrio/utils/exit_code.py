"""Validation of raw script exit codes."""

from typing import Any


def validate_exit_code(value: Any) -> int:
    """Return a signed 32-bit integer exit code without coercion.

    Raises:

        ValueError: If the value is not an integer in the supported range.
    """
    if type(value) is not int or not -2147483648 <= value <= 2147483647:
        raise ValueError(
            "Exit code must be an integer between -2147483648 and 2147483647, "
            f"is: {value!r}."
        )
    return value
