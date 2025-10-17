from enum import Enum


# A sentinel object to detect if an attribute has been returned by REST API
class _MissingType:
    pass


MISSING = _MissingType()


class ObjectTypes(Enum):
    # https://www2.microstrategy.com/producthelp/Current/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLObjectTypes.html
    FILTER = 1
    TEMPLATE = 2
    REPORT_DEFINITION = 3
    METRIC = 4
    AUTO_STYLE = 6
    AGG_METRIC = 7
    FOLDER = 8
    SUBSCRIPTION_DEVICE = 9
    PROMPT = 10
    FUNCTION = 11
    ATTRIBUTE = 12
    FACT = 13
    DIMENSION = 14
    TABLE = 15
    DATAMART_REPORT = 16
    FACT_GROUP = 17
    SHORTCUT_TYPE = 18
    RESOLUTION = 19
    MONITOR = 20
    ATTRIBUTE_FORM = 21
    SCHEMA = 22
    FORMAT = 23
    CATALOG = 24
    CATALOG_DEFINITION = 25
    COLUMN = 26
    PROPERTY_SET = 28
    DBROLE = 29
    DBLOGIN = 30
    DBCONNECTION = 31
    PROJECT = 32
    SERVER_DEFINITION = 33
    USER = 34
    USERGROUP = 34
    SUBSCRIPTION_TRANSMITTER = 35
    CONFIGURATION = 36
    REQUEST = 37
    SEARCH = 39
    SEARCH_FOLDER = 40
    DATAMART = 41
    PACKAGE_DEFINITION = 42
    ROLE = 43
    SECURITY_ROLE = 44
    LOCALE = 45
    CONSOLIDATION = 47
    CONSOLIDATION_ELEMENT = 48
    SCHEDULE_EVENT = 49
    SCHEDULE_OBJECT = 50
    SCHEDULE_TRIGGER = 51
    LINK = 52
    DBTABLE = 53
    TABLE_SOURCE = 54
    DOCUMENT_DEFINITION = 55
    DRILL_MAP = 56
    DBMS = 57
    SECURITY_FILTER = 58
    PROMPT_ANSWER = 59
    PROMPT_ANSWERS = 60
    GRAPH_STYLE = 61
    BLOB = 63
    OBJECT_TAG = 65
    CHANGE_JOURNAL = 66
    SHORTCUT = 67
    SHORTCUT_TARGET = 68
    RECONCILIATION = 69
    LAYER = 70
    PALETTE = 71
    THRESHOLDS = 72
    DASHBOARD_PERSONAL_VIEW = 73
    FEATURE_FLAG = 74
    SCRIPT = 76
    CONTENT_BUNDLE = 77
    APPLICATION = 78
    TIMEZONE = 79
    RUNTIME = 80
    CALENDAR = 81
    IAM = 82
    KPI_WATCHER = 83
    DRIVER = 84
    INTERFACE_LANGUAGE = 85
    WORKFLOW = 86
    TEST_SUITE = 93
    NOT_SUPPORTED = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value

    @classmethod
    def _rest_aliases(cls):
        return {
            ObjectTypes.AUTO_STYLE: 'style',
            ObjectTypes.SUBSCRIPTION_DEVICE: 'device',
            ObjectTypes.SHORTCUT_TYPE: 'type_shortcut',
            ObjectTypes.DBROLE: 'db_role',
            ObjectTypes.DBLOGIN: 'db_login',
            ObjectTypes.DBCONNECTION: 'db_connection',
            ObjectTypes.SERVER_DEFINITION: 'server_def',
            ObjectTypes.SUBSCRIPTION_TRANSMITTER: 'transmitter',
            ObjectTypes.PACKAGE_DEFINITION: 'function_package_definition',
            ObjectTypes.DBTABLE: 'db_table',
            ObjectTypes.DBMS: 'type_dbms',
            ObjectTypes.SECURITY_FILTER: 'md_security_filter',
            ObjectTypes.SHORTCUT: 'external_shortcut',
            ObjectTypes.SHORTCUT_TARGET: 'external_shortcut_target',
            ObjectTypes.DASHBOARD_PERSONAL_VIEW: 'dossier_personal_view',
            ObjectTypes.SCRIPT: 'command_manager_script',
            ObjectTypes.RUNTIME: 'script_runtime_env',
        }

    @classmethod
    def _missing_(cls, value):
        aliases = cls._rest_aliases()
        aliases_to_enum_items = {aliases[enum_item]: enum_item for enum_item in aliases}
        if value in aliases_to_enum_items:
            return aliases_to_enum_items[value]
        else:
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

    @classmethod
    def from_rest_value(cls, source, *args, **kwargs):
        """Handle missing values in the enum."""
        aliases = cls._rest_aliases()
        aliases_to_enum_items = {aliases[enum_item]: enum_item for enum_item in aliases}
        if source in aliases_to_enum_items:
            return aliases_to_enum_items[source]
        else:
            return cls[source.upper()]

    def to_rest_value(self):
        """Return the REST alias for the object subtype."""
        aliases = self._rest_aliases()
        return aliases.get(self, self.name.lower())


class ObjectSubTypes(Enum):
    # https://www2.microstrategy.com/producthelp/Current/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLObjectSubTypes.html
    FILTER = 256
    CUSTOM_GROUP = 257
    TEMPLATE = 512
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
    SUPER_CUBE_IRR = 780
    REPORT_HYPER_CARD = 781
    METRIC = 1024
    SUBTOTAL_DEFINITION = 1025
    SYSTEM_SUBTOTAL = 1026
    METRIC_DMX = 1027
    METRIC_TRAINING = 1028
    STYLE = 1536
    METRIC_AGG = 1792
    FOLDER = 2048
    DEVICE = 2304
    PROMPT = 2560
    PROMPT_BOOLEAN = 2561
    PROMPT_LONG = 2562
    PROMPT_STRING = 2563
    PROMPT_DOUBLE = 2564
    PROMPT_DATE = 2565
    PROMPT_OBJECTS = 2566
    PROMPT_ELEMENTS = 2567
    PROMPT_EXPRESSION = 2568
    PROMPT_EXPRESSION_DRAFT = 2569
    PROMPT_DIMTY = 2570
    PROMPT_BIG_DECIMAL = 2571
    FUNCTION = 2816
    ATTRIBUTE = 3072
    ATTRIBUTE_ROLE = 3073
    ATTRIBUTE_TRANSFORMATION = 3074
    ATTRIBUTE_ABSTRACT = 3075
    ATTRIBUTE_RECURSIVE = 3076
    ATTRIBUTE_DERIVED = 3077
    ATTRIBUTE_SMART = 3078
    FACT = 3328
    DIMENSION_SYSTEM = 3584
    DIMENSION_USER = 3585
    DIMENSION_ORDERED = 3586
    DIMENSION_USER_HIERARCHY = 3587
    TABLE = 3840
    TABLE_PARTITION_MD = 3841
    TABLE_PARTITION_WH = 3842
    DATAMART_REPORT = 4096
    FACT_GROUP = 4352
    SHORTCUT = 4608
    LIBRARY_SHORTCUT = 4609
    RESOLUTION = 4864
    ATTRIBUTE_FORM = 5376
    ATTRIBUTE_FORM_SYSTEM = 5377
    ATTRIBUTE_FORM_NORMAL = 5378
    SCHEMA = 5632
    FORMAT = 5888
    CATALOG = 6144
    CATALOG_DEFINITION = 6400
    COLUMN = 6656
    PROPERTY_GROUP = 6912
    PROPERTY_SET = 7168
    DB_ROLE = 7424
    DB_ROLE_DATA_IMPORT = 7425
    DB_ROLE_DATA_IMPORT_PRIMARY = 7426
    DB_ROLE_OAUTH = 7427
    DB_ROLE_REMOTE_DATA_SOURCE = 7428
    DB_ROLE_URL_AUTH = 7429
    DB_ROLE_GENERIC_DATA_CONNECTOR = 7430
    DB_LOGIN = 7680
    DB_LOGIN_SECRET_VAULT = 7681
    DB_CONNECTION = 7936
    PROJECT = 8192
    SERVER_DEFINITION = 8448
    USER = 8704
    USER_GROUP = 8705
    TRANSMITTER = 8705
    CONFIGURATION = 9216
    REQUEST = 9472
    SEARCH = 9984
    SEARCH_FOLDER = 10240
    DATAMART = 10496
    FUNCTION_PACKAGE_DEFINITION = 10752
    ROLE = 11008
    ROLE_TRANSFORMATION = 11009
    SECURITY_ROLE = 11264
    INBOX = 11520
    INBOX_MESSAGE = 11776
    CONSOLIDATION = 12032
    CONSOLIDATION_MANAGED = 12033
    CONSOLIDATION_ELEMENT = 12288
    SCHEDULE_EVENT = 12544
    SCHEDULE_OBJECT = 12800
    SCHEDULE_TRIGGER = 13056
    LINK = 13312
    DB_TABLE = 13568
    DB_TABLE_PMT = 13569
    TABLE_SOURCE = 13824
    DOCUMENT_DEFINITION = 14080
    REPORT_WRITING_DOCUMENT = 14081
    DOCUMENT_THEME = 14082
    DOCUMENT_BOT = 14084
    DOCUMENT_BOT_2_0 = 14087
    DOCUMENT_BOT_UNIVERSAL = 14091
    DOCUMENT_AGENT = 14087
    DOCUMENT_AGENT_UNIVERSAL = 14091
    DRILL_MAP = 14336
    DBMS = 14592
    MD_SECURITY_FILTER = 14848
    MONITOR_PERFORMANCE = 15104
    MONITOR_JOBS = 15105
    MONITOR_USER_CONNECTIONS = 15106
    MONITOR_DB_CONNECTIONS = 15107
    PROMPT_ANSWER = 15232
    PROMPT_ANSWERS = 15360
    PROMPT_ANSWER_BOOLEAN = 15233
    PROMPT_ANSWER_LONG = 15234
    PROMPT_ANSWER_STRING = 15235
    PROMPT_ANSWER_DOUBLE = 15236
    PROMPT_ANSWER_DATE = 15237
    PROMPT_ANSWER_OBJECTS = 15238
    PROMPT_ANSWER_ELEMENTS = 15239
    PROMPT_ANSWER_EXPRESSION = 15240
    PROMPT_ANSWER_EXPRESSION_DRAFT = 15241
    PROMPT_ANSWER_DIMTY = 15242
    PROMPT_ANSWER_BIG_DECIMAL = 15243
    PROMPT_ANSWER_INT64 = 15244
    GRAPH_STYLE = 15616
    CHANGE_JOURNAL_SEARCH = 15872
    BLOB_UNKNOWN = 16128
    BLOB_OTHER = 16129
    BLOB_IMAGE = 16130
    BLOB_PROJECT_PACKAGE = 16131
    BLOB_EXCEL = 16132
    BLOB_HTML_TEMPLATE = 16133
    DASHBOARD_TEMPLATE = 16384
    FLAG = 16640
    CHANGE_JOURNAL = 16896
    EXTERNAL_SHORTCUT_UNKNOWN = 17152
    EXTERNAL_SHORTCUT_URL = 17153
    EXTERNAL_SHORTCUT_SNAPSHOT = 17154
    EXTERNAL_SHORTCUT_TARGET = 17408
    RECONCILIATION = 17664
    SYSTEM_PALETTE = 17920
    CUSTOM_PALETTE = 17921
    THRESHOLDS = 18432
    COMMAND_MANAGER_SCRIPT = 19456
    SCRIPT = 19457
    JUPYTER_NOTEBOOK_SCRIPT = 19458
    DATASOURCE_SCRIPT = 19459
    TRANSACTION_SCRIPT = 19460
    APPLICATION = 19968
    APPLICATION_POWERPOINT = 19969
    APPLICATION_EXCEL = 19970
    APPLICATION_TEAMS = 19971
    APPLICATION_TABLEAU = 19972
    APPLICATION_GOOGLE_SHEETS = 19973
    TIMEZONE_SYSTEM = 20224
    TIMEZONE_CUSTOM = 20225
    CALENDAR_SYSTEM = 20736
    CALENDAR_CUSTOM = 20737
    INTERFACE_LANGUAGE_SYSTEM = 21760
    INTERFACE_LANGUAGE_CUSTOM = 21761
    WORKFLOW = 22016
    IAM_SECRET_VAULT = 21002
    NUGGETS_FILE = 23040
    STREAM_CHANNEL = 23552
    SUBSCRIPTION_ADDRESS = 65281
    SUBSCRIPTION_CONTACT = 65282
    SUBSCRIPTION_INSTANCE = 65283
    NOT_SUPPORTED = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value

    @classmethod
    def _rest_aliases(cls):
        return {
            ObjectSubTypes.OLAP_CUBE: 'report_cube',
            ObjectSubTypes.INCREMENTAL_REFRESH_REPORT: 'report_incremental_refresh',
            ObjectSubTypes.SUPER_CUBE: 'report_emma_cube',
            ObjectSubTypes.SUPER_CUBE_IRR: 'report_emma_incremental_refresh',
            ObjectSubTypes.REPORT_HYPER_CARD: 'report_hypercard',
            ObjectSubTypes.METRIC_AGG: 'agg_metric',
            ObjectSubTypes.PROMPT_BIG_DECIMAL: 'prompt_bigdecimal',
            ObjectSubTypes.ATTRIBUTE_DERIVED: 'derived_attribute',
            ObjectSubTypes.ATTRIBUTE_FORM_SYSTEM: 'form_system',
            ObjectSubTypes.ATTRIBUTE_FORM_NORMAL: 'form_normal',
            ObjectSubTypes.CATALOG_DEFINITION: 'catalog_def',
            ObjectSubTypes.DB_ROLE_GENERIC_DATA_CONNECTOR: (
                'db_role_generic_dataconnector'
            ),
            ObjectSubTypes.SERVER_DEFINITION: 'server_def',
            ObjectSubTypes.FUNCTION_PACKAGE_DEFINITION: 'function_package_def',
            ObjectSubTypes.INBOX_MESSAGE: 'inbox_msg',
            ObjectSubTypes.DOCUMENT_DEFINITION: 'document_def',
            ObjectSubTypes.DOCUMENT_BOT: 'chat_bot',
            ObjectSubTypes.DOCUMENT_BOT_2_0: 'chat_bot_v2',
            ObjectSubTypes.DOCUMENT_BOT_UNIVERSAL: 'universal_chat_bot',
            ObjectSubTypes.DOCUMENT_AGENT: 'chat_bot_v2',
            ObjectSubTypes.DOCUMENT_AGENT_UNIVERSAL: 'universal_chat_bot',
            ObjectSubTypes.PROMPT_ANSWER_BIG_DECIMAL: 'prompt_answer_bigdecimal',
            ObjectSubTypes.CHANGE_JOURNAL_SEARCH: 'changejournal_search',
            ObjectSubTypes.CHANGE_JOURNAL: 'changejournal',
            ObjectSubTypes.SYSTEM_PALETTE: 'palette_system',
            ObjectSubTypes.CUSTOM_PALETTE: 'palette_custom',
            ObjectSubTypes.SCRIPT: 'command_manager_script_python',
            ObjectSubTypes.JUPYTER_NOTEBOOK_SCRIPT: (
                'command_manager_script_jupyter_notebook'
            ),
            ObjectSubTypes.IAM_SECRET_VAULT: 'vault_connection',
        }

    @classmethod
    def from_rest_value(cls, source, *args, **kwargs):
        """Handle missing values in the enum."""
        aliases = cls._rest_aliases()
        aliases_to_enum_items = {aliases[enum_item]: enum_item for enum_item in aliases}
        if source in aliases_to_enum_items:
            return aliases_to_enum_items[source]
        else:
            return cls[source.upper()]

    def to_rest_value(self):
        """Return the REST alias for the object subtype."""
        aliases = self._rest_aliases()
        return aliases.get(self, self.name.lower())


class ExtendedType(Enum):
    RESERVED = 0
    RELATIONAL = 1
    MDX = 2
    CUSTOM_SQL_FREE_FORM = 3
    CUSTOM_SQL_WIZARD = 4
    FLAT_FILE = 5
    DATA_IMPORT_GENERAL = 0x100
    DATA_IMPORT_FILE_EXCEL = 0x110
    DATA_IMPORT_FILE_TEXT = 0x120
    DATA_IMPORT_CUSTOM_SQL = 0x130
    DATA_IMPORT_TABLE = 0x140
    DATA_IMPORT_OAUTH = 0x150
    DATA_IMPORT_OAUTH_SFDC = 0x151
    DATA_IMPORT_OAUTH_GDRIVE = 0x152
    DATA_IMPORT_OAUTH_DROPBOX = 0x153
    _ = 0x155
    DATA_IMPORT_CUSTOM_SQL_WIZARD = 0x160
    DATA_IMPORT_SINGLE_TABLE = 0x170
    DATA_IMPORT_SPARK = 0x1A0
    DATA_IMPORT_DATASET = 0x1C0
    DATA_IMPORT_OLAP_CUBE = 0x1000
    DATA_IMPORT_LIVE_CUBE = 0x1001

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value


TypeOrSubtype = (
    int | ObjectTypes | ObjectSubTypes | list[int | ObjectTypes | ObjectSubTypes]
)
