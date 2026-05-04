# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: rspec_tests (1 it block → 1 VERIFIED AC).
require 'rails_helper'

RSpec.describe Api::PaymentsController, type: :controller do
  let(:customer) { Customer.create!(email: 'ctrl@x.com', name: 'X', password: 'secret123') }

  describe 'POST #create' do
    it 'creates a payment for the authenticated customer' do
      sign_in_as(customer)
      post :create, params: { payment: { amount_cents: 200, currency: 'USD' } }
      expect(response).to have_http_status(:created)
    end
  end
end
