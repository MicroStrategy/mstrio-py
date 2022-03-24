from dataclasses import dataclass
from enum import auto
from typing import Optional

from mstrio.utils.enum_helper import AutoName
from mstrio.utils.helper import Dictable


class SubType(AutoName):
    """String literal used to identify the type of a metadata object.
    Some MicroStrategy APIs make a distinction between an object's type
    and subtype because in some cases (e.g. the different kinds of reports)
    it can be useful to see one "report" concept rather than to have to always
    distinguish between different kinds of reports. But there are cases
    (e.g. filters versus custom-groups or users versus user-groups ) where
    users want to see the different subtypes of the same type as fundamentally
    different.
    Used across different modeling modules e.g. attributes, user hierarchies.
    """
    FILTER = auto()
    CUSTOM_GROUP = auto()
    FILTER_PARTITION = auto()
    SEGMENT = auto()
    TEMPLATE = auto()
    REPORT_GRID = auto()
    REPORT_GRAPH = auto()
    REPORT_ENGINE = auto()
    REPORT_TEXT = auto()
    REPORT_DATAMART = auto()
    REPORT_BASE = auto()
    REPORT_GRID_AND_GRAPH = auto()
    REPORT_NON_INTERACTIVE = auto()
    REPORT_CUBE = auto()
    REPORT_INCREMENT_REFRESH = auto()
    REPORT_TRANSACTION = auto()
    REPORT_EMMA_CUBE = auto()
    REPORT_EMMA_CUBE_IRR = auto()
    REPORT_HYPER_CARD = auto()
    METRIC = auto()
    METRIC_SUBTOTAL = auto()
    SYSTEM_SUBTOTAL = auto()
    METRIC_DMX = auto()
    METRIC_TRAINING = auto()
    METRIC_EXTREME = auto()
    METRIC_REFERENCE_LINE = auto()
    METRIC_RELATIONSHIP = auto()
    STYLE = auto()
    AGG_METRIC = auto()
    FOLDER = auto()
    FOLDER_SYSTEM = auto()
    DEVICE = auto()
    PROMPT = auto()
    PROMPT_BOOLEAN = auto()
    PROMPT_LONG = auto()
    PROMPT_STRING = auto()
    PROMPT_DOUBLE = auto()
    PROMPT_DATE = auto()
    PROMPT_OBJECTS = auto()
    PROMPT_ELEMENTS = auto()
    PROMPT_EXPRESSION = auto()
    PROMPT_EXPRESSION_DRAFT = auto()
    PROMPT_DIMTY = auto()
    PROMPT_BIG_DECIMAL = auto()
    FUNCTION = auto()
    FUNCTION_THIRD_PARTY = auto()
    ATTRIBUTE = auto()
    ATTRIBUTE_ROLE = auto()
    ATTRIBUTE_TRANSFORMATION = auto()
    ATTRIBUTE_ABSTRACT = auto()
    ATTRIBUTE_RECURSIVE = auto()
    ATTRIBUTE_DERIVED = auto()
    FACT = auto()
    DIMENSION_SYSTEM = auto()
    DIMENSION_USER = auto()
    DIMENSION_ORDERED = auto()
    DIMENSION_USER_HIERARCHY = auto()
    LOGICAL_TABLE = auto()
    TABLE_PARTITION_MD = auto()
    TABLE_PARTITION_WH = auto()
    DATAMART_REPORT = auto()
    FACT_GROUP = auto()
    SHORTCUT = auto()
    SHORTCUT_WEAK_REF = auto()
    RESOLUTION = auto()
    ATTRIBUTE_FORM_SYSTEM = auto()
    ATTRIBUTE_FORM_NORMAL = auto()
    SCHEMA = auto()
    FORMAT = auto()
    CATALOG = auto()
    CATALOG_DEFN = auto()
    COLUMN = auto()
    COLUMN_NORMAL = auto()
    COLUMN_CUSTOM = auto()
    PROPERTY_GROUP = auto()
    PROPERTY_SET = auto()
    DB_ROLE = auto()
    DB_ROLE_IMPORT = auto()
    DB_ROLE_IMPORT_PRIMARY = auto()
    DB_ROLE_O_AUTH = auto()
    DB_ROLE_REMOTE_DATE_SOURCE = auto()
    DB_ROLE_URL_AUTH = auto()
    DB_ROLE_GENERIC_DATA_CONNECTOR = auto()
    DB_ROLE_DATA_IMPORT_SERVER = auto()
    DB_ROLE_CLOUD_ELEMENT = auto()
    DB_LOGIN = auto()
    DB_CONNECTION = auto()
    PROJECT = auto()
    SERVER_DEF = auto()
    USER = auto()
    USER_GROUP = auto()
    TRANSMITTER = auto()
    CONFIGURATION = auto()
    REQUEST = auto()
    SEARCH = auto()
    INDEXED_SEARCH = auto()
    RELATIONSHIP_SEARCH = auto()
    SEARCH_FOLDER = auto()
    SEARCH_FOLDER_CROSS_PROJECT = auto()
    DATAMART = auto()
    FUNCTION_PACKAGE_DEFINITION = auto()
    ROLE = auto()
    ROLE_TRANSFORMATION = auto()
    SECURITY_ROLE = auto()
    LOCALE = auto()
    CONSOLIDATION = auto()
    CONSOLIDATION_DERIVED = auto()
    CONSOLIDATION_ELEMENT = auto()
    SCHEDULE_EVENT = auto()
    SCHEDULE_OBJECT = auto()
    SCHEDULE_TRIGGER = auto()
    LINK = auto()
    PHYSICAL_TABLE = auto()
    DB_TABLE_PMT = auto()
    DB_TABLE_SOURCE = auto()
    DOCUMENT_DEFINITION = auto()
    REPORT_WRITING_DOCUMENT = auto()
    DOCUMENT_THEME = auto()
    DOSSIER = auto()
    DRILL_MAP = auto()
    DBMS = auto()
    MD_SECURITY_FILTER = auto()
    MONITOR_PERFORMANCE = auto()
    MONITOR_JOBS = auto()
    MONITOR_USER_CONNECTIONS = auto()
    MONITOR_DB_CONNECTIONS = auto()
    PROMPT_ANSWER = auto()
    PROMPT_ANSWER_BOOLEAN = auto()
    PROMPT_ANSWER_LONG = auto()
    PROMPT_ANSWER_STRING = auto()
    PROMPT_ANSWER_DOUBLE = auto()
    PROMPT_ANSWER_DATE = auto()
    PROMPT_ANSWER_OBJECTS = auto()
    PROMPT_ANSWER_ELEMENTS = auto()
    PROMPT_ANSWER_EXPRESSION = auto()
    PROMPT_ANSWER_EXPRESSION_DRAFT = auto()
    PROMPT_ANSWER_DIMTY = auto()
    PROMPT_ANSWER_BIG_DECIMAL = auto()
    PROMPT_ANSWER_INT64 = auto()
    PROMPT_ANSWERS = auto()
    GRAPH_STYLE = auto()
    CHANGE_JOURNAL_SEARCH = auto()
    BLOB_UNKNOWN = auto()
    BLOB_OTHER = auto()
    BLOB_IMAGE = auto()
    BLOB_PROJECT_PACKAGE = auto()
    BLOB_EXCEL = auto()
    BLOB_HTML_TEMPLATE = auto()
    DASHBOARD_TEMPLATE = auto()
    FLAG = auto()
    CHANGE_JOURNAL = auto()
    EXTERNAL_SHORTCUT_UNKNOWN = auto()
    EXTERNAL_SHORTCUT_URL = auto()
    EXTERNAL_SHORTCUT_SNAPSHOT = auto()
    EXTERNAL_SHORTCUT_TARGET = auto()
    RECONCILIATION = auto()
    PALETTE_SYSTEM = auto()
    PALETTE_CUSTOM = auto()
    THRESHOLDS = auto()
    SUBSCRIPTION_ADDRESS = auto()
    SUBSCRIPTION_CONTACT = auto()
    SUBSCRIPTION_INSTANCE = auto()


@dataclass
class SchemaObjectReference(Dictable):
    """Information about an object referenced within the specification
    of another object. An object reference typically contains only enough
    fields to uniquely identify the referenced objects.

    Arguments:
        object_id: object's id, a globally unique identifier used to
            distinguish between metadata objects within the same project
        sub_type:  string literal used to identify the type of a metadata object
        name: the name of the metadata object
        is_embedded: if true indicates that the target object of this reference
            is embedded within this object, bool
    """
    _FROM_DICT_MAP = {'sub_type': SubType}
    sub_type: SubType
    object_id: str
    name: Optional[str] = None
    is_embedded: bool = False

    def __eq__(self, other):
        return self.sub_type == other.sub_type and self.object_id == other.object_id
