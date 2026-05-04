"""Conflict detection + InstallResult shape for loam-pr-safety
installers.

Per plan-doc §5 Surfaces #2 + #3 — sentinel-comment-based loam-managed
detection, with a separate `start..end` block delimiter for files
that may legitimately have non-loam content alongside loam's snippet
(.gitlab-ci.yml, .circleci/config.yml).

Per plan-doc §6 — :class:`InstallResult` is the typed return from
each installer. Its ``action`` discriminates between created /
refreshed / noop / conflict-halted / force-replaced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from loam_pr_safety.errors import PRSafetyError


# The current loam-pr-safety version — propagated into sentinel
# comments. Bumped when Cycle 2 lands (0.1.0 → 0.2.0). Source:
# pyproject.toml.
LOAM_PR_SAFETY_VERSION = "0.2.0"


# Sentinel patterns (Surface #2 + Surface #3).
_SENTINEL_RE = re.compile(
    r"loam-pr-safety:managed:(?P<version>[\d.]+)",
)
_SENTINEL_BLOCK_START_RE = re.compile(
    r"^[#\s]*loam-pr-safety:managed:start:(?P<version>[\d.]+)",
    re.MULTILINE,
)
_SENTINEL_BLOCK_END_RE = re.compile(
    r"^[#\s]*loam-pr-safety:managed:end\s*$",
    re.MULTILINE,
)


def detect_loam_managed(content: str) -> str | None:
    """Return the version string if ``content`` carries the loam
    sentinel comment; else ``None``.

    Per Surface #2 — sentinel is detectable via regex; matches:

      - ``# loam-pr-safety:managed:0.2.0`` (shell / YAML)
      - ``<!-- loam-pr-safety:managed:0.2.0 -->`` (markdown)

    The first match wins.
    """
    if not content:
        return None
    m = _SENTINEL_RE.search(content)
    return m.group("version") if m else None


def detect_loam_managed_block(content: str) -> tuple[int, int, str] | None:
    """For YAML files with ``managed:start..end`` block delimiters,
    return ``(start_offset, end_offset, version)`` of the loam-managed
    region. Returns ``None`` if no block found.

    Per Surface #3 — used for .gitlab-ci.yml / .circleci/config.yml
    where loam's snippet may co-exist with non-loam content.

    The end-offset includes the ``loam-pr-safety:managed:end`` line
    itself (so replacing ``content[start:end]`` substitutes the
    complete loam region).
    """
    if not content:
        return None
    start_m = _SENTINEL_BLOCK_START_RE.search(content)
    if start_m is None:
        return None
    # Search for end after the start match.
    end_m = _SENTINEL_BLOCK_END_RE.search(content, start_m.end())
    if end_m is None:
        return None
    return (start_m.start(), end_m.end(), start_m.group("version"))


_NON_TRIVIAL_LINE_RE = re.compile(r"^\s*[^#\s].*$", re.MULTILINE)


def is_effectively_empty(content: str) -> bool:
    """Return ``True`` iff ``content`` has no non-whitespace,
    non-comment lines.

    Per Surface #3 — informs the conflict-halt rule. Pure-comment
    files are considered effectively-empty (safe to overwrite).
    Markdown files with `<!-- comments only -->` are NOT considered
    empty (markdown comments are a content choice, not boilerplate).
    """
    if not content or not content.strip():
        return True
    # Strip shell/YAML comments — lines starting with `#` after
    # optional whitespace.
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        return False
    return True


@dataclass
class InstallResult:
    """Typed return from each installer.

    Per plan-doc §6.

    ``surface`` discriminates which installer produced this result.
    ``action`` discriminates the outcome:

      - ``created`` — new file written.
      - ``refreshed`` — loam-managed file rewritten with new version.
      - ``noop`` — loam-managed file already at current version;
        no write.
      - ``conflict-halted`` — non-loam file present; no write
        (force=False).
      - ``force-replaced`` — non-loam file backed up + replaced.
      - ``dry-run`` — would write but ``dry_run=True``.
    """

    surface: Literal[
        "pre-commit",
        "pre-push",
        "ci/github-actions",
        "ci/gitlab-ci",
        "ci/circleci",
        "pr-template",
    ]
    target_path: Path
    action: Literal[
        "created",
        "refreshed",
        "noop",
        "conflict-halted",
        "force-replaced",
        "dry-run",
    ]
    husky_routed: bool = False
    prior_version: str | None = None
    new_version: str = LOAM_PR_SAFETY_VERSION
    backup_path: Path | None = None
    detail: str = ""
    conflict_excerpt: str = ""  # populated on conflict-halted

    @property
    def is_conflict(self) -> bool:
        return self.action == "conflict-halted"

    @property
    def is_no_change(self) -> bool:
        return self.action in ("noop", "dry-run")

    @property
    def did_write(self) -> bool:
        return self.action in (
            "created",
            "refreshed",
            "force-replaced",
        )

    def to_audit_payload(self) -> dict:
        """Build the audit-log payload for this result.

        Per AC.PRSI.{1..8} — every install action audit-logs via
        Cycle 1's `write_audit_entry` with `event_kind: install_*`.
        """
        return {
            "surface": self.surface,
            "target_path": str(self.target_path),
            "action": self.action,
            "husky_routed": self.husky_routed,
            "prior_version": self.prior_version,
            "new_version": self.new_version,
            "backup_path": (
                str(self.backup_path) if self.backup_path else None
            ),
            "detail": self.detail,
        }


class InstallConflictError(PRSafetyError):
    """Raised when an installer's target has non-loam content.

    Per AC.PRSI.8 — conflict-halt with exit code 6 (CLI surface).
    Per Surface #3 — conflict-halt is the structurally-required
    behaviour absent ``--force``.

    Carries the ``InstallResult`` so callers can audit-log + emit
    structured halt payload to stderr.
    """

    def __init__(self, result: InstallResult, message: str = ""):
        self.result = result
        super().__init__(
            message
            or (
                f"install conflict at {result.target_path}: "
                f"non-loam content present (use --force to replace "
                f"with backup)"
            )
        )

    def to_result(self) -> InstallResult:
        """Return the underlying :class:`InstallResult` (for callers
        catching the exception in `--all` mode).
        """
        return self.result
