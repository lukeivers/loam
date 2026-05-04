# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: jobs (include Sidekiq::Job; perform method).
class ProcessPaymentJob
  include Sidekiq::Job

  sidekiq_options queue: 'critical', retry: 3

  def perform(payment_id)
    payment = Payment.find(payment_id)
    return unless payment.status == 'pending'

    payment.update!(status: 'processing')

    result = charge_payment_gateway(payment)

    if result[:success]
      payment.update!(
        status: 'succeeded',
        gateway_reference: result[:reference]
      )
    else
      payment.update!(
        status: 'failed',
        failure_reason: result[:error]
      )
    end
  end

  private

  def charge_payment_gateway(payment)
    # Stub gateway call — synthetic.
    { success: true, reference: "ch_#{SecureRandom.hex(12)}" }
  end
end
