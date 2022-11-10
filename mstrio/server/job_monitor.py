from enum import auto, Enum
import logging
from typing import List, Optional, TYPE_CHECKING, Union

from packaging import version

from mstrio import config
from mstrio.api import monitors
from mstrio.api.exceptions import MstrException, PartialSuccess, Success, VersionException
from mstrio.connection import Connection
from mstrio.server import Node, Project
from mstrio.utils.entity import Entity, EntityBase
from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import validate_param_value
from mstrio.utils.monitors import all_nodes_async
from mstrio.utils.time_helper import DatetimeFormats, map_str_to_datetime
from mstrio.utils.version_helper import class_version_handler, method_version_handler

if TYPE_CHECKING:
    from mstrio.users_and_groups import User

logger = logging.getLogger(__name__)

ISERVER_VERSION_11_3_2 = '11.3.0200'


class DeliveryType(AutoName):
    RESERVED = auto()
    EMAIL = auto()
    FILE = auto()
    PRINTER = auto()
    CUSTOM = auto()
    INBOX = auto()
    CLIENT = auto()
    CACHE = auto()
    MOBILE = auto()
    BLACKBERRY = auto()
    IPHONE = auto()
    IPAD = auto()
    CAMPAIGN = auto()
    SNAPSHOT = auto()
    FTP = auto()
    ANDROID = auto()
    LAST_ONE = auto()
    COUNT = auto()
    ALL_INCLUDING_SNAPSHOT = auto()


class SortByV1(Enum):
    JOB_TYPE = 'jobType'
    USER_FULL_NAME = 'userFullName'
    OBJECT_ID = 'objectId'
    STATUS = 'status'
    PROJECT_ID = 'projectId'
    # check if valid as there are multiple
    # inconsistent information about sorting
    PROJECT_NAME = 'projectName'
    CREATION_TIME = 'creationTime'
    DESCRIPTION = 'description'
    JOB_ID = 'jobId'


class JobStatus(AutoName):
    READY = auto()
    EXECUTING = auto()
    WAITING = auto()
    COMPLETED = auto()
    ERROR = auto()
    CANCELING = auto()
    STOPPED = auto()
    WAITING_ON_GOVERNOR = auto()
    WAITING_FOR_AUTOPROMPT = auto()
    WAITING_FOR_PROJECT = auto()
    WAITING_FOR_CACHE = auto()
    WAITING_FOR_CHILDREN = auto()
    WAITING_FOR_RESULTS = auto()
    LOADING_PROMPT = auto()
    RESOLVING_DESTINATION = auto()
    DELIVERING = auto()
    EXPORTING = auto()
    CACHE_READY = auto()
    WAITING_FOR_DI_FILE = auto()
    WAITING_FOR_CONFLICT_RESOLVE = auto()
    STEP_PAUSING = auto()


class JobType(AutoName):
    INTERACTIVE = auto()
    SUBSCRIPTION = auto()
    PREDICTIVE_CACHE = auto()


# NOTE: new endpoint Enums below:
class ObjectType(AutoName):
    OTHERS = auto()
    REPORT = auto()
    CUBE = auto()
    DOCUMENT = auto()
    DOSSIER = auto()


class PUName(AutoName):
    BROWSING = auto()
    RESOLUTION = auto()
    QUERY_EXECUTIONS = 'query_execution'
    ANALYTICAL = auto()
    SQL_ENGINE = auto()
    DATA_FORMATTING = auto()
    NCS = auto()
    REST_ASYNCHRONOUS = auto()


class SubscriptionType(AutoName):
    RESERVED = auto()
    EMAIL = auto()
    PRINTER = auto()
    CUSTOM = auto()
    INBOX = auto()
    CLIENT = auto()
    CACHE = auto()
    MOBILE = auto()
    MOBILE_BLACKBERRY = auto()
    MOBILE_IPHONE = auto()
    MOBILE_IPAD = auto()
    CAMPAIGN = auto()
    SNAPSHOT = auto()
    FTP = auto()
    MOBILE_ANDROID = auto()
    LAST_ONE = auto()
    COUNT = auto()
    ALL = auto()
    ALL_INCLUDING_SNAPSHOT = auto()


class SortBy(Enum):
    ID_ASC = '+id'
    ID_DESC = '-id'
    TYPE_ASC = '+type'
    TYPE_DESC = '-type'
    STATUS_ASC = '+status'
    STATUS_DESC = '-status'
    USER_ASC = '+user'
    USER_DESC = '-user'
    DESCRIPTION_ASC = '+description'
    DESCRIPTION_DESC = '-description'
    OBJECT_TYPE_ASC = '+objectType'
    OBJECT_TYPE_DESC = '-objectType'
    OBJECT_ID_ASC = '+objectId'
    OBJECT_ID_DESC = '-objectId'
    SUBSCRIPTION_TYPE_ASC = '+subscriptionType'
    SUBSCRIPTION_TYPE_DESC = '-subscriptionType'
    PROCESSING_UNIT_PRIORITY_ASC = '+processingUnitPriority'
    PROCESSING_UNIT_PRIORITY_DESC = '-processingUnitPriority'
    CREATION_TIME_ASC = '+creationTime'
    CREATION_TIME_DESC = '-creationTime'
    COMPLETED_TASKS_ASC = '+completedTasks'
    COMPLETED_TASKS_DESC = '-completedTasks'
    PROJECT_ID_ASC = '+projectId'
    PROJECT_ID_DESC = '-projectId'
    PROJECT_NAME_ASC = '+projectName'
    PROJECT_NAME_DESC = '-projectName'
    SUBSCRIPTION_RECIPIENT_ASC = '+subscriptionRecipient'
    SUBSCRIPTION_RECIPIENT_DESC = '-subscriptionRecipient'
    MEMORY_USAGE_ASC = '+memoryUsage'
    MEMORY_USAGE_DESC = '-memoryUsage'
    ELAPSED_TIME_ASC = '+elapsedTime'
    ELAPSED_TIME_DESC = '-elapsedTime'


@method_version_handler('11.3.0200')
def _set_api_wrappers(connection) -> dict:
    if version.parse(connection.iserver_version) == version.parse(ISERVER_VERSION_11_3_2):
        return {
            (
                'id',
                'description',
                'status',
                'type',
                'priority',
                'processing_unit_priority',
                'warehouse_priority',
                'object_id',
                'user',
                'project_name',
                'creation_time',
                'total_tasks',
                'completed_tasks',
                'filter_name',
                'template_name',
                'sql',
                'subscription_owner',
                'subscription_recipient',
                'destination'
            ): monitors.get_job
        }
    else:
        return {
            (
                'id',
                'type',
                'status',
                'user',
                'description',
                'object_type',
                'object_id',
                'parent_id',
                'child_ids',
                'subscription_type',
                'processing_unit_priority',
                'step_id',
                'pu_name',
                'creation_time',
                'completed_tasks',
                'total_tasks',
                'project_name',
                'subscription_recipient',
                'memory_usage',
                'elapsed_time',
                'step_elapsed_time',
                'filter_name',
                'template_name',
                'sql',
                'subscription_owner',
                'error_time',
                'error_message',
                'step_statistics'
            ): monitors.get_job_v2
        }


@method_version_handler('11.3.0200')
def list_jobs(
    connection: "Connection",
    node: Optional[Union[Node, str]] = None,
    user: Optional[Union["User", str]] = None,
    description: Optional[str] = None,
    type: Optional[Union[JobType, str]] = None,
    status: Optional[Union[JobStatus, str]] = None,
    object_id: Optional[str] = None,
    object_type: Optional[ObjectType] = None,
    project: Optional[Union[Project, str]] = None,
    pu_name: Optional[Union[PUName, str]] = None,
    subscription_type: Optional[Union[SubscriptionType, str]] = None,
    subscription_recipient: Optional[Union["User", str]] = None,
    memory_usage: Optional[str] = None,
    elapsed_time: Optional[str] = None,
    sort_by: Optional[Union[SortBy, str]] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters
) -> Union[List["Job"], List[dict]]:
    """List jobs objects or job dictionaires.
    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`
        node(Node, str, optional): Node object or name, if not passed list jobs
            on all nodes
        user(User, str, optional): Field to filter on job owner's full name
        (exact match)
        description(str, optional): Field to filter on job description (partial
            match)
        type(JobType, optional): Field to filter on job type (exact match),
        status(JobStatus, optional): Field to filter on job status (exact match)
        object_id(str, optional): Field to filter on object type (exact
            match)
        object_type(ObjectType, optional): Field to filter on object type (exact
            match)
        project(Project, str, optional): Field to filter on project name (exact
            match)
        pu_name(PUName, optional): Field to filter on processing unit name
            (exact match)
        subscription_type(SubscriptionType, optional): Field to filter on
        subscription type (exact match)
        subscription_recipient(User, str, optional): Field to filter on
            subscription recipient's full name (exact match)
        memory_usage(str, optional): Field to filter on the job elapsed time,
            for example 'gt:100' means filtering jobs with memory usage greater
            than to 100 MB. Valid operators are:
            gt - greater than
            lt - less than
        elapsed_time(str, optional): Field to filter on the job elapsed time,
            for example 'gt:100' means filtering jobs with elapsed time greater
            than 100 milliseconds(11.3.3+) or seconds(11.3.2). Valid operators:
            gt - greater than
            lt - less than
        sort_by(SortBy, optional): Specify sorting criteria, for example
            SortBy.STATUS_ASC means sorting status is ascending order
            or SortBy.USER_DESC means sorting user in descending order.
            Currently, the server supports sorting only by single field.
        to_dictionary(bool, optional): if True, return Schedules as
            list of dicts
        limit(int, optional): maximum number of schedules returned
        **filters(optional): Local filter parameters

    Examples:
        >>> list_jobs_v1(connection, duration='gt:100')

    Returns:
        Union[List["Job"], List[dict]]: list of Job objects or dictionaries.
    """
    user = user.full_name if isinstance(user, Entity) else user
    subscription_recipient = subscription_recipient.full_name if isinstance(
        user, Entity
    ) else subscription_recipient
    if project:
        project = project if isinstance(project, Project) else Project(connection, name=project)

    # depending on version call either one or the other
    if version.parse(connection.iserver_version) == version.parse(ISERVER_VERSION_11_3_2):
        filters = __prepare_v1_request(
            description,
            object_type,
            pu_name,
            subscription_type,
            subscription_recipient,
            memory_usage,
            elapsed_time,
            filters
        )
        return list_jobs_v1(
            connection=connection,
            node=node,
            project=project,
            status=status,
            job_type=type,
            user=user,
            limit=limit,
            to_dictionary=to_dictionary,
            **filters
        )
    else:
        project_name = project.name if project else None
        node_name = node.name if isinstance(node, Node) else node
        msg = "Error fetching chunk of jobs."
        objects = all_nodes_async(
            connection,
            async_api=monitors.get_jobs_v2_async,
            filters=filters,
            error_msg=msg,
            unpack_value='jobs',
            limit=limit,
            node_name=node_name,
            user=user,
            description=description,
            type=type,
            object_id=object_id,
            object_type=object_type,
            project_name=project_name,
            status=status,
            pu_name=pu_name,
            subscription_type=subscription_type,
            subscription_recipient=subscription_recipient,
            memory_usage=memory_usage,
            elapsed_time=elapsed_time,
            sort_by=sort_by,
            fields=['jobs']
        )

    if to_dictionary:
        return objects
    else:
        return [Job.from_dict(source=obj, connection=connection) for obj in objects]


@method_version_handler('11.3.0200')
def list_jobs_v1(
    connection: Connection,
    node: Optional[Union[Node, str]] = None,
    project: Optional[Union[Project, str]] = None,
    status: Optional[Union[JobStatus, str]] = None,
    job_type: Optional[Union[JobType, str]] = None,
    user: Optional[Union["User", str]] = None,
    object_id: Optional[str] = None,
    sort_by: Optional[Union[SortBy, str]] = None,
    to_dictionary: bool = False,
    limit: Optional[int] = None,
    **filters
) -> Union[List["Job"], List[dict]]:
    """List job objects or job dictionaries. Optionally filter list.
    NOTE: list_jobs can return up to 1024 jobs per request.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection()'
        node(Node, str, optional): Node object or name, if not passed list jobs
            on all nodes
        project(str, Project, optional): Project id or object to filter by
        status(JobStatus, optional): Job status to filter by
        job_type(JobType, optional): Job type to filter by
        user(User, str, optional): User object or full name to filter by
        object_id(str, optional): Object id to filter by
        sort_by(SortBy, optional): Specifies sorting criteria to sort by
        to_dictionary(bool, optional): if True, return Schedules as
            list of dicts
        limit(int, optional): maximum number of schedules returned.
        **filters: Available filter parameters:[id, description, status,
            jobType, duration, jobId, objectd]
            - duration(str, optional): Field to filter on the job elapsed time,
                for example 'gt:100' means filtering jobs with elapsed time
                greater than to 100 seconds. Valid operators:
                gt - greater than
                lt - less than

    Examples:
        >>> list_jobs_v1(connection, duration='gt:100')

    Returns:
        Union[List["Job"], List[dict]]: list of Job objects or dictionaries.
    """
    project_id = project.id if isinstance(project, Project) else project
    user_full_name = user.full_name if isinstance(user, Entity) else user

    if 'duration' in filters:
        filters['duration'] = __elapsed_filtering(filters['duration'])

    node_name = node.name if isinstance(node, Node) else node
    msg = "Error fetching chunk of jobs."
    objects = all_nodes_async(
        connection,
        async_api=monitors.get_jobs_async,
        filters=filters,
        error_msg=msg,
        unpack_value='jobs',
        limit=limit,
        node_name=node_name,
        project_id=project_id,
        status=status,
        job_type=job_type,
        user_full_name=user_full_name,
        object_id=object_id,
        sort_by=sort_by
    )

    if to_dictionary:
        return objects
    else:
        return [Job.from_dict(source=obj, connection=connection) for obj in objects]


@method_version_handler('11.3.0200')
def kill_jobs(connection: Connection,
              jobs: List[Union["Job", str]]) -> Union[Success, PartialSuccess, MstrException]:
    """Kill existing jobs by Job objects or job ids.

    Args:
        connection(object): MicroStrategy connection object returned by
            'connection.Connection()'
        jobs: List of Job objects or job ids to kill

    Returns:
        Success: object if all jobs were killed
        PartialSuccess: if not all jobs were killed
        MstrException: otherwise
    """
    validate_param_value("jobs", jobs, list)
    jobs = [job.id if isinstance(job, Job) else job for job in jobs]
    return monitors.cancel_jobs(connection, jobs)


@method_version_handler('11.3.0200')
def kill_all_jobs(
    connection: Connection,
    user: Optional[Union["User", str]] = None,
    description: Optional[str] = None,
    type: Optional[Union[JobType, str]] = None,
    status: Optional[Union[JobStatus, str]] = None,
    object_id: Optional[str] = None,
    object_type: Optional[Union[ObjectType, str]] = None,
    project: Optional[Union[Project, str]] = None,
    pu_name: Optional[Union[PUName, str]] = None,
    subscription_type: Optional[Union[SubscriptionType, str]] = None,
    subscription_recipient: Optional[Union["User", str]] = None,
    memory_usage: Optional[str] = None,
    elapsed_time: Optional[str] = None,
    force: bool = False,
    **filters
) -> Union[Success, PartialSuccess, MstrException]:
    """Kill jobs filtered by passed fields

    Args:
        connection(object): MicroStrategy connection object returned by
            `connection.Connection()`
         node(Node, str, optional): Node object or name, if not passed kill jobs
            on all nodes
        user(User, str, optional): Field to filter on job owner's full name
        (exact match)
        description(str, optional): Field to filter on job description (partial
            match)
        type(JobType, optional): Field to filter on job type (exact match),
        status(JobStatus, optional): Field to filter on job status (exact match)
        object_id(str, optional): Field to filter on object id (exact
            match)
        object_type(ObjectType, optional): Field to filter on object type (exact
            match)
        project(Project, str, optional): Field to filter on project name (exact
            match)
        pu_name(PUName, optional): Field to filter on processing unit name
            (exact match)
        subscription_type(SubscriptionType, optional): Field to filter on
        subscription type (exact match)
        subscription_recipient(User, str, optional): Field to filter on
            subscription recipient's full name (exact match)
        memory_usage(str, optional): Field to filter on the job elapsed time,
            for example 'gt:100' means filtering jobs with memory usage greater
            than to 100 MB. Valid operators are:
            gt - greater than
            lt - less than
        elapsed_time(str, optional): Field to filter on the job elapsed time,
            for example 'gt:100' means filtering jobs with elapsed time greater
            than 100 milliseconds(11.3.3+) or seconds(11.3.2). Valid operators:
            gt - greater than
            lt - less than
        force(bool, optional): Force flag

    Returns:
        Success: object if all jobs were killed
        PartialSuccess: if not all jobs were killed
        MstrException: otherwise
    """

    jobs = list_jobs(
        connection,
        user,
        description,
        type,
        status,
        object_id,
        object_type,
        project,
        pu_name,
        subscription_type,
        subscription_recipient,
        memory_usage,
        elapsed_time,
        filters
    )
    assert jobs, "No jobs to kill"

    jobs_ids = [job.id for job in jobs]
    if not force:
        print(f"Found jobs: {jobs}")
        user_input = input("Are you sure you want to kill those jobs?[Y/N]: ") or 'N'
    if force or user_input == 'Y':
        return kill_jobs(connection, jobs_ids)


def __prepare_v1_request(
    description: str,
    object_type: str,
    pu_name: str,
    subscription_type: str,
    subscription_recipient: str,
    memory_usage: str,
    elapsed_time: str,
    filters: dict
) -> dict:
    # raise VersionException if parameter not supported in v1
    unsupported_parameters = [
        description, object_type, pu_name, subscription_type, subscription_recipient, memory_usage
    ]
    params_str = (
        "description, object_type, pu_name, subscription_type, "
        "subscription_recipient, memory_usage"
    )
    if any(unsupported_parameters):
        msg = (
            f"Passed unsupported parameter for this version of IServer "
            f"({ISERVER_VERSION_11_3_2}) Parameters supported only in 11.3.3+ "
            f"versions: {params_str}"
        )
        raise VersionException(msg)

    if elapsed_time:
        filters['duration'] = elapsed_time
    return filters


def __elapsed_filtering(elapsed: str) -> str:
    if isinstance(elapsed, str) and len(elapsed) > 3 and (elapsed.startswith('gt:')
                                                          or elapsed.startswith('lt:')):
        if elapsed.startswith('gt'):
            return f'>{elapsed[3:]}'
        elif elapsed.startswith('lt'):
            return f'<{elapsed[3:]}'
        else:
            return elapsed
    else:
        raise TypeError('Incorrect "duration" format, correct example: "gt:100" ')


@class_version_handler('11.3.0200')
class Job(EntityBase):
    """Python representation of a Job object.
    Note: Some functionality is missing when working with 11.3.2 I-Server
        versions. To use all functionality 11.3.3 and up will be required.
        There are also some differences between 11.3.2 and 11.3.3+ Job
        attributes values.

    Attributes:
        connection: A MicroStrategy connection object
        id: Job information id
        description: Description of the job
        status: Status of the job
        type: Type of the job
        object_id: Id of object
        object_type: Type of object
        parent_id: Parent ID
        childs_ids: Array of children IDs
        subscription_recipient: Subscription recipient of the job
        subscription_type: Subscription delivery type of the job
        processing_unit_priority: Job Processing Unit Priority
        step_id: Step ID of the job
        user: Full name of the job initiator
        project_name: Name of the project in which the job is active
        project_id: Id of the project in which the job is active
        pu_name: Processing Unit name
        creation_time: Creation time of the job
        elapsed_time: Time elapsed since the creation of the job in milliseconds
            (11.3.3+) or seconds (11.3.2)
        step_elapsed_time: Time elapsed since the creation of the step
            in milliseconds
        memory_usage: Memory usage of the job in bytes
        client_machine: Client machine running the job
        total_tasks: Total tasks of the job
        completed_tasks: Completed tasks of the job
        error_message: Error message for the job
        error_time: Error time of the job
        filter_name: Name of the filter for the job
        sql: SQL of the job
        subscription_owner: Subscription owner
        template_name: Name of the template for the job
        step_statistics: Step statistics for the job
    """

    _FROM_DICT_MAP = {
        'creation_time': DatetimeFormats.FULLDATETIME,
        'error_time': DatetimeFormats.FULLDATETIME,
        'type': JobType,
        'status': JobStatus,
        'object_type': ObjectType,
        'subscription_type': SubscriptionType,
        'pu_name': PUName,
    }
    _API_GETTERS = {
        (
            'id',
            'type',
            'status',
            'user',
            'description',
            'object_type',
            'object_id',
            'parent_id',
            'child_ids',
            'subscription_type',
            'processing_unit_priority',
            'step_id',
            'pu_name',
            'creation_time',
            'completed_tasks',
            'total_tasks',
            'project_name',
            'subscription_recipient',
            'memory_usage',
            'elapsed_time',
            'step_elapsed_time',
            'filter_name',
            'template_name',
            'sql',
            'subscription_owner',
            'error_time',
            'error_message',
            'step_statistics'
        ): monitors.get_job_v2
    }
    _REST_ATTR_MAP = {
        "job_id": None,  # delete job_id and only use id
        "job_type": "type",
        "user_full_name": "user",
        "total_task": "total_tasks",
        "completed_task": "completed_tasks",
        "filter": "filter_name",
        "template": "template_name",
        "machine": "client_machine",
        "priority": None,
        "warehouse_priority": None,
        "destination": None,
        "project_id": None,
        "username": None,
        "delivery_type": None,
        "duration": "elapsed_time",
    }

    def __init__(self, connection: Connection, id: str) -> None:
        """Initialize the Job object, populates it with I-Server data.

        Args:
            connection: MicroStrategy connection object returned
                by `connection.Connection()`
            id: Job information id
        """
        Job._API_GETTERS = _set_api_wrappers(connection)
        super().__init__(connection, object_id=id)

    def _init_variables(self, **kwargs):
        """Initialize variables given kwargs.

        Note: attributes not accepted by any implementation of this function
            in the inheritance chain will be disregarded.
        """
        kwargs = self._rest_to_python(kwargs)
        # create _AVAILABLE_ATTRIBUTES map
        self._AVAILABLE_ATTRIBUTES.update({key: type(val) for key, val in kwargs.items()})

        self._connection = kwargs.get('connection')
        self._id = kwargs.get('id')
        self._description = kwargs.get('description')
        self._status = JobStatus(kwargs.get('status')) if kwargs.get('status') else None
        self._processing_unit_priority = kwargs.get('processing_unit_priority')
        self._creation_time = map_str_to_datetime(
            "creation_time", kwargs.get("creation_time"), self._FROM_DICT_MAP
        )
        self._elapsed_time = kwargs.get('elapsed_time')
        self._project_name = kwargs.get('project_name')
        self._object_id = kwargs.get('object_id')
        self._object_type = ObjectType(kwargs.get('object_type')
                                       ) if kwargs.get('object_type') else None
        self._sql = kwargs.get('sql')
        self._subscription_owner = kwargs.get('subscription_owner')
        self._subscription_recipient = kwargs.get('subscription_recipient')
        self._client_machine = kwargs.get('client_machine')
        self._type = JobType(kwargs.get('type')) if kwargs.get('type') else None
        self._user = kwargs.get('user')
        self._total_tasks = kwargs.get('total_tasks')
        self._completed_tasks = kwargs.get('completed_tasks')
        self._parent_id = kwargs.get('parent_id')
        self._child_ids = kwargs.get('child_ids')
        self._subscription_type = SubscriptionType(
            kwargs.get('subscription_type')
        ) if kwargs.get('subscription_type') else kwargs.get('subscription_type')
        self._step_id = kwargs.get('step_id')
        self._pu_name = PUName(kwargs.get('pu_name')) if kwargs.get('pu_name') else None
        self._memory_usage = kwargs.get('memory_usage')
        self._step_elapsed_time = kwargs.get('step_elapsed_time')
        self._filter_name = kwargs.get('filter_name')
        self._template_name = kwargs.get('template_name')
        self._error_time = map_str_to_datetime(
            "error_time", kwargs.get("error_time"), self._FROM_DICT_MAP
        ) if kwargs.get("error_time") else None
        self._error_message = kwargs.get('error_message')
        self._step_statistics = kwargs.get('step_statistics')

    def kill(self) -> bool:
        """Kill the job.

        Returns:
            True if successfully killed job, False otherwise.
        """
        response = monitors.cancel_job(self._connection, str(self.id))
        if config.verbose:
            success_msg = f"Successfully killed {self.id}."
            fail_msg = f"Error killing job {self.id}."
            msg = success_msg if response.ok else fail_msg
            logger.info(msg)
        return response.ok

    def list_properties(self) -> dict:
        """List Job object properties."""
        properties = super().list_properties()
        properties.pop('connection', None)
        return properties

    @property
    def status(self):
        return self._status

    @property
    def description(self):
        return self._description

    @property
    def processing_unit_priority(self):
        return self._processing_unit_priority

    @property
    def creation_time(self):
        return self._creation_time

    @property
    def project_name(self):
        return self._project_name

    @property
    def object_type(self):
        return self._object_type

    @property
    def object_id(self):
        return self._object_id

    @property
    def sql(self):
        return self._sql

    @property
    def subscription_owner(self):
        return self._subscription_owner

    @property
    def subscription_recipient(self):
        return self._subscription_recipient

    @property
    def client_machine(self):
        return self._client_machine

    @property
    def user(self):
        return self._user

    @property
    def total_tasks(self):
        return self._total_tasks

    @property
    def completed_tasks(self):
        return self._completed_tasks

    @property
    def parent_id(self):
        return self._parent_id

    @property
    def child_ids(self):
        return self._child_ids

    @property
    def subscription_type(self):
        return self._subscription_type

    @property
    def step_id(self):
        return self._step_id

    @property
    def pu_name(self):
        return self._pu_name

    @property
    def memory_usage(self):
        return self._memory_usage

    @property
    def elapsed_time(self):
        return self._elapsed_time

    @property
    def step_elapsed_time(self):
        return self._step_elapsed_time

    @property
    def filter_name(self):
        return self._filter_name

    @property
    def template_name(self):
        return self._template_name

    @property
    def error_time(self):
        return self._error_time

    @property
    def error_message(self):
        return self._error_message

    @property
    def step_statistics(self):
        return self._step_statistics
