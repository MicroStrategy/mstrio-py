#!/usr/bin/env bash



function set_workspace_settings_to_linux_workspace() {
  export VAGRANT_DEFAULT_PROVIDER=virtualbox
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/linux_workspace"
  export PATHS_PROJECT_DEPLOY_VAGRANT_HOME="${PATHS_PROJECT_WORKSPACE_SETTINGS_HOME}/vagrant"
 
  export TEST_TYPES=linux_workspace
  export HATS=linux_workspace
}