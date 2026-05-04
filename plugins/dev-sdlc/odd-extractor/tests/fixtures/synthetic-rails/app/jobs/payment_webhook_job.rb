# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: jobs (ActiveJob superclass + queue_as).
class PaymentWebhookJob < ApplicationJob
  queue_as :webhooks

  def perform(payment_id)
    payment = Payment.find(payment_id)
    WebhookClient.send_for(payment)
  end
end
