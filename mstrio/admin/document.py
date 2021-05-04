from mstrio.application_objects.document import (  # noqa: F401
    Document, list_documents, list_documents_across_projects)
from mstrio.utils.helper import deprecation_warning

deprecation_warning("mstrio.admin.document", "mstrio.application_objects.document", "11.3.2.101")
