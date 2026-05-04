# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: concerns (extend ActiveSupport::Concern + included
# do block); before_save callback on the host model.
module Timestampable
  extend ActiveSupport::Concern

  included do
    before_save :update_seen_at
  end

  private

  def update_seen_at
    self.seen_at = Time.current if respond_to?(:seen_at=)
  end
end
