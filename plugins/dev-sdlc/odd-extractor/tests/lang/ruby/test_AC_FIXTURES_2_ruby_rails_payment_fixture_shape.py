"""AC.FIXTURES.2 (v0.1.8 Cycle 4b) — canonical ruby-rails-payment
fixture file-tree + content sanity checks.

Verifies the canonical fixture exposes the master plan AC.FIXTURES.2
shape (5–10 routes + 3 ActiveRecord models with callbacks/concerns/
polymorphic + 2 Sidekiq jobs + ≥10 RSpec specs + LICENSE + README +
Gemfile + migrations).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


FIXTURE_ROOT = (
    Path(__file__).parent.parent.parent / "fixtures" / "ruby-rails-payment"
)


def test_fixture_directory_exists() -> None:
    assert FIXTURE_ROOT.is_dir(), (
        f"Canonical Ruby fixture missing at {FIXTURE_ROOT}"
    )


def test_fixture_has_at_least_18_files() -> None:
    """AC.FIXTURES.2 floor — fixture is shape-rich (5–10 routes +
    3 models + 2 concerns + 2 jobs + 3 controllers + 3 migrations +
    ≥6 RSpec specs + Gemfile + README + LICENSE + routes.rb).
    """
    files = [p for p in FIXTURE_ROOT.rglob("*") if p.is_file()]
    assert len(files) >= 18, (
        f"Canonical fixture has {len(files)} files; expected ≥18"
    )


@pytest.mark.parametrize(
    "rel_path",
    [
        "Gemfile",
        "LICENSE",
        "README.md",
        "config/routes.rb",
        "app/models/payment.rb",
        "app/models/customer.rb",
        "app/models/webhook_event.rb",
        "app/models/concerns/auditable.rb",
        "app/models/concerns/timestampable.rb",
        "app/jobs/process_payment_job.rb",
        "app/jobs/payment_webhook_dispatcher_job.rb",
        "app/controllers/api/payments_controller.rb",
        "app/controllers/api/customers_controller.rb",
        "app/controllers/api/webhook_events_controller.rb",
        "db/migrate/20260101000001_create_payments.rb",
        "db/migrate/20260101000002_create_customers.rb",
        "db/migrate/20260101000003_create_webhook_events.rb",
        "spec/models/payment_spec.rb",
        "spec/models/customer_spec.rb",
        "spec/models/webhook_event_spec.rb",
        "spec/jobs/process_payment_job_spec.rb",
        "spec/jobs/payment_webhook_dispatcher_job_spec.rb",
        "spec/controllers/api/payments_controller_spec.rb",
    ],
)
def test_fixture_has_named_file(rel_path: str) -> None:
    assert (FIXTURE_ROOT / rel_path).is_file(), (
        f"Canonical fixture missing required file: {rel_path}"
    )


def test_readme_has_synthetic_banner() -> None:
    """README must clearly label the fixture as SYNTHETIC."""
    readme = (FIXTURE_ROOT / "README.md").read_text()
    # "SYNTHETIC" appears as a banner near the top.
    assert "SYNTHETIC" in readme, "README missing SYNTHETIC banner"


def test_license_is_apache_2() -> None:
    """LICENSE is non-empty + recognisable Apache-2.0 header."""
    license_text = (FIXTURE_ROOT / "LICENSE").read_text()
    assert license_text.strip(), "LICENSE is empty"
    assert "Apache License" in license_text, (
        "LICENSE missing 'Apache License' header"
    )
    assert "Version 2.0" in license_text, (
        "LICENSE missing 'Version 2.0' line"
    )


def test_gemfile_declares_required_gems() -> None:
    """Gemfile names the master plan AC.FIXTURES.2 gem set: rails,
    rspec, sidekiq.
    """
    gemfile = (FIXTURE_ROOT / "Gemfile").read_text()
    assert re.search(r"^gem 'rails'", gemfile, re.MULTILINE), (
        "Gemfile missing rails"
    )
    assert "rspec-rails" in gemfile, "Gemfile missing rspec-rails"
    assert "sidekiq" in gemfile, "Gemfile missing sidekiq"
    assert "bcrypt" in gemfile, "Gemfile missing bcrypt"


def test_routes_file_declares_at_least_4_resources() -> None:
    """config/routes.rb has 5–10 RESTful routes (master plan
    AC.FIXTURES.2 floor).
    """
    routes = (FIXTURE_ROOT / "config" / "routes.rb").read_text()
    resources = re.findall(r"resources :\w+", routes)
    assert len(resources) >= 4, (
        f"routes.rb has {len(resources)} resources; expected ≥4"
    )


def test_at_least_10_rspec_it_blocks() -> None:
    """AC.FIXTURES.2 floor — ≥10 ``it`` blocks across spec files
    (drives the test-first VERIFIED-band ACs).
    """
    spec_files = list((FIXTURE_ROOT / "spec").rglob("*_spec.rb"))
    assert len(spec_files) > 0, "No RSpec spec files found"
    total_it = 0
    for f in spec_files:
        text = f.read_text()
        # Count `it 'foo' do` or `it "foo" do` lines.
        total_it += len(re.findall(r"^\s*it [\"']", text, re.MULTILINE))
    assert total_it >= 10, (
        f"Only {total_it} `it` blocks across spec files; "
        f"AC.FIXTURES.2 requires ≥10"
    )


def test_at_least_one_polymorphic_belongs_to() -> None:
    """AC.FIXTURES.2 — polymorphic association declared on at least
    one model (drives polymorphic inference HYPOTHESISED AC).
    """
    models_dir = FIXTURE_ROOT / "app" / "models"
    found = False
    for model_file in models_dir.rglob("*.rb"):
        text = model_file.read_text()
        if re.search(r"belongs_to\s+:\w+,\s+polymorphic:\s+true", text):
            found = True
            break
    assert found, (
        "No polymorphic belongs_to declaration found in canonical "
        "fixture's models"
    )


def test_at_least_one_sidekiq_job() -> None:
    """AC.FIXTURES.2 — at least 2 Sidekiq jobs (the master plan floor)."""
    jobs_dir = FIXTURE_ROOT / "app" / "jobs"
    job_files = list(jobs_dir.glob("*.rb"))
    assert len(job_files) >= 2, (
        f"Only {len(job_files)} job files; expected ≥2"
    )
    for f in job_files:
        text = f.read_text()
        assert "include Sidekiq::Job" in text, (
            f"{f.name} missing include Sidekiq::Job"
        )


def test_concerns_declare_active_support_concern() -> None:
    """AC.FIXTURES.2 — ≥2 concerns under app/models/concerns/, each
    extending ActiveSupport::Concern.
    """
    concerns_dir = FIXTURE_ROOT / "app" / "models" / "concerns"
    concern_files = list(concerns_dir.glob("*.rb"))
    assert len(concern_files) >= 2, (
        f"Only {len(concern_files)} concern files; expected ≥2"
    )
    for f in concern_files:
        text = f.read_text()
        assert "extend ActiveSupport::Concern" in text, (
            f"{f.name} missing extend ActiveSupport::Concern"
        )


def test_callbacks_present_across_models() -> None:
    """AC.FIXTURES.2 — at least 3 callback declarations across
    Payment / Customer / WebhookEvent (drives callback-based
    HYPOTHESISED inferences).
    """
    models_dir = FIXTURE_ROOT / "app" / "models"
    callback_count = 0
    for model_file in models_dir.glob("*.rb"):
        text = model_file.read_text()
        callback_count += len(re.findall(
            r"\b(before_validation|before_save|after_create|after_save|after_commit)\b\s+:",
            text,
        ))
    assert callback_count >= 3, (
        f"Only {callback_count} callbacks across models; expected ≥3"
    )
