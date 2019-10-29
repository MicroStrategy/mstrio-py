#!/usr/bin/env bash

register_workspace_setting 'dev'

function set_workspace_settings_to_dev() {
  export TEST_TYPES=dev:acceptance
  export HATS=dev
}
