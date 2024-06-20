"""
Create a dataframe from a Report.
List available reports, retrieve their attributes and metrics. Operate with
given report.

1. Connect to the environment using data from workstation
2. List available reports (with limit of 10)
3. Get report with given id and check its available attributes and metrics
4. Choose attributes and metrics for filtering
5. Apply filters to the report specifying attributes and metrics
6. Create a dataframe from the filtered report
7. Print first few rows of newly created dataframe
"""

from mstrio.connection import get_connection
from mstrio.project_objects import Report, Prompt, list_reports

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

# Set and view VLDB properties for the report
vldb_properties = sample_report.list_vldb_settings()
sample_report.alter_vldb_settings(property_set_name='VLDB Select',name='Base Table Join for Template',value=2)
print(vldb_properties)

# View Owner/ACL properties for the report
acls = sample_report.list_acl()
owner_properties = sample_report.owner.list_properties().get('name')
print(f"ACLs: {acls}\nOwner_property 'name': '{owner_properties}'")


# Page by operations for report
page_by_report = Report(connection, '918EFA5F46E541B9F2799BA36E184811')

# List available elements
pg_elements = page_by_report.page_by_elements
print(pg_elements)


ATTR_QUARTER = '8D679D4A11D3E4981000E787EC6DE8A4'
ATTR_CC = '8D679D3511D3E4981000E787EC6DE8A4'
element_quarter = pg_elements[ATTR_QUARTER][0]

page_by_dataframe = page_by_report.to_dataframe(page_element_id={ATTR_QUARTER: element_quarter, ATTR_CC: 'h1;'})
print(page_by_dataframe.head())


# Prompt operations for report
prompt_report = Report(connection=connection, id='87FDA2E94FCD7C00B0A43AA2C52767B4')
prompt = Prompt(type='VALUE', key='CA6906D3499B6AEE259BFE9C308076D7@0@10', answers=100, use_default=False)

prompt_report_df = prompt_report.to_dataframe(prompt_answers=[prompt])
print("Prompt report dataframe:\n", prompt_report_df.head())
