from mstrio.server.server import ServerSettings  # noqa: F401
from mstrio.server.cluster import Cluster  # noqa: F401
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.server", "mstrio.server.server and mstrio.server.cluster",
                    "11.3.2.101")
