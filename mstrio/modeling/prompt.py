from dataclasses import dataclass
from enum import auto
from typing import Any

from mstrio.api import prompts
from mstrio.connection import Connection
from mstrio.helpers import VersionException
from mstrio.modeling import Attribute
from mstrio.modeling.expression import ExpressionFormat
from mstrio.modeling.schema.helpers import ObjectSubType
from mstrio.object_management import (
    Folder,
    SearchPattern,
    full_search,
)
from mstrio.server import Project
from mstrio.types import ObjectSubTypes, ObjectTypes
from mstrio.users_and_groups.user import User
from mstrio.utils.entity import CopyMixin, DeleteMixin, Entity, MoveMixin
from mstrio.utils.enum_helper import AutoName, AutoUpperName, get_enum_val
from mstrio.utils.helper import (
    Dictable,
    filter_params_for_func,
    find_object_with_name,
    get_owner_id,
    is_valid_str_id,
)
from mstrio.utils.resolvers import (
    get_folder_id_from_params_set,
    get_project_id_from_params_set,
    validate_owner_key_in_filters,
)
from mstrio.utils.response_processors import objects as objects_processors
from mstrio.utils.version_helper import is_server_min_version, method_version_handler


class PromptType(AutoUpperName):
    """Enum for prompt types."""

    UNSUPPORTED = auto()
    VALUE = auto()
    ELEMENTS = auto()
    EXPRESSION = auto()
    OBJECTS = auto()
    LEVEL = auto()


class PersonalAnswerMode(AutoName):
    """Enum for personal answer modes in prompt restrictions."""

    NONE = auto()
    SINGLE = auto()
    MULTIPLE = auto()


@dataclass
class PromptRestrictions(Dictable):
    """Class representing prompt restrictions."""

    allow_personal_answers: PersonalAnswerMode | str
    required: bool
    max_elements_per_selection: int | None = None
    min: int | None = None
    max: int | None = None

    def __post_init__(self):
        """Convert string values to enum if needed."""
        if isinstance(self.allow_personal_answers, str):
            if self.allow_personal_answers.lower() not in (
                possible_values := [mode.value for mode in PersonalAnswerMode]
            ):
                raise ValueError(
                    f"Invalid value '{self.allow_personal_answers}' for "
                    f"allow_personal_answers. Possible values are: "
                    f"{possible_values}"
                )
            self.allow_personal_answers = PersonalAnswerMode(
                self.allow_personal_answers.lower()
            )


@method_version_handler('11.4.0600')
def list_prompts(
    connection: Connection,
    name: str | None = None,
    to_dictionary: bool = False,
    limit: int | None = None,
    project: 'Project | str | None' = None,
    project_id: str | None = None,
    project_name: str | None = None,
    search_pattern: SearchPattern | int = SearchPattern.CONTAINS,
    show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    folder: 'Folder | tuple[str] | list[str] | str | None' = None,
    folder_id: str | None = None,
    folder_name: str | None = None,
    folder_path: tuple[str] | list[str] | str | None = None,
    **filters,
) -> list['Prompt'] | list[dict]:
    """Get list of Prompt objects or dicts with them.

    Args:
        connection (object): Strategy One connection object returned by
            `connection.Connection()`
        name (optional, str): value the search pattern is set to, which
            will be applied to the names of prompts being searched
        to_dictionary (optional, bool): If `True` returns dictionaries, by
            default (`False`) returns `Prompt` objects.
        limit (optional, int): limit the number of elements returned. If `None`
            (default), all objects are returned.
        project (Project | str, optional): Project object or ID or name
            specifying the project. May be used instead of `project_id` or
            `project_name`.
        project_id (str, optional): Project ID
        project_name (str, optional): Project name
        search_pattern (SearchPattern enum or int, optional): pattern to
            search for, such as Begin With or Exactly. Possible values are
            available in ENUM `mstrio.object_management.SearchPattern`.
            Default value is CONTAINS (4).
        show_expression_as (optional, enum or str): specify how expressions
            should be presented.
            Available values:
                - `ExpressionFormat.TREE` or `tree` (default)
                - `ExpressionFormat.TOKENS or `tokens`
        folder (Folder | tuple | list | str, optional): Folder object or ID or
            name or path specifying the folder. May be used instead of
            `folder_id`, `folder_name` or `folder_path`.
        folder_id (str, optional): ID of a folder.
        folder_name (str, optional): Name of a folder.
        folder_path (str, optional): Path of the folder.
            The path has to be provided in the following format:
                if it's inside of a project, start with a Project Name:
                    /MicroStrategy Tutorial/Public Objects/Metrics
                if it's a root folder, start with `CASTOR_SERVER_CONFIGURATION`:
                    /CASTOR_SERVER_CONFIGURATION/Users
        **filters: Available filter parameters: ['id', 'subtype',
            'date_created', 'date_modified', 'version', 'acg', 'owner',
            'ext_type']

    Returns:
        list of prompt objects or list of prompt dictionaries.
    """

    proj_id = get_project_id_from_params_set(
        connection,
        project,
        project_id,
        project_name,
    )

    validate_owner_key_in_filters(filters)

    objects = full_search(
        connection,
        object_types=ObjectTypes.PROMPT,
        project=proj_id,
        name=name,
        pattern=search_pattern,
        root=folder,
        root_id=folder_id,
        root_name=folder_name,
        root_path=folder_path,
        limit=limit,
        **filters,
    )
    if to_dictionary:
        return objects
    else:
        show_expression_as = (
            show_expression_as
            if isinstance(show_expression_as, ExpressionFormat)
            else ExpressionFormat(show_expression_as)
        )
        return [
            Prompt.from_dict(
                source={**obj, 'show_expression_as': show_expression_as},
                connection=connection,
                with_missing_value=False,
            )
            for obj in objects
        ]


class Prompt(CopyMixin, DeleteMixin, Entity, MoveMixin):
    """A Strategy One class representing a prompt.

    This class can be used in two modes:
        1. Answer mode: Create local prompt objects for providing answers
            without API calls
        2. API mode: Fetch and manage prompt objects from the MicroStrategy
            server

    Attributes:
        id (str): ID of the prompt
        name (str): Name of the prompt
        prompt_type (str): Type of the prompt. Possible values are:
            - UNSUPPORTED
            - VALUE
            - ELEMENTS
            - EXPRESSION
            - OBJECTS
            - LEVEL
        sub_type (ObjectSubType): Sub-type of the prompt (e.g., PROMPT_STRING,
            PROMPT_DOUBLE)
        title (str): Title of the prompt displayed in the interface
        instruction (str): Instruction text for the prompt
        default_answer (dict): Default answer configuration
        restriction (PromptRestrictions): Restrictions applied to the prompt
        answers (Any | list[Any]): Answer(s) to the prompt (answer mode only)
        key (str): Unique key of the prompt (answer mode only)
        use_default (bool): Whether to use default value (answer mode only)
        date_created (str): Date when the prompt was created
        date_modified (str): Date when the prompt was last modified
        owner (User): Owner of the prompt
        personal_answers (list[dict]): List of personal answers for the prompt

    Examples:
        Creating a prompt for answering (answer mode):
        >>> prompt = Prompt(
        >>>     key='8891A8AF4A747A3EA8506DBB6189F252@0@10',
        >>>     answers=[{'name': 'Cost', 'id':
                        '7FD5B69611D5AC76C000D98A4CC5F24F'}],
        >>>     type='OBJECTS'
        >>> )

        Fetching a prompt from server (API mode):
        >>> prompt = Prompt(connection, id='prompt_id')
        >>> prompt = Prompt(connection, name='My Prompt')

        Creating a new value prompt:
        >>> prompt = Prompt.create_value_prompt(
        >>>     connection=conn,
        >>>     name='Number Input',
        >>>     sub_type=ObjectSubType.PROMPT_DOUBLE,
        >>>     destination_folder=folder_id
        >>> )

    Note:
        In answer mode, only key needs to be provided along with answers or
            use_default.
        In API mode, either id or name must be provided along with a connection
            object.
    """

    _OBJECT_TYPE = ObjectTypes.PROMPT

    _API_GETTERS = {
        **Entity._API_GETTERS,
        (
            'id',
            'name',
            'sub_type',
            'title',
            'instruction',
            'default_answer',
            'restriction',
            'date_created',
            'date_modified',
        ): prompts.get_prompt,
    }
    _API_PATCH = {
        ('folder_id', 'comments', 'hidden', 'owner'): (
            objects_processors.update,
            'partial_put',
        ),
        (
            'title',
            'instruction',
            'default_answer',
            'restriction',
            'information',
            'name',
            'sub_type',
        ): (prompts.update_prompt, 'put'),
    }
    _FROM_DICT_MAP = {
        **Entity._FROM_DICT_MAP,
        'owner': User.from_dict,
        'sub_type': ObjectSubType,
        'restriction': PromptRestrictions.from_dict,
    }
    _PATCH_PATH_TYPES = {
        **Entity._PATCH_PATH_TYPES,
        'title': str,
        'instruction': str,
        'default_answer': dict,
        'restriction': dict,
    }

    def __init__(
        self,
        connection: Connection | None = None,
        id: str | None = None,
        key: str | None = None,
        name: str | None = None,
        type: 'str | PromptType | None' = None,
        answers: Any | list[Any] | None = None,
        use_default: bool = False,
    ) -> None:
        """Initialize a new instance of Prompt class.

        Can be used in two ways:
            1. Answer mode: Provide key and answers to create a local prompt
                object without API calls
            2. API mode: Provide connection and identification to fetch from
                server

        Args:
            connection (Connection, optional): Strategy One connection object
            id (str, optional): Identifier of a prompt object
            key (str, optional): Unique key of the prompt
            name (str, optional): Name of a prompt object
            type (str, PromptType, optional): Type of the prompt (ELEMENTS,
                OBJECTS, etc.)
            answers (Any | list[Any], optional): Answers to the prompt
            use_default (bool, optional): Whether to use default value.
                Defaults to False.
        """
        # Check if this is answer mode - key and answers provided
        if (
            connection is None
            and key is not None
            and (answers is not None or use_default)
        ):
            # Create local prompt object without API call
            self._init_local_prompt(
                type=type,
                answers=answers,
                key=key,
                id=id,
                name=name,
                use_default=use_default,
            )
        elif connection is not None and (id is not None or name is not None):
            # API mode - fetch from server
            if not is_server_min_version(connection, '11.4.0600'):
                raise VersionException(
                    'Initializing Prompt in API mode requires I-Server version '
                    '11.4.0600 or later.'
                )
            if id is None:
                prompt = find_object_with_name(
                    connection=connection,
                    cls=self.__class__,
                    name=name,
                    listing_function=list_prompts,
                    search_pattern=SearchPattern.EXACTLY,
                )
                id = prompt['id']

            super().__init__(
                connection=connection, object_id=id, project_id=connection.project_id
            )
        else:
            raise ValueError(
                "Either provide (key + answers/use_default) without connection for "
                "answer mode or (connection + id/name) for API-based initialization"
            )

    def _init_local_prompt(
        self,
        type: str | None = None,
        answers: Any | list[Any] | None = None,
        key: str | None = None,
        id: str | None = None,
        name: str | None = None,
        use_default: bool = False,
    ):
        """Initialize prompt with local data (answers mode)."""
        self._connection = None
        self._id = id
        self.prompt_type = type
        self.answers = answers
        self.key = key
        self.name = name
        self.use_default = use_default

    def _init_variables(self, default_value, **kwargs) -> None:
        """Initialize all properties of the Prompt class."""
        super()._init_variables(default_value=default_value, **kwargs)
        self.answers = kwargs.get('answers')
        self.use_default = kwargs.get('use_default')
        self.name = kwargs.get('name')
        self.default_answer = kwargs.get('default_answer', {})
        self.required = kwargs.get('required')
        self.closed = kwargs.get('closed')
        self.instruction = kwargs.get('instruction')
        self.question = kwargs.get('question', {})
        self.sub_type = (
            ObjectSubType(kwargs.get('sub_type')) if kwargs.get('sub_type') else None
        )
        self._restriction = (
            PromptRestrictions.from_dict(kwargs['restriction'])
            if kwargs.get('restriction')
            else None
        )

        self.data_type = kwargs.get('data_type')
        self.title = kwargs.get('title')
        self._personal_answers = kwargs.get('personal_answers', [])
        self.prompt_type = (
            PromptType(kwargs.get('type'))
            if kwargs.get('type') in PromptType.__members__
            else None
        )
        self.key = kwargs.get('key')

    @classmethod
    @method_version_handler('11.4.0600')
    def create(
        cls,
        connection: Connection,
        prompt_data: dict,
        name: str,
        sub_type: ObjectSubTypes | str,
        destination_folder: 'Folder | tuple[str] | list[str] | str | None' = None,
        destination_folder_path: tuple[str] | list[str] | str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> 'Prompt':
        """Create a new prompt object.

        Args:
            connection (Connection): Strategy One connection object.
            prompt_data (dict): Dictionary containing prompt configuration data.
            name (str): Name of the prompt.
            sub_type (ObjectSubType | str): Sub-type of the prompt.
            destination_folder (Folder | tuple | list | str, optional): Folder
                object or ID or name or path specifying the folder where to
                create object.
            destination_folder_path (str, optional): Path of the folder.
                The path has to be provided in the following format:
                    /MicroStrategy Tutorial/Public Objects/Metrics
            show_expression_as (ExpressionFormat | str, optional): How
                expressions should be presented. Defaults to
                ExpressionFormat.TREE.

        Returns:
            Prompt: An instance of the Prompt class.
        """
        dest_id = get_folder_id_from_params_set(
            connection,
            connection.project_id,
            folder=destination_folder,
            folder_path=destination_folder_path,
        )

        if 'information' not in prompt_data:
            prompt_data['information'] = {}

        prompt_data['information']['name'] = name
        prompt_data['information']['destinationFolderId'] = dest_id
        prompt_data['information']['subType'] = (
            sub_type.value if isinstance(sub_type, ObjectSubType) else sub_type
        )
        response = prompts.create_prompt(
            connection,
            prompt_data,
            show_expression_as=get_enum_val(show_expression_as, ExpressionFormat),
        ).json()
        return cls.from_dict(source=response, connection=connection)

    @classmethod
    @method_version_handler('11.4.0600')
    def create_value_prompt(
        cls,
        connection: Connection,
        name: str,
        sub_type: ObjectSubType | str,
        destination_folder: Folder | str,
        title: str | None = None,
        instruction: str | None = None,
        restrictions: dict | PromptRestrictions | None = None,
        default_answer: dict | str | int | float | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> 'Prompt':
        """Create a new value prompt object.

        Args:
            connection (Connection): Strategy One connection object.
            name (str): Name of the prompt.
            sub_type (ObjectSubType | str): Sub-type of the prompt
                (PROMPT_STRING, PROMPT_DATE, PROMPT_DOUBLE, PROMPT_BIG_DECIMAL).
            destination_folder (Folder | str): Destination folder object or
                folder ID/path.
            title (str, optional): Title of the prompt. If not provided, will be
                auto-generated based on sub_type.
            instruction (str, optional): Instruction for the prompt. If not
                provided, will be auto-generated.
            restrictions (dict | PromptRestrictions, optional): Restrictions for
                the prompt.
            default_answer (dict | str | int | float, optional): Default answer
                value. Can be a dictionary, string, integer, or floating-point
                number.
            show_expression_as (ExpressionFormat | str, optional): How
            expressions should be presented. Defaults to ExpressionFormat.TREE.

        Returns:
            Prompt: An instance of the Prompt class.
        """
        VALUE_PROMPT_SUB_TYPES = [
            ObjectSubType.PROMPT_STRING,
            ObjectSubType.PROMPT_DATE,
            ObjectSubType.PROMPT_DOUBLE,
            ObjectSubType.PROMPT_BIG_DECIMAL,
        ]

        if not isinstance(sub_type, ObjectSubType):
            sub_type = ObjectSubType(sub_type)
        if sub_type not in VALUE_PROMPT_SUB_TYPES:
            raise ValueError(
                f"Invalid sub_type '{sub_type}'. "
                f"Possible values are: {VALUE_PROMPT_SUB_TYPES}"
            )
        if not title:
            title_mapping = {
                ObjectSubType.PROMPT_STRING: 'Text',
                ObjectSubType.PROMPT_DATE: 'Date',
                ObjectSubType.PROMPT_DOUBLE: 'Number',
                ObjectSubType.PROMPT_BIG_DECIMAL: 'Big Decimal',
            }
            title = title_mapping.get(sub_type)
        if not instruction:
            instruction = f"Enter a value ({title})."
        if not restrictions:
            restrictions = PromptRestrictions(
                required=False,
                allow_personal_answers=PersonalAnswerMode.NONE.value,
            )
        if default_answer:
            if isinstance(default_answer, (str, int, float)):
                default_answer = {'value': default_answer}
        else:
            default_answer = {}

        prompt_data = cls.prepare_prompt_data(
            title=title,
            instruction=instruction,
            restrictions=restrictions,
            default_answer=default_answer,
            question={},
        )
        return cls.create(
            connection=connection,
            name=name,
            prompt_data=prompt_data,
            sub_type=sub_type,
            destination_folder=destination_folder,
            show_expression_as=show_expression_as,
        )

    @classmethod
    @method_version_handler('11.4.0600')
    def create_attr_elements_prompt(
        cls,
        connection: Connection,
        name: str,
        destination_folder: Folder | str,
        attribute: Attribute | str,
        title: str | None = None,
        instruction: str | None = None,
        restrictions: dict | PromptRestrictions | None = None,
        default_answer: dict | list | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> 'Prompt':
        """Create a new attribute element prompt.

        Args:
            connection (Connection): Connection object.
            name (str): Name of the prompt.
            destination_folder (Folder | str): Destination folder object or
                folder ID/path.
            attribute (Attribute | str): Attribute object or ID or name of the
                attribute to be used in the prompt.
            title (str, optional): Title of the prompt. If not provided, will be
                auto-generated based on the attribute name.
            instruction (str, optional): Instruction for the prompt. If not
                provided, will be auto-generated.
            restrictions (dict | PromptRestrictions, optional): Restrictions for
                the prompt.
            default_answer (dict | list, optional): Default answer value. Can
                be a dictionary or a list of element dictionaries.
            show_expression_as (ExpressionFormat | str, optional): How
                expressions should be presented. Defaults to
                ExpressionFormat.TREE.

        Returns:
            Prompt: An instance of the Prompt class.
        """

        if not isinstance(attribute, Attribute):
            if is_valid_str_id(attribute):
                attribute = Attribute(connection=connection, id=attribute)
            else:
                attribute = Attribute(connection=connection, name=attribute)
        if isinstance(attribute, Attribute):
            attribute = {
                'objectId': attribute.id,
                'subType': ObjectSubType.ATTRIBUTE.value,
                'name': attribute.name,
            }
        if not title:
            title = attribute.get('name', 'Attribute')
        if not instruction:
            instruction = f"Choose elements of {title}."
        if not restrictions:
            restrictions = PromptRestrictions(
                required=False,
                allow_personal_answers=PersonalAnswerMode.NONE.value,
            )
        if default_answer:
            if isinstance(default_answer, list):
                default_answer = {'elements': default_answer}
        else:
            default_answer = {}

        prompt_data = cls.prepare_prompt_data(
            title=title,
            instruction=instruction,
            restrictions=restrictions,
            default_answer=default_answer,
            question={'attribute': attribute, 'listAllElements': True},
        )
        return cls.create(
            connection=connection,
            name=name,
            prompt_data=prompt_data,
            sub_type=ObjectSubType.PROMPT_ELEMENTS,
            destination_folder=destination_folder,
            show_expression_as=show_expression_as,
        )

    @staticmethod
    def prepare_prompt_data(
        title, instruction, restrictions, default_answer, question
    ) -> dict:
        return {
            'title': title,
            'instruction': instruction,
            'restriction': (
                restrictions.to_dict()  # NOSONAR due to SonarQube issue
                # https://community.sonarsource.com/t/python-s930-fp-on-pathlib-path-method-calls/134261/7
                if isinstance(restrictions, PromptRestrictions)
                else restrictions
            ),
            'defaultAnswer': default_answer,
            'question': question,
        }

    @method_version_handler('11.4.0600')
    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        default_answer: dict | None = None,
        instruction: str | None = None,
        restriction: dict | PromptRestrictions | None = None,
        title: str | None = None,
        owner: str | User | None = None,
        owner_id: str | None = None,
        owner_username: str | None = None,
        show_expression_as: ExpressionFormat | str = ExpressionFormat.TREE,
    ) -> None:
        """Alter prompt properties.

        Args:
        name (str, optional): Name of the prompt.
        description (str, optional): Description of the prompt.
        default_answer (dict , optional): Default answer value.
        instruction (str, optional): Instruction text for the prompt.
        restriction (dict | PromptRestrictions, optional): Restrictions for the
            prompt. Can be a dictionary or PromptRestrictions instance.
        title (str, optional): Title of the prompt.
        owner (str | User, optional): New owner of the prompt.
            Can be a User object, user ID or username.
        owner_id (str, optional): ID of the new owner.
        owner_username (str, optional): Username of the new owner.
        show_expression_as (ExpressionFormat | str, optional): How expressions
        should be presented. Defaults to ExpressionFormat.TREE.
        """
        if owner or owner_id or owner_username:
            owner = get_owner_id(self.connection, owner, owner_id, owner_username)
            owner_id = None
            owner_username = None
        properties = filter_params_for_func(self.alter, locals(), exclude=['self'])
        properties['subType'] = self.sub_type.value
        self._alter_properties(**properties)

    @method_version_handler('11.4.0600')
    def add_personal_answer(
        self, answer: Any, name_of_personal_answer: str, set_as_default: bool = False
    ) -> bool:
        """Add a personal answer to the prompt.

        Args:
            answer (Any): The personal answer to be added.
            name_of_personal_answer (str): The name of the personal answer.
            set_as_default (bool): Whether to set the answer as the default.

        Returns:
            bool: True if the personal answer was added successfully,
                False otherwise.
        """
        body = {
            "personalPromptAnswerName": name_of_personal_answer,
            "isDefaultPromptAnswer": set_as_default,
            "values": [answer],
        }
        response = prompts.create_personal_answer(
            connection=self.connection,
            id=self.id,
            project_id=self.connection.project_id,
            body=body,
        )
        if response.ok:
            new_answer = response.json()
            self._personal_answers.append(new_answer)
            return True
        else:
            return False

    def to_dict(self, camel_case: bool = True) -> dict:
        result = super().to_dict(camel_case)
        for key in ['promptType', 'prompt_type']:
            if value := result.pop(key, None):
                result['type'] = value.value if isinstance(value, PromptType) else value
                break
        return result

    @property
    def personal_answers(self) -> list[dict]:
        """Get personal answers for the prompt."""
        if not hasattr(self, '_personal_answers') or self._personal_answers is None:
            return []
        return self._personal_answers

    @property
    def restriction(self) -> PromptRestrictions | None:
        """Get the restriction for the prompt."""
        if not hasattr(self, '_restriction') or self._restriction is None:
            self.fetch('restriction')
        return self._restriction
