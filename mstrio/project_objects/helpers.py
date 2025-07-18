import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from mstrio import config
from mstrio.utils.helper import get_response_json

if TYPE_CHECKING:
    from mstrio.project_objects import Prompt

logger = logging.getLogger(__name__)


def get_prompt_answer(
    prompt: dict, prompt_answers: list[dict], force: bool
) -> Any | list[Any]:
    answer = prompt.get('answers')
    if not force and answer:
        input_msg = (
            f"Prompt: '{prompt.get('name')}' already has an answer. "
            "Would you like to keep the current answer? "
            "(Enter 'Y' to keep it, or 'N' to provide a new one from the "
            "`prompt_answers` list): "
        )
        if input(input_msg) != 'Y':
            answer = None

    if force or not answer:
        answer = next(
            (
                p.get('answers')
                for p in prompt_answers
                if p.get('key') == prompt.get('key')
            ),
            None,
        )
        if not answer:
            if not prompt.get('required'):
                return None

            msg = (
                "Cannot find an answer for the prompt: "
                f"`{prompt.get('name')}` in the `prompt_answers` list."
            )

            if force:
                raise ValueError(msg)

            input_msg = f"{msg} Please provide an answer:"
            answer = input(input_msg)

    return answer


def answer_prompts_helper(
    instance_id: str,
    prompt_answers: list['Prompt'],
    get_status_func: Callable,
    get_prompts_func: Callable,
    answer_prompts_func: Callable,
    force: bool,
) -> bool:
    """Helper function to answer prompts for a report or dashboard/document.

    Args:
        instance_id (str): Instance ID of the report or dashboard/document.
        prompt_answers (list[Prompt]): List of Prompt class objects answering
            the prompts.
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

        answer_prompts_func(body={'prompts': body})

        instance_status = get_response_json(get_status_func()).get('status')

    if config.verbose:
        msg = f'Prompts for the instance with ID: {instance_id} have been answered.'
        logger.info(msg)

    return True
