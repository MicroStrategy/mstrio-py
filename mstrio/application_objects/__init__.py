# flake8: noqa
from mstrio.project_objects.datasets import *
from mstrio.project_objects.document import Document, list_documents, list_documents_across_projects
from mstrio.project_objects.dossier import Dossier, list_dossiers, list_dossiers_across_projects
from mstrio.project_objects.library import Library
from mstrio.project_objects.report import list_reports, Report
from mstrio.utils.helper import deprecation_warning

deprecation_warning(
    'mstrio.application_objects',
    'mstrio.project_objects',
    '11.3.4.101',  # NOSONAR
    False)
