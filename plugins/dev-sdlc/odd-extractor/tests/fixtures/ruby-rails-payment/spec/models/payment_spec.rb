# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (4 it blocks → 4 VERIFIED ACs).
require 'rails_helper'

RSpec.describe Payment, type: :model do
  let(:customer) { Customer.create!(email: 'a@b.com', name: 'A B', password: 'secret123') }

  describe 'validations' do
    it 'requires amount_cents' do
      payment = Payment.new(customer: customer, amount_cents: nil, currency: 'USD', status: 'pending')
      expect(payment).not_to be_valid
    end

    it 'requires positive amount_cents' do
      payment = Payment.new(customer: customer, amount_cents: 0, currency: 'USD', status: 'pending')
      expect(payment).not_to be_valid
    end
  end

  describe 'callbacks' do
    it 'normalizes currency to uppercase' do
      payment = Payment.create!(customer: customer, amount_cents: 100, currency: 'usd', status: 'pending')
      expect(payment.currency).to eq('USD')
    end

    it 'enqueues processing job after create' do
      expect {
        Payment.create!(customer: customer, amount_cents: 500, currency: 'USD', status: 'pending')
      }.to change(ProcessPaymentJob.jobs, :size).by(1)
    end
  end
end
