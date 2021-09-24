from enum import Enum
from typing import List, Union


class ObjectTypes(Enum):
    FILTER = 1
    REPORT_DEFINITION = 3
    METRIC = 4
    AGG_METRIC = 7
    FOLDER = 8
    SUBSCRIPTION_DEVICE = 9
    PROMPT = 10
    FUNCTION = 11
    ATTRIBUTE = 12
    FACT = 13
    TABLE = 15
    SHORTCUT_TYPE = 18
    MONITOR = 20
    ATTRIBUTE_FORM = 21
    COLUMN = 26
    DBROLE = 29
    DBLOGIN = 30
    DBCONNECTION = 31
    PROJECT = 32
    USER = 34
    USERGROUP = 34
    CONFIGURATION = 36
    SEARCH = 39
    SECURITY_ROLE = 44
    LOCALE = 45
    CONSOLIDATION = 47
    SCHEDULE_EVENT = 49
    SCHEDULE_OBJECT = 50
    SCHEDULE_TRIGGER = 51
    DBTABLE = 53
    DOCUMENT_DEFINITION = 55
    DBMS = 57
    SECURITY_FILTER = 58
    SHORTCUT = 67
    SHORTCUT_TARGET = 68
    NONE = None

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        return member

    def __int__(self):
        return self.value

    @staticmethod
    def contains(item):
        if isinstance(item, ObjectTypes):
            return True
        return item in [v.value for v in ObjectTypes.__members__.values()]


class ObjectSubTypes(Enum):
    OLAP_CUBE = 776
    SUPER_CUBE = 779
    USER = 8704
    USER_GROUP = 8705
    SEARCH = 9984
    MD_SECURITY_FILTER = 14848
    NONE = None

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


TypeOrSubtype = Union[int, ObjectTypes, ObjectSubTypes, List[Union[int, ObjectTypes,
                                                                   ObjectSubTypes]]]
