# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (2 it blocks → 2 VERIFIED ACs).
require 'rails_helper'

RSpec.describe ProcessPaymentJob, type: :job do
  let(:customer) { Customer.create!(email: 'p@q.com', name: 'P Q', password: 'secret123') }
  let(:payment) { Payment.create!(customer: customer, amount_cents: 1500, currency: 'USD', status: 'pending') }

  describe '#perform' do
    it 'transitions a pending payment to succeeded on gateway success' do
      described_class.new.perform(payment.id)
      expect(payment.reload.status).to eq('succeeded')
    end

    it 'is a no-op for non-pending payments' do
      payment.update!(status: 'failed')
      expect {
        described_class.new.perform(payment.id)
      }.not_to change { payment.reload.status }
    end
  end
end
