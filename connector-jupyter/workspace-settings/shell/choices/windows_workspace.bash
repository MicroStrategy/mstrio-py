#!/usr/bin/env bash



function set_workspace_settings_to_windows_workspace() {
  export VAGRANT_DEFAULT_PROVIDER=virtualbox
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/windows_workspace"
  export PATHS_PROJECT_DEPLOY_VAGRANT_HOME="${PATHS_PROJECT_WORKSPACE_SETTINGS_HOME}/vagrant"
 
  export TEST_TYPES=windows_workspace
  export HATS=windows_workspace
}