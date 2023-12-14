from mstrio.connection import get_connection
from mstrio.project_objects import Report, list_reports

# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
connection = get_connection(workstationData, project_name='MicroStrategy Tutorial')

# List available Reports (limited to 10)
sample_reports = list_reports(connection, limit=10)
for report in sample_reports:
    print(report)

# Check available attributes and metrics of a Report
sample_report_id = '759C0B5340E0AD6FAEDFF19D4DBC3488'
sample_report = Report(connection, id=sample_report_id)
attributes = sample_report.attributes
metrics = sample_report.metrics
print(f"Attributes: {attributes}\nMetrics: {metrics}")

# Choose attributes and metrics
category_attribute = attributes[0].get('id')
subcategory_attribute = attributes[1].get('id')

cost_metric = metrics[0].get('id')
profit_metric = metrics[1].get('id')

# Filter which attributes and metrics to use in a dataframe
sample_report.apply_filters(
    attributes=[category_attribute, subcategory_attribute],
    metrics=[cost_metric, profit_metric],
)

# Create a dataframe from a Report
dataframe = sample_report.to_dataframe()
print(dataframe.head())
