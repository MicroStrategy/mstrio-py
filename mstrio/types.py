from enum import Enum


# A sentinel object to detect if a attribute has been returned by REST API
class _MissingType:
    pass


MISSING = _MissingType()


class ObjectTypes(Enum):
    FILTER = 1
    TEMPLATE = 2
    REPORT_DEFINITION = 3
    METRIC = 4
    AGG_METRIC = 7
    FOLDER = 8
    SUBSCRIPTION_DEVICE = 9
    PROMPT = 10
    FUNCTION = 11
    ATTRIBUTE = 12
    FACT = 13
    DIMENSION = 14
    TABLE = 15
    SHORTCUT_TYPE = 18
    MONITOR = 20
    ATTRIBUTE_FORM = 21
    COLUMN = 26
    PROPERTY_SET = 28
    DBROLE = 29
    DBLOGIN = 30
    DBCONNECTION = 31
    PROJECT = 32
    USER = 34
    USERGROUP = 34
    SUBSCRIPTION_TRANSMITTER = 35
    CONFIGURATION = 36
    SEARCH = 39
    ROLE = 43
    SECURITY_ROLE = 44
    LOCALE = 45
    CONSOLIDATION = 47
    CONSOLIDATION_ELEMENT = 48
    SCHEDULE_EVENT = 49
    SCHEDULE_OBJECT = 50
    SCHEDULE_TRIGGER = 51
    DBTABLE = 53
    DOCUMENT_DEFINITION = 55
    DRILL_MAP = 56
    DBMS = 57
    GRAPH_STYLE = 61
    SECURITY_FILTER = 58
    SHORTCUT = 67
    SHORTCUT_TARGET = 68
    PALETTE = 71
    SCRIPT = 76
    CONTENT_BUNDLE = 77
    APPLICATION = 78
    TIMEZONE = 79
    RUNTIME = 80
    CALENDAR = 81
    DRIVER = 84
    NOT_SUPPORTED = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value

    @classmethod
    def _missing_(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        member._name_ = f'UNDEFINED_TYPE:{value}'
        return member

    @staticmethod
    def contains(item):
        if isinstance(item, ObjectTypes):
            return True
        return item in [v.value for v in ObjectTypes.__members__.values()]

    def get_subtypes(self):
        # This takes advantage of how subtypes are defined in DSS.
        # All subtypes are defined as the corresponding type followed
        # by 8 bits of subtype ID
        return [
            subtype
            for subtype in ObjectSubTypes
            if subtype.value and subtype.value >> 8 == self.value
        ]


class ObjectSubTypes(Enum):
    FILTER = 256
    CUSTOM_GROUP = 257
    REPORT_GRID = 768
    REPORT_GRAPH = 769
    REPORT_ENGINE = 770
    REPORT_TEXT = 771
    REPORT_DATAMART = 772
    REPORT_BASE = 773
    REPORT_GRID_AND_GRAPH = 774
    REPORT_NON_INTERACTIVE = 775
    OLAP_CUBE = 776
    INCREMENTAL_REFRESH_REPORT = 777
    REPORT_TRANSACTION = 778
    SUPER_CUBE = 779
    SUBER_CUBE_IRR = 780
    REPORT_HYPER_CARD = 781
    METRIC = 1024
    SUBTOTAL_DEFINITION = 1025
    SYSTEM_SUBTOTAL = 1026
    FUNCTION = 2816
    USER = 8704
    USER_GROUP = 8705
    SEARCH = 9984
    FUNCTION_PACKAGE_DEFINITION = 10752
    REPORT_WRITING_DOCUMENT = 14081
    DOCUMENT_BOT = 14084
    MD_SECURITY_FILTER = 14848
    ATTRIBUTE = 3072
    ATTRIBUTE_ROLE = 3073
    ATTRIBUTE_TRANSFORMATION = 3074
    ATTRIBUTE_ABSTRACT = 3075
    ATTRIBUTE_RECURSIVE = 3076
    ATTRIBUTE_DERIVED = 3077
    ATTRIBUTE_SMART = 3078
    DIMENSION_SYSTEM = 3584
    DIMENSION_USER = 3585
    DIMENSION_ORDERED = 3586
    DIMENSION_USER_HIERARCHY = 3587
    ATTRIBUTE_FORM = 5376
    ROLE_TRANSFORMATION = 11009
    SYSTEM_PALETTE = 17920
    CUSTOM_PALETTE = 17921
    SCRIPT = 19457
    DATASOURCE_SCRIPT = 19459
    TRANSACTION_SCRIPT = 19460
    TIMEZONE_SYSTEM = 20224
    TIMEZONE_CUSTOM = 20225
    CALENDAR_SYSTEM = 20736
    CALENDAR_CUSTOM = 20737
    NOT_SUPPORTED = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


class ExtendedType(Enum):
    RESERVED = 0
    RELATIONAL = 1
    MDX = 2
    CUSTOM_SQL_FREE_FORM = 3
    CUSTOM_SQL_WIZARD = 4
    DATA_IMPORT_GENERAL = 256
    DATA_IMPORT_FILE_EXCEL = 272
    DATA_IMPORT_FILE_TEXT = 288
    DATA_IMPORT_CUSTOM_SQL = 304
    DATA_IMPORT_TABLE = 320
    DATA_IMPORT_OAUTH = 336
    DATA_IMPORT_OAUTH_SFDC = 337
    DATA_IMPORT_OAUTH_GDRIVE = 338
    DATA_IMPORT_OAUTH_DROPBOX = 339
    _ = 341
    DATA_IMPORT_CUSTOM_SQL_WIZARD = 352
    DATA_IMPORT_SPARK = 416

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


TypeOrSubtype = (
    int | ObjectTypes | ObjectSubTypes | list[int | ObjectTypes | ObjectSubTypes]
)
