from typing import Any, Callable, TypeVar

T = TypeVar('T')


def remove_duplicate_objects(objects: list[T], getter: Callable[[T], Any]) -> list[T]:
    """
    Remove duplicate objects from a list of objects
    based on the value returned by the getter function.
    This function assumes that getter will always return
    a comparable value and will not fail.

    Args:
        objects (list[T]): List of objects to filter.
        getter (Callable[[T], Any]): Function to get the value from the object
            by which the objects should be compared.

    Returns:
        list[T]: List of unique objects.
    """
    seen = set()
    unique_objects = []

    for obj in objects:
        value = getter(obj)
        if value not in seen:
            seen.add(value)
            unique_objects.append(obj)

    return unique_objects
