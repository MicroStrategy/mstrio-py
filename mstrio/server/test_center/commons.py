import json
import logging
import os
from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from datetime import datetime
from enum import auto

from pandas import DataFrame
from requests import Response
from tqdm import tqdm

from mstrio import config
from mstrio.connection import Connection
from mstrio.helpers import IServerError
from mstrio.types import ObjectTypes
from mstrio.utils.entity import DeleteMixin, Entity, EntityBase
from mstrio.utils.enum_helper import AutoUpperName
from mstrio.utils.helper import (
    Dictable,
    delete_none_values,
    fetch_objects,
    find_object_with_name,
)
from mstrio.utils.object_mapping import map_object
from mstrio.utils.time_helper import DatetimeFormats, map_str_to_datetime

logger = logging.getLogger(__name__)


def _object_from_dict(source: dict, connection: Connection):
    """Wraps `map_object` to be used with dict operations
    in `EntityBase`."""
    return map_object(connection, source)


# TODO: convert more `list_*` methods to use this pattern
def _list_object_by_class(
    cls: type["IntegrityTest | IntegrityTestResult"],
    connection: Connection,
    api: Callable,
    dict_unpack_value: str | None = None,
    to_dictionary: bool = False,
    to_dataframe: bool = False,
    limit: int | None = None,
    **filters,
):
    if to_dictionary and to_dataframe:
        raise ValueError(
            "Please select either `to_dictionary=True` or `to_dataframe=True`, "
            "but not both."
        )
    objects = fetch_objects(
        connection=connection,
        api=api,
        limit=limit,
        filters=filters,
        dict_unpack_value=dict_unpack_value,
    )

    if to_dictionary:
        return objects
    elif to_dataframe:
        return DataFrame(objects)
    else:
        return cls.bulk_from_dict(source_list=objects, connection=connection)


def _create_export_folder(location: str) -> str:
    """Create a folder for exporting test center objects.

    Args:
        location (str): Path to the folder where the export folder should be
            created. Must be an existing folder.

    Returns:
        str: Absolute path to the created export folder.
    """
    # Convert to an absolute path before any operations
    absolute_path = os.path.abspath(location)

    # Check if the provided path exists
    if not os.path.exists(absolute_path):
        raise FileNotFoundError(f"The specified path does not exist: {absolute_path}")

    # Check if the provided path is a directory
    if not os.path.isdir(absolute_path):
        raise NotADirectoryError(
            f"The specified path is not a directory: {absolute_path}"
        )

    # Create folder with current datetime as name (format: YYYYMMDD_HHMMSS)
    folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = os.path.join(absolute_path, folder_name)

    # Create the folder
    os.makedirs(folder_path)

    return folder_path


def _bulk_delete_helper(
    connection: Connection,
    api: Callable,
    objects: "list[str | IntegrityTest | IntegrityTestResult]",
    delete_confirm_msg: str,
    delete_success_msg: str,
    delete_failure_msg: str,
    force: bool = False,
):
    if not force:
        user_input = input(delete_confirm_msg)
        if user_input != "Y":
            return False
    try:
        body = {"ids": [t.id if isinstance(t, EntityBase) else t for t in objects]}
        res: Response = api(connection, body)

        if config.verbose and res.ok:
            logger.info(delete_success_msg)

        return res.ok
    except Exception:
        logger.warning(delete_failure_msg)
        return False


class ObjectResult(EntityBase, metaclass=ABCMeta):
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        "date_created": DatetimeFormats.FULLDATETIME,
        "date_modified": DatetimeFormats.FULLDATETIME,
        "tested_object": _object_from_dict,
    }
    _REST_ATTR_MAP = {
        "creation_time": "date_created",
        "last_modified_time": "date_modified",
    }

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self.test_id = kwargs.get("test_id", default_value)
        self.result_id = kwargs.get("result_id", default_value)
        self.viz_key = kwargs.get("viz_key", default_value)
        self._date_created = (
            map_str_to_datetime(
                "date_created", kwargs.get("creation_time"), self._FROM_DICT_MAP
            )
            if kwargs.get("creation_time")
            else default_value
        )
        self._date_modified = (
            map_str_to_datetime(
                "date_modified", kwargs.get("last_modified_time"), self._FROM_DICT_MAP
            )
            if kwargs.get("last_modified_time")
            else default_value
        )
        self._tested_object = (
            _object_from_dict(kwargs["tested_object"], self._connection)
            if kwargs.get("tested_object")
            else default_value
        )

    @abstractmethod
    def _to_export_entries(self) -> dict[str, dict]:
        pass

    @property
    def export_id(self) -> str:
        objres_id = self.tested_object.id
        viz_key = self.viz_key
        return f"{objres_id}_{viz_key}" if viz_key else objres_id

    @property
    def date_created(self) -> DatetimeFormats:
        return self._date_created

    @property
    def date_modified(self) -> DatetimeFormats:
        return self._date_modified

    @property
    def tested_object(self):
        return self._tested_object


class TestExecutionStatus(AutoUpperName):
    """Enum for test execution status."""

    UNKNOWN = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()
    CANCELLING = auto()
    CANCELLED = auto()
    SKIPPED = auto()


class IntegrityTestResult(EntityBase, metaclass=ABCMeta):
    _FROM_DICT_MAP = {
        **EntityBase._FROM_DICT_MAP,
        "date_created": DatetimeFormats.FULLDATETIME,
        "date_modified": DatetimeFormats.FULLDATETIME,
        "status": TestExecutionStatus,
    }
    _REST_ATTR_MAP = {
        "creation_time": "date_created",
        "last_modified_time": "date_modified",
    }
    _API_CANCEL: Callable
    _API_DELETE: Callable
    _API_BULK_DELETE: Callable

    def __init__(self, connection: Connection, id: str, test_id: str | None = None):
        if test_id is None:
            test_id_key = "test_id"
            mapping = [
                rest_key
                for rest_key, python_key in self._REST_ATTR_MAP.items()
                if python_key == "test_id"
            ]
            if mapping:
                test_id_key = mapping[0]

            candidate_objs = self._list_all(
                connection=connection, to_dictionary=True, id=id
            )
            if not candidate_objs:
                raise ValueError(
                    f"There is no {self.__class__.__name__} with the given ID: '{id}'"
                )
            obj = candidate_objs[0]
            test_id = obj[test_id_key]
        self._test_id = test_id
        super().__init__(connection=connection, object_id=id)

    def _init_variables(self, default_value=None, **kwargs):
        super()._init_variables(default_value, **kwargs)
        self._date_created = (
            map_str_to_datetime(
                "date_created", kwargs.get("creation_time"), self._FROM_DICT_MAP
            )
            if kwargs.get("creation_time")
            else default_value
        )
        self._date_modified = (
            map_str_to_datetime(
                "date_modified", kwargs.get("last_modified_time"), self._FROM_DICT_MAP
            )
            if kwargs.get("last_modified_time")
            else default_value
        )
        self._status = (
            TestExecutionStatus(kwargs.get("status"))
            if kwargs.get("status")
            else default_value
        )
        self._summary = kwargs.get("summary", default_value)
        self._object_results = kwargs.get("object_results", default_value)

    def cancel_execution(self) -> bool:
        """Cancel this instance of a test execution."""
        try:
            response = self._API_CANCEL(self.connection, self.test_id, self.id)
        except IServerError:
            logger.error(
                f"Failed to cancel execution of test result with ID: '{self._id}'."
            )
            return False

        if response.status_code == 202 and config.verbose:
            logger.info(
                "Successfully cancelled execution of test result "
                f"with ID: '{self._id}'."
            )

        return response.ok

    def delete(self, force: bool = False) -> bool:
        """Delete this test result.

        Args:
            force: If True, no additional prompt will be shown before deleting
                the result.

        Returns:
            True when the result was successfully deleted, False otherwise.
        """
        # no DeleteMixin, because it uses `name` attribute
        object_name = self.__class__.__name__
        if not force:
            message = (
                f"Are you sure you want to delete {object_name} "
                f"with ID: {self._id}? [Y/N]: "
            )
            user_input = input(message)
            if user_input != "Y":
                return False

        response = self._API_DELETE(self.connection, self.test_id, self.id)

        if response.status_code == 204 and config.verbose:
            msg = f"Successfully deleted {object_name} with ID: '{self._id}'."
            logger.info(msg)

        return response.ok

    def get_object_result(
        self, id: str, viz_key: str | None = None, to_list: bool = False
    ):
        """Get a specific object result by ID.

        Args:
            id (str): ID of the object result.
            viz_key (str, optional): Visualization key for the object result.
                Will be ignored if only one object result is matching.
            to_list (bool, optional): If True, return a list of matching object
                results, which may be empty or contain multiple entries.
                If False, return a single object result or raise if no such
                object result can be found. Defaults to False.

        Returns:
            ObjectBaseline | list: The specified object result(s).
        """
        candidates = [obj for obj in self.object_results if obj.id == id]
        if viz_key and len(candidates) > 1:
            candidates = [obj for obj in candidates if obj.viz_key == viz_key]

        if to_list:
            return candidates
        if len(candidates) == 1:
            return candidates[0]
        error_msg = (
            "Object result with given ID(s) not found"
            if not candidates
            else "Multiple object results with given ID(s) found"
        )
        raise ValueError(error_msg)

    @classmethod
    def bulk_delete(
        cls,
        connection: Connection,
        objects: "list[str | IntegrityTestResult]",
        force: bool = False,
    ) -> bool:
        """Delete multiple test results by their IDs.

        Note:
            If the test results are running and not finished,
            deletion will fail.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`
            objects (list [str | object]): List of test result IDs or objects
                to be deleted.
            force (bool): If True, no additional prompt will be shown before
                deleting the results.

        Returns:
            True if deletion was successful, False otherwise.
        """
        object_str = "result" if len(objects) == 1 else f"{len(objects)} results"
        delete_confirm_msg = (
            f"Are you sure you want to delete the selected {object_str}? [Y/N]: "
        )
        return _bulk_delete_helper(
            connection=connection,
            objects=objects,
            api=cls._API_BULK_DELETE,
            delete_confirm_msg=delete_confirm_msg,
            delete_success_msg="Successfully deleted the batch of results.",
            delete_failure_msg="Deleting some of the results failed.",
            force=force,
        )

    @abstractmethod
    def _get_result_details_to_fetch(self):
        pass

    def _to_export_entries(self) -> dict[str, dict]:
        d = self.to_dict(skip_private_keys=True)
        d.pop("objectResults", None)
        entries = {f"summary_{self.id}": d}
        for objres in self.object_results:
            entries.update(objres._to_export_entries())
        return entries

    def fetch_result_details(self):
        """Fetch all object result details for the test result."""
        to_fetch = self._get_result_details_to_fetch()

        with tqdm(
            total=len(to_fetch),
            desc="Fetching result details...",
            disable=not config.verbose or not config.progress_bar,
            delay=3,
        ) as pbar:
            for objres, key in to_fetch:
                objres.fetch(key)
                pbar.update()

    def export_json(self, location: str = "."):
        """Export the test result to JSON files.

        Args:
            location (str): The file path where the JSON files will be saved.
                Default is the running script's current working directory.
        """
        # Ensure that all object result details are fetched before exporting
        self.fetch_result_details()

        # Convert all results to serializable dicts
        export_entries = self._to_export_entries()
        dump_targets = {
            f"{entry_id}.json": content for entry_id, content in export_entries.items()
        }

        # Create folder and files
        folder_path = _create_export_folder(location)
        for file_name, content in dump_targets.items():
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as f:
                json.dump(content, f, indent=4)

    @classmethod
    @abstractmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        **filters,
    ):
        pass

    @property
    def test_id(self) -> str:
        return self._test_id

    @property
    def status(self) -> dict:
        return self._status

    @property
    def summary(self) -> dict:
        return self._summary

    @property
    def object_results(self):
        return self._object_results

    @property
    def date_created(self) -> DatetimeFormats:
        return self._date_created

    @property
    def date_modified(self) -> DatetimeFormats:
        return self._date_modified


class IntegrityTest(Entity, DeleteMixin, metaclass=ABCMeta):
    _OBJECT_TYPE = ObjectTypes.TEST_SUITE
    _API_BULK_DELETE: Callable

    def __init__(
        self,
        connection: Connection,
        id: str | None = None,
        name: str | None = None,
    ):
        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the constructor."
                )

            obj = find_object_with_name(
                connection=connection,
                cls=self.__class__,
                name=name,
                listing_function=self._list_all,
            )
            id = obj["id"]
        super().__init__(
            connection=connection,
            object_id=id,
            name=name,
        )

    @classmethod
    @abstractmethod
    def _list_all(
        cls,
        connection: Connection,
        to_dictionary: bool = False,
        to_dataframe: bool = False,
        limit: int | None = None,
        **filters,
    ):
        pass

    @staticmethod
    def _normalize_execution_settings(
        content_dict_key: str,
        initial_settings: Dictable | dict,
        settings_delta: Dictable | dict | None,
        execute_sql: bool | None = None,
        execute_data: bool | None = None,
    ) -> dict:
        """Combine initial (or default) settings with user-specified new
            settings and apply explicit changes in execution content (SQL/DATA).

        Args:
            content_dict_key (str): The key in the settings dict that contains
                the content types (e.g. "compareContent" or "executeContent").
            initial_settings (Dictable or dict): Initial or default settings.
            settings_delta (Dictable or dict, optional): User-specified settings
                that should override the initial settings. Defaults to None.
            execute_sql (bool, optional): User-specified flag. Modifies the
                `execute_content` field in `settings` if specified.
            execute_data (bool, optional): User-specified flag. Modifies the
                `execute_content` field in `settings` if specified.

        Returns:
            dict: The normalized settings dictionary to be sent in the REST API
                request body.
        """
        if isinstance(initial_settings, Dictable):
            initial_settings = initial_settings.to_dict()
        if isinstance(settings_delta, Dictable):
            settings_delta = settings_delta.to_dict()
        if settings_delta:
            settings_delta = delete_none_values(settings_delta, recursion=False)
        settings = initial_settings
        if settings_delta:
            settings |= settings_delta

        content_set = set(settings.get(content_dict_key))
        if execute_sql is True:
            content_set.add("SQL")
        if execute_sql is False:
            content_set.discard("SQL")
        if execute_data is True:
            content_set.add("DATA")
        if execute_data is False:
            content_set.discard("DATA")

        if not content_set:
            raise ValueError("At least one of SQL or DATA must be selected.")
        if set(initial_settings.get(content_dict_key)) != content_set:
            settings[content_dict_key] = list(content_set)

        return settings

    @classmethod
    def bulk_delete(
        cls,
        connection: Connection,
        objects: "list[str | IntegrityTest]",
        force: bool = False,
    ) -> bool:
        """Delete multiple tests by their IDs.

        Args:
            connection (Connection): Strategy connection object returned by
                `connection.Connection()`
            objects (list [str | object]): List of test IDs or objects
                to be deleted.
            force (bool): If True, no additional prompt will be shown before
                deleting the tests.
        Returns:
            True if deletion was successful, False otherwise.
        """
        object_str = "test" if len(objects) == 1 else f"{len(objects)} tests"
        delete_confirm_msg = (
            f"Are you sure you want to delete the selected {object_str}? [Y/N]: "
        )
        return _bulk_delete_helper(
            connection=connection,
            objects=objects,
            api=cls._API_BULK_DELETE,
            delete_confirm_msg=delete_confirm_msg,
            delete_success_msg="Successfully deleted the batch of tests.",
            delete_failure_msg="Deleting some of the tests failed.",
            force=force,
        )
