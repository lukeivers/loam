# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: (no specific recognizer in Cycle 3 — controller-level
# recognition is RF gap §10 #3, deferred to Cycle 4+)
class PaymentsController < ApplicationController
  def index
    @payments = Payment.all
    render json: @payments
  end

  def create
    @payment = Payment.new(payment_params)
    if @payment.save
      render json: @payment, status: :created
    else
      render json: @payment.errors, status: :unprocessable_entity
    end
  end

  def show
    @payment = Payment.find(params[:id])
    render json: @payment
  end

  private

  def payment_params
    params.require(:payment).permit(:amount_cents, :owner_type, :owner_id)
  end
end
