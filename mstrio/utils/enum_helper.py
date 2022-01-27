from enum import Enum
from itertools import chain
from typing import Tuple, Union


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class AutoUpperName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


def get_enum_val(obj, enum: Union[Enum, Tuple[Enum]] = Enum) -> Union[str, None]:
    """Safely extract value from enum or str."""
    if obj is None:
        return obj
    if isinstance(obj, Enum) and isinstance(obj, enum):
        return obj.value
    elif isinstance(obj, (str, int)):
        validate_enum_value(obj, enum)
        return obj
    else:
        raise TypeError(f"Incorrect type. Value should be of type: {enum}")


def validate_enum_value(obj, enum):
    """Validate provided value. If not correct,
    error message with possible options will be displayed.
    """
    from mstrio.utils.helper import exception_handler
    possible_values = [[e.value for e in item] for item in enum] if isinstance(
        enum, tuple) else [e.value for e in enum]
    err_msg = f"Incorrect enum value '{obj}'. Possible values are {possible_values}"
    if obj not in list(chain(possible_values)):
        exception_handler(err_msg, exception_type=ValueError)
