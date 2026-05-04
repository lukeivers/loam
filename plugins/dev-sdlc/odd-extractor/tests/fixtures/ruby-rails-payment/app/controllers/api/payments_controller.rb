# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: rails_controllers (controller class + 5 RESTful
# actions + before_action + strong_params).
module Api
  class PaymentsController < ApplicationController
    before_action :authenticate_customer!
    before_action :set_payment, only: %i[show update destroy refund]

    def index
      @payments = current_customer.payments.order(created_at: :desc).page(params[:page])
      render json: @payments
    end

    def show
      render json: @payment
    end

    def create
      @payment = current_customer.payments.new(payment_params)
      if @payment.save
        render json: @payment, status: :created
      else
        render json: { errors: @payment.errors }, status: :unprocessable_entity
      end
    end

    def update
      if @payment.update(payment_params)
        render json: @payment
      else
        render json: { errors: @payment.errors }, status: :unprocessable_entity
      end
    end

    def destroy
      @payment.destroy
      head :no_content
    end

    def refund
      RefundPaymentJob.perform_async(@payment.id, params[:reason])
      render json: { status: 'refund_enqueued' }, status: :accepted
    end

    private

    def set_payment
      @payment = current_customer.payments.find(params[:id])
    end

    def payment_params
      params.require(:payment).permit(:amount_cents, :currency, :description)
    end
  end
end
