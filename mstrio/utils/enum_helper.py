from enum import Enum


class AutoName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.lower()

    @classmethod
    def has_value(cls, value):
        return value in {item.value for item in cls}

    def __repr__(self) -> str:
        return self.__str__()


class AutoUpperName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self


class AutoCapitalizedName(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.capitalize()


def __get_enum_helper(
    obj, enum: type[Enum] = Enum, get_value: bool = False
) -> str | int | type[Enum] | None:
    """Helper function for `get_enum` and `get_enum_val`."""
    if obj is None:
        return obj

    if isinstance(obj, enum):
        return obj.value if get_value else obj

    if isinstance(obj, (str, int)):
        validate_enum_value(obj, enum)
        return obj if get_value else enum(obj)

    raise TypeError(f"Incorrect type. Value should be of type: {enum}.")


def get_enum(obj, enum: type[Enum] = Enum) -> type[Enum] | None:
    """Safely get enum from enum or str."""
    return __get_enum_helper(obj, enum)


def get_enum_val(obj, enum: type[Enum] = Enum) -> str | int | None:
    """Safely extract value from enum or str."""
    return __get_enum_helper(obj, enum, True)


def validate_enum_value(
    obj: str | int, enum: type[Enum] | tuple[type[Enum]] | list[type[Enum]]
) -> None:
    """Validate provided value. If not correct,
    error message with possible options will be displayed.
    """
    from mstrio.utils.helper import exception_handler

    possible_values = [
        e.value
        for item in enum
        for e in (item if isinstance(enum, (tuple, list)) else [item])
    ]
    err_msg = f"Incorrect enum value '{obj}'. Possible values are {possible_values}"
    if obj not in possible_values:
        exception_handler(err_msg, exception_type=ValueError)
