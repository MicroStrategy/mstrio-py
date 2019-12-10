#!/usr/bin/env bash



function set_workspace_settings_to_esxi_test() {
  export VAGRANT_DEFAULT_PROVIDER=esxi
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/test"
  
  export TEST_TYPES=acceptance
  export HATS=test:pipeline
}