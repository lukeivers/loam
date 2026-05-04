# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: active_record (model declaration + validations +
# associations + has_secure_password auth); callbacks
# (before_validation normalize_email); concerns (include Auditable);
# uniqueness validation drives a HYPOTHESISED inferred AC.
class Customer < ApplicationRecord
  include Auditable

  has_secure_password

  has_many :payments, dependent: :destroy
  has_many :webhook_events, as: :owner, dependent: :destroy

  validates :email, presence: true,
                    uniqueness: { case_sensitive: false },
                    format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :name, presence: true, length: { maximum: 120 }

  before_validation :normalize_email

  scope :active, -> { where(suspended: false) }

  def primary_payment_method
    payments.succeeded.order(created_at: :desc).first
  end

  def suspend!
    update!(suspended: true, suspended_at: Time.current)
  end

  private

  def normalize_email
    self.email = email.to_s.downcase.strip if email.present?
  end
end
