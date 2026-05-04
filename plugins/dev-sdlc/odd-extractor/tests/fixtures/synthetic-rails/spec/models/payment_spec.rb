# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (3 it blocks → 3 VERIFIED ACs).
require 'rails_helper'

RSpec.describe Payment, type: :model do
  describe 'validations' do
    it 'validates amount_cents presence' do
      payment = Payment.new(amount_cents: nil)
      expect(payment).not_to be_valid
    end

    it 'normalizes amount before save' do
      payment = Payment.new(amount_cents: -100)
      payment.save
      expect(payment.amount_cents).to eq(100)
    end
  end

  describe 'callbacks' do
    it 'enqueues webhook job after create' do
      expect {
        Payment.create!(amount_cents: 500)
      }.to change(PaymentWebhookJob.jobs, :size).by(1)
    end
  end
end
