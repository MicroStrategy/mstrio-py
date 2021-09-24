from enum import Enum, IntEnum


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
    CONFIGURATION_AND_ALL_PROJECTS = 5


class SearchResultsFormat(Enum):
    """Enumeration constants used to specify the format to return
    from search functions."""
    LIST = 'LIST'
    TREE = 'TREE'
