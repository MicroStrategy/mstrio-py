from enum import Enum, IntEnum, auto

from mstrio.utils.enum_helper import AutoUpperName


class CertifiedStatus(Enum):
    """Enumeration that represents what can be passed in the certified_status
    attribute of the IServer quick search command."""

    ALL = 'ALL'
    CERTIFIED_ONLY = 'CERTIFIED_ONLY'
    NOT_CERTIFIED_ONLY = 'NOT_CERTIFIED_ONLY'
    OFF = 'OFF'


class SearchPattern(IntEnum):
    """Enumeration constants used to specify searchType used to control BI
    Search. More details can be found in EnumDSSXMLSearchTypes in a browser."""

    CONTAINS_ANY_WORD = 0
    BEGIN_WITH = 1
    EXACTLY = 2
    BEGIN_WITH_PHRASE = 3
    CONTAINS = 4
    END_WITH = 5


class SearchDomain(IntEnum):
    """Enumeration constants used to specify the search domains. More details
    can be found in EnumDSSXMLSearchDomain in a browser."""

    LOCAL = 1
    PROJECT = 2
    REPOSITORY = 3
    CONFIGURATION = 4


class SearchResultsFormat(Enum):
    """Enumeration constants used to specify the format to return
    from search functions."""

    LIST = 'LIST'
    TREE = 'TREE'


class SearchScope(AutoUpperName):
    """Enumeration constants used to specify the scope of the search with regard
    to System Managed Objects."""

    ROOTED = auto()  # For compatibility
    NOT_MANAGED_ONLY = auto()
    MANAGED_ONLY = auto()
    ALL = auto()
