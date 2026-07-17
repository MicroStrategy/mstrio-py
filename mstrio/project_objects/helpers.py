import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from mstrio import config
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import get_response_json

if TYPE_CHECKING:
    from mstrio.project_objects import Prompt

logger = logging.getLogger(__name__)


class EnableForAiStatus(AutoName):
    """Enumeration of AI enablement status values."""

    NULL = auto()
    READY = auto()
    PENDING = auto()
    FAILED = auto()
    STARTED = auto()
    DECERTIFIED = auto()
    BASE_CUBE_DECERTIFIED = auto()
    RESERVED = auto()


class EnableForAiErrorReason(Enum):
    """
    Enumeration of AI enablement error reason codes.

    OK (0)
        "No error."

    UNKNOWN_ERROR (-1)
        "An unknown error occurred."

    EXCEPTION_WRITING_TO_CLICKHOUSE (1)
        "An unexpected error occurred while saving data to ClickHouse."

    FAILED_WRITING_TO_CLICKHOUSE (2)
        "Failed to write data to ClickHouse."

    ERROR_WHEN_GETTING_SAMPLE_DATA_FROM_CLICKHOUSE (3)
        "Failed to retrieve sample data from ClickHouse."

    CUBE_INSTANCE_NOT_FOUND (4)
        "Cube instance not found."

    AI_INFORMATION_GENERATION_FAILED (5)
        "Failed to generate AI information from the AI service."

    DISK_FULL_IN_CLICKHOUSE (6)
        "Failed to write data to ClickHouse due to disk full."

    ERR_GENERAL (100)
        "An unspecified error occurred."

    OUTDATED_DISK (11)
    ERR_DISK (101)
        "Failed to dump cube due to disk error."

    OUTDATED_CLOUD (12)
    ERR_CLOUD (102)
        "Failed to upload file stream to cloud storage."

    ERR_DB (103)
        "Failed to generate AI metadata."

    ERR_CLICKHOUSE (104)
        "Failed to load into Clickhouse."

    ERR_AI (105)
        "Failed to generate AI-assisted descriptions."
    """

    OK = 0
    UNKNOWN_ERROR = -1
    EXCEPTION_WRITING_TO_CLICKHOUSE = 1
    FAILED_WRITING_TO_CLICKHOUSE = 2
    ERROR_WHEN_GETTING_SAMPLE_DATA_FROM_CLICKHOUSE = 3
    CUBE_INSTANCE_NOT_FOUND = 4
    AI_INFORMATION_GENERATION_FAILED = 5
    DISK_FULL_IN_CLICKHOUSE = 6

    ERR_GENERAL = 100
    ERR_DISK = 101
    ERR_CLOUD = 102
    ERR_DB = 103
    ERR_CLICKHOUSE = 104
    ERR_AI = 105
    OUTDATED_DISK = 11
    OUTDATED_CLOUD = 12

    RESERVED = -100


@dataclass
class EnableForAiState:
    """Result of a bot cube status query.

    Attributes:
        id: ID of cube, report or mosaic model.
        status: Current enablement status.
        error_reason: Error reason if applicable.
        progress: progress: Progress percentage (0-100). Available
            since 25.09 release.
        remaining_time: Estimated remaining time for completion in seconds.
            Available since 25.09 release, but not guaranteed in every
            server response (for example, it may be missing for terminal
            statuses). In those cases this value is `None`.
        last_updated_at: Timestamp of last status update.
        user: User who initiated the enablement.
    """

    id: str
    status: 'EnableForAiStatus'
    error_reason: 'EnableForAiErrorReason | None'
    progress: int | None
    remaining_time: int | None
    last_updated_at: int | None
    user: str | None


def get_prompt_answer(
    prompt: dict, prompt_answers: list[dict] | None, force: bool
) -> Any | list[Any]:
    existing_answer = prompt.get('answers')
    default_answer = prompt.get('defaultAnswer')

    # Find the user's configuration for this specific prompt by key
    user_prompt_config = None
    if prompt_answers:
        user_prompt_config = next(
            (p for p in prompt_answers if p.get('key') == prompt.get('key')), None
        )

    if not force and existing_answer:
        input_msg = (
            f"Prompt: '{prompt.get('name')}' already has an answer. "
            "Would you like to keep the current answer? "
            "(Enter 'Y' to keep it, or 'N' to provide a new one from the "
            "`prompt_answers` list): "
        )
        if input(input_msg).upper() == 'Y':
            return existing_answer

    # Check if user wants to use default for this specific prompt
    if user_prompt_config and user_prompt_config.get('use_default', False):
        if default_answer is not None:
            return default_answer
        else:
            raise ValueError(
                f"Default answer not found for prompt: {prompt.get('name')}"
            )

    if user_prompt_config and 'answers' in user_prompt_config:
        return user_prompt_config.get('answers')

    # Required prompt without answer
    msg = (
        "Cannot find an answer for the required prompt: "
        f"`{prompt.get('name')}` in the `prompt_answers` list."
    )

    if force:
        raise ValueError(msg)

    # Handle optional prompts
    if not prompt.get('required'):
        # For optional prompts, offer default if available
        if default_answer is not None:
            input_msg = (
                f"Optional prompt '{prompt.get('name')}' has a default answer: "
                f"{default_answer}. "
                "Use default? (Y/N): "
            )
            if input(input_msg).upper() == 'Y':
                return default_answer
        return None

    # Interactive mode for required prompts
    if default_answer is not None:
        input_msg = f"{msg} Use default answer ({default_answer})? (Y/N): "
        if input(input_msg).upper() == 'Y':
            return default_answer
        input_msg = (
            f"Please provide a custom answer for '{prompt.get('name')}' - "
            f"{prompt.get('instruction')}':"
        )
    else:
        input_msg = (
            f"{msg} Please provide an answer for '{prompt.get('name')}' - "
            f"'{prompt.get('instruction')}':"
        )
    return input(input_msg)


def answer_prompts_helper(
    instance_id: str,
    prompt_answers: list['Prompt'] | None,
    get_status_func: Callable,
    get_prompts_func: Callable,
    answer_prompts_func: Callable,
    force: bool,
) -> bool:
    """Helper function to answer prompts for a report or dashboard/document.

    Args:
        instance_id (str): Instance ID of the report or dashboard/document.
        prompt_answers (list[Prompt] | None): List of Prompt class objects
            answering the prompts. Can be None for interactive mode.
        get_status_func (callable): Function to get the status of
            the report or dashboard/document.
        get_prompts_func (callable): Function to get the prompts for
            the report or dashboard/document.
        answer_prompts_func (callable): Function to answer the prompts for
            the report or dashboard/document.
        force (bool): If True, then the report/document/dashboard's existing
            prompt will be overwritten by ones from the prompt_answers list,
            and additional input from the user won't be asked.
            Otherwise, the user will be asked for input if the prompt
            is not answered, or if prompt was already answered.

    Returns:
        bool: True if prompts were answered successfully, False otherwise.
    """
    instance_status = get_response_json(get_status_func()).get('status')

    if instance_status != 2:
        if config.verbose:
            msg = (
                'There are no unanswered prompts '
                f'for the instance with ID: {instance_id}'
            )
            logger.warning(msg)
        return False
    if prompt_answers:
        prompt_answers = [prompt.to_dict() for prompt in prompt_answers]

    while instance_status == 2:
        prompted_instance = get_response_json(get_prompts_func())

        body = [
            {
                'key': prompt.get('key'),
                'id': prompt.get('id'),
                'name': prompt.get('name'),
                'type': prompt.get('type'),
                'answers': answer,
            }
            for prompt in prompted_instance
            if (answer := get_prompt_answer(prompt, prompt_answers, force)) is not None
        ]

        if not body:
            if config.verbose:
                logger.info("No answers provided for any prompts.")
            break

        answer_prompts_func(body={'prompts': body})

        instance_status = get_response_json(get_status_func()).get('status')

    if config.verbose:
        msg = f'Prompts for the instance with ID: {instance_id} have been answered.'
        logger.info(msg)

    return True
