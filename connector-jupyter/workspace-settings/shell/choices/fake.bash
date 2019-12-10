#!/usr/bin/env bash



function set_workspace_settings_to_fake() {
  # export VAGRANT_DEFAULT_PROVIDER=virtualbox
  # export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/fake"
  export TEST_TYPES=dev:acceptance
  export HATS=jenkins
}
