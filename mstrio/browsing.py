from enum import IntEnum

from mstrio.object_management import full_search as list_objects  # noqa: F401
from mstrio.utils.helper import deprecation_warning  # noqa: F401

deprecation_warning("mstrio.browsing.browsing", "mstrio.object_management.search_operations",
                    "11.3.4.101")  # NOSONAR


class SearchType(IntEnum):
    """Enumeration constants used to specify searchType used to control BI
    Search. More details can be found in EnumDSSXMLSearchTypes in a browser."""
    BEGIN_WITH = 1,
    BEGIN_WITH_PHRASE = 3,
    CONTAINS = 4,
    CONTAINS_ANY_WORD = 0,
    END_WITH = 5,
    EXACTLY = 2,


class SearchDomain(IntEnum):
    """Enumeration constants used to specify the search domains. More details
     can be found in EnumDSSXMLSearchDomain in a browser."""
    CONFIGURATION_AND_ALL_PROJECTS = 5,
    DOMAIN_CONFIGURATION = 4,
    DOMAIN_LOCAL = 1,
    DOMAIN_PROJECT = 2,
    DOMAIN_REPOSITORY = 3,
