# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: concerns (extend ActiveSupport::Concern + included
# do block); after_create callback on the host model.
module Auditable
  extend ActiveSupport::Concern

  included do
    after_create :record_audit_log
  end

  private

  def record_audit_log
    AuditLog.create!(
      record_type: self.class.name,
      record_id: id,
      event: 'created',
      occurred_at: Time.current
    )
  end
end
