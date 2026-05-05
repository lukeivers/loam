require_relative "boot"
require "rails/all"

Bundler.require(*Rails.groups)

module FixtureRailsApp
  class Application < Rails::Application
    config.load_defaults 7.1
  end
end
