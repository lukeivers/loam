# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: rspec_tests (3 it blocks → 3 VERIFIED ACs).
require 'rails_helper'

RSpec.describe Customer, type: :model do
  describe 'validations' do
    it 'requires unique email (case-insensitive)' do
      Customer.create!(email: 'a@b.com', name: 'A', password: 'secret123')
      duplicate = Customer.new(email: 'A@B.COM', name: 'B', password: 'secret123')
      expect(duplicate).not_to be_valid
    end

    it 'requires email in valid format' do
      bad = Customer.new(email: 'not-an-email', name: 'X', password: 'secret123')
      expect(bad).not_to be_valid
    end
  end

  describe 'callbacks' do
    it 'normalizes email to lowercase before validation' do
      c = Customer.create!(email: 'MIXED@Case.com', name: 'X', password: 'secret123')
      expect(c.email).to eq('mixed@case.com')
    end
  end
end
