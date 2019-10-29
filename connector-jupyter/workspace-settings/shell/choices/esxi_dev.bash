#!/usr/bin/env bash



function set_workspace_settings_to_esxi_dev() {
  export VAGRANT_DEFAULT_PROVIDER=esxi
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/dev"
  
  export TEST_TYPES=dev:acceptance
  export HATS=dev:pipeline
}