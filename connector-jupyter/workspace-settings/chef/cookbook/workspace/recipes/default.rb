#
# Cookbook Name:: workspace
# Recipe:: default
#

if ENV['USER'] == 'jenkins'
  include_recipe 'workspace::jenkins'
else
  include_recipe 'workspace::user'
end