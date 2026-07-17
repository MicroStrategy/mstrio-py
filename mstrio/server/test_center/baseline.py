import logging
from dataclasses import dataclass
from enum import Enum, auto

import pandas as pd

from mstrio import config
from mstrio.connection import Connection
from mstrio.server.test_center.commons import (
    IntegrityTest,
    IntegrityTestResult,
    ObjectResult,
    _list_object_by_class,
)
from mstrio.types import ExtendedType, ObjectSubTypes, ObjectTypes
from mstrio.utils.entity import Entity
from mstrio.utils.enum_helper import AutoUpperName, get_enum_val
from mstrio.utils.helper import Dictable
from mstrio.utils.object_mapping import map_objects_list
from mstrio.utils.response_processors import test_center as tc_processors
from mstrio.utils.test_center.export_html import Raw, Template
from mstrio.utils.version_helper import (
    class_version_handler,
    meets_minimal_version,
    method_version_handler,
)

logger = logging.getLogger(__name__)


def _object_list_from_dict(source: list[dict], connection: Connection):
    """Wraps `map_objects_list` to be used with dict operations
    in `EntityBase`."""
    return map_objects_list(connection, source)


@method_version_handler("11.5.0600")
def list_baseline_tests(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
):
    """Get all Baseline Test definitions stored on the configured storage.

    Args:
        connection (Connection): Strategy connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Baseline Tests as list
            of dicts.
        to_dataframe (bool, optional): if True, return Baseline Tests as
            Pandas DataFrame
        limit (int, optional): limit for the number of elements returned
        **filters: Available filter parameters: ['name', 'id', 'description',
            'date_created', 'date_modified', 'version', 'acg', 'owner']

    Returns:
        List of Baseline Test objects in specified format
            (objects, dicts, or DataFrame)
    """
    return BaselineTest._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        to_dataframe=to_dataframe,
        limit=limit,
        **filters,
    )


@method_version_handler("11.5.0600")
def list_baseline_results(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
):
    """Get all Baselines stored on the configured storage.

    Args:
        connection (Connection): Strategy connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Baselines as list
            of dicts.
        to_dataframe (bool, optional): if True, return Baselines as
            Pandas DataFrame
        limit (int, optional): limit for the number of elements returned
        **filters: Available filter parameters: ['name', 'id', 'description',
            'date_created', 'date_modified', 'version', 'acg', 'owner']

    Returns:
        List of Baseline objects in specified format
            (objects, dicts, or DataFrame)
    """
    return Baseline._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        to_dataframe=to_dataframe,
        limit=limit,
        **filters,
    )


class PromptAnswerSource(AutoUpperName):
    """Prompt answer source enumeration.

    Specifies the precedence for choosing prompt answers during baseline
    testing.
    """

    PERSONAL_ANSWER = auto()
    DEFAULT_ANSWER = auto()
    CUSTOM_ANSWER = auto()
    INTERNAL_ANSWER = auto()


@dataclass
class BaselineTestSettings(Dictable):
    """Settings for configuring a Baseline Test.

    Controls which content types are captured and how prompts are answered
    during baseline testing.

    Attributes:
        dashboard_sql_enabled: Whether to capture dashboard SQL.
        dashboard_data_enabled: Whether to capture dashboard data.
        dashboard_visualization_screenshot_enabled: Whether to capture
            dashboard visualization screenshots.
        cube_data_enabled: Whether to capture cube data.
        cube_sql_enabled: Whether to capture cube SQL.
        report_data_enabled: Whether to capture report data.
        report_sql_enabled: Whether to capture report SQL.
        prompt_answer_source_precedence: Precedence for selecting prompt
            answers.
        execute_content: List of content types to test against. Valid values
            are "DATA" and "SQL".
    """

    _FROM_DICT_MAP = {
        "prompt_answer_source_precedence": [PromptAnswerSource],
    }
    dashboard_sql_enabled: bool | None = None
    dashboard_data_enabled: bool | None = None
    dashboard_visualization_screenshot_enabled: bool | None = None
    cube_data_enabled: bool | None = None
    cube_sql_enabled: bool | None = None
    report_data_enabled: bool | None = None
    report_sql_enabled: bool | None = None
    prompt_answer_source_precedence: list[PromptAnswerSource] | None = None
    execute_content: list[str] | None = None


class ObjectBaselineStatus(Enum):
    COMPLETED = 0
    RUNNABLE = 1
    RUNNING = 2
    ANALYZING = 3
    NOT_SUPPORTED = 4
    TIMEOUT = 5
    NOT_RUNNABLE = 6
    ERROR = 7
    PAUSED = 8
    COMPLETED_WITH_ERRORS = 9
    PROMPT_PENDING = 10
    SUBMITTED = 11
    CREATED = 12
    SKIPPED = 16


class ObjectBaseline(ObjectResult):
    """Python representation of a per-object, per-visualization integrity
        baseline result, part of a `Baseline`.

    Attributes:
        id: The ID of the object baseline.
        test_id: The ID of the Baseline Test that was run to generate the
            baseline.
        result_id: The ID of the Baseline result that contains this object
            baseline.
        viz_key: The visualization key for the compared object.
        viz_name: The visualization name for the compared object.
        library_url: The Strategy Library URL of the baseline.
        tested_object: The object (report, cube, etc.) that this result
            corresponds to.
        date_created: The date and time when the baseline was created.
        date_modified: The date and time when the baseline was last modified.
        sql_status: Status of the SQL baseline.
        data_status: Status of the data baseline.
        sql: The SQL baseline for the tested object.
        data: The data baseline for the tested object.
    """

    _API_GETTERS = {
        "sql": tc_processors.get_baseline_object_result_sql,
        "data": tc_processors.get_baseline_object_result_data,
    }
    _FROM_DICT_MAP = {
        **ObjectResult._FROM_DICT_MAP,
        "settings": BaselineTestSettings.from_dict,
        "sql_status": ObjectBaselineStatus,
        "data_status": ObjectBaselineStatus,
    }
    _REST_ATTR_MAP = {
        **ObjectResult._REST_ATTR_MAP,
        "baseline_id": "id",
    }

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self._id = kwargs.get("baseline_id", default_value)
        self._viz_name = kwargs.get("viz_name", default_value)
        self._library_url = kwargs.get("library_url", default_value)
        self.settings = (
            BaselineTestSettings.from_dict(kwargs["settings"])
            if kwargs.get("settings")
            else default_value
        )
        self._sql_status = (
            ObjectBaselineStatus(kwargs.get("sql_status", default_value))
            if kwargs.get("sql_status") is not None
            else default_value
        )
        self._data_status = (
            ObjectBaselineStatus(kwargs.get("data_status", default_value))
            if kwargs.get("data_status") is not None
            else default_value
        )
        self._sql = kwargs.get("sql", default_value)
        self._data = kwargs.get("data", default_value)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the baseline data to a Pandas `DataFrame`.

        Returns:
            pd.DataFrame: A DataFrame containing the baseline data.
        """
        d = self.data
        attr_data_headers = [col["name"] for col in d["rows"]]
        metric_data_headers = [
            ",".join(entry) for cols in d["columns"] for entry in cols["data"]
        ]
        attr_data_values = zip(
            *([",".join(entry) for entry in col["data"]] for col in d["rows"])
        )
        metric_data_values = d["metrics_values"]

        attribute_df = pd.DataFrame(data=attr_data_values, columns=attr_data_headers)
        metric_df = pd.DataFrame(data=metric_data_values, columns=metric_data_headers)

        return pd.concat([attribute_df, metric_df], axis=1)

    def _to_export_entries(self) -> dict[str, dict]:
        d = self.to_dict(skip_private_keys=True)

        # This is because `skip_private_keys` does not propagate down
        d["testedObject"] = self.tested_object.to_dict(skip_private_keys=True)

        return {self.export_id: d}

    def _to_html_entries(self) -> dict[str, Template]:
        """Generate HTML detail pages for this object baseline.

        Returns:
            dict: Map of entry IDs to rendered HTML strings. Each key
                becomes the filename (without .html) when exported.
        """
        obj_title = self.tested_object.name
        if self.viz_name:
            obj_title += f"/{self.viz_name}"

        entries: dict[str, str] = {}

        if self.sql:
            entries[f"{self.export_id}_sql"] = Template(
                "comparison_detail",
                title=f"SQL Baseline — {obj_title}",
                content=self.sql,
            )

        if self.data:
            df = self.to_dataframe()
            is_empty_df = df.empty and len(df.columns) == 0
            entries[f"{self.export_id}_data"] = Template(
                "baseline_data",
                title=f"Data Baseline — {obj_title}",
                len_string=f"Number of rows: {len(df)}",
                table=(
                    "No data returned" if is_empty_df else Raw(df.to_html(index=False))
                ),
            )

        return entries

    @property
    def viz_name(self) -> str | None:
        """The visualization name for the compared object."""
        return self._viz_name

    @property
    def library_url(self) -> str | None:
        """The Strategy Library URL of the baseline."""
        return self._library_url

    @property
    def sql_status(self) -> ObjectBaselineStatus | None:
        """Status of the SQL baseline."""
        return self._sql_status

    @property
    def data_status(self) -> ObjectBaselineStatus | None:
        """Status of the data baseline."""
        return self._data_status

    @property
    def sql(self) -> str | None:
        """SQL content for this object result."""
        return self._sql

    @property
    def data(self) -> dict | None:
        """Data payload for this object result."""
        return self._data

    def __repr__(self):
        params = [f"id={self.id}"]
        if self.viz_key:
            params.append(f"viz_key={self.viz_key}")
        formatted_params = ", ".join(params)
        return f"{self.__class__.__name__}({formatted_params})"


@class_version_handler("11.5.0600")
class Baseline(IntegrityTestResult):
    """Python representation of a Strategy Baseline object, a result
        of a Baseline Test execution.

    Attributes:
        library_url: The Strategy Library URL of the baseline.
        status: The running status of the baseline test.
        preparation_status: The preparation status of the baseline test.
        summary: The summary of the comparison test result.
    """

    _API_GETTERS = {
        **IntegrityTestResult._API_GETTERS,
        (
            "date_created",
            "date_modified",
            "library_url",
            "status",
            "preparation_status",
            "object_results",
        ): tc_processors.get_baseline_result,
        "summary": tc_processors.get_baseline_result_summary,
    }
    _API_CANCEL = staticmethod(tc_processors.cancel_baseline_run)
    _API_DELETE = staticmethod(tc_processors.delete_baseline_result)
    _API_BULK_DELETE = staticmethod(tc_processors.bulk_delete_baseline_results)
    _REST_ATTR_MAP = {
        **IntegrityTestResult._REST_ATTR_MAP,
        "baseline_id": "id",
        "integrity_test_id": "test_id",
    }

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)

        # _test_id can be set from from_dict source or from __init__ arg
        if not hasattr(self, "_test_id") or not self._test_id:
            self._test_id = kwargs.get("integrity_test_id", default_value)

        self._library_url = kwargs.get("library_url", default_value)
        self._preparation_status = kwargs.get("preparation_status", default_value)
        self._object_results = kwargs.get("object_results", default_value)
        self._parsed_object_results = None

    def _get_result_details_to_fetch(self):
        return [
            (objres, key)
            for objres in self.object_results
            for key in ["sql", "data"]
            if key not in objres._fetched_attributes
        ]

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        **filters,
    ):
        filters = cls._python_to_rest(filters)
        return _list_object_by_class(
            cls=cls,
            connection=connection,
            api=tc_processors.get_all_baseline_results,
            to_dictionary=to_dictionary,
            to_dataframe=to_dataframe,
            limit=limit,
            **filters,
        )

    @property
    def library_url(self) -> str:
        """Strategy Library URL of the baseline."""
        return self._library_url

    @property
    def preparation_status(self) -> str:
        """The preparation status of the baseline test."""
        return self._preparation_status

    @property
    def object_results(self) -> list[ObjectBaseline]:
        """The list of object results for the baseline test."""
        if self._parsed_object_results is None:
            self._parsed_object_results = []
            for objres_dict in self._object_results:
                obj = ObjectBaseline.from_dict(objres_dict, self._connection)
                self._parsed_object_results.append(obj)
        return self._parsed_object_results


@class_version_handler("11.5.0600")
class BaselineTest(IntegrityTest):
    """Python representation of a Strategy Baseline Test object.

    Attributes:
        settings: The settings of the baseline test.
    """

    _OBJECT_SUBTYPES = [ObjectSubTypes.BASELINE_TEST]

    _API_GETTERS = {
        **IntegrityTest._API_GETTERS,
        ("settings", "test_objects"): tc_processors.get_baseline_test,
    }
    _API_PATCH = {
        (
            "name",
            "test_objects",
            "settings",
        ): (tc_processors.update_baseline_test, "put"),
    }
    _API_DELETE = staticmethod(tc_processors.delete_baseline_test)
    _API_BULK_DELETE = staticmethod(tc_processors.bulk_delete_baseline_tests)

    _FROM_DICT_MAP = {
        **IntegrityTest._FROM_DICT_MAP,
        "settings": BaselineTestSettings.from_dict,
        "test_objects": _object_list_from_dict,
    }
    _FN_LIST_ALL = list_baseline_tests

    def _init_variables(self, default_value, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self.settings = (
            BaselineTestSettings.from_dict(kwargs["settings"])
            if kwargs.get("settings")
            else default_value
        )

        self.test_objects = (
            map_objects_list(self._connection, kwargs["test_objects"])
            if kwargs.get("test_objects")
            else default_value
        )

    @staticmethod
    def _entity_to_rest_request(obj, connection: Connection) -> dict:
        if isinstance(obj, Entity):
            return {
                "id": obj.id,
                "name": obj.name,
                "type": get_enum_val(obj.type, ObjectTypes),
                "subtype": get_enum_val(obj.subtype, ObjectSubTypes),
                "extType": get_enum_val(obj.ext_type, ExtendedType),
                "viewMedia": obj.view_media,
                "projectId": obj.project_id or connection.project_id,
                "ancestors": obj.ancestors,
            }
        elif isinstance(obj, dict):
            return obj
        else:
            raise ValueError(
                f"Test object must be either an Entity or a dict, got {type(obj)}"
            )

    @classmethod
    def _normalize_prompt_answer_source_precedence(
        cls, settings: dict, connection: Connection
    ) -> dict:
        """Normalize prompt answer source values in test settings to format
        expected in POST/PUT body, depending on I-Server version.
        """
        if "promptAnswerSourcePrecedence" not in settings or meets_minimal_version(
            connection.iserver_version, "11.6.0600"
        ):
            return settings

        source_to_write_value = {
            "PERSONAL_ANSWER": 0,
            "DEFAULT_ANSWER": 1,
            "CUSTOM_ANSWER": 2,
        }

        try:
            settings["promptAnswerSourcePrecedence"] = [
                source_to_write_value[source]
                for source in settings["promptAnswerSourcePrecedence"]
            ]
        except KeyError as error:
            raise ValueError(f"Unsupported prompt answer source: {error.args[0]}")

        return settings

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        test_objects: list[Entity | dict],
        settings: BaselineTestSettings | None = None,
        execute_sql: bool | None = None,
        execute_data: bool | None = None,
        to_dictionary=False,
    ) -> "BaselineTest | dict":
        """Create a new Baseline Test.

        Args:
            connection (Connection): Strategy connection object returned
                by 'connection.Connection()'.
            name (str): Name of the Baseline Test.
            test_objects (list[Entity or dict]): List of test objects to include
                in the Baseline Test.
            settings (BaselineTestSettings, optional): Settings for the Baseline
                Test. Default settings will apply for any settings that are
                not specified.
            execute_sql (bool, optional): Whether to include SQL content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            execute_data (bool, optional): Whether to include data content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            to_dictionary (bool, optional): If True, return the new Baseline
                Test as a dictionary instead of an object. Defaults to False.

            Returns:
                BaselineTest or dict: The newly created Baseline Test.
        """
        default_settings_dict = {
            "dashboardSqlEnabled": True,
            "dashboardDataEnabled": True,
            "cubeDataEnabled": True,
            "cubeSqlEnabled": True,
            "reportDataEnabled": True,
            "reportSqlEnabled": True,
            "promptAnswerSourcePrecedence": [
                PromptAnswerSource.PERSONAL_ANSWER.value,
                PromptAnswerSource.DEFAULT_ANSWER.value,
            ],
            "executeContent": ["DATA", "SQL"],
        }
        settings = cls._normalize_execution_settings(
            content_dict_key="executeContent",
            initial_settings=default_settings_dict,
            settings_delta=settings,
            execute_sql=execute_sql,
            execute_data=execute_data,
        )
        settings = cls._normalize_prompt_answer_source_precedence(settings, connection)

        body = {
            "name": name,
            "testObjects": [
                cls._entity_to_rest_request(obj, connection) for obj in test_objects
            ],
            "settings": settings,
        }
        res_dict = tc_processors.create_baseline_test(connection, body)

        if config.verbose:
            logger.info(
                f"Successfully created Baseline Test named: '{name}' "
                f"with ID: '{res_dict.get('id')}'"
            )
        return (
            res_dict
            if to_dictionary
            else cls.from_dict(res_dict, connection=connection)
        )

    def alter(
        self,
        name: str | None = None,
        test_objects: list[Entity] | None = None,
        settings: BaselineTestSettings | None = None,
        execute_sql: bool | None = None,
        execute_data: bool | None = None,
    ):
        """Alter the properties of the Baseline Test.

        Args:
            name (str): Name of the Baseline Test.
            test_objects (list[Entity or dict]): List of test objects to include
                in the Baseline Test.
            settings (BaselineTestSettings, optional): Settings for the Baseline
                Test. Settings that are not specified will not be updated.
            execute_sql (bool, optional): Whether to include SQL content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            execute_data (bool, optional): Whether to include data content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
        """
        name = name or self.name
        test_objects = test_objects or self.test_objects
        test_objects = [
            self._entity_to_rest_request(obj, self._connection) for obj in test_objects
        ]

        settings = self._normalize_execution_settings(
            content_dict_key="executeContent",
            initial_settings=self.settings,
            settings_delta=settings,
            execute_sql=execute_sql,
            execute_data=execute_data,
        )
        settings = self._normalize_prompt_answer_source_precedence(
            settings, self._connection
        )

        self._alter_properties(name=name, test_objects=test_objects, settings=settings)

    def execute(self) -> Baseline:
        """Executes the test.

        Returns:
            Object containing the result execution status and results.
        """
        res = tc_processors.run_baseline_test(self._connection, self.id).json()
        return Baseline.from_dict(res, self._connection)

    @classmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        **filters,
    ):
        filters = cls._python_to_rest(filters)
        return _list_object_by_class(
            cls=cls,
            connection=connection,
            api=tc_processors.get_all_baseline_tests,
            to_dictionary=to_dictionary,
            to_dataframe=to_dataframe,
            limit=limit,
            **filters,
        )
