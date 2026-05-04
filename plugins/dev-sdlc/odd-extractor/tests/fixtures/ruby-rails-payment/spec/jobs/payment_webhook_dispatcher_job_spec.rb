# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (2 it blocks → 2 VERIFIED ACs).
require 'rails_helper'

RSpec.describe PaymentWebhookDispatcherJob, type: :job do
  let(:customer) { Customer.create!(email: 'w@x.com', name: 'W X', password: 'secret123') }
  let(:payment) { Payment.create!(customer: customer, amount_cents: 1, currency: 'USD', status: 'succeeded') }
  let(:event) { WebhookEvent.create!(owner: payment, event_type: 'payment.succeeded', payload: { id: payment.id }) }

  describe '#perform' do
    it 'marks the event as dispatched' do
      described_class.new.perform(event.id)
      expect(event.reload).to be_dispatched
    end

    it 'is a no-op when the event is already dispatched' do
      event.update!(dispatched_at: 1.hour.ago)
      expect {
        described_class.new.perform(event.id)
      }.not_to change { event.reload.dispatched_at }
    end
  end
end
