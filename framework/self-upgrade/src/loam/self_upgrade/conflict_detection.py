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

"""Pre-install conflict detection (clause g operational path).

For every file in the manifest with expected_pre_sha set, the framework
compares ``sha256(live_file)`` against ``expected_pre_sha``:

- matches expected_pre_sha → update cleanly (will overwrite on swap)
- matches expected_post_sha → ``auto-accept-local-matches-upstream``
- disagrees with both → conflict, user must resolve in the YAML

Resolutions permitted are in ``ConflictReport.Resolution`` (enum
does NOT contain 'skipped' — clause g structural).

Workflow:

1. ``detect_conflicts(manifest, live_root)`` → ConflictReport
2. If the report has any PENDING resolutions, framework writes the
   YAML to ``~/.loam/framework/history/<tag>-conflicts.yaml`` and
   halts.
3. User edits the YAML to set each pending entry's resolution.
4. User re-runs ``pos upgrade <tag>`` which reloads the YAML,
   re-validates schema (rejecting 'skipped' at parse time), and
   proceeds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    ConflictSummary,
    Resolution,
)
from .manifest import ChangeKind, Manifest, sha256_of_file


def detect_conflicts(
    manifest: Manifest, live_root: Path, prior_tag: str | None = None
) -> ConflictReport:
    """Inspect every file in the manifest against the live tree.

    Files with no expected_pre_sha (new files in this release) are
    expected to be absent in live_root — if present, they count as a
    conflict. Files with expected_pre_sha must match it; if they don't,
    the sha comparison decides the change_kind.
    """
    conflicts: list[ConflictEntry] = []
    unchanged = 0
    will_update = 0
    auto_resolved = 0

    for f in manifest.files:
        target = live_root / f.path
        live_sha = sha256_of_file(target) if target.exists() else None

        if f.change_kind is ChangeKind.NEW:
            if live_sha is None:
                # Expected: file doesn't exist yet
                will_update += 1
                continue
            if live_sha == f.expected_post_sha:
                # Already present at the right sha — auto-resolvable
                auto_resolved += 1
                conflicts.append(
                    ConflictEntry(
                        path=f.path,
                        prior_release_sha256=None,
                        installed_sha256=live_sha,
                        new_release_sha256=f.expected_post_sha,
                        change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
                        resolution=Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM,
                    )
                )
                continue
            # Unexpected file at an unexpected sha
            conflicts.append(
                ConflictEntry(
                    path=f.path,
                    prior_release_sha256=None,
                    installed_sha256=live_sha,
                    new_release_sha256=f.expected_post_sha,
                    change_kind=ConflictChangeKind.LOCAL_MODIFIED_ONLY,
                    resolution=Resolution.PENDING,
                )
            )
            continue

        if f.change_kind is ChangeKind.DELETED:
            if live_sha is None:
                # Already absent — clean
                will_update += 1
                continue
            if live_sha == f.expected_pre_sha:
                will_update += 1
                continue
            conflicts.append(
                ConflictEntry(
                    path=f.path,
                    prior_release_sha256=f.expected_pre_sha,
                    installed_sha256=live_sha,
                    new_release_sha256=None,
                    change_kind=ConflictChangeKind.LOCAL_MODIFIED_ONLY,
                    resolution=Resolution.PENDING,
                )
            )
            continue

        if f.change_kind is ChangeKind.UNCHANGED:
            if live_sha == f.expected_pre_sha:
                unchanged += 1
                continue
            # File is in the "unchanged" manifest but live diverged
            conflicts.append(
                ConflictEntry(
                    path=f.path,
                    prior_release_sha256=f.expected_pre_sha,
                    installed_sha256=live_sha,
                    new_release_sha256=f.expected_post_sha,
                    change_kind=ConflictChangeKind.LOCAL_MODIFIED_ONLY,
                    resolution=Resolution.PENDING,
                )
            )
            continue

        # MODIFIED: we expect live_sha == expected_pre_sha; apply plans
        # to swap to expected_post_sha.
        if live_sha == f.expected_pre_sha:
            will_update += 1
            continue
        if live_sha == f.expected_post_sha:
            # Someone already applied this file locally
            auto_resolved += 1
            conflicts.append(
                ConflictEntry(
                    path=f.path,
                    prior_release_sha256=f.expected_pre_sha,
                    installed_sha256=live_sha,
                    new_release_sha256=f.expected_post_sha,
                    change_kind=ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM,
                    resolution=Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM,
                )
            )
            continue
        # Both local edit AND upstream change — conflict
        conflicts.append(
            ConflictEntry(
                path=f.path,
                prior_release_sha256=f.expected_pre_sha,
                installed_sha256=live_sha,
                new_release_sha256=f.expected_post_sha,
                change_kind=ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
                resolution=Resolution.PENDING,
            )
        )

    summary = ConflictSummary(
        total_framework_files=len(manifest.files),
        unchanged=unchanged,
        will_update_cleanly=will_update,
        conflicts_requiring_resolution=sum(
            1 for c in conflicts if c.resolution is Resolution.PENDING
        ),
        auto_resolved=sum(
            1
            for c in conflicts
            if c.resolution
            is Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM
        ),
    )
    return ConflictReport(
        upgrade_tag=manifest.release_tag,
        prior_tag=prior_tag,
        detected_at=datetime.now(timezone.utc).isoformat(),
        conflicts=conflicts,
        summary=summary,
    )
