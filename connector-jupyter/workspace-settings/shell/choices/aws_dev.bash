#!/usr/bin/env bash



function set_workspace_settings_to_aws_dev() {
  export VAGRANT_DEFAULT_PROVIDER=aws
  export VAGRANT_CONTEXT="${VAGRANT_DEFAULT_PROVIDER}/dev"
  
  export TEST_TYPES=dev:acceptance
  export HATS=dev:pipeline
}