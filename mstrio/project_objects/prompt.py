from dataclasses import dataclass
from typing import Any

from mstrio.utils.helper import Dictable, deprecation_warning


deprecation_warning("mstrio.project_objects.prompt", "mstrio.modeling.prompt", "11.6.9")


@dataclass
class Prompt(Dictable):
    """A Strategy One class representing a prompt.

    Attributes:
        type (str): Type of the prompt
            Possible values are:
                - UNSUPPORTED
                - VALUE
                - ELEMENTS
                - EXPRESSION
                - OBJECTS
                - LEVEL
        answers (Any | list[Any]): Singular answer or list of
            answers to the prompt.
        key (str, optional): Unique key of the prompt.
        id (str, optional): ID of the prompt.
        name (str, optional): Name of the prompt.
        use_default (bool, optional): Whether to use default value.
            If True, provided answer will be ignored. Defaults to False.

    Note that only one of the key, id, or name needs to be provided.
    It is recommended to always provide the key as it's always unique
    as opposed to ID or name that can be shared among prompts.
    """

    type: str
    answers: Any | list[Any]
    key: str | None = None
    id: str | None = None
    name: str | None = None
    use_default: bool = False
