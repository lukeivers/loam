# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""D7 — conflict report schema + clause-(g) structural enforcement."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from loam.self_upgrade.conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    ConflictSummary,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)


def _sample_report() -> ConflictReport:
    return ConflictReport(
        upgrade_tag="pos-v2-v0.2.0",
        prior_tag="pos-v2-v0.1.0",
        detected_at="2026-04-19T14:23:11Z",
        conflicts=[
            ConflictEntry(
                path="framework/memory/upgrade.py",
                prior_release_sha256="a" * 64,
                installed_sha256="b" * 64,
                new_release_sha256="c" * 64,
                change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
                three_way_diff_path="~/.loam/framework/history/<tag>-conflicts/memory_upgrade.diff",
                resolution=Resolution.PENDING,
            ),
        ],
        summary=ConflictSummary(
            total_framework_files=1,
            unchanged=0,
            will_update_cleanly=0,
            conflicts_requiring_resolution=1,
            auto_resolved=0,
        ),
    )


def test_round_trip(tmp_path: Path) -> None:
    r = _sample_report()
    p = tmp_path / "conflicts.yaml"
    save_conflict_report(r, p)
    reloaded = load_conflict_report(p)
    assert reloaded == r


def test_skipped_resolution_rejected_at_schema(tmp_path: Path) -> None:
    """Clause (g) — the literal acceptance criterion.

    A YAML document with resolution: skipped must fail validation.
    """
    bad = {
        "upgrade_tag": "pos-v2-v0.2.0",
        "detected_at": "2026-04-19T14:23:11Z",
        "conflicts": [
            {
                "path": "framework/a.py",
                "prior_release_sha256": "a" * 64,
                "installed_sha256": "b" * 64,
                "new_release_sha256": "c" * 64,
                "change_kind": "upstream_modified_and_local_modified",
                "resolution": "skipped",
            },
        ],
        "summary": {},
    }
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(bad))

    with pytest.raises(ValidationError) as exc:
        load_conflict_report(p)
    assert "skipped" in str(exc.value).lower()


def test_resolution_enum_has_no_skipped_value() -> None:
    """Clause (g) structural: the enum itself does not contain it."""
    assert "skipped" not in {r.value for r in Resolution}
    assert "SKIPPED" not in {r.name for r in Resolution}


def test_three_way_merge_requires_resolved_content_path() -> None:
    with pytest.raises(ValidationError):
        ConflictEntry(
            path="framework/a.py",
            prior_release_sha256="a" * 64,
            installed_sha256="b" * 64,
            new_release_sha256="c" * 64,
            change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
            resolution=Resolution.THREE_WAY_MERGE,
        )


def test_auto_accept_requires_matching_change_kind() -> None:
    with pytest.raises(ValidationError):
        ConflictEntry(
            path="framework/a.py",
            prior_release_sha256="a" * 64,
            installed_sha256="b" * 64,
            new_release_sha256="c" * 64,
            change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
            resolution=Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM,
        )


def test_has_pending_and_has_abort() -> None:
    r = _sample_report()
    assert r.has_pending() is True
    assert r.has_abort() is False
    assert r.unresolved_paths() == ["framework/memory/upgrade.py"]

    r.conflicts[0].resolution = Resolution.ABORT
    assert r.has_pending() is False
    assert r.has_abort() is True


def test_abort_resolution_valid() -> None:
    e = ConflictEntry(
        path="framework/a.py",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.ABORT,
    )
    assert e.resolution is Resolution.ABORT


def test_accept_upstream_resolution_valid() -> None:
    e = ConflictEntry(
        path="framework/a.py",
        prior_release_sha256="a" * 64,
        installed_sha256="b" * 64,
        new_release_sha256="c" * 64,
        change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
        resolution=Resolution.ACCEPT_UPSTREAM,
    )
    assert e.resolution is Resolution.ACCEPT_UPSTREAM
