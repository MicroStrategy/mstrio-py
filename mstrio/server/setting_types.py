from enum import Enum

_COMMON_ENUM_FIELDS = {
    'SUBSCRIPTION_RECIPIENT_NAME': 'recipient_name',
    'SUBSCRIPTION_OWNER_NAME': 'owner_name',
    'SUBSCRIPTION_REPORT_OR_DOCUMENT_NAME': 'report_document_name',
    'SUBSCRIPTION_PROJECT_NAME': 'project_name',
    'SUBSCRIPTION_DELIVERY_METHOD': 'delivery_method',
    'SUBSCRIPTION_SCHEDULE': 'schedule',
    'SUBSCRIPTION_NAME': 'subscription_name',
    'DELIVERY_STATUS': 'delivery_status',
    'DELIVERY_DATE': 'date',
    'DELIVERY_TIME': 'time',
    'DELIVERY_ERROR_MESSAGE': 'error_message',
}

FailedEmailDelivery = Enum(
    'FailedEmailDelivery',
    {**_COMMON_ENUM_FIELDS, 'DELIVERY_EMAIL_ADDRESS': 'email_address'},
)

FailedFileDelivery = Enum(
    'FailedFileDelivery',
    {
        **_COMMON_ENUM_FIELDS,
        'FILE_LOCATION': 'file_location',
        'LINK_TO_FILE': 'link_to_file',
    },
)

FailedFTPDelivery = Enum(
    'FailedFTPDelivery',
    {
        **_COMMON_ENUM_FIELDS,
        'FILE_LOCATION': 'file_location',
        'LINK_TO_FILE': 'link_to_file',
    },
)

FailedPrinterDelivery = Enum(
    'FailedPrinterDelivery',
    {
        **_COMMON_ENUM_FIELDS,
        'PRINTER_NAME': 'printer_name',
    },
)

FailedHistoryListDelivery = Enum(
    'FailedHistoryListDelivery',
    {
        **_COMMON_ENUM_FIELDS,
        'LINK_TO_HISTORY_LIST': 'link_to_history_list',
    },
)

FailedMobileDelivery = Enum('FailedMobileDelivery', _COMMON_ENUM_FIELDS)

FailedCacheCreation = Enum('FailedCacheCreation', _COMMON_ENUM_FIELDS)


class CompressionLevel(Enum):
    """Level of File | Email | FTP delivery compression"""

    OFF = 0
    LOW = 3
    MEDIUM = 6
    HIGH = 9


class CacheEncryptionLevel(Enum):
    """Cache encryption level on disk"""

    NONE = 0
    LOW = 1
    HIGH = 2


class ShowBaseViewInLibrary(Enum):
    """Always open dossiers/documents with the last saved view in Library"""

    DEFAULT = 'use_inherited_value'
    YES = 'yes'
    NO = 'no'


class SmartMemoryUsageForIntelligenceServer(Enum):
    """Smart Memory Usage for Intelligence Server"""

    USE_INHERITED_VALUE = -1
    APPLY_BEST_STRATEGY = 0
    TURN_OFF_THE_CAPABILITY_WITHOUT_EXCEPTIONS = 1
    DISABLE_THE_CAPABILITY = 2
    ENABLE_THE_CAPABILITY = 3


class OrderMultiSourceDBI(Enum):
    """Rules to order multi-source Database Instances"""

    MULTISOURCE_DEFAULT_ORDERING = 0
    PROJECT_LEVEL_DATABASE_ORDERING = 1


class DisplayEmptyReportMessageInRWD(Enum):
    """Display mode for empty Grid/Graphs in documents"""

    DISPLAY_MESSAGE_IN_DOCUMENT_GRIDS = -1
    HIDE_DOCUMENT_GRID = 0


class MergeSecurityFilters(Enum):
    """Rules to merge multiple Security Filters across user groups and users"""

    UNION = 0
    INTERSECT = 3
