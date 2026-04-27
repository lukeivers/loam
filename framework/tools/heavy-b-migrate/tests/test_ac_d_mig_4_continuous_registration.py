"""AC.D-mig.4 — continuous registration via pos-amend post-Phase-γ.

A fixture amendment is registered via ``pos-amend``'s public
``register_objectives`` + ``update_source_commits`` helpers (the
same surface ``pos-amend apply`` and ``pos-amend seal`` invoke). The
fixture's ACs appear in the tracker; ``source_commit`` is populated
by the seal step.

Composes against the actual pos-amend tracker_registration helper
(per builder-plan §3 fence: heavy-b-migrate is dev-discipline; pos-
amend is dev-discipline; the cross-tool import is in scope).
"""

from __future__ import annotations

from heavy_b_migrate.verify import verify_continuous_registration


def test_verify_continuous_registration_passes() -> None:
    report = verify_continuous_registration()
    assert report.failure_reason is None, report.failure_reason
    assert report.registered_count == 1
    assert report.source_commit_updated_count == 1
    assert report.contributor_surfaces_record is True
