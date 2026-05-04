# SYNTHETIC TEST FIXTURE — see ../../../../README.md
# RECOGNIZER: concerns — module + extend ActiveSupport::Concern.
module Auditable
  extend ActiveSupport::Concern

  included do
    after_save :record_audit_entry
  end

  private

  def record_audit_entry
    AuditEntry.create!(record_type: self.class.name, record_id: id)
  end
end
