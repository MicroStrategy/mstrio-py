from dataclasses import dataclass, field
from enum import auto

from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable

# The server's magic "Full Control" ACL rights mask. It is a single opaque
# value and must NOT be decomposed from individual right flag names.
_ACL_RIGHT_FULL_CONTROL = 255


class DataServeMode(AutoName):
    """Modes in which a Mosaic data model serves data."""

    CONNECT_LIVE = auto()
    IN_MEMORY = auto()
    HYBRID = auto()
    # Additional value present in the `ms-DataModel.dataServeMode` REST schema
    OFF_MEMORY = auto()


class RefreshPolicy(AutoName):
    """Table refresh policies used when publishing a data model."""

    ADD = auto()
    REPLACE = auto()
    DELETE = auto()
    UPDATE = auto()
    UPSERT = auto()
    IGNORE = auto()
    RESERVED = auto()


@dataclass
class TablePublishStatus(Dictable):
    """Publish status of a single table of a Mosaic data model.

    Attributes:
        id (str): logical table ID
        status (str): table load status; progresses `reserved` ->
            `schema_comparison_completed` -> `loaded`, or `error` on failure
        error_code (int, optional): error code when `status` is `error`
        error_message (str, optional): error message when `status` is `error`
    """

    id: str | None = None
    status: str | None = None
    error_code: int | None = None
    error_message: str | None = None


@dataclass
class DataModelPublishStatus(Dictable):
    """Publish status of a Mosaic data model instance.

    Attributes:
        status (int): overall status; 0 = all tables loaded (success),
            1 = queued/running, 5 = reserved, 6 = schema compared,
            negative values are server errors (e.g. -2147212544 indicates a
            tenant-side QueryEngine stall - do not retry in a loop)
        tables (list[TablePublishStatus]): per-table publish statuses
    """

    _FROM_DICT_MAP = {'tables': [TablePublishStatus.from_dict]}

    status: int | None = None
    tables: list[TablePublishStatus] = field(default_factory=list)


@dataclass
class DataModelFolder(Dictable):
    """Folder living inside a Mosaic data model (`ms-DataModelFolder`).

    Attributes:
        information (dict): object information block (objectId, name, ...)
        contents (list): objects placed in the folder
    """

    information: dict | None = None
    contents: list | None = None

    @property
    def id(self) -> str | None:
        """ID of the folder taken from the `information` block."""
        return (self.information or {}).get('object_id') or (
            self.information or {}
        ).get('objectId')

    @property
    def name(self) -> str | None:
        """Name of the folder taken from the `information` block."""
        return (self.information or {}).get('name')


@dataclass
class DataModelLink(Dictable):
    """Link between data model objects (`ms-DataModelLink`).

    Attributes:
        id (str): link ID
        targets (list): list of link units
        source_object_id (str): ID of the source object
        alias (str): link alias
        linked_attribute (dict): the attribute which contains the source
            attribute's forms and other target attributes' non-key single forms
    """

    id: str | None = None
    targets: list | None = None
    source_object_id: str | None = None
    alias: str | None = None
    linked_attribute: dict | None = None


@dataclass
class ExternalDataModel(Dictable):
    """External data model reference (`ms-ExternalDataModel`).

    Attributes:
        id (str): external data model ID
        base_data_model (dict): reference to the base data model
        alias (str): alias of the external data model
        objects (list): external data model units
    """

    id: str | None = None
    base_data_model: dict | None = None
    alias: str | None = None
    objects: list | None = None


def unpack_information_dict(source: dict) -> dict:
    """Merge the `information` block of a Modeling-Service payload into the
    top level of the dictionary.

    Mirrors the response half of
    `mstrio.utils.api_helpers.unpack_information`, for use on single elements
    of collection responses.

    Args:
        source (dict): dictionary possibly containing an `information` block

    Returns:
        A copy of `source` with `information` merged to the top level and
        `id` set from `information.objectId`.
    """
    result = source.copy()
    if result.get('information'):
        result.update(result.pop('information'))
        result['id'] = result.pop('objectId', None)
    return result
