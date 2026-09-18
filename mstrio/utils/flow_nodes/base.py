"""Common contracts for Flow node specifications."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

AnyEntry = dict[str, Any]
EntrySteps = list[AnyEntry]
CompiledValue = tuple[Any, ...]


class InvalidInput(ValueError):
    """Exception raised for invalid input in the Flow generator."""


class ValidationContext:
    """State accumulated while validating one Flow document."""

    def __init__(self) -> None:
        self.found_objects: set[tuple[str, str]] = set()

    def add_object(self, object_id: str, project_id: str) -> None:
        self.found_objects.add((object_id, project_id))


class CompileContext(Protocol):
    """Compiler services exposed to node specifications."""

    def get_step_id(self, step: AnyEntry, node_id: int) -> str: ...

    def compile_variable(self, value: Any) -> CompiledValue: ...

    def compile_condition(self, condition: AnyEntry) -> CompiledValue: ...


@dataclass(frozen=True)
class ChildScopeDescriptor:
    """Describe one family of nested execution scopes owned by a node."""

    name: str
    source_key: str
    scope_kind: str = "nested"
    ownership: str = "node"


@dataclass(frozen=True)
class ControlFlowSpec:
    """Declarative control-flow capabilities for one node type."""

    outcomes: tuple[str, ...] = ()
    fallthrough: bool = True
    terminal: bool = False
    reference_target: bool = False
    child_scopes: tuple[ChildScopeDescriptor, ...] = ()


ChildScopeEntry = tuple[ChildScopeDescriptor, EntrySteps]
OutcomeEntry = tuple[str, EntrySteps]


class BaseNode:
    """Contract implemented by every supported Flow node type."""

    type_name: ClassVar[str]
    control_flow: ClassVar[ControlFlowSpec] = ControlFlowSpec()
    runtime_handler_name: ClassVar[str | None] = None
    runtime_source_text: ClassVar[str] = ""
    runtime_required_helpers: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def validate(
        cls,
        entry: AnyEntry,
        previous_entry: AnyEntry | None,
        context: ValidationContext,
    ) -> None:
        """Validate fields specific to this node type."""
        raise NotImplementedError

    @classmethod
    def child_scopes(cls, entry: AnyEntry) -> Iterable[ChildScopeEntry]:
        """Return nested step lists and their scope descriptors."""
        return ()

    @classmethod
    def outcome_step_lists(cls, entry: AnyEntry) -> Iterable[OutcomeEntry]:
        """Return outcome names mapped to their nested step lists."""
        return (
            (outcome, entry[outcome])
            for outcome in cls.control_flow.outcomes
            if outcome in entry
        )

    @classmethod
    def compile(
        cls, compiler: CompileContext, node_id: int, entry: AnyEntry
    ) -> AnyEntry:
        """Compile this node into a normalized graph record."""
        raise NotImplementedError

    @classmethod
    def runtime_source(cls) -> str:
        """Return the embeddable runtime source for this node."""
        return cls.runtime_source_text.strip()
