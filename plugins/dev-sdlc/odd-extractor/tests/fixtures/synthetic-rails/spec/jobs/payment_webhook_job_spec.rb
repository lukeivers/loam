# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (1 it block → 1 VERIFIED AC).
require 'rails_helper'

RSpec.describe PaymentWebhookJob, type: :job do
  it 'sends a webhook for the payment' do
    payment = Payment.create!(amount_cents: 250)
    expect(WebhookClient).to receive(:send_for).with(payment)
    PaymentWebhookJob.perform_now(payment.id)
  end
end
