"""AC.RAILS.8 — Adapter unit tests against synthetic Rails snippets.

Hand-authored Ruby snippets exercise each recognizer in isolation
without requiring the full synthetic fixture. Per-snippet test:
positive case (recognizer detects the named pattern) AND negative
case (recognizer doesn't fire on unrelated code).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.lang.ruby.parser import parse_source
from loam_odd_extractor.lang.ruby.recognizers import (
    recognize_active_record_models,
    recognize_callbacks,
    recognize_concerns,
    recognize_jobs,
    recognize_polymorphic_associations,
)
from loam_odd_extractor.lang.ruby.heuristic_inferences import (
    infer_domain_rules,
)


# Each snippet test follows the pattern:
#   - positive: snippet contains the idiom; recognizer emits ≥ 1 AC.
#   - negative: snippet is plain Ruby without the idiom; recognizer
#     emits 0 ACs.


def test_active_record_positive_negative() -> None:
    pos_src = b"""
class Order < ApplicationRecord
  has_many :line_items
  validates :total_cents, presence: true
end
"""
    neg_src = b"""
class Order
  def call; end
end
"""
    tree = parse_source(pos_src)
    out = recognize_active_record_models(
        tree, pos_src, Path("o.rb"), Path("/"), "deadbeef"
    )
    assert len(out) >= 2  # model + has_many + validates → 3
    tree = parse_source(neg_src)
    out = recognize_active_record_models(
        tree, neg_src, Path("o.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_callbacks_positive_negative() -> None:
    pos_src = b"""
class Foo < ApplicationRecord
  before_save :do_thing
  after_destroy :cleanup
end
"""
    neg_src = b"""
class Foo < ApplicationRecord
  def normal_method; end
end
"""
    tree = parse_source(pos_src)
    out = recognize_callbacks(
        tree, pos_src, Path("f.rb"), Path("/"), "deadbeef"
    )
    methods = {a.text for a in out}
    assert any("before_save" in m for m in methods)
    assert any("after_destroy" in m for m in methods)
    tree = parse_source(neg_src)
    out = recognize_callbacks(
        tree, neg_src, Path("f.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_concerns_definition_positive_negative() -> None:
    pos_src = b"""
module Locatable
  extend ActiveSupport::Concern
end
"""
    neg_src = b"""
module Locatable
  def method; end
end
"""
    tree = parse_source(pos_src)
    out = recognize_concerns(
        tree, pos_src, Path("l.rb"), Path("/"), "deadbeef"
    )
    assert len(out) == 1  # Locatable definition
    tree = parse_source(neg_src)
    out = recognize_concerns(
        tree, neg_src, Path("l.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_polymorphic_positive_negative() -> None:
    pos_src = b"""
class Comment < ApplicationRecord
  belongs_to :commentable, polymorphic: true
end
"""
    neg_src = b"""
class Comment < ApplicationRecord
  belongs_to :user
end
"""
    tree = parse_source(pos_src)
    out = recognize_polymorphic_associations(
        tree, pos_src, Path("c.rb"), Path("/"), "deadbeef"
    )
    assert len(out) == 1
    tree = parse_source(neg_src)
    out = recognize_polymorphic_associations(
        tree, neg_src, Path("c.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_jobs_active_job_positive_negative() -> None:
    pos_src = b"""
class EmailJob < ApplicationJob
  queue_as :mailers
end
"""
    neg_src = b"""
class EmailService
  def perform; end
end
"""
    tree = parse_source(pos_src)
    out = recognize_jobs(
        tree, pos_src, Path("j.rb"), Path("/"), "deadbeef"
    )
    assert any("ActiveJob job" in a.text for a in out)
    # The queue_as text is rendered as "runs on queue :mailers".
    assert any(
        "queue :mailers" in a.text and "queue_as" in a.text
        for a in out
    )
    tree = parse_source(neg_src)
    out = recognize_jobs(
        tree, neg_src, Path("j.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_jobs_sidekiq_positive_negative() -> None:
    pos_src = b"""
class WorkerOne
  include Sidekiq::Worker
  sidekiq_options queue: :background
end

class WorkerTwo
  include Sidekiq::Job
end
"""
    neg_src = b"""
class WorkerThree
  include MyOwnModule
end
"""
    tree = parse_source(pos_src)
    out = recognize_jobs(
        tree, pos_src, Path("w.rb"), Path("/"), "deadbeef"
    )
    assert sum(1 for a in out if "Sidekiq job" in a.text) == 2
    tree = parse_source(neg_src)
    out = recognize_jobs(
        tree, neg_src, Path("w.rb"), Path("/"), "deadbeef"
    )
    assert out == []


def test_heuristic_uniqueness_inference() -> None:
    """The uniqueness heuristic (not exercised in the synthetic
    fixture) fires on a snippet."""
    from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence

    # Hand-construct a PLAUSIBLE AC matching the heuristic shape.
    plausible = BandedAC(
        ac_id="AC.RAILS.active_record.user.validates_uniqueness_of.email.x",
        text="User declares validates_uniqueness_of :email",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(kind="source", citations=["x.rb:1"]),
    )
    inferred = infer_domain_rules([plausible])
    assert any(
        "is unique across all User instances" in a.text
        for a in inferred
    )
    for ac in inferred:
        assert ac.confidence is ConfidenceBand.HYPOTHESISED
        assert "uniqueness-validator" in ac.evidence.rationale


def test_heuristic_required_on_create() -> None:
    """Presence-validator → required-on-create heuristic."""
    from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence

    plausible = BandedAC(
        ac_id="AC.RAILS.active_record.user.validates.email.x",
        text="User declares validates :email, presence: true",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(kind="source", citations=["x.rb:1"]),
    )
    inferred = infer_domain_rules([plausible])
    assert any(
        "User creation requires email to be present" in a.text
        for a in inferred
    )
