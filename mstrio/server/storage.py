from dataclasses import dataclass
from enum import Enum
from logging import getLogger

from mstrio.utils.helper import Dictable

logger = getLogger(__name__)


class StorageType(Enum):
    """Enumeration of Storage Service types."""

    UNSET = "unset"
    UNKNOWN = "unknown"
    FILE_SYSTEM = "file_system"
    S3 = "S3"
    AZURE = "Azure"
    GCS = "GCS"


@dataclass
class StorageService(Dictable):
    """StorageService configuration of environment.
    Attributes:
        type (StorageType): Type of storage (e.g. file system, S3)
        alias (str, optional): Alias of the storage configuration,
        location (str, optional): Storage location, e.g.
            bucket name for S3, absolute path of folder for File System
        s3_region (str, optional): S3 bucket region
        aws_access_id (str, optional): Access ID for AWS S3
        aws_secret_key (str, optional): Access key for AWS S3
        azure_storage_account_name (str, optional): Account name for Azure
        azure_secret_key (str, optional): Access key for Azure
        configured (bool): whether Storage Service is configured
    """

    _FROM_DICT_MAP = {
        'type': StorageType,
    }

    type: StorageType = StorageType.UNSET
    alias: str | None = None
    location: str | None = None
    s3_region: str | None = None
    aws_access_id: str | None = None
    aws_secret_key: str | None = None
    azure_storage_account_name: str | None = None
    azure_secret_key: str | None = None
    gcs_service_account_key: str | None = None
    configured: bool = False

    # Give a warning when changing type
    # This is equivalent to the warning present in Workstation
    def __setattr__(self, name, value):
        if (
            name == 'type'
            and hasattr(self, 'type')
            and value != self.type
            and self.type != StorageType.UNSET
        ):
            logger.warning(
                "Changing the storage service type. The existing packages "
                "in the previous location will not be available."
            )
        super().__setattr__(name, value)
