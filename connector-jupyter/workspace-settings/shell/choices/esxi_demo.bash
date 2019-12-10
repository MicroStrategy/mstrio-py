#!/usr/bin/env bash



function set_workspace_settings_to_esxi_demo() {
  export VAGRANT_DEFAULT_PROVIDER=esxi
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/demo"

  export TEST_TYPES=:
  export HATS=pipeline
}
