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

"""D7 — conflict report + structural clause-(g) enforcement.

When the manifest-diff step discovers a local file whose sha disagrees
with both the prior release sha AND the new release sha, the upgrade
emits a YAML conflict report at
``~/.loam/framework/history/<tag>-conflicts.yaml``. The report
enumerates every conflict with a ``resolution`` field the user must
set.

Clause (g) — "no silent skip" — is enforced **structurally**, not at
runtime. The ``Resolution`` enum below does not contain ``skipped``.
A YAML document that sets ``resolution: skipped`` fails Pydantic
validation when the upgrade CLI re-reads the file after user edits.
There is no code path that can accept a skipped resolution, because
the type does not exist.

Permitted resolutions:

- ``pending`` — user has not decided; upgrade blocks
- ``auto-accept-local-matches-upstream`` — installed sha == new-release
  sha already; deterministic auto-resolution
- ``accept-upstream`` — overwrite local edit with new release
- ``keep-local`` — preserve local edit, record workspace override
- ``three-way-merge`` — user supplies merged file content
- ``abort`` — cancel the upgrade entirely; no state change
- ``inferred-accept-canonical`` — clause-(h) LLM verdict: accept
  canonical content (rationale + confidence required)
- ``inferred-accept-workspace`` — clause-(h) LLM verdict: preserve
  workspace content (rationale + confidence required)
- ``inferred-merged`` — clause-(h) LLM verdict: take a synthesised
  merge (resolved_content_path + rationale + confidence required)

"skipped" is **deliberately not an option** — clause (g) extends to
clause (h): inferred resolutions never include "skipped".

Clause (h) extension fields on ``ConflictEntry``:

- ``rationale`` — free-text explanation from resolver or operator
- ``confidence`` — 0.0–1.0 float on the resolver's verdict
- ``user_override`` — bool flag; when True the entry was hand-edited
  by the operator after the resolver landed its verdict
- ``override_rationale`` — required when ``user_override=True``

The same conflicts YAML doubles as the clause-(h) audit log
(rationale + confidence per inferred entry; sortable
low-confidence-first via ``ConflictReport.sorted_low_confidence_first``).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Resolution(str, Enum):
    """Closed set of permitted conflict resolutions.

    Note the deliberate absence of ``skipped``. Clause (g)'s "no silent
    skip" is enforced at the schema level: a YAML document that sets
    ``resolution: skipped`` fails validation because the enum does not
    include that value.
    """

    PENDING = "pending"
    AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM = "auto-accept-local-matches-upstream"
    ACCEPT_UPSTREAM = "accept-upstream"
    KEEP_LOCAL = "keep-local"
    THREE_WAY_MERGE = "three-way-merge"
    ABORT = "abort"

    # Clause-(h) extensions — LLM-mediated semantic-merge verdicts.
    # All three carry rationale + confidence on the ConflictEntry;
    # INFERRED_MERGED additionally requires resolved_content_path
    # (same shape as THREE_WAY_MERGE).
    INFERRED_ACCEPT_CANONICAL = "inferred-accept-canonical"
    INFERRED_ACCEPT_WORKSPACE = "inferred-accept-workspace"
    INFERRED_MERGED = "inferred-merged"


# Resolutions whose verdict came from the clause-(h) LLM resolver.
# Each requires rationale + confidence on the ConflictEntry.
INFERRED_RESOLUTIONS: frozenset[Resolution] = frozenset(
    {
        Resolution.INFERRED_ACCEPT_CANONICAL,
        Resolution.INFERRED_ACCEPT_WORKSPACE,
        Resolution.INFERRED_MERGED,
    }
)


class ConflictChangeKind(str, Enum):
    """How a file's pre-install state diverges from expectation."""

    LOCAL_MODIFIED_ONLY = "local_modified_only"
    UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED = (
        "upstream_modified_and_local_modified"
    )
    LOCAL_MODIFIED_EQUALS_UPSTREAM = "local_modified_equals_upstream"


class ConflictEntry(BaseModel):
    """One conflicting framework file."""

    model_config = ConfigDict(extra="forbid")

    path: str
    prior_release_sha256: str | None
    installed_sha256: str | None
    new_release_sha256: str | None
    change_kind: ConflictChangeKind
    three_way_diff_path: str | None = None
    resolution: Resolution = Resolution.PENDING
    resolved_content_path: str | None = None

    # Clause-(h) extension fields. Required for INFERRED_* resolutions
    # (rationale + confidence) and user_override=True (override_rationale).
    rationale: str | None = None
    confidence: float | None = None
    user_override: bool = False
    override_rationale: str | None = None

    @model_validator(mode="after")
    def _resolution_requires(self) -> "ConflictEntry":
        r = self.resolution
        if r is Resolution.THREE_WAY_MERGE and not self.resolved_content_path:
            raise ValueError(
                f"{self.path}: resolution=three-way-merge requires "
                "resolved_content_path"
            )
        if (
            r is Resolution.AUTO_ACCEPT_LOCAL_MATCHES_UPSTREAM
            and self.change_kind is not ConflictChangeKind.LOCAL_MODIFIED_EQUALS_UPSTREAM
        ):
            raise ValueError(
                f"{self.path}: auto-accept-local-matches-upstream only "
                "valid when change_kind=local_modified_equals_upstream"
            )
        # Clause-(h) inferred resolutions require rationale + confidence.
        if r in INFERRED_RESOLUTIONS:
            if self.rationale is None or self.rationale.strip() == "":
                raise ValueError(
                    f"{self.path}: inferred resolution requires non-empty rationale"
                )
            if self.confidence is None:
                raise ValueError(
                    f"{self.path}: inferred resolution requires confidence (0.0-1.0)"
                )
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError(
                    f"{self.path}: confidence must be in [0.0, 1.0], "
                    f"got {self.confidence}"
                )
            if (
                r is Resolution.INFERRED_MERGED
                and not self.resolved_content_path
            ):
                raise ValueError(
                    f"{self.path}: resolution=inferred-merged requires "
                    "resolved_content_path"
                )
        # user_override demands override_rationale.
        if self.user_override and (
            self.override_rationale is None
            or self.override_rationale.strip() == ""
        ):
            raise ValueError(
                f"{self.path}: user_override=True requires override_rationale"
            )
        return self

    @field_validator("resolution", mode="before")
    @classmethod
    def _reject_skipped(cls, v: Any) -> Any:
        """Structural clause (g) enforcement.

        The enum itself would already reject 'skipped' because the
        value is not present; this validator makes the error message
        explicit so users who try it understand *why* it is rejected.
        """
        if isinstance(v, str) and v.strip().lower() == "skipped":
            raise ValueError(
                "resolution 'skipped' is structurally forbidden "
                "(clause g: no silent skip). Choose one of: "
                "pending, accept-upstream, keep-local, three-way-merge, abort."
            )
        return v


class ConflictSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_framework_files: int = 0
    unchanged: int = 0
    will_update_cleanly: int = 0
    conflicts_requiring_resolution: int = 0
    auto_resolved: int = 0


class ConflictReport(BaseModel):
    """Root of ``<tag>-conflicts.yaml``."""

    model_config = ConfigDict(extra="forbid")

    upgrade_tag: str
    prior_tag: str | None = None
    detected_at: str
    conflicts: list[ConflictEntry] = Field(default_factory=list)
    summary: ConflictSummary = Field(default_factory=ConflictSummary)

    def has_pending(self) -> bool:
        return any(c.resolution is Resolution.PENDING for c in self.conflicts)

    def has_abort(self) -> bool:
        return any(c.resolution is Resolution.ABORT for c in self.conflicts)

    def unresolved_paths(self) -> list[str]:
        return [
            c.path
            for c in self.conflicts
            if c.resolution is Resolution.PENDING
        ]

    def sorted_low_confidence_first(self) -> list[ConflictEntry]:
        """Return conflicts ordered low-confidence-first then path-asc.

        Entries without a confidence (manual resolutions or PENDING) sort
        last; entries with confidence sort by ascending confidence so a
        reviewer scanning the audit sees the most-uncertain verdicts
        first. Stable secondary sort on path provides deterministic
        ordering inside each confidence bucket.
        """
        return sorted(
            self.conflicts,
            key=lambda c: (
                c.confidence is None,
                c.confidence if c.confidence is not None else 0.0,
                c.path,
            ),
        )

    def inferred_entries(self) -> list[ConflictEntry]:
        """Return conflicts whose resolution came from the clause-(h)
        resolver."""
        return [
            c
            for c in self.conflicts
            if c.resolution in INFERRED_RESOLUTIONS
        ]

    def as_yaml(self) -> str:
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            default_flow_style=False,
            sort_keys=False,
        )


def load_conflict_report(path: str | Path) -> ConflictReport:
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: top-level must be a mapping")
    return ConflictReport.model_validate(raw)


def save_conflict_report(report: ConflictReport, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(report.as_yaml())
