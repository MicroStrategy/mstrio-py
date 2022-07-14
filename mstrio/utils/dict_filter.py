from enum import Enum
import logging
from typing import Any, Callable, Dict, Iterable, List, TYPE_CHECKING, TypeVar, Union

if TYPE_CHECKING:
    from mstrio.utils.entity import EntityBase

    SupportedExpression = Union[list, str, dict, int, float, bool, EntityBase, Enum]

logger = logging.getLogger(__name__)

SupportedExpression = Union[list, str, dict, int, float, bool, Enum]
KT = TypeVar("KT")
VT = TypeVar("VT")

EQUAL = '='
SMALLER_EQUAL = '<='
LARGER_EQUAL = '>='
NOT_EQUAL = '!='
NOT = '!'
SMALLER = '<'
LARGER = '>'
IS = 'is'
IN = 'in'
DICT_COMPARE = 'dict'
ENTITY_COMPARE = 'entity'


def check_valid_param(dict_object: Dict[KT, VT], params: Iterable) -> None:
    """Check if filter parameters can be used with given dict."""
    # all keys from dict that are supported for filtering
    allowed = list(
        filter(lambda el: not isinstance(dict_object[el], (list, tuple, set)), dict_object.keys())
    )

    # check filter param is in the allowed
    for param in params:
        if param not in allowed:
            raise KeyError(
                f"The filter parameter '{param}' is not valid. "
                f"Please filter by one of: {allowed}"
            )


def parse_filter_expression(param: str, expression: SupportedExpression) -> tuple:
    """Parse the filter expression only once"""
    from mstrio.utils.entity import EntityBase

    op = None

    # unpack enum value
    if isinstance(expression, Enum):
        expression = expression.value

    if isinstance(expression, list):
        op = IN
        filter_value = expression
    elif isinstance(expression, str):
        # extract the operation from the expression if it exists
        if expression and expression[0] in [SMALLER, LARGER, NOT, EQUAL]:
            op = expression[0]
            if expression[0] in [SMALLER, LARGER, NOT] and expression[1] == EQUAL:
                op += expression[1]
        filter_value = expression[len(op):] if op is not None else expression

        if filter_value.lower() == 'true':  # Support string bool values
            filter_value = True
            op = IS
        elif filter_value.lower() == 'false':
            filter_value = False
            op = IS
        op = op or EQUAL
    elif isinstance(expression, bool):
        op = IS
        filter_value = expression
    elif isinstance(expression, (int, float)):
        op = EQUAL
        filter_value = expression
    elif isinstance(expression, dict):
        op = DICT_COMPARE
        filter_value = expression
    elif isinstance(expression, EntityBase):
        op = ENTITY_COMPARE
        filter_value = expression
    else:
        raise TypeError(
            f"'{param}' filter value must be either a string, "
            "bool, int, float dict or list"
        )
    return (op, filter_value)


def make_dict_filter(param: str, op: str, filter_value: Any) -> Callable:
    """Return a filter function that takes a dictionary object as parameter.

    Once evaluated it return bool value indicating if given parameter-
    expression is True or False. This function can be used in the
    filter() method.
    """

    def cast_filter_value_if_needed(value_type: type) -> Any:
        # entity -> Entity will take care of ValueType errors -> don't cast
        # dict -> type must match exactly -> don't cast
        # str -> type must match exactly -> cast
        # int -> type must match exactly to int or float -> cast
        # float -> type must match exactly to int or float -> cast
        # bool -> type must match exactly to bool -> cast
        # enum -> could be anything as value is extracted

        if op == ENTITY_COMPARE:
            return filter_value
        elif isinstance(filter_value, value_type) and op != IN:
            return filter_value
        elif not isinstance(filter_value, value_type):
            # check if all other types are not equal to value_type and cast
            if op in (DICT_COMPARE, IS):
                # do not cast to bool or to dict
                raise TypeError(f"'{param}' needs to be compatible with type {value_type}.")

            try:
                # cast filter_value to dict element type
                if op == IN:
                    return [value_type(val) for val in filter_value]

                else:
                    # cast filter_value to int, float, str as in dict
                    return value_type(filter_value)
            except ValueError as e:
                logger.error(f"'{param}' filter value is incorrect.")
                raise e

    def my_filter(dict_object: Dict[KT, VT]) -> bool:
        """This function will be executed when passed into filter() function"""
        # extract actual value from dict
        if param not in dict_object:
            return False

        value = dict_object[param]
        value_type = type(value)
        filter_value = cast_filter_value_if_needed(value_type)

        if op in (EQUAL, ENTITY_COMPARE):
            return value == filter_value
        elif op in (NOT_EQUAL, NOT):
            return value != filter_value
        elif op == IS:
            return value is filter_value
        elif op == LARGER:
            return value > filter_value
        elif op == SMALLER:
            return value < filter_value
        elif op == LARGER_EQUAL:
            return value >= filter_value
        elif op == SMALLER_EQUAL:
            return value <= filter_value
        elif op == IN:
            return value in filter_value
        elif op == DICT_COMPARE:
            return all((value[k] == v if k in value else False for k, v in filter_value.items()))

    return my_filter


def filter_list_of_dicts(
    list_of_dicts: List[Dict[KT, VT]], **filters: Dict[str, SupportedExpression]
) -> List[Dict[KT, VT]]:
    """Filter a list of dicts by providing one or more key-value pair filters.

    Args:
        list_of_dicts: list of dicts that will be filtered
        **kwargs: Supports filtering by list, str, dict, int, float, bool,
            EntityBase, Enum as filter value.
            Support simple logical operators like: '<,>,<=,>=,!' if value
            is str.

    Examples:
        >>>filter_list_of_dicts(l, val=[0, 1, 2], val2=">2", val3=False)
        >>>filter_list_of_dicts(l, val=2, val2="!2", val3=SomeEnum(1))
        >>>filter_list_of_dicts(l, val={"id":"123", "name":"xxx"})
        >>>filter_list_of_dicts(l, val=User(conn, id="123"))
    """
    # check dict keys include the filter (only first element due to performance)
    if list_of_dicts:
        model_dict = list_of_dicts[0]
        check_valid_param(model_dict, filters.keys())

        for param, expression in filters.items():
            op, filter_value = parse_filter_expression(param, expression)
            filter_function = make_dict_filter(param, op, filter_value)
            list_of_dicts = list(filter(filter_function, list_of_dicts))

    return list_of_dicts
