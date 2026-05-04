# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: minitest_tests (1 test block → 1 VERIFIED AC).
require 'test_helper'

class PaymentFlowTest < ActionDispatch::IntegrationTest
  test 'full payment flow' do
    post '/payments', params: { payment: { amount_cents: 1000 } }
    assert_response :created
  end
end
