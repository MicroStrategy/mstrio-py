"""Validation for Flow YAML documents and node-specific fields."""

from collections.abc import Sequence
from typing import Any

from mstrio.connection import Connection
from mstrio.utils.helper import get_args_from_func

from .flow_nodes.base import AnyEntry, EntrySteps, InvalidInput, ValidationContext
from .flow_nodes.common import (
    all_keys_present,
    validate_object_entry,
    validate_variable_reference,
)
from .flow_nodes.registry import get_node_spec

GENERATOR_VERSION = 1


def _validate_yaml_collections(value: Any) -> None:
    active_collection_ids = set()
    stack = [(value, False)]
    while stack:
        current, leaving = stack.pop()
        if not isinstance(current, (dict, list)):
            continue

        collection_id = id(current)
        if leaving:
            active_collection_ids.remove(collection_id)
            continue
        if collection_id in active_collection_ids:
            raise InvalidInput(
                "Input YAML contains a recursive alias, which is not supported."
            )

        active_collection_ids.add(collection_id)
        stack.append((current, True))
        children = current.values() if isinstance(current, dict) else current
        stack.extend((child, False) for child in reversed(list(children)))


def list_with_prev_ref(
    lst: list[Any], first_prev: AnyEntry | None = None
) -> Sequence[tuple[Any, Any | None]]:
    """Return pairs containing each item and its previous item."""
    if not lst:
        return zip([], [])
    return zip(lst, [first_prev] + lst[:-1], strict=True)


def validate_conditional_branches(
    entry: AnyEntry,
    context: ValidationContext | None = None,
    outcomes: tuple[str, ...] = ("on_fail", "on_success"),
) -> None:
    context = context or ValidationContext()
    for key in outcomes:
        if key not in entry:
            continue
        steps = entry[key]
        if not isinstance(steps, list):
            raise InvalidInput(
                f"Conditional branch '{key}' should be a list of valid steps "
                "when provided."
            )

        _validate_step_list(steps, context, first_prev=entry)


def _validate_step_list(
    steps: EntrySteps,
    context: ValidationContext,
    first_prev: AnyEntry | None = None,
) -> None:
    for index, (step, previous) in enumerate(
        list_with_prev_ref(steps, first_prev=first_prev)
    ):
        _validate_step_entry(step, previous, context)
        if step["type"] == "ref" and index != len(steps) - 1:
            raise InvalidInput(
                "Ref Entry must be the final entry in its containing step list."
            )


def _validate_step_entry(
    entry: AnyEntry,
    previous_entry: AnyEntry | None,
    context: ValidationContext,
) -> None:
    if not all_keys_present(entry, ["type", "unique_id"]):
        raise InvalidInput("Step entry does not contain `type` or `unique_id` keys.")
    if not isinstance(entry["unique_id"], str):
        raise InvalidInput("`unique_id` should be a string.")

    node_spec = get_node_spec(entry["type"])
    node_spec.validate(entry, previous_entry, context)
    if node_spec.control_flow.outcomes:
        validate_conditional_branches(
            entry,
            context,
            node_spec.control_flow.outcomes,
        )
    for _, child_steps in node_spec.child_scopes(entry):
        _validate_step_list(child_steps, context, first_prev=entry)


def validate_any_step_entry(
    entry: AnyEntry,
    previous_entry: AnyEntry | None = None,
    context: ValidationContext | None = None,
) -> None:
    """Validate one step and all of its nested step lists."""
    _validate_step_entry(entry, previous_entry, context or ValidationContext())


def validate_input_yaml_structure(parsed_input_yaml: AnyEntry) -> None:
    """Validate the structure and required data of parsed Flow YAML."""
    _validate_yaml_collections(parsed_input_yaml)
    if not isinstance(parsed_input_yaml, dict) or not all_keys_present(
        parsed_input_yaml, ["version", "dependencies", "connection", "steps"]
    ):
        raise InvalidInput(
            "Input yaml should be a dictionary with required keys: "
            "version, dependencies, connection and steps."
        )

    version = parsed_input_yaml["version"]
    if type(version) is not int:
        raise InvalidInput(f"Version should be an integer, is {type(version)}.")
    if version > GENERATOR_VERSION:
        raise InvalidInput(
            f"Input data comes from plugin with later version ({version}) "
            f"than the generator ({GENERATOR_VERSION}). "
            "The generator cannot handle this input."
        )

    dependencies = parsed_input_yaml["dependencies"]
    if not isinstance(dependencies, list) or not all(
        validate_object_entry(dependency) for dependency in dependencies
    ):
        raise InvalidInput("Some dependency entries are not in the required format.")

    connection = parsed_input_yaml["connection"]
    if connection != "get_connection":
        connection_params = get_args_from_func(Connection)
        valid_connection = (
            isinstance(connection, dict)
            and "base_url" in connection
            and all(
                key in connection_params
                and isinstance(value, str)
                and value.startswith("flow_var.")
                for key, value in connection.items()
            )
        )
        if valid_connection:
            try:
                for value in connection.values():
                    validate_variable_reference(value)
            except InvalidInput:
                valid_connection = False
        if not valid_connection:
            raise InvalidInput(
                "Connection data is not in the required format. Either some "
                "keys are not valid `Connection` initialization keys or some "
                "values are not in proper format `flow_var.<var_name>`."
            )

    steps = parsed_input_yaml["steps"]
    if not isinstance(steps, list):
        raise InvalidInput(f"Steps should be a list of valid steps, is {steps}")
    context = ValidationContext()
    _validate_step_list(steps, context)

    dependencies_objects = {
        (dependency["id"], dependency["project_id"]) for dependency in dependencies
    }
    if not context.found_objects <= dependencies_objects:
        raise InvalidInput(
            "Not all used scripts added to dependencies. "
            "Scripts not in dependencies (<script-id>, <project-id>): "
            f"{context.found_objects - dependencies_objects}"
        )
