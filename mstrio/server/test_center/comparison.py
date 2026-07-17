import difflib
import logging
import os
import re
from dataclasses import dataclass
from enum import auto

import pandas as pd

from mstrio import config
from mstrio.connection import Connection
from mstrio.server.environment import Environment
from mstrio.server.test_center.baseline import Baseline, BaselineTest
from mstrio.server.test_center.commons import (
    IntegrityTest,
    IntegrityTestResult,
    ObjectResult,
    _create_export_folder,
    _list_object_by_class,
)
from mstrio.types import ObjectSubTypes
from mstrio.utils.entity import EntityBase
from mstrio.utils.enum_helper import AutoName, get_enum_val
from mstrio.utils.helper import Dictable, delete_none_values, snake_to_camel
from mstrio.utils.resolvers import get_conn_and_env_from_mixed_param
from mstrio.utils.response_processors import test_center as tc_processors
from mstrio.utils.test_center.export_html import CssTemplate, Template
from mstrio.utils.version_helper import class_version_handler, method_version_handler

logger = logging.getLogger(__name__)


@method_version_handler("11.5.0600")
def list_comparison_tests(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
):
    """Get all Comparison Tests stored on the configured storage.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): Strategy connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Comparison Tests as
            list of dicts
        to_dataframe (bool, optional): if True, return Comparison Tests as
            Pandas DataFrame
        limit (int, optional): limit for the number of elements returned
        **filters: Available filter parameters: ['name', 'id', 'description',
            'date_created', 'date_modified', 'version', 'acg', 'owner']

    Returns:
        List of Comparison Test objects in specified format
            (objects, dicts, or DataFrame)
    """
    return ComparisonTest._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        to_dataframe=to_dataframe,
        limit=limit,
        **filters,
    )


@method_version_handler("11.5.0600")
def list_comparison_test_results(
    connection: Connection,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
):
    """Get all Comparison Test Results stored on the configured storage.

    Optionally use `to_dictionary` or `to_dataframe` to choose output format.
    If `to_dictionary` is True, `to_dataframe` is omitted.

    Args:
        connection (Connection): Strategy connection object returned
            by 'connection.Connection()'
        to_dictionary (bool, optional): if True, return Comparison Test Results
            as list of dicts
        to_dataframe (bool, optional): if True, return Comparison Test Results
            as Pandas DataFrame
        limit (int, optional): limit for the number of elements returned
        **filters: Available filter parameters: ['name', 'id', 'description',
            'date_created', 'date_modified', 'version', 'acg', 'owner']

    Returns:
        List of Comparison Test Result objects in specified format
            (objects, dicts, or DataFrame)
    """
    return ComparisonTestResult._list_all(
        connection=connection,
        to_dictionary=to_dictionary,
        to_dataframe=to_dataframe,
        limit=limit,
        **filters,
    )


class ObjectComparisonStatus(AutoName):
    MATCHED = auto()
    NOT_MATCHED = auto()
    ERROR = auto()
    NOT_COMPARED = auto()


class ObjectComparison(ObjectResult):
    """Python representation of a per-object, per-visualization integrity
        comparison result, part of a `ComparisonTestResult`.

    Attributes:
        id: The ID of the object comparison.
        test_id: The ID of the Comparison Test that was run to generate the
            comparison.
        result_id: The ID of the Comparison Test Result that contains this
            object comparison.
        viz_key: The visualization key for the compared object.
        tested_object: The object (report, cube, etc.) that this result
            corresponds to.
        date_created: The date and time when the comparison was created.
        date_modified: The date and time when the comparison was last modified.
        sql_status: Status of the SQL comparison.
        data_status: Status of the data comparison.
        sql_diff: The SQL diff result for the tested object.
        data_diff: The data diff result for the tested object.
    """

    _API_GETTERS = {
        "sql_diff": tc_processors.get_comparison_object_result_sql_diff,
        "data_diff": tc_processors.get_comparison_object_result_data_diff,
    }
    _FROM_DICT_MAP = {
        **ObjectResult._FROM_DICT_MAP,
        "sql_status": ObjectComparisonStatus,
        "data_status": ObjectComparisonStatus,
    }
    _REST_ATTR_MAP = {
        **ObjectResult._REST_ATTR_MAP,
        "comparison_id": "id",
    }

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self._id = kwargs.get("comparison_id", default_value)
        self._sql_status = (
            ObjectComparisonStatus(kwargs.get("sql_status"))
            if kwargs.get("sql_status")
            else default_value
        )
        self._data_status = (
            ObjectComparisonStatus(kwargs.get("data_status"))
            if kwargs.get("data_status")
            else default_value
        )
        self._sql_diff = kwargs.get("sql_diff", default_value)
        self._data_diff = kwargs.get("data_diff", default_value)
        self._source = None
        self._target = None

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the comparison data to a Pandas `DataFrame`.

        Returns:
            pd.DataFrame: A DataFrame containing the comparison data. Its shape
                corresponds to the shape of source and target baselines.
                Each cell contains a boolean value indicating whether the
                corresponding data point is different between the source and
                target baselines.
        """
        src_d = self._source.data

        attr_data_headers = [col["name"] for col in src_d["rows"]]
        metric_data_headers = [
            ",".join(entry) for cols in src_d["columns"] for entry in cols["data"]
        ]

        d = self.data_diff
        attr_data_values = list(
            zip(
                *(
                    [
                        any(diff_entry["row"] == ii for diff_entry in diff_col["data"])
                        for (ii, _row) in enumerate(src_col["data"])
                    ]
                    for (src_col, diff_col) in zip(src_d["rows"] or [], d["rows"] or [])
                )
            )
        )
        metric_data_values = [
            [False] * len(row) for row in src_d["metrics_values"] or []
        ]
        for diff_entry in d["metrics_values"] or []:
            if diff_entry["row"] < len(metric_data_values) and diff_entry["col"] < len(
                metric_data_values[diff_entry["row"]]
            ):
                metric_data_values[diff_entry["row"]][diff_entry["col"]] = True

        attribute_df = pd.DataFrame(data=attr_data_values, columns=attr_data_headers)
        metric_df = pd.DataFrame(data=metric_data_values, columns=metric_data_headers)

        return pd.concat([attribute_df, metric_df], axis=1)

    def _to_export_entries(self) -> dict:
        d = self.to_dict(skip_private_keys=True)

        # This is because `skip_private_keys` does not propagate down
        tested_object_d = self.tested_object.to_dict(skip_private_keys=True)
        source_d = self._source.to_dict(skip_private_keys=True)
        target_d = self._target.to_dict(skip_private_keys=True)

        d["testedObject"] = tested_object_d
        source_d["testedObject"] = tested_object_d
        target_d["testedObject"] = tested_object_d

        return {
            self.export_id: d,
            f"source_{self.export_id}": source_d,
            f"target_{self.export_id}": target_d,
        }

    @staticmethod
    def _build_highlighted_table_template(
        df: pd.DataFrame, diff_mask: pd.DataFrame | None = None
    ) -> Template:
        """Render DataFrame table template with highlighted changed cells."""
        header_cells = [
            Template("comparison_data_diff_header_cell", value=str(col))
            for col in df.columns
        ]
        rows = []

        for row_idx, (_idx, row) in enumerate(df.iterrows()):
            cells = []
            for col_idx, value in enumerate(row):
                changed = False
                if diff_mask is not None and row_idx < len(diff_mask.index):
                    col_name = df.columns[col_idx]
                    if col_name in diff_mask.columns:
                        changed = bool(diff_mask.iloc[row_idx][col_name])

                cell_template = (
                    "comparison_data_diff_cell_changed"
                    if changed
                    else "comparison_data_diff_cell"
                )
                cells.append(Template(cell_template, value=str(value)))
            rows.append(Template("comparison_data_diff_row", cells=cells))

        return Template(
            "comparison_data_diff_table",
            header_cells=header_cells,
            rows=rows,
        )

    @staticmethod
    def _build_sql_line_templates(
        sql_lines: list[str], changed_lines: set[int]
    ) -> list[Template]:
        templates = []
        for idx, line in enumerate(sql_lines, start=1):
            cell_template = (
                "comparison_sql_diff_line_changed"
                if idx - 1 in changed_lines
                else "comparison_sql_diff_line"
            )
            templates.append(
                Template(
                    cell_template,
                    line_no=str(idx),
                    value=line,
                )
            )
        return templates

    @staticmethod
    def _build_sql_diff_blocks(
        source_sql: str,
        target_sql: str,
    ) -> tuple[Template, Template]:
        source_lines = source_sql.splitlines() or [""]
        target_lines = target_sql.splitlines() or [""]

        source_changed: set[int] = set()
        target_changed: set[int] = set()
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                source_changed.update(range(i1, i2))
                target_changed.update(range(j1, j2))

        source_block = Template(
            "comparison_sql_diff_block",
            lines=ObjectComparison._build_sql_line_templates(
                source_lines, source_changed
            ),
        )
        target_block = Template(
            "comparison_sql_diff_block",
            lines=ObjectComparison._build_sql_line_templates(
                target_lines, target_changed
            ),
        )
        return source_block, target_block

    def _to_html_entries(self) -> dict[str, Template]:
        """Generate HTML detail pages for this object comparison.

        Returns:
            dict: Map of entry IDs to rendered HTML strings. Each key
                becomes the filename (without .html) when exported.
        """
        entries = {}

        if self._source is not None:
            for entry_id, html_entry in self._source._to_html_entries().items():
                entries[f"source_{entry_id}"] = html_entry
        if self._target is not None:
            for entry_id, html_entry in self._target._to_html_entries().items():
                entries[f"target_{entry_id}"] = html_entry

        if self.sql_diff:
            source_sql = (
                str(self._source.sql)
                if self._source is not None and self._source.sql is not None
                else ""
            )
            target_sql = (
                str(self._target.sql)
                if self._target is not None and self._target.sql is not None
                else ""
            )
            source_block, target_block = self._build_sql_diff_blocks(
                source_sql, target_sql
            )

            entries[f"{self.export_id}_sql_diff"] = Template(
                "comparison_sql_diff",
                title=f"SQL Diff \u2014 {self.tested_object.name}",
                source_block=source_block,
                target_block=target_block,
            )

        if self.data_diff:
            entries[f"{self.export_id}_data_diff"] = Template(
                "comparison_data_diff",
                title=f"Data Diff \u2014 {self.tested_object.name}",
                source_table=self._build_highlighted_table_template(
                    self._source.to_dataframe(),
                    self.to_dataframe(),
                ),
                target_table=self._build_highlighted_table_template(
                    self._target.to_dataframe(),
                    self.to_dataframe(),
                ),
            )

        return entries

    @property
    def sql_status(self) -> ObjectComparisonStatus | None:
        """Status of the SQL comparison."""
        return self._sql_status

    @property
    def data_status(self) -> ObjectComparisonStatus | None:
        """Status of the data comparison."""
        return self._data_status

    @property
    def sql_diff(self):
        """SQL diff result for this object comparison."""
        return self._sql_diff

    @property
    def data_diff(self):
        """Data diff result for this object comparison."""
        return self._data_diff

    def __repr__(self):
        params = [f"id={self.id}"]
        if self.viz_key:
            params.append(f"viz_key={self.viz_key}")
        formatted_params = ", ".join(params)
        return f"{self.__class__.__name__}({formatted_params})"


@class_version_handler("11.5.0600")
class ComparisonTestResult(IntegrityTestResult):
    """Python representation of a Strategy Comparison Test Result object.

    Attributes:
        source: The source baseline of the comparison.
        target: The target baseline of the comparison.
        status: The running status of the comparison test.
        preparation_status: The preparation status of the comparison test.
        summary: The summary of the comparison test result.
    """

    _API_GETTERS = {
        **IntegrityTestResult._API_GETTERS,
        (
            "date_created",
            "date_modified",
            "source",
            "target",
            "status",
            "preparation_status",
            "object_results",
        ): tc_processors.get_comparison_result,
        "summary": tc_processors.get_comparison_result_summary,
    }
    _API_CANCEL = staticmethod(tc_processors.cancel_comparison_run)
    _API_DELETE = staticmethod(tc_processors.delete_comparison_result)
    _API_BULK_DELETE = staticmethod(tc_processors.bulk_delete_comparison_results)
    _REST_ATTR_MAP = {
        **IntegrityTestResult._REST_ATTR_MAP,
        "comparison_id": "id",
        "integrity_comparison_id": "test_id",
        "test_object_comparisons": "object_results",
    }

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)

        # _test_id can be set from from_dict source or from __init__ arg
        if not hasattr(self, "_test_id") or not self._test_id:
            self._test_id = kwargs.get("integrity_comparison_id", default_value)

        self._source = kwargs.get("source", default_value)
        self._target = kwargs.get("target", default_value)
        self._status = kwargs.get("status", default_value)
        self._summary = kwargs.get("summary", default_value)
        self._preparation_status = kwargs.get("preparation_status", default_value)
        self._object_results = kwargs.get("object_results", default_value)
        self._parsed_object_results = None

    def _get_result_details_to_fetch(self):
        return [
            (o, key)
            for objres in self.object_results
            for (o, key) in [
                (objres, "sql_diff"),
                (objres, "data_diff"),
                (objres._source, "sql"),
                (objres._source, "data"),
                (objres._target, "sql"),
                (objres._target, "data"),
            ]
            if key not in o._fetched_attributes
        ]

    def _to_html_entries(self):
        date_created = self.date_created.strftime("%Y-%m-%d %H:%M:%S %Z")
        created_version = self.created_version

        def _status_cell(status, baseline_file, diff_file):
            status_name = status.replace("_", " ")
            if status == "matched":
                return Template(
                    "comparison_status_link",
                    href=baseline_file,
                    text=status_name,
                )
            if status == "not_matched":
                return Template(
                    "comparison_status_link",
                    href=diff_file,
                    text=status_name,
                )
            return status_name

        object_results: list[ObjectComparison] = self.object_results
        table_rows = [
            Template(
                "comparison_summary_row",
                object=(
                    f"({objres.tested_object.__class__.__name__}) "
                    f"{objres.tested_object.name}"
                ),
                viz=objres._source.viz_name,
                sql_status=_status_cell(
                    get_enum_val(objres.sql_status, ObjectComparisonStatus),
                    f"source_{objres.export_id}_sql.html",
                    f"{objres.export_id}_sql_diff.html",
                ),
                data_status=_status_cell(
                    get_enum_val(objres.data_status, ObjectComparisonStatus),
                    f"source_{objres.export_id}_data.html",
                    f"{objres.export_id}_data_diff.html",
                ),
            )
            for objres in object_results
        ]
        template = Template(
            "comparison_summary",
            id=self.id,
            source_environment=self.source["environment"]["name"],
            target_environment=self.target["environment"]["name"],
            created_version=created_version,
            date_created=date_created,
            table_rows=table_rows,
        )

        entries = {f"summary_{self.id}": template}
        for objres in self.object_results:
            entries.update(objres._to_html_entries())
        return entries

    def export_html(self, location: str = "."):
        """Export the comparison test result to an HTML summary file.

        Args:
            location (str): The folder path where the HTML file will be saved.
                Default is the running script's current working directory.
        """
        # Ensure that all object result details are fetched before exporting
        self.fetch_result_details()

        # Convert all results to populated HTML templates
        export_entries = self._to_html_entries()
        write_targets = {
            f"{entry_id}.html": content for entry_id, content in export_entries.items()
        }
        write_targets["style.css"] = CssTemplate("style")

        # Create folder and files
        folder_path = _create_export_folder(location)
        for file_name, template in write_targets.items():
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as f:
                f.write(template.render())

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
            api=tc_processors.get_all_comparison_results,
            to_dictionary=to_dictionary,
            to_dataframe=to_dataframe,
            limit=limit,
            **filters,
        )

    @property
    def object_results(self):
        if self._parsed_object_results is None:
            source_baseline = Baseline(
                self._connection,
                id=self.source["baseline_id"],
                test_id=self.source["test_id"],
            )
            target_baseline = Baseline(
                self._connection,
                id=self.target["baseline_id"],
                test_id=self.target["test_id"],
            )
            self._parsed_object_results = []
            for objres_dict in self._object_results:
                obj = ObjectComparison.from_dict(objres_dict, self._connection)
                obj._source = source_baseline.get_object_result(
                    objres_dict["source"]["baselineId"], objres_dict["vizKey"]
                )
                obj._target = target_baseline.get_object_result(
                    objres_dict["target"]["baselineId"], objres_dict["vizKey"]
                )
                obj._tested_object = obj._source.tested_object
                self._parsed_object_results.append(obj)
        return self._parsed_object_results

    @property
    def source(self):
        """The source baseline of the comparison."""
        return self._source

    @property
    def target(self):
        """The target baseline of the comparison."""
        return self._target

    @property
    def status(self):
        """The running status of the comparison test."""
        return self._status

    @property
    def summary(self):
        """The summary of the comparison test result."""
        return self._summary

    @property
    def preparation_status(self):
        """The preparation status of the comparison test."""
        return self._preparation_status


class ComparisonMethod(AutoName):
    """Comparison method enumeration.

    Specifies how objects should be matched during comparison.
    """

    BY_ID = auto()
    BY_PATH = auto()


@dataclass
class ComparisonTestSettings(Dictable):
    """Settings for configuring a Comparison Test.

    Attributes:
        compare_content: List of content types to compare: "SQL" and/or "DATA"
        compare_method: Method used to match objects during comparison.
    """

    _FROM_DICT_MAP = {
        "compare_method": ComparisonMethod,
    }
    compare_content: list[str] | None = None
    compare_method: ComparisonMethod | None = None


@class_version_handler("11.5.0600")
class ComparisonTest(IntegrityTest):
    """Python representation of a Strategy Comparison Test object.

    Attributes:
        settings: The comparison test settings.
        source: The source baseline in the comparison.
        target: The target baseline in the comparison.
    """

    _OBJECT_SUBTYPES = [ObjectSubTypes.COMPARISON_TEST]

    _API_GETTERS = {
        **IntegrityTest._API_GETTERS,
        ("settings", "source", "target"): tc_processors.get_comparison_test,
    }
    _API_PATCH = {
        (
            "name",
            "source",
            "target",
            "settings",
        ): (tc_processors.update_comparison_test, "put"),
    }
    _API_DELETE = staticmethod(tc_processors.delete_comparison_test)
    _API_BULK_DELETE = staticmethod(tc_processors.bulk_delete_comparison_tests)

    _FROM_DICT_MAP = {
        **IntegrityTest._FROM_DICT_MAP,
        "settings": ComparisonTestSettings.from_dict,
    }

    def _init_variables(self, default_value, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self.settings = (
            ComparisonTestSettings.from_dict(kwargs["settings"])
            if kwargs.get("settings")
            else default_value
        )
        self.source = kwargs.get("source", default_value)
        self.target = kwargs.get("target", default_value)

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
            api=tc_processors.get_all_comparison_tests,
            dict_unpack_value="integrityComparisons",
            to_dictionary=to_dictionary,
            to_dataframe=to_dataframe,
            limit=limit,
            **filters,
        )

    @staticmethod
    def _normalize_env_url(url: str) -> str:
        return url if url.endswith("/") else url + "/"

    @staticmethod
    def _extract_env_name_from_url(url: str) -> str:
        matches = re.findall(r"[\w-]+", url)
        return matches[min(1, len(matches) - 1)] if matches else ""

    @staticmethod
    def _extract_base_domain_from_url(url: str) -> str:
        matches = re.findall(r"[\w\-.]+", url)
        return matches[min(1, len(matches) - 1)] if matches else ""

    @staticmethod
    def _baseline_test_to_body_entry(b: BaselineTest):
        return {
            "type": "integrity_test",
            "testId": b.id,
            "environment": {
                "id": ComparisonTest._normalize_env_url(b._connection.base_url),
                "name": ComparisonTest._extract_env_name_from_url(
                    b._connection.base_url
                ),
            },
        }

    @staticmethod
    def _baseline_to_body_entry(b: Baseline):
        return {
            "type": "integrity_test_baseline",
            "baselineId": b.id,
            "testId": b.test_id,
            "environment": {
                "id": ComparisonTest._normalize_env_url(b.library_url),
                "name": ComparisonTest._extract_env_name_from_url(b.library_url),
            },
        }

    @staticmethod
    def _integrity_test_to_body_entry(s_t: dict | BaselineTest | Baseline):
        if isinstance(s_t, dict):
            return snake_to_camel(s_t)
        elif isinstance(s_t, BaselineTest):
            return ComparisonTest._baseline_test_to_body_entry(s_t)
        elif isinstance(s_t, Baseline):
            return ComparisonTest._baseline_to_body_entry(s_t)
        else:
            raise ValueError(
                "Integrity test must be of type `BaselineTest`, `Baseline` "
                f"or `dict`. Got {type(s_t)}"
            )

    @staticmethod
    def _normalize_source_target(
        source: dict | BaselineTest | Baseline, target: dict | BaselineTest | Baseline
    ):
        is_remote = True
        if isinstance(source, EntityBase) and isinstance(target, EntityBase):
            source_domain = ComparisonTest._extract_base_domain_from_url(
                source._connection.base_url
            )
            target_domain = ComparisonTest._extract_base_domain_from_url(
                target._connection.base_url
            )
            is_remote = (
                source._connection is not target._connection
                and source_domain != target_domain
            )

        source = ComparisonTest._integrity_test_to_body_entry(source)
        target = ComparisonTest._integrity_test_to_body_entry(target)
        source_domain = ComparisonTest._extract_base_domain_from_url(
            source["environment"]["id"]
        )
        target_domain = ComparisonTest._extract_base_domain_from_url(
            target["environment"]["id"]
        )
        is_remote = is_remote and source_domain != target_domain
        target["remote"] = is_remote

        return source, target

    @classmethod
    def create(
        cls,
        connection: Connection,
        name: str,
        source: dict | BaselineTest | Baseline,
        target: dict | BaselineTest | Baseline,
        settings: ComparisonTestSettings | None = None,
        execute_sql: bool | None = None,
        execute_data: bool | None = None,
        to_dictionary: bool = False,
    ):
        """Create a new Comparison Test.

        Args:
            connection (object): Strategy connection object returned
                by 'connection.Connection()'.
            name (str): Name of the Comparison Test.
            source (dict | BaselineTest | Baseline): The source integrity test
                for the comparison. If a Baseline Test definition is provided,
                a new Baseline result will be generated for the test execution.
            target (dict | BaselineTest | Baseline): The target integrity test.
            settings (ComparisonTestSettings, optional): Settings for the
                Comparison Test. Default settings will apply for any settings
                that are not specified.
            execute_sql (bool, optional): Whether to include SQL content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            execute_data (bool, optional): Whether to include data content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            to_dictionary (bool, optional): If True, return the new Comparison
                Test as a dictionary instead of an object. Defaults to False.

            Returns:
                ComparisonTest or dict: The newly created Comparison Test.
        """
        default_settings_dict = {
            "compareContent": ["SQL", "DATA"],
            "compareMethod": "by_id",
        }

        settings = cls._normalize_execution_settings(
            content_dict_key="compareContent",
            initial_settings=default_settings_dict,
            settings_delta=settings,
            execute_sql=execute_sql,
            execute_data=execute_data,
        )
        source, target = cls._normalize_source_target(source, target)
        body = {
            "name": name,
            "source": source,
            "target": target,
            "settings": settings,
        }
        body = delete_none_values(body, recursion=True)
        res_dict = tc_processors.create_comparison_test(connection, body).json()

        if config.verbose:
            logger.info(
                f"Successfully created Comparison Test named: '{name}' "
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
        source: dict | BaselineTest | Baseline | None = None,
        target: dict | BaselineTest | Baseline | None = None,
        settings: ComparisonTestSettings | None = None,
        execute_sql: bool | None = None,
        execute_data: bool | None = None,
    ):
        """Alter the properties of the Comparison Test.

        Args:
            name (str): Name of the Comparison Test.
            source (dict | BaselineTest | Baseline): The source integrity test
                for the comparison. If a Baseline Test definition is provided,
                a new Baseline result will be generated for the test execution.
            target (dict | BaselineTest | Baseline): The target integrity test.
            settings (ComparisonTestSettings, optional): Settings for the
                Comparison Test. Default settings will apply for any settings
                that are not specified.
            execute_sql (bool, optional): Whether to include SQL content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
            execute_data (bool, optional): Whether to include data content
                in the test. Overrides the `execute_content` field in `settings`
                if specified.
        """
        name = name or self.name
        source, target = self._normalize_source_target(
            source or self.source, target or self.target
        )

        settings = self._normalize_execution_settings(
            content_dict_key="compareContent",
            initial_settings=self.settings,
            settings_delta=settings,
            execute_sql=execute_sql,
            execute_data=execute_data,
        )
        self._alter_properties(
            name=name, source=source, target=target, settings=settings
        )

    def execute(
        self, target_env: Connection | Environment | None = None
    ) -> ComparisonTestResult:
        """Executes the Comparison Test.

        Args:
            target_env (Connection | Environment, optional): Connection to the
                target environment or Environment object. Required for
                cross-environment comparisons. Target must have the same
                Storage Service configuration as the source environment.

        Returns:
            ComparisonTestResult: Object containing the result execution status
                and results.
        """
        if self.is_cross_environment:
            if not target_env:
                raise ValueError(
                    "Target environment connection must be provided for "
                    "cross-environment comparison tests."
                )
            source_env = Environment(self._connection)
            target_conn, target_env = get_conn_and_env_from_mixed_param(target_env)
            if source_env.storage_service != target_env.storage_service:
                raise ValueError(
                    "Source and target environments must have the same Storage "
                    "Service configuration for cross-environment comparison tests."
                )
            match self.target["type"]:
                case "integrity_test_baseline":
                    storage_file_id = (
                        tc_processors.sync_baseline_result(
                            target_conn,
                            self.target["test_id"],
                            self.target["baseline_id"],
                        )
                        .json()
                        .get("fileId")
                    )
                case "integrity_test":
                    baseline_res = tc_processors.run_baseline_test(
                        target_conn, self.target["test_id"], body={"storageSync": True}
                    ).json()
                    storage_file_id = baseline_res.get("syncFileId")
                case _:
                    raise ValueError(
                        "Unknown comparison target type. "
                        "Expected 'integrity_test' or 'integrity_test_baseline'."
                    )
            body = {"storageSyncInfo": {"targetFileId": storage_file_id}}
        else:
            body = {}
        res = tc_processors.run_comparison_test(self._connection, self.id, body).json()
        return ComparisonTestResult.from_dict(res, self._connection)

    @property
    def is_cross_environment(self) -> bool:
        """Whether this Comparison Test is a cross-environment comparison."""
        return bool(self.target.get("remote"))
