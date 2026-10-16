import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mstrio import config
from mstrio.api import runtimes as runtimes_api
from mstrio.utils.entity import DeleteMixin, EntityBase
from mstrio.utils.helper import Dictable, delete_none_values, fetch_objects
from mstrio.utils.response_processors import runtimes as runtimes_processor

if TYPE_CHECKING:
    from mstrio.connection import Connection


logger = logging.getLogger(__name__)


@dataclass
class RuntimePackage(Dictable):
    """Package installed in a runtime."""

    name: str
    version: str | None = None
    description: str | None = None


@dataclass
class RuntimeResource(Dictable):
    """Resource limits assigned to a runtime."""

    cpu: str | None = None
    mem: int | None = None
    disk: int | None = None
    proc_count: int | None = None


def _to_runtime_package(package: RuntimePackage | dict) -> dict:
    if isinstance(package, RuntimePackage):
        return package.to_dict()
    if isinstance(package, dict):
        return package.copy()
    raise TypeError("Runtime packages must be RuntimePackage objects or dictionaries.")


def _to_runtime_resource(resource: RuntimeResource | dict) -> dict:
    if isinstance(resource, RuntimeResource):
        resource = resource.to_dict()
    elif isinstance(resource, dict):
        resource = resource.copy()
    else:
        raise TypeError(
            "Runtime resources must be RuntimeResource objects or dictionaries."
        )
    if resource.get("mem") is not None and resource["mem"] < 0:
        raise ValueError("Runtime resource memory must be non-negative.")
    return resource


def _build_runtime_body(
    *,
    name: str | None = None,
    description: str | None = None,
    whitelist: list[str] | None = None,
    packages: list[RuntimePackage | dict] | None = None,
    resource: RuntimeResource | dict | None = None,
    exec_timeout: int | None = None,
    min_cached_instances: int | None = None,
    max_cached_instances: int | None = None,
    runtime_version: str | None = None,
    others: str | None = None,
    execution_target: str | None = None,
    journal_comment: str | None = None,
) -> dict:
    if (
        min_cached_instances is not None
        and max_cached_instances is not None
        and min_cached_instances > max_cached_instances
    ):
        raise ValueError(
            "Minimum cached instances cannot exceed maximum cached instances."
        )
    body = {
        "name": name,
        "description": description,
        "whitelist": whitelist,
        "packages": (
            [_to_runtime_package(package) for package in packages]
            if packages is not None
            else None
        ),
        "resource": (_to_runtime_resource(resource) if resource is not None else None),
        "execTimeout": exec_timeout,
        "minCachedInstances": min_cached_instances,
        "maxCachedInstances": max_cached_instances,
        "runtimeVersion": runtime_version,
        "others": others,
        "executionTarget": execution_target,
    }
    body = delete_none_values(body, recursion=True)
    if journal_comment:
        body["changeJournal"] = {"userComments": journal_comment}
    return body


def _delete_runtime(
    connection: "Connection",
    id: str,
    journal_comment: str | None = None,
    error_msg: str | None = None,
):
    return runtimes_api.delete_runtime(
        connection=connection,
        id=id,
        journal_comment=journal_comment,
        error_msg=error_msg,
    )


def list_runtimes(
    connection: "Connection",
    to_dictionary: bool = False,
    limit: int | None = None,
    **filters,
) -> list["Runtime"] | list[dict]:
    """Get runtimes.

    Args:
        connection (Connection): Strategy connection object returned by
            `connection.Connection()`.
        to_dictionary (bool, optional): If True, return dictionaries instead
            of Runtime objects. Defaults to False.
        limit (int, optional): Maximum number of runtimes to return.
        **filters: Available filter parameters: ``id``, ``name``, and
            ``description``.

    Returns:
        List of Runtime objects or dictionaries.
    """

    runtimes = fetch_objects(
        connection=connection,
        api=runtimes_processor.list_runtimes,
        filters=filters,
        limit=limit,
    )
    if to_dictionary:
        return runtimes
    return [Runtime.from_dict(runtime, connection) for runtime in runtimes]


def get_runtime_versions(connection: "Connection") -> list[str]:
    """Get available runtime versions."""

    return runtimes_processor.get_runtime_versions(connection=connection)


class Runtime(EntityBase, DeleteMixin):
    """Python representation of a Strategy Python execution runtime."""

    _API_GETTERS = {
        (
            "id",
            "name",
            "description",
            "whitelist",
            "packages",
            "resource",
            "exec_timeout",
            "min_cached_instances",
            "max_cached_instances",
            "runtime_version",
            "others",
            "status",
            "execution_target",
        ): runtimes_processor.get_runtime,
    }
    _FROM_DICT_MAP = {
        "packages": [RuntimePackage.from_dict],
        "resource": RuntimeResource.from_dict,
    }
    _API_DELETE = staticmethod(_delete_runtime)
    _API_DEL_JOURNAL_MIN_VER = "11.5.0300"

    def __init__(
        self,
        connection: "Connection",
        id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize a Runtime by ID or name."""

        if id is None:
            if name is None:
                raise ValueError(
                    "Please specify either 'name' or 'id' parameter in the "
                    "constructor."
                )

            matches = list_runtimes(
                connection=connection,
                name=name,
                to_dictionary=True,
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Cannot uniquely identify Runtime by name '{name}'. "
                    f"Found {len(matches)} hits. Please provide ID instead."
                )
            id = matches[0]["id"]

        super().__init__(connection=connection, object_id=id, name=name)

    def _init_variables(self, default_value=None, **kwargs) -> None:
        super()._init_variables(default_value=default_value, **kwargs)
        self.description = kwargs.get("description", default_value)
        self.whitelist = kwargs.get("whitelist", default_value)
        packages = kwargs.get("packages")
        if packages is None:
            packages = []
        if isinstance(packages, list) and (
            not packages or isinstance(packages[0], dict)
        ):
            packages = [RuntimePackage.from_dict(package) for package in packages]
        self.packages = packages
        resource = kwargs.get("resource", default_value)
        if isinstance(resource, dict):
            resource = RuntimeResource.from_dict(resource)
        self.resource = resource
        self.exec_timeout = kwargs.get("exec_timeout", default_value)
        self.min_cached_instances = kwargs.get("min_cached_instances", default_value)
        self.max_cached_instances = kwargs.get("max_cached_instances", default_value)
        self.runtime_version = kwargs.get("runtime_version", default_value)
        self.others = kwargs.get("others", default_value)
        self.status = kwargs.get("status", default_value)
        self.execution_target = kwargs.get("execution_target", default_value)

    @classmethod
    def create(
        cls,
        connection: "Connection",
        name: str,
        description: str | None = None,
        whitelist: list[str] | None = None,
        packages: list[RuntimePackage | dict] | None = None,
        resource: RuntimeResource | dict | None = None,
        exec_timeout: int = 600,
        min_cached_instances: int | None = None,
        max_cached_instances: int | None = None,
        runtime_version: str | None = None,
        others: str | None = None,
        execution_target: str | None = None,
        journal_comment: str | None = None,
    ) -> "Runtime":
        """Create a runtime."""

        body = _build_runtime_body(
            name=name,
            description=description,
            whitelist=whitelist,
            packages=packages,
            resource=resource,
            exec_timeout=exec_timeout,
            min_cached_instances=min_cached_instances,
            max_cached_instances=max_cached_instances,
            runtime_version=runtime_version,
            others=others,
            execution_target=execution_target,
            journal_comment=journal_comment,
        )
        data = runtimes_processor.create_runtime(connection=connection, body=body)
        runtime_id = data.get("id")
        if not runtime_id:
            raise ValueError("The runtime creation response did not contain an ID.")

        runtime = cls(connection=connection, id=runtime_id)
        if config.verbose:
            logger.info(
                "Successfully created Runtime named: '%s' with ID: '%s'",
                name,
                runtime_id,
            )
        return runtime

    def alter(
        self,
        name: str | None = None,
        description: str | None = None,
        whitelist: list[str] | None = None,
        packages: list[RuntimePackage | dict] | None = None,
        resource: RuntimeResource | dict | None = None,
        exec_timeout: int | None = None,
        min_cached_instances: int | None = None,
        max_cached_instances: int | None = None,
        runtime_version: str | None = None,
        others: str | None = None,
        execution_target: str | None = None,
        journal_comment: str | None = None,
    ) -> None:
        """Alter runtime properties."""

        if name is None:
            name = self.name  # REST requires name in body, even if not changing
        body = _build_runtime_body(
            name=name,
            description=description,
            whitelist=whitelist,
            packages=packages,
            resource=resource,
            exec_timeout=exec_timeout,
            min_cached_instances=min_cached_instances,
            max_cached_instances=max_cached_instances,
            runtime_version=runtime_version,
            others=others,
            execution_target=execution_target,
            journal_comment=journal_comment,
        )
        if not body:
            if config.verbose:
                logger.info("No changes specified for Runtime '%s'.", self.name)
            return

        runtimes_api.update_runtime(
            connection=self.connection,
            id=self.id,
            body=body,
        )
        self._set_object_attributes(
            **{key: value for key, value in body.items() if key != "changeJournal"}
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(connection, id={self.id!r}, name={self.name!r})"
        )
