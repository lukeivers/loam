# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: active_record (model declaration + validation +
# associations); callbacks (before_save / after_create);
# concerns (include Auditable usage); polymorphic (belongs_to
# :owner, polymorphic: true).
class Payment < ApplicationRecord
  include Auditable

  belongs_to :owner, polymorphic: true

  validates :amount_cents, presence: true

  before_save :normalize_amount
  after_create :enqueue_webhook_job

  private

  def normalize_amount
    self.amount_cents = amount_cents.to_i.abs
  end

  def enqueue_webhook_job
    PaymentWebhookJob.perform_later(id)
  end
end
