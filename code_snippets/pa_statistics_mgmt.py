"""This is the demo script to show how administrator can manage
Platform Analytics configuration for both each project separately and for
whole environment at once.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import get_connection
from mstrio.server import Environment, Project

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project to interact with

conn = get_connection(workstationData)
env = Environment(connection=conn)
project = Project(connection=conn, name=PROJECT_NAME)

# [Environment]
# get reference to PA Statistics handler
pa_env = env.pa_statistics

# get information about repository ID and PA project ID
repository_info = pa_env.get_repository_info()
print(repository_info.repository_id)
print(repository_info.pa_project_id)

# update repository information
new_repo_info = pa_env.RepositoryInfo(
    repository_id='<new_repository_id>',
    pa_project_id='<new_pa_project_id>',
)
pa_env.update_repository_info(new_repo_info)

# get telemetry basic configurations for all projects
telemetry_configs = pa_env.get_telemetry_basic_configurations()
for project_name, config in telemetry_configs.items():
    print(f"{project_name}: basic_stats={config.basic_stats}, "
          f"client_telemetry={config.client_telemetry}")

# enable/disable basic telemetry for all projects
pa_env.enable_basic_telemetry_for_all_projects()
pa_env.disable_basic_telemetry_for_all_projects()

# get telemetry connections information
telemetry_connections = pa_env.get_telemetry_connections_info()
print(telemetry_connections.servers)
print(telemetry_connections.protocol)

# update telemetry connections information
new_connections = pa_env.TelemetryConnections(
    servers=['kafka.example.com:9092'],
    protocol=pa_env.TelemetryConnections.Protocol.SASL_SSL
)
pa_env.update_telemetry_connections_info(new_connections)

# validate telemetry connections
validation_results = pa_env.validate_telemetry_connections()
for server, is_valid in validation_results.items():
    print(f"{server}: {is_valid}")

# get details about each telemetry connection validity
validation_details = pa_env.get_telemetry_connections_validation_info()
for server, details in validation_details.items():
    print(f"{server}: {details}")

# [Project]
# get reference to PA Statistics handler for project
pa_project = project.pa_statistics

# get project telemetry configuration
project_telemetry_config = pa_project.get_telemetry_configuration()
print(project_telemetry_config.basic_stats)  # Example property, one of many

# enable/disable telemetry for project
pa_project.enable_telemetry_basic_configuration()
pa_project.disable_telemetry_basic_configuration()  # cannot be disabled if "advanced" is enabled
pa_project.enable_telemetry_advanced_configuration()  # will enable basic as well
pa_project.disable_telemetry_advanced_configuration()

# update project telemetry configuration
new_config = pa_project.TelemetryConfig(
    basic_stats=True,
    client_telemetry=True
)
pa_project.update_telemetry_configuration(new_config)
