from dataclasses import dataclass


@dataclass
class CreateAttributeDto:
    body: dict
    show_expression_as: list[str] | None = None
    show_potential_tables: str | None = None
    show_fields: str | None = None
    fields: str | None = None
