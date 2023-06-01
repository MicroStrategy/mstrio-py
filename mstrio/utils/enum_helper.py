from enum import Enum
from itertools import chain
from typing import Type


class AutoName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.lower()

    @classmethod
    def has_value(cls, value):
        return value in set(item.value for item in cls)

    def __repr__(self) -> str:
        return self.__str__()


class AutoUpperName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self


class AutoCapitalizedName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.capitalize()


def __get_enum_helper(
    obj, enum: Type[Enum] = Enum, get_value: bool = False
) -> str | Type[Enum] | None:
    """Helper function for `get_enum` and `get_enum_val`."""
    if obj is None:
        return obj

    if isinstance(obj, Enum) and isinstance(obj, enum):
        obj = obj.value if get_value else obj
    elif isinstance(obj, (str, int)):
        validate_enum_value(obj, enum)
        obj = obj if get_value else enum(obj)
    else:
        raise TypeError(f"Incorrect type. Value should be of type: {enum}.")

    return obj


def get_enum(obj, enum: Type[Enum] = Enum) -> Type[Enum] | None:
    """Safely get enum from enum or str."""
    return __get_enum_helper(obj, enum)


def get_enum_val(obj, enum: Type[Enum] = Enum) -> str | None:
    """Safely extract value from enum or str."""
    return __get_enum_helper(obj, enum, True)


def validate_enum_value(obj, enum):
    """Validate provided value. If not correct,
    error message with possible options will be displayed.
    """
    from mstrio.utils.helper import exception_handler

    possible_values = (
        [[e.value for e in item] for item in enum]
        if isinstance(enum, tuple)
        else [e.value for e in enum]
    )
    err_msg = f"Incorrect enum value '{obj}'. Possible values are {possible_values}"
    if obj not in list(chain(possible_values)):
        exception_handler(err_msg, exception_type=ValueError)
