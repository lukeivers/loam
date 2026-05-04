# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: active_record (model declaration + validations +
# polymorphic association); callbacks (before_save serialize_payload;
# after_create enqueue_dispatch); polymorphic (belongs_to :owner,
# polymorphic: true) — drives PLAUSIBLE+HYPOTHESISED inferred ACs.
class WebhookEvent < ApplicationRecord
  belongs_to :owner, polymorphic: true

  validates :event_type, presence: true,
                         inclusion: { in: %w[
                           payment.succeeded
                           payment.failed
                           payment.refunded
                           customer.created
                           customer.suspended
                         ] }
  validates :payload, presence: true

  before_save :serialize_payload
  after_create :enqueue_dispatch

  scope :pending_dispatch, -> { where(dispatched_at: nil) }
  scope :for_owner_type, ->(t) { where(owner_type: t) }

  def dispatched?
    dispatched_at.present?
  end

  private

  def serialize_payload
    self.payload = payload.to_json if payload.is_a?(Hash)
  end

  def enqueue_dispatch
    PaymentWebhookDispatcherJob.perform_async(id)
  end
end
