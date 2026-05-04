# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (3 it blocks → 3 VERIFIED ACs).
require 'rails_helper'

RSpec.describe WebhookEvent, type: :model do
  let(:customer) { Customer.create!(email: 'c@d.com', name: 'C D', password: 'secret123') }
  let(:payment) { Payment.create!(customer: customer, amount_cents: 100, currency: 'USD', status: 'succeeded') }

  describe 'polymorphic association' do
    it 'can belong to a Payment' do
      event = WebhookEvent.create!(owner: payment, event_type: 'payment.succeeded', payload: { id: payment.id })
      expect(event.owner).to eq(payment)
      expect(event.owner_type).to eq('Payment')
    end

    it 'can belong to a Customer' do
      event = WebhookEvent.create!(owner: customer, event_type: 'customer.created', payload: { id: customer.id })
      expect(event.owner).to eq(customer)
      expect(event.owner_type).to eq('Customer')
    end
  end

  describe 'callbacks' do
    it 'enqueues dispatcher job after create' do
      expect {
        WebhookEvent.create!(owner: payment, event_type: 'payment.succeeded', payload: { id: 1 })
      }.to change(PaymentWebhookDispatcherJob.jobs, :size).by(1)
    end
  end
end
