# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: active_record (model declaration + validations +
# associations); callbacks (before_save normalize_amount; after_create
# enqueue_processing_job); concerns (include Auditable +
# Timestampable); has_many through.
class Payment < ApplicationRecord
  include Auditable
  include Timestampable

  belongs_to :customer
  has_many :webhook_events, as: :owner, dependent: :destroy

  validates :amount_cents, presence: true,
                           numericality: { greater_than: 0 }
  validates :currency, presence: true, length: { is: 3 }
  validates :status, presence: true,
                     inclusion: { in: %w[pending processing succeeded failed refunded] }

  before_save :normalize_amount
  after_create :enqueue_processing_job

  scope :succeeded, -> { where(status: 'succeeded') }
  scope :pending, -> { where(status: 'pending') }

  def total_with_fees
    amount_cents + (amount_cents * fee_percentage).to_i
  end

  private

  def fee_percentage
    0.029
  end

  def normalize_amount
    self.amount_cents = amount_cents.to_i.abs
    self.currency = currency.to_s.upcase
  end

  def enqueue_processing_job
    ProcessPaymentJob.perform_async(id)
  end
end
