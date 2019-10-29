#!/usr/bin/env bash

register_workspace_setting 'test'

function set_workspace_settings_to_test() {
  export TEST_TYPES=acceptance
  export HATS=test
}
