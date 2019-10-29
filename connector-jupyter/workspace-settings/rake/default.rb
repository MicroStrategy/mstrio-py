require 'compiler/maven'

Compiler::Maven.artifact_info(
  artifact_file_extension: "TKN-.-artifact_file_extension-.-TKN",
  output_dir: "#{$WORKSPACE_SETTINGS[:paths][:project][:production][:home]}/connector-jupyter/.build",
)
