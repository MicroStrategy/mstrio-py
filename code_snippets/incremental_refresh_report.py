from mstrio.connection import get_connection
from mstrio.project_objects.incremental_refresh_report import ( 
    IncrementalRefreshReport,
    list_incremental_refresh_reports,
)
from mstrio.project_objects.datasets.helpers import (
    Template,
    AttributeTemplateUnit,
    MetricTemplateUnit,
    MetricElement,
)
from mstrio.project_objects.datasets.olap_cube import OlapCube


# Define variables which can be later used in a script
PROJECT_NAME = $project_name  # Name of project
FOLDER_ID = $folder_id  # Folder ID for listing and creating reports
FOLDER_PATH = $folder_path  # Folder path for listing reports
REPORT_NAME = $report_name  # Name of new report
CUBE_ID = $cube_id  # ID of target cube for new report

template_attribute_ids = $template_attribute_ids  # List of attribute IDs
template_metric_ids = $template_metric_ids  # List of metric IDs

template = Template(
    rows=[
        AttributeTemplateUnit(attribute_id) for attribute_id in template_attribute_ids
    ],
    columns=[
        MetricTemplateUnit([MetricElement(metric_id)])
        for metric_id in template_metric_ids
    ],
    page_by=[],  # page_by is optional if empty
)

conn = get_connection(workstationData, PROJECT_NAME)

# List all incremental refresh reports in a project
list_incremental_refresh_reports(conn, project_name=PROJECT_NAME)

# List all incremental refresh reports in a folder, by id
list_incremental_refresh_reports(conn, folder_id=FOLDER_ID)

# List all incremental refresh reports in a folder, by path
list_incremental_refresh_reports(conn, folder_path=FOLDER_PATH)

# Create an incremental refresh report given a cube
# This will use the cube's template.
new_report_from_cube = IncrementalRefreshReport.create_from_cube(
    conn,
    name=REPORT_NAME,
    destination_folder=FOLDER_ID,
    target_cube=OlapCube(conn, CUBE_ID),
    refresh_type=IncrementalRefreshReport.RefreshType.UPDATE_ONLY,
)

# Create an incremental refresh report given a cube
# and a custom template
new_report = IncrementalRefreshReport.create(
    conn,
    name=REPORT_NAME + 'Custom Template',
    destination_folder=FOLDER_ID,
    target_cube=OlapCube(conn, CUBE_ID),
    increment_type=IncrementalRefreshReport.IncrementType.REPORT,
    template=template,
    refresh_type=IncrementalRefreshReport.RefreshType.UPDATE_ONLY,
)

# Alter the incremental refresh report
new_template_attribute_ids = $new_template_attribute_ids  # List of attribute IDs
new_template_metric_ids = $new_template_metric_ids  # List of metric IDs

new_template = Template(
    rows=[
        AttributeTemplateUnit(attribute_id)
        for attribute_id in new_template_attribute_ids
    ],
    columns=[
        MetricTemplateUnit([MetricElement(metric_id)])
        for metric_id in new_template_metric_ids
    ],
)
new_report.alter(
    name=REPORT_NAME + 'altered',
    description='New description',
    refresh_type=IncrementalRefreshReport.RefreshType.UPDATE,
    template=new_template,
)

# Publish an incremental refresh report by ID
publish_id = $publish_id  # ID of report to publish
report_to_publish = IncrementalRefreshReport(conn, id=publish_id)
report_to_publish.execute()

# Delete an incremental refresh report by ID
delete_id = $delete_id  # ID of report to delete
report_to_delete = IncrementalRefreshReport(conn, id=delete_id)
report_to_delete.delete()
