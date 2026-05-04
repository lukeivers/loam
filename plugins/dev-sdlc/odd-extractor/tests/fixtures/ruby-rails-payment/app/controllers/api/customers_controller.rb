# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: rails_controllers (controller class + 4 RESTful
# actions + before_action + strong_params + custom collection action).
module Api
  class CustomersController < ApplicationController
    before_action :authenticate_admin!, only: %i[index search]
    before_action :set_customer, only: %i[show update]

    def index
      @customers = Customer.active.order(:name).page(params[:page])
      render json: @customers
    end

    def show
      render json: @customer
    end

    def create
      @customer = Customer.new(customer_params)
      if @customer.save
        render json: @customer, status: :created
      else
        render json: { errors: @customer.errors }, status: :unprocessable_entity
      end
    end

    def update
      if @customer.update(customer_params)
        render json: @customer
      else
        render json: { errors: @customer.errors }, status: :unprocessable_entity
      end
    end

    def search
      @customers = Customer.where('email ILIKE ?', "%#{params[:q]}%").limit(20)
      render json: @customers
    end

    private

    def set_customer
      @customer = Customer.find(params[:id])
    end

    def customer_params
      params.require(:customer).permit(:email, :name, :password, :password_confirmation)
    end
  end
end
