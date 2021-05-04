from mstrio.distribution_services.schedule import (  # noqa: F401
    Schedule, ScheduleManager)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.schedule", "mstrio.distribution_services.schedule", "11.3.2.101")
