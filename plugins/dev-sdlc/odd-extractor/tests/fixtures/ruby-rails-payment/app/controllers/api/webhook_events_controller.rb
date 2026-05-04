# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: rails_controllers (controller class + 2 RESTful
# read-only actions + before_action filter).
module Api
  class WebhookEventsController < ApplicationController
    before_action :authenticate_admin!

    def index
      @events = WebhookEvent.order(created_at: :desc).limit(100)
      @events = @events.for_owner_type(params[:owner_type]) if params[:owner_type].present?
      render json: @events
    end

    def show
      @event = WebhookEvent.find(params[:id])
      render json: @event
    end
  end
end
