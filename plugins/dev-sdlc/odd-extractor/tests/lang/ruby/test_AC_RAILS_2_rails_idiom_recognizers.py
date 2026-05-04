"""AC.RAILS.2 — Rails-idiom recognizers (six idioms).

Verifies each recognizer fires on its target idiom (positive) and
does not fire on unrelated patterns (negative). Uses the synthetic
fixture as the integration target; each recognizer also has a
hand-authored micro-snippet test for isolated verification.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.bands import BandedAC, ConfidenceBand
from loam_odd_extractor.lang.ruby.parser import parse_file, parse_source
from loam_odd_extractor.lang.ruby.recognizers import (
    recognize_active_record_models,
    recognize_callbacks,
    recognize_concerns,
    recognize_jobs,
    recognize_migrations,
    recognize_polymorphic_associations,
    recognize_routes,
)
from loam_odd_extractor.lang.ruby.recognizers.migrations import (
    is_migration_file,
)
from loam_odd_extractor.lang.ruby.recognizers.routes import (
    is_routes_file,
)


# ---- ActiveRecord -------------------------------------------------


def test_active_record_finds_model(synthetic_rails_repo: Path) -> None:
    rb = synthetic_rails_repo / "app" / "models" / "payment.rb"
    tree, src = parse_file(rb)
    out = recognize_active_record_models(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    # Should produce: 1 model + 1 belongs_to + 1 validates.
    names = [a.text for a in out]
    assert any(
        "Payment is an ActiveRecord model" in n for n in names
    )
    assert any(
        "belongs_to :owner" in n for n in names
    )
    assert any(
        "validates :amount_cents" in n for n in names
    )
    for ac in out:
        assert ac.confidence is ConfidenceBand.PLAUSIBLE


def test_active_record_skips_non_models() -> None:
    src = b"class Payment\n  def call\n  end\nend\n"
    tree = parse_source(src)
    out = recognize_active_record_models(
        tree, src, Path("x.rb"), Path("/"), "deadbeef"
    )
    assert out == []


# ---- Callbacks ----------------------------------------------------


def test_callbacks_finds_before_save_and_after_create(
    synthetic_rails_repo: Path,
) -> None:
    rb = synthetic_rails_repo / "app" / "models" / "payment.rb"
    tree, src = parse_file(rb)
    out = recognize_callbacks(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    methods = {a.text for a in out}
    assert any("before_save :normalize_amount" in m for m in methods)
    assert any("after_create :enqueue_webhook_job" in m for m in methods)
    for ac in out:
        assert ac.confidence is ConfidenceBand.PLAUSIBLE


def test_callbacks_skips_non_active_record_classes() -> None:
    """Callbacks recognizer only fires inside ActiveRecord-model classes."""
    src = b"""
class FooService
  before_save :do_thing
end
"""
    tree = parse_source(src)
    out = recognize_callbacks(
        tree, src, Path("x.rb"), Path("/"), "deadbeef"
    )
    assert out == []


# ---- Concerns -----------------------------------------------------


def test_concerns_finds_definition(synthetic_rails_repo: Path) -> None:
    rb = (
        synthetic_rails_repo
        / "app"
        / "models"
        / "concerns"
        / "auditable.rb"
    )
    tree, src = parse_file(rb)
    out = recognize_concerns(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    assert any(
        "Auditable is an ActiveSupport::Concern" in a.text
        for a in out
    )


def test_concerns_finds_usage(synthetic_rails_repo: Path) -> None:
    rb = synthetic_rails_repo / "app" / "models" / "payment.rb"
    tree, src = parse_file(rb)
    out = recognize_concerns(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    assert any(
        "Payment includes Auditable" in a.text for a in out
    )


def test_concerns_skips_modules_without_extend() -> None:
    src = b"""
module Plain
  def foo; end
end
"""
    tree = parse_source(src)
    out = recognize_concerns(
        tree, src, Path("x.rb"), Path("/"), "deadbeef"
    )
    # No definition AC; no usage AC either (no class included).
    assert out == []


# ---- Polymorphic --------------------------------------------------


def test_polymorphic_finds_polymorphic_belongs_to(
    synthetic_rails_repo: Path,
) -> None:
    rb = synthetic_rails_repo / "app" / "models" / "payment.rb"
    tree, src = parse_file(rb)
    out = recognize_polymorphic_associations(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    assert len(out) == 1
    assert "polymorphic belongs_to :owner" in out[0].text
    assert out[0].confidence is ConfidenceBand.PLAUSIBLE


def test_polymorphic_skips_non_polymorphic_belongs_to() -> None:
    src = b"""
class A
  belongs_to :user
end
"""
    tree = parse_source(src)
    out = recognize_polymorphic_associations(
        tree, src, Path("x.rb"), Path("/"), "deadbeef"
    )
    assert out == []


# ---- Jobs ---------------------------------------------------------


def test_jobs_finds_active_job(synthetic_rails_repo: Path) -> None:
    rb = (
        synthetic_rails_repo
        / "app"
        / "jobs"
        / "payment_webhook_job.rb"
    )
    tree, src = parse_file(rb)
    out = recognize_jobs(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    job_acs = [a for a in out if "is a ActiveJob job" in a.text]
    queue_acs = [a for a in out if "queue_as" in a.text]
    assert len(job_acs) == 1
    assert len(queue_acs) == 1


def test_jobs_finds_sidekiq_worker(synthetic_rails_repo: Path) -> None:
    rb = (
        synthetic_rails_repo
        / "app"
        / "jobs"
        / "sidekiq_metrics_worker.rb"
    )
    tree, src = parse_file(rb)
    out = recognize_jobs(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    job_acs = [a for a in out if "is a Sidekiq job" in a.text]
    queue_acs = [a for a in out if "Sidekiq queue" in a.text]
    assert len(job_acs) == 1
    assert len(queue_acs) == 1


def test_jobs_skips_plain_classes() -> None:
    src = b"class Plain; def call; end; end\n"
    tree = parse_source(src)
    out = recognize_jobs(
        tree, src, Path("x.rb"), Path("/"), "deadbeef"
    )
    assert out == []


# ---- Migrations ---------------------------------------------------


def test_migrations_finds_create_table_and_add_index(
    synthetic_rails_repo: Path,
) -> None:
    rb = (
        synthetic_rails_repo
        / "db"
        / "migrate"
        / "20260101000001_create_payments.rb"
    )
    tree, src = parse_file(rb)
    out = recognize_migrations(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    methods = {a.text for a in out}
    assert any("create_table :payments" in m for m in methods)
    assert any("add_index :payments" in m for m in methods)


def test_migrations_skips_non_migration_files(tmp_path: Path) -> None:
    """A `.rb` file outside ``db/migrate/`` returns []."""
    rb = tmp_path / "not_a_migration.rb"
    rb.write_text("create_table :foo\n", encoding="utf-8")
    tree, src = parse_file(rb)
    out = recognize_migrations(tree, src, rb, tmp_path, "deadbeef")
    assert out == []


def test_is_migration_file_path_check(tmp_path: Path) -> None:
    """File-path classification is correct."""
    p = tmp_path / "db" / "migrate" / "20260101_x.rb"
    p.parent.mkdir(parents=True)
    p.write_text("", encoding="utf-8")
    assert is_migration_file(p) is True
    assert (
        is_migration_file(tmp_path / "app" / "models" / "x.rb")
        is False
    )


# ---- Routes -------------------------------------------------------


def test_routes_finds_resources_namespace_get(
    synthetic_rails_repo: Path,
) -> None:
    rb = synthetic_rails_repo / "config" / "routes.rb"
    tree, src = parse_file(rb)
    out = recognize_routes(
        tree, src, rb, synthetic_rails_repo, "deadbeef"
    )
    methods = [a.text for a in out]
    assert any("resources :payments" in m for m in methods)
    assert any("namespace :api" in m for m in methods)
    assert any("get '/health'" in m for m in methods)


def test_routes_skips_non_routes_files(tmp_path: Path) -> None:
    """A `.rb` file not at ``config/routes.rb`` returns []."""
    rb = tmp_path / "other.rb"
    rb.write_text("get '/foo'\n", encoding="utf-8")
    tree, src = parse_file(rb)
    out = recognize_routes(tree, src, rb, tmp_path, "deadbeef")
    assert out == []


def test_is_routes_file_path_check(tmp_path: Path) -> None:
    p = tmp_path / "config" / "routes.rb"
    p.parent.mkdir(parents=True)
    p.write_text("", encoding="utf-8")
    assert is_routes_file(p) is True
    assert is_routes_file(tmp_path / "app" / "x.rb") is False
